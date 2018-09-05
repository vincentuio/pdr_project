from src.structures.queue import Queue
from src.structures.thread import threatStructure
from src.functions.rotation import *
import src.functions.vector as vctr
import time
import numpy as np

class orientation(threatStructure):

    def __init__(self,inputQueue,outputQueue):
        super(orientation, self).__init__()
        self.target = self.run
        
        self.inputQueue = inputQueue
        self.outputQueue = outputQueue

        self.q_global = np.array([1, 0, 0, 0])  # current quaternion


    def run(self):

        window = Queue()
        while self.active:

            if len(self.inputQueue) != 0:
                dtp = self.inputQueue.dequeue()

                # last point
                if dtp == 'end':

                    for _ in range(len(window)):
                        pop = window.dequeue()
                        if pop.q_local is None:
                            pop.roll_pitch_yaw = quaternion_to_roll_pitch_yaw(self.q_global)
                            pop.q_local = np.array([1,0,0,0])
                            pop.q_global = self.q_global
                        self.outputQueue.enqueue(pop)
                    self.outputQueue.enqueue('end')

                    self.active = False
                    return

                window.enqueue(dtp)

                # implement Kalman Filter below!

                # first point
                if len(window) == 1:
                    dtp.q_local = np.array([1,0,0,0])
                    dtp.q_global = self.q_global
                    dtp.roll_pitch_yaw = np.array([0,0,0])

                # intermediate points
                else:
                    # average gyro between two points and time in s (convert from ms)
                    g_av = (window[1].g + window[0].g) / 2
                    dt = (window[1].time - window[0].time) / 1000

                    # compute local and global quaternion for single data point
                    q_local = vctr.normalise(angular_rate_to_quaternion_rotation(g_av, dt))
                    self.q_global = vctr.normalise(quaternion_product(self.q_global, q_local))
                    roll_pitch_yaw = quaternion_to_roll_pitch_yaw(self.q_global)

                    window[1].q_local = q_local
                    window[1].q_global = self.q_global
                    window[1].roll_pitch_yaw = roll_pitch_yaw

                    # append oldest point to output queue
                    pop = window.dequeue()
                    self.outputQueue.enqueue(pop)
            else:
                time.sleep(0.05)

    # fancy way of interpolating between multiple descrete points (not used)
    def average_rotation_old(self, window):
        gx = [x.gx for x in window]
        gy = [x.gy for x in window]
        gz = [x.gz for x in window]
        t = [x.time for x in window]
        t1 = window[self.midpoint-1].time
        t2 = window[self.midpoint].time
        dt = t2 - t1

        p = np.polyfit(t,gx, len(t) -1)
        P = np.poly1d(np.polyint(p))
        gx_av = (P(t2) - P(t1)) / dt

        p = np.polyfit(t,gy, len(t) -1)
        P = np.poly1d(np.polyint(p))
        gy_av = (P(t2) - P(t1)) / dt

        p = np.polyfit(t,gz, len(t) -1)
        P = np.poly1d(np.polyint(p))
        gz_av = (P(t2) - P(t1)) / dt

        return np.array([gx_av, gy_av, gz_av]), dt






