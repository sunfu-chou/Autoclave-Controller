import bisect


class Controller:
    def __init__(self):
        # PID
        self.press_fb = 0.0
        self.press_fb_n = 0.0
        self.temp_fb = 0.0
        self.temp_fb_n = 0.0
        self.setpoint_press = 0.0
        self.integrated_press = 0.0
        self.error_press = 0.0
        self.kp_press = 0.2
        self.ki_press = 0.0003
        self.kd_press = 0.0

        self.setpoint_temp = 0.0
        self.integrated_temp = 0.0
        self.error_temp = 0.0
        self.kp_temp = 0.5
        self.ki_temp = 0.000001
        self.kd_temp = 0.0

        self.bp_press = [0.4782, 0.6701, 1.045, 1.6158, 2.3332, 3.4363, 3.8378, 4.3367, 6.4171, 9.4081]
        self.table_press = [-1.7934, -2.2213, -2.6226, -3.2101, -3.78, -4.4052, -4.5385, -4.7455, -5.4985, -6.2973]
        self.bp_temp = [
            30.1872595638511,
            31.6409528432436,
            31.9704263189301,
            42.179105008502,
            63.6552080230948,
            63.6898877078096,
            63.7978469738978,
            64.4951212851203,
            85.4914717116415,
            111.485040539424,
            113.59430155581,
            113.695598993841,
            129.212866342344,
            139.138331793732,
            140.406275335562,
            144.483082776884,
            145.130889411771,
            151.665873380536,
            165.504586356226,
            165.547908995439,
        ]
        self.table_temp = [
            -2.40592041889992,
            -2.40193714475503,
            -1.96606164384795,
            -1.88280410083362,
            -1.83294240935630,
            -1.77167222675508,
            -1.70512504336492,
            -1.53387209202276,
            -1.26307193253703,
            -1.25128960532926,
            -1.22594106279314,
            -0.721695991192625,
            -0.328835604819290,
            -0.313099765124867,
            -0.306065933410559,
            -0.299478277011540,
            -0.0826493895778796,
            0.252424838633181,
            0.264867254792093,
            0.335251202542455,
        ][::-1]

        # SS
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
        self.KL = 4.94774704061055e-5
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
        # deplicated below
        self.x1_past = 0.0
        self.x2_past = 0.0
        self.x3_past = 0.0
        self.x4_past = 0.0
        self.x5_past = 0.0
        self.x6_past = 0.0

    def PID(self):
        self.error_press = self.setpoint_press - self.press_fb
        self.integrated_press += self.error_press * 0.25

        self.duty = self.kp_press * self.error_press + self.ki_press * self.integrated_press
        return self.duty

    def MISO_PID(self):
        self.error_press = self.setpoint_press - self.press_fb_n
        self.integrated_press += self.error_press * 0.25

        self.setpoint_temp = self.kp_press * self.error_press + self.ki_press * self.integrated_press

        self.error_temp = self.setpoint_temp - self.temp_fb_n
        self.integrated_temp += self.error_temp * 0.25
        self.duty = self.kp_temp * self.error_temp + self.ki_temp * self.integrated_temp
        return -self.duty

    def PressLUT(self, press):
        idx = bisect.bisect_left(self.bp_press, press)
        press_fb = self.table_press[idx - 1] + (self.table_press[idx] - self.table_press[idx - 1]) * (
            press - self.bp_press[idx - 1]
        ) / (self.bp_press[idx] - self.bp_press[idx - 1])
        return press_fb

    def TempLUT(self, temp):
        idx = bisect.bisect_left(self.bp_temp, temp)
        temp_fb = self.table_temp[idx - 1] + (self.table_temp[idx] - self.table_temp[idx - 1]) * (
            temp - self.bp_temp[idx - 1]
        ) / (self.bp_temp[idx] - self.bp_temp[idx - 1])
        return temp_fb

    def SS(self, timestamp, duty):
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
        integrated_aug = (-1) * self.KL * integrated_press

        self.integrated_press_past = integrated_press
        self.press_err_past = press_err

        press_est_err = press_estimate - self.press_fb  # 估測器誤差回授

        self.x1 = 0.999920615899239 * self.x1_past + 1013.34788210607 * duty + (-0.0429342294059150) * press_est_err
        self.x2 = 0.998226013220676 * self.x2_past + (-1012.53688592551) * duty + (-0.00165406863850045) * press_est_err
        self.x3 = (-0.781914434948314) * self.x3_past + 1.30835342044720 * duty + (-0.222898623775228) * press_est_err
        self.x4 = (
            (-0.384411449265331) * self.x4_past + (-1.30467015871265) * duty + (-0.549408061645774) * press_est_err
        )
        self.x5 = (
            0.131101849447955 * self.x5_past
            + 0.326002234363228 * self.x6_past
            + (0.249872166084580) * duty
            + (-0.417498782854124) * press_est_err
        )
        self.x6 = (
            (-0.326002234363228) * self.x5_past
            + 0.131101849447955 * self.x6_past
            + (1.68659769272441) * duty
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

        duty = self.feedback + self.u_steady_state + integrated_aug
        return duty
