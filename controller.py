import bisect
import skfuzzy as fuzz
import numpy as np
import skfuzzy.control as ctrl
import time
from heater_controller import _constrain


class LUT:
    def __init__(self) -> None:
        self.bp = []
        self.table = []

    def find(self, input: float) -> float:
        if len(self.bp) and len(self.table):
            if input >= self.bp[0] and input <= self.bp[-1]:
                idx = bisect.bisect_left(self.bp, input)
                output = self.table[idx - 1] + (self.table[idx] - self.table[idx - 1]) * (input - self.bp[idx - 1]) / (
                    self.bp[idx] - self.bp[idx - 1]
                )
                return output
        return -1


class Controller:
    def __init__(self) -> None:
        self.press_fb = 0
        self.press_sp = 0
        self.press_int = 0

    def run(self, timestamp: float, duty: float, press: float, temp: float = 0) -> float:
        pass

    def setPressSetpoint(self, setpoint):
        self.press_sp = setpoint


class SS(Controller):
    def __init__(self) -> None:
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

        self.integrated_press_past = 0.0
        self.press_err_past = 0.0
        self.x1_past = 0
        self.x2_past = 0
        self.x3_past = 0
        self.x4_past = 0
        self.x5_past = 0
        self.x6_past = 0

        self.u_steady_state = 0.2446
        self.x1_steady_state = 3.457e06
        self.x2_steady_state = -1.546e05
        self.x3_steady_state = 0.2175
        self.x4_steady_state = -0.2805
        self.x5_steady_state = 0.1553
        self.x6_steady_state = 0.476

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
        self.fuzzy_trigger = False

    def run(self, timestamp: float, duty: float, press: float, temp: float = 0) -> float:

        self.press_fb = self.pressLUT.find(press)

        if timestamp < 0.2:
            self.x1_past = 0
            self.x2_past = 0
            self.x3_past = 0
            self.x4_past = 0
            self.x5_past = 0
            self.x6_past = 0
            self.x1 = 0
            self.x2 = 0
            self.x3 = 0
            self.x4 = 0
            self.x5 = 0
            self.x6 = 0
        press_estimate = (
            -1.612876133705310e-06 * self.x1
            - 1.388759709639552e-06 * self.x2
            + 0.035875457390861 * self.x3
            + 0.347498852399868 * self.x4
            - 0.030532189729400 * self.x5
            - 0.288206336960354 * self.x6
        )

        press_err = self.u_steady_state - self.press_fb

        integrated_press = self.integrated_press_past + self.press_err_past * 0.25  # 積分器
        integrated_aug = self.KL * integrated_press

        self.integrated_press_past = integrated_press
        self.press_err_past = press_err

        press_est_err = press_estimate - self.press_fb  # 估測器誤差回授

        self.x1 = 0.999920615899177 * self.x1_past + 1121.76082548340 * duty + (-0.0429342294059150) * press_est_err
        self.x2 = 0.998226013220742 * self.x2_past + (-1121.48468411130) * duty + (-0.00165406863850045) * press_est_err
        self.x3 = (-0.781914434948315) * self.x3_past + 1.58439928733227 * duty + (-0.222898623775228) * press_est_err
        self.x4 = (
            (-0.384411449265332) * self.x4_past + (-1.58739336744947) * duty + (-0.549408061645774) * press_est_err
        )
        self.x5 = (
            0.131101849447955 * self.x5_past
            + 0.326002234363228 * self.x6_past
            + (-0.0828234008843126) * duty
            + (-0.417498782854124) * press_est_err
        )
        self.x6 = (
            (-0.326002234363228) * self.x5_past
            + 0.131101849447955 * self.x6_past
            + (1.89755072155957) * duty
            + (-0.0105720190036861) * press_est_err
        )

        self.feedback = (-1) * (
            self.K1 * (self.x1 - self.x1_steady_state)
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

        return self.feedback + self.u_steady_state + integrated_aug


class Fuzzy(Controller):
    def __init__(self) -> None:
        super().__init__()
        self.setPressSetpoint(6)

        self.control_period = 8.0  # unit: sec

        self.filter_len = 6.0  # unit: sec

        self.timestamp_last = 0.0
        self.revised = 0.0
        self.idx_press_history = 0.0
        self.output = 0.0

        # 參數範圍
        self.p_err_range = np.arange(-1, 1, 0.01, np.float32)
        self.duty_revision_range = np.arange(-0.1, 0.1, 0.001, np.float32)

        # 模糊變數
        self.p_err = ctrl.Antecedent(self.p_err_range, "p_err")
        self.duty_revision = ctrl.Consequent(self.duty_revision_range, "duty_revision")

        # 模糊集合&歸屬函數
        self.p_err["super hot"] = fuzz.trimf(self.p_err_range, [-1, -0.65, -0.2])
        self.p_err["very hot"] = fuzz.trimf(self.p_err_range, [-1, -0.3, -0.1])
        self.p_err["little hot"] = fuzz.trimf(self.p_err_range, [-0.2, -0.1, 0])
        self.p_err["mid"] = fuzz.trimf(self.p_err_range, [-0.1, 0, 0.1])
        self.p_err["little cold"] = fuzz.trimf(self.p_err_range, [0, 0.1, 0.2])
        self.p_err["very cold"] = fuzz.trimf(self.p_err_range, [0.1, 0.3, 1])
        self.p_err["super cold"] = fuzz.trimf(self.p_err_range, [0.2, 0.65, 1])

        self.duty_revision["super hot"] = fuzz.trimf(self.duty_revision_range, [-0.1, -0.065, -0.02])
        self.duty_revision["very hot"] = fuzz.trimf(self.duty_revision_range, [-0.1, -0.03, -0.01])
        self.duty_revision["little hot"] = fuzz.trimf(self.duty_revision_range, [-0.02, -0.01, 0])
        self.duty_revision["mid"] = fuzz.trimf(self.duty_revision_range, [-0.01, 0, 0.01])
        self.duty_revision["little cold"] = fuzz.trimf(self.duty_revision_range, [0, 0.01, 0.02])
        self.duty_revision["very cold"] = fuzz.trimf(self.duty_revision_range, [0.01, 0.03, 0.1])
        self.duty_revision["super cold"] = fuzz.trimf(self.duty_revision_range, [0.02, 0.065, 0.1])

        # 解模糊化——質心法
        self.duty_revision.defuzzify_method = "centroid"

        # 模糊規則
        self.rule1 = ctrl.Rule(
            antecedent=((self.p_err["super hot"])),
            consequent=self.duty_revision["super hot"],
            label="super hot",
        )
        self.rule2 = ctrl.Rule(
            antecedent=((self.p_err["very hot"])),
            consequent=self.duty_revision["very hot"],
            label="very hot",
        )
        self.rule3 = ctrl.Rule(
            antecedent=((self.p_err["little hot"])),
            consequent=self.duty_revision["little hot"],
            label="little hot",
        )
        self.rule4 = ctrl.Rule(antecedent=((self.p_err["mid"])), consequent=self.duty_revision["mid"], label="mid")
        self.rule5 = ctrl.Rule(
            antecedent=((self.p_err["little cold"])),
            consequent=self.duty_revision["little cold"],
            label="little cold",
        )
        self.rule6 = ctrl.Rule(
            antecedent=((self.p_err["very cold"])),
            consequent=self.duty_revision["very cold"],
            label="very cold",
        )
        self.rule7 = ctrl.Rule(
            antecedent=((self.p_err["super cold"])),
            consequent=self.duty_revision["super cold"],
            label="super cold",
        )
        self.press_history = [0 for _ in range(6 * 4)]

    def run(self, timestamp: float, duty: float, press: float, temp: float = 0):
        self.output = 0.0

        for i in range(int(self.filter_len) * 4 - 1):
            self.press_history[i] = self.press_history[i + 1]
        self.press_history[int(self.filter_len) * 4 - 1] = press
        self.press_fb = np.mean(self.press_history)

        if timestamp - self.timestamp_last >= self.control_period:

            self.timestamp_last = timestamp
            press_err = self.press_sp - self.press_fb

            press_err = _constrain(press_err, -1, 1)

            # 運作
            system = ctrl.ControlSystem(
                rules=[
                    self.rule1,
                    self.rule2,
                    self.rule3,
                    self.rule4,
                    self.rule5,
                    self.rule6,
                    self.rule7,
                ]
            )
            sim = ctrl.ControlSystemSimulation(system)
            sim.input["p_err"] = press_err
            # 計算
            try:
                sim.compute()
                self.output = sim.output["duty_revision"]
            except ValueError:
                print("Error at press err:", press_err)

        return self.output


class SS_Fuzzy(Controller):
    def __init__(self) -> None:
        super().__init__()
        self.SS = SS()
        self.Fuzzy = Fuzzy()
        self.idx = 0
        self.state_Flag = [True, False, False]

        self.duty_ss = 0.0
        self.duty_fuzzy = 0.0
        self.duty = 0.0

    def run(self, timestamp: float, duty: float, press: float, temp: float = 0) -> float:
        self.press_fb = press
        press_err = self.press_sp - self.press_fb

        if press_err < 0.2 and self.state_Flag[1] == False:
            self.duty_fuzzy = 0.0
            self.state_Flag[1] = True

        if press_err < 0.0 and self.state_Flag[2] == False:
            self.duty_fuzzy = 0.0
            self.state_Flag[2] = True

        self.idx = len(self.state_Flag) - self.state_Flag[::-1].index(True) - 1

        if self.idx == 0:
            self.duty_ss = self.SS.run(timestamp, duty, press)
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
