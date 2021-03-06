import bisect
from numpy.linalg import LinAlgError
import skfuzzy as fuzz
import numpy as np
import skfuzzy.control as ctrl
from heater_controller import _constrain


class LUT:
    """Look up table for converting sensor feedback data to another range
    """
    def __init__(self) -> None:
        """The method of LUT
        """
        
        # data in range
        self.bp = []
        
        # data out range
        self.table = []

    def find(self, input: float) -> float:
        """To map data in to data out range

        Args:
            input (float): Data in

        Returns:
            float: Data out
        """
        if len(self.bp) and len(self.table):
            if input < self.bp[0]:
                return 0
            if input > self.bp[-1]:
                return self.table[-1]

            idx = bisect.bisect_left(self.bp, input)
            output = self.table[idx - 1] + (self.table[idx] - self.table[idx - 1]) * (input - self.bp[idx - 1]) / (
                self.bp[idx] - self.bp[idx - 1]
            )
            return output
        return -1


class Controller:
    """Parent Class Controller
    """
    def __init__(self) -> None:
        """The init method of Controller
        """
        self.press_fb = 0
        self.press_sp = 0
        self.press_int = 0

    def run(self, timestamp: float, duty: float, press: float, temp: float = 0) -> float:
        """Run controller

        Args:
            timestamp (float): Now time
            duty (float): last output duty cycle
            press (float): press feedback
            temp (float, optional): temperature feedback. Defaults to 0.

        Returns:
            float: output duty cycle.
        """
        pass

    def setPressSetpoint(self, setpoint: float) -> float:
        """Set press setpoint

        Args:
            setpoint (float): setpoint

        Returns:
            float: setpoint
        """
        self.press_sp = setpoint
        return self.press_sp


class SS(Controller):
    """State space Controller(Controller)
    """
    def __init__(self) -> None:
        """The init method of State space Controller
        """
        super().__init__()

        self.pressLUT = LUT()

        self.pressLUT.bp = [
            0.4782,
            0.6701,
            1.045,
            1.6158,
            2.3332,
            3.4363,
            3.8378,
            4.3367,
            6.4171,
            9.4081,
        ]
        self.pressLUT.table = [
            -1.7934,
            -2.2213,
            -2.6226,
            -3.2101,
            -3.78,
            -4.4052,
            -4.5385,
            -4.7455,
            -5.4985,
            -6.2973,
        ]
        self.A = [[0.999920615899239,0,0,0,0,0],
                  [0,0.998226013220676,0,0,0,0],
                  [0,0,-0.781914434948314,0,0,0],
                  [0,0,0,-0.384411449265331,0,0],
                  [0,0,0,0,0.131101849447955,0.326002234363228],
                  [0,0,0,0,-0.326002234363228,0.131101849447955]]
        
        self.B = [[1.013347882106066e+03],
                  [-1.012536885925512e+03],
                  [1.308353420447204],
                  [-1.304670158712651],
                  [0.249872166084580],
                  [1.686597692724413]]
        self.K_dc = -1/21.86
        self.integrated_press_past = 0.0
        self.press_err_past = 0.0
        self.x1_past = 0
        self.x2_past = 0
        self.x3_past = 0
        self.x4_past = 0
        self.x5_past = 0
        self.x6_past = 0
        
        self.u_steady_state = 0.0
        self.x1_steady_state = 0.0
        self.x2_steady_state = 0.0
        self.x3_steady_state = 0.0
        self.x4_steady_state = 0.0
        self.x5_steady_state = 0.0
        self.x6_steady_state = 0.0

        self.KL = 4.94774704061055e-3
        self.K1 = 6.850957196992270e-04
        self.K2 = -3.013768145255261e-04
        self.K3 = -2.252202811353843e-06
        self.K4 = 5.138524754988651e-07
        self.K5 = -2.208657973554493e-07
        self.K6 = 2.858375134903800e-07
        self.x1 = 0.0
        self.x2 = 0.0
        self.x3 = 0.0
        self.x4 = 0.0
        self.x5 = 0.0
        self.x6 = 0.0
        self.feedback = 0.0
        
        self.antiwindup_fb = 0.0
        self.output = 0.0
        
        self.filter_len = 4.0 # unit: second
        self.press_history = [0 for _ in range(4*4)]
        
        self.x_initial = 0
        self.ss_flag = True
        self.press_fb_l = 0.0

    def run(self, timestamp: float, duty: float, press: float, temp: float = 0) -> float:
        """Run controller

        Args:
            timestamp (float): Now time
            duty (float): last output duty cycle
            press (float): press feedback
            temp (float, optional): temperature feedback. Defaults to 0.

        Returns:
            float: output duty cycle.
        """
        for i in range(int(self.filter_len) * 4 - 1):
            self.press_history[i] = self.press_history[i + 1]
        self.press_history[int(self.filter_len) * 4 - 1] = press
        self.press_fb = np.mean(self.press_history)
        self.press_fb_l = self.pressLUT.find(self.press_fb)

        if self.press_fb > 0.5 and self.ss_flag == True:
            self.ss_flag = False
            try:
                self.x_initial = np.linalg.solve(np.identity(6) - np.array(self.A), np.multiply(np.array(self.B), self.press_fb_l * self.K_dc))

            except LinAlgError:
                self.x_initial = [0 for _ in range(6)]
                print('solve error')

            self.x1_past = self.x_initial[0]
            self.x2_past = self.x_initial[1]
            self.x3_past = self.x_initial[2]
            self.x4_past = self.x_initial[3]
            self.x5_past = self.x_initial[4]
            self.x6_past = self.x_initial[5]
            self.x1 = 0
            self.x2 = 0
            self.x3 = 0
            self.x4 = 0
            self.x5 = 0
            self.x6 = 0
            
        press_estimate = (
            - 1.612876133705310e-06 * self.x1
            - 1.388759709639552e-06 * self.x2
            + 0.035875457390861 * self.x3
            + 0.347498852399868 * self.x4
            - 0.030532189729400 * self.x5
            - 0.288206336960354 * self.x6
        )

        press_err = self.u_steady_state / self.K_dc - self.press_fb_l

        integrated_press = self.integrated_press_past + self.press_err_past * 0.25 + (-1) * self.antiwindup_fb # ?????????
        integrated_aug = self.KL * integrated_press * (-1)

        self.integrated_press_past = integrated_press
        self.press_err_past = press_err
        
        #try:
        #    x_now = np.linalg.solve(np.identity(6) - np.array(self.A), np.multiply(np.array(self.B), self.pressLUT.find(press)*self.K_dc))

        #except LinAlgError:
        #    x_now = [0 for _ in range(6)]
        #    print('solve error')
        #if self.press_fb > -1.7935:
        press_est_err = press_estimate - self.press_fb_l  # ?????????????????????
        self.x1 = 0.999920615899239 * self.x1_past + 1013.34788210607 * duty   + (-0.0429342294059150)  * press_est_err
        self.x2 = 0.998226013220676 * self.x2_past + (-1012.53688592551) * duty   + (-0.00165406863850045)  *press_est_err
        self.x3 = (-0.781914434948314) * self.x3_past + 1.30835342044720 * duty   + (-0.222898623775228)  *  press_est_err
        self.x4 = (-0.384411449265331) * self.x4_past + (-1.30467015871265) * duty   + (-0.549408061645774)  *  press_est_err
        self.x5 = (
            0.131101849447955 * self.x5_past + 0.326002234363228 * self.x6_past + (0.249872166084580) * duty   + (-0.417498782854124)  *  press_est_err
        )
        self.x6 = (
            (-0.326002234363228) * self.x5_past + 0.131101849447955 * self.x6_past + (1.68659769272441) * duty   + (-0.0105720190036861)  * press_est_err
        )
 
        #else:
        #    self.x1 = x_now[0]
        #    self.x2 = x_now[1]
        #    self.x3 = x_now[2]
        #    self.x4 = x_now[3]
        #    self.x5 = x_now[4]
        #    self.x6 = x_now[5]

        self.feedback = (-1) * (
            + self.K1 * (self.x1 - self.x1_steady_state)
            + self.K2 * (self.x2 - self.x2_steady_state)
            + self.K3 * (self.x3 - self.x3_steady_state)
            + self.K4 * (self.x4 - self.x4_steady_state)
            + self.K5 * (self.x5 - self.x5_steady_state)
            + self.K6 * (self.x6 - self.x6_steady_state)
        )
        self.x1_past = self.x1
        self.x2_past = self.x2
        self.x3_past = self.x3
        self.x4_past = self.x4
        self.x5_past = self.x5
        self.x6_past = self.x6
        
        #if abs(duty - self.u_steady_state) > 0.001:
        #    self.feedback = 0.0
        
        if integrated_aug - duty > 0.0:
            self.antiwindup_fb = (integrated_aug - duty) * (-218.6)
        else:
            self.antiwindup_fb = 0.0
            
        if press <= 0.5:
            self.feedback = 1.0
            integrated_aug = 0.0
        
        return self.feedback + self.u_steady_state + integrated_aug
    
    def setPressSetpoint(self, setpoint):
        """Set press setpoint and Convert setpress to state variable

        Args:
            setpoint (float): setpoint

        Returns:
            float: setpoint
        """
        self.u_steady_state = self.pressLUT.find(setpoint) * self.K_dc

        try:
            x = np.linalg.solve(np.identity(6) - np.array(self.A), np.multiply(np.array(self.B), self.u_steady_state))
        except LinAlgError:
            x = [0 for _ in range(6)]
            print('solve error')
        
        self.x1_steady_state = x[0]
        self.x2_steady_state = x[1]
        self.x3_steady_state = x[2]
        self.x4_steady_state = x[3]
        self.x5_steady_state = x[4]
        self.x6_steady_state = x[5]
        return super().setPressSetpoint(setpoint)


class Fuzzy(Controller):
    """Fuzzy Controller(Controller)
    """
    def __init__(self) -> None:
        """The init method of Fuzzy Controller
        """
        super().__init__()
        self.setPressSetpoint(6.0)

        self.press_last = 0.0
        self.press_dif = 0.0
        
        self.control_period = 120.0  # unit: sec

        self.filter_len = 6.0  # unit: sec

        self.timestamp_last = 0.0
        self.revised = 0.0
        self.output = 0.0

        # ????????????
        self.p_err_range = np.arange(-1, 1, 2/15, np.float32)
        self.duty_revision_range = np.arange(-0.04, 0.04, 0.0008, np.float32)

        # ????????????
        self.p_err = ctrl.Antecedent(self.p_err_range, "p_err")
        self.duty_revision = ctrl.Consequent(self.duty_revision_range, "duty_revision")

        # ????????????&????????????
        self.p_err["hot6"] = fuzz.trapmf(self.p_err_range, [-1.5, -1.5, -0.9, -0.75])
        self.p_err["hot5"] = fuzz.trimf(self.p_err_range, [-0.9, -0.8, -0.3])
        self.p_err["hot4"] = fuzz.trimf(self.p_err_range, [-0.4, -0.3, -0.2])
        self.p_err["hot3"] = fuzz.trimf(self.p_err_range, [-0.3, -0.2, -0.2])
        self.p_err["hot2"] = fuzz.trimf(self.p_err_range, [-0.25, -0.15, -0.05])
        self.p_err["hot1"] = fuzz.trimf(self.p_err_range, [-0.1, -0.1, 0])
        self.p_err["mid"] = fuzz.trimf(self.p_err_range, [-0.05, 0, 0.05])
        self.p_err["cold1"] = fuzz.trimf(self.p_err_range, [0, 0.1, 0.1])
        self.p_err["cold2"] = fuzz.trimf(self.p_err_range, [0.05, 0.15, 0.25])
        self.p_err["cold3"] = fuzz.trimf(self.p_err_range, [0.2, 0.2, 0.3])
        self.p_err["cold4"] = fuzz.trimf(self.p_err_range, [0.2, 0.3, 0.4])
        self.p_err["cold5"] = fuzz.trimf(self.p_err_range, [0.3, 0.8, 0.9])
        self.p_err["cold6"] = fuzz.trapmf(self.p_err_range, [0.75, 0.9, 1.5, 1.5])

        self.duty_revision["hot6"] = fuzz.trapmf(self.duty_revision_range, [-0.06, -0.06, -0.04, -0.032])
        self.duty_revision["hot5"] = fuzz.trimf(self.duty_revision_range, [-0.06, -0.036, -0.03])
        self.duty_revision["hot4"] = fuzz.trimf(self.duty_revision_range, [-0.06, -0.02, -0.015])
        self.duty_revision["hot3"] = fuzz.trimf(self.duty_revision_range, [-0.04, -0.012, -0.008])
        self.duty_revision["hot2"] = fuzz.trimf(self.duty_revision_range, [-0.012, -0.008, -0.004])
        self.duty_revision["hot1"] = fuzz.trimf(self.duty_revision_range, [-0.008, -0.004, 0])
        self.duty_revision["mid"] = fuzz.trimf(self.duty_revision_range, [-0.004, 0, 0.004])
        self.duty_revision["cold1"] = fuzz.trimf(self.duty_revision_range, [0, 0.004, 0.008])
        self.duty_revision["cold2"] = fuzz.trimf(self.duty_revision_range, [0.004, 0.008, 0.012])
        self.duty_revision["cold3"] = fuzz.trimf(self.duty_revision_range, [0.008, 0.012, 0.04])
        self.duty_revision["cold4"] = fuzz.trimf(self.duty_revision_range, [0.015, 0.02, 0.06])
        self.duty_revision["cold5"] = fuzz.trimf(self.duty_revision_range, [0.03, 0.036, 0.06])
        self.duty_revision["cold6"] = fuzz.trapmf(self.duty_revision_range, [0.032, 0.04, 0.06, 0.06])

        # ???????????????????????????
        self.duty_revision.defuzzify_method = "centroid"

        # ????????????
        self.rule1 = ctrl.Rule(antecedent=((self.p_err["hot6"])),consequent=self.duty_revision["hot6"],label="hot6")
        self.rule2 = ctrl.Rule(antecedent=((self.p_err["hot5"])),consequent=self.duty_revision["hot5"],label="hot5")
        self.rule3 = ctrl.Rule(antecedent=((self.p_err["hot4"])),consequent=self.duty_revision["hot4"],label="hot4")
        self.rule4 = ctrl.Rule(antecedent=((self.p_err["hot3"])),consequent=self.duty_revision["hot3"],label="hot3")
        self.rule5 = ctrl.Rule(antecedent=((self.p_err["hot2"])),consequent=self.duty_revision["hot2"],label="hot2")
        self.rule6 = ctrl.Rule(antecedent=((self.p_err["hot1"])),consequent=self.duty_revision["hot1"],label="hot1")
        self.rule7 = ctrl.Rule(antecedent=((self.p_err["mid"])), consequent=self.duty_revision["mid"], label="mid")
        self.rule8 = ctrl.Rule(antecedent=((self.p_err["cold1"])),consequent=self.duty_revision["cold1"],label="cold1")
        self.rule9 = ctrl.Rule(antecedent=((self.p_err["cold2"])),consequent=self.duty_revision["cold2"],label="cold2")
        self.rule10 = ctrl.Rule(antecedent=((self.p_err["cold3"])),consequent=self.duty_revision["cold3"],label="cold3")
        self.rule11 = ctrl.Rule(antecedent=((self.p_err["cold4"])),consequent=self.duty_revision["cold4"],label="cold4")
        self.rule12 = ctrl.Rule(antecedent=((self.p_err["cold5"])),consequent=self.duty_revision["cold5"],label="cold5")
        self.rule13 = ctrl.Rule(antecedent=((self.p_err["cold6"])),consequent=self.duty_revision["cold6"],label="cold6")
        
        self.press_history = [0 for _ in range(6 * 4)]
        
        self.gain_output = 1

    def run(self, timestamp: float, duty: float, press: float, temp: float = 0):
        """Run controller

        Args:
            timestamp (float): Now time
            duty (float): last output duty cycle
            press (float): press feedback
            temp (float, optional): temperature feedback. Defaults to 0.

        Returns:
            float: output duty cycle.
        """
        sgn = 1
        self.output = 0.0
        trigger_dev_range = self.press_sp / 12 #????????????????????????
        trigger_dev_closed = self.press_sp / 200 #????????????????????????
        
        for i in range(int(self.filter_len) * 4 - 1):
            self.press_history[i] = self.press_history[i + 1]
        self.press_history[int(self.filter_len) * 4 - 1] = press
        self.press_fb = np.mean(self.press_history)

        if timestamp - self.timestamp_last >= self.control_period:
            self.timestamp_last = timestamp
            self.press_dif =  (self.press_fb - self.press_last) / self.control_period
            self.press_last = self.press_fb
            
            press_err = self.press_sp - self.press_fb

            press_err = _constrain(press_err, -1, 1)

            if press_err * self.press_dif >= 0.0:
                if trigger_dev_closed < abs(press_err) < trigger_dev_range:
                    sgn = -0.75
                else:
                    sgn = 0
                
            # ??????
            system = ctrl.ControlSystem(
                rules=[
                    self.rule1,
                    self.rule2,
                    self.rule3,
                    self.rule4,
                    self.rule5,
                    self.rule6,
                    self.rule7,
                    self.rule8,
                    self.rule9,
                    self.rule10,
                    self.rule11,
                    self.rule12,
                    self.rule13,
                ]
            )
            sim = ctrl.ControlSystemSimulation(system)
            sim.input["p_err"] = press_err
            # ??????
            try:
                sim.compute()
                self.output = sim.output["duty_revision"]
            except ValueError:
                print("Error at press err:", press_err)

        return self.output * self.gain_output * sgn


class SS_Fuzzy(Controller):
    """Integrate SS and Fuzzy Controller(Controller)
    """
    def __init__(self) -> None:
        """The init method of State space and Fuzzy Controller
        """
        super().__init__()
        self.SS = SS()
        self.Fuzzy = Fuzzy()
        self.idx = 0
        self.state_Flag = [True, False, False]

        self.duty_ss = 0.0
        self.duty_fuzzy = 0.0
        self.duty = 0.0

    def run(self, timestamp: float, duty: float, press: float, temp: float = 0) -> float:
        """Run controller

        Args:
            timestamp (float): Now time
            duty (float): last output duty cycle
            press (float): press feedback
            temp (float, optional): temperature feedback. Defaults to 0.

        Returns:
            float: output duty cycle.
        """
        self.press_fb = press
        press_err = self.press_sp - self.press_fb
        trigger_range = self.press_sp / 10 #??????????????????

        if press_err < trigger_range and self.state_Flag[1] == False:
            self.duty_fuzzy = 0.0
            self.state_Flag[1] = True

        if press_err < trigger_range and self.state_Flag[2] == False:
            self.duty_fuzzy = 0.0
            self.state_Flag[2] = True

        self.idx = len(self.state_Flag) - self.state_Flag[::-1].index(True) - 1

        if self.idx == 0:
            self.duty_ss = self.SS.run(timestamp, duty, press)
            self.Fuzzy.run(timestamp, duty, press)
            self.duty_fuzzy = 0.0
        elif self.idx == 1:
            self.duty_ss = self.SS.run(timestamp, duty, press)
            self.duty_fuzzy += self.Fuzzy.run(timestamp, duty, press)
        elif self.idx == 2:
            self.duty_ss = duty
            self.duty_fuzzy = self.Fuzzy.run(timestamp, duty, press)
        else:
            self.duty_ss = 0.0
            self.duty_fuzzy = 0.0

        self.duty = self.duty_ss + self.duty_fuzzy
        return self.duty

    def setPressSetpoint(self, setpoint):
        """Set press setpoint

        Args:
            setpoint (float): setpoint

        Returns:
            float: setpoint
        """
        super().setPressSetpoint(setpoint)
        self.SS.setPressSetpoint(setpoint)
        self.Fuzzy.setPressSetpoint(setpoint)


# class Controller:
#     def __init__(self):
# PID
# self.press_fb = 0.0
# self.press_fb_n = 0.0
# self.temp_fb = 0.0
# self.temp_fb_n = 0.0
# self.setpoint_press = 0.0
# self.integrated_press = 0.0
# self.error_press = 0.0
# self.kp_press = 0.2
# self.ki_press = 0.0003
# self.kd_press = 0.0

# self.setpoint_temp = 0.0
# self.integrated_temp = 0.0
# self.error_temp = 0.0
# self.kp_temp = 0.5
# self.ki_temp = 0.000001
# self.kd_temp = 0.0


# def PID(self):
#     self.error_press = self.setpoint_press - self.press_fb
#     self.integrated_press += self.error_press * 0.25

#     self.duty = self.kp_press * self.error_press + self.ki_press * self.integrated_press
#     return self.duty

# def MISO_PID(self):
#     self.error_press = self.setpoint_press - self.press_fb_n
#     self.integrated_press += self.error_press * 0.25

#     self.setpoint_temp = self.kp_press * self.error_press + self.ki_press * self.integrated_press

#     self.error_temp = self.setpoint_temp - self.temp_fb_n
#     self.integrated_temp += self.error_temp * 0.25
#     self.duty = self.kp_temp * self.error_temp + self.ki_temp * self.integrated_temp
#     return -self.duty
