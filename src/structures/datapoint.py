GLOBAL_GRAVITY = 9.80655


class datapoint:

    def __init__(self, time, a = None, g = None, m = None):
        # raw data input
        self.time = time
        self.a = a
        self.g = g
        self.m = m
        self.a_true_device = None
        self.ypr_device = None

        # processed data
        self.a_norm = None
        self.g_norm = None

        # filtered data
        self.a_norm_smooth = None
        self.g_norm_smooth = None

        # heading quaternion
        self.q_local = None
        self.q_global = None
        self.roll_pitch_yaw = None

        # true xyz of acceleration
        self.a_true = None

        # position coordinates
        self.position = None

        # booleans for stepcount
        self.isStep = False
        self.gyrActive = True
        self.accActive = True

        # step length
        self.stepLength = 1

        # Special parameters for Brynes2016
        self.accNormNew = None
        self.gyrNormNew = None

    def scaleTime(self, startTime, factor = 1000):
        self.time = (self.time - startTime)/factor

    def computeAccNorm(self):
        self.a_norm = self.a.norm()

    def computeGyrNorm(self):
        self.g_norm = self.g.norm()

    def removeGravity(self):
        if self.a_norm is not None:
            self.a_norm -= GLOBAL_GRAVITY

    def convertGtoAcc(self):
        self.a *= GLOBAL_GRAVITY
        if self.a_norm is not None:
            self.a_norm *= GLOBAL_GRAVITY
