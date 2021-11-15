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
        self.kp_press = 0.25
        self.ki_press = 0.00015
        self.kd_press = 0.0

        self.setpoint_temp = 0.0
        self.integrated_temp = 0.0
        self.error_temp = 0.0
        self.kp_temp = 0.5
        self.ki_temp = 0.000001
        self.kd_temp = 0.0

        self.bp_press = [0.3303, 0.7198, 1.2265, 1.9892, 2.8447, 3.8727, 4.7846, 5.3701, 5.9401, 6.5050]
        self.table_press = [2.0202, 4.5511, 7.044, 9.5392, 12.0301, 14.526, 16.9685, 19.4498, 21.8550, 24.3024]
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
        self.x1_past = 0
        self.x2_past = 0
        self.x3_past = 0
        self.x4_past = 0
        self.x5_past = 0
        self.x6_past = 0

        self.u_steady_state = 0.1195
        self.x1_steady_state = -1.539e06
        self.x2_steady_state = -5.518e04
        self.x3_steady_state = -0.01954
        self.x4_steady_state = 0.07864
        self.x5_steady_state = 2.364
        self.x6_steady_state = -0.384
        self.K1 = -0.00122424140197130
        self.K2 = -0.000532555571343705
        self.K3 = -1.19498414873539e-05
        self.K4 = -1.12534521766320e-05
        self.K5 = -0.00120580151903556
        self.K6 = 0.00127834779555466
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

        press_estimate = (
            -1.216549597987671e-05 * self.x1
            + 1.471140990491615e-05 * self.x2
            + 0.071087637176236 * self.x3
            + 0.454480600223431 * self.x4
            - 1.659858241875173e-05 * self.x5
            + 1.875880868871518e-05 * self.x6
        )

        press_err = press_estimate - self.press_fb

        self.x1 = 0.999962549618763 * self.x1_past + (-482.397408085760) * duty + (-0.707267860376471) * press_err
        self.x2 = 0.998955191473366 * self.x2_past + (-482.360920371058) * duty + (0.0372765564060354) * press_err
        self.x3 = (
            (-0.256582692790596) * self.x3_past
            + 0.882367801174803 * self.x4_past
            + (-0.785997168278096) * duty
            + (1.69823662861514) * press_err
        )
        self.x4 = (
            (-0.882367801174803) * self.x3_past
            + (-0.256582692790596) * self.x4_past
            + (0.682480660641171) * duty
            + (-1.08221378337274) * press_err
        )
        self.x5 = (
            (-0.999974148486798) * self.x5_past
            + 0.00719250631302813 * self.x6_past
            + (0.201183210316409) * duty
            + (1.53503616502204) * press_err
        )
        self.x6 = (
            (-0.00719250631302813) * self.x5_past
            + (-0.999974148486798) * self.x6_past
            + (-119.713005405615) * duty
            + (-1.69464121288180) * press_err
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

        duty = self.feedback + self.u_steady_state
        return duty
