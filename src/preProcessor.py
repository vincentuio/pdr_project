from src.structures.queue import Queue
from src.structures.thread import threatStructure
from src.structures.datapoint import datapoint as dtp
import src.functions.vector as vctr

import math



class preprocessor(threatStructure):

    def __init__(self, inputQueue, outputQueue, convertG=True, samplingFreq = None):
        super(preprocessor, self).__init__()
        self.target = self.run
        self.inputQueue = inputQueue
        self.outputQueue = outputQueue
        self.convertG = convertG
        self.samplingFreq = samplingFreq

    def skip(self):
        while self.active:
            if len(self.inputQueue) != 0:
                dp = self.inputQueue.dequeue()
                if dp == 'end':
                    self.outputQueue.enqueue('end')
                    self.active = False
                    return
                self.outputQueue.enqueue(dp)

    def run(self):

        window = Queue()
        interpolation_count = 0

        # if sampling frequency is given, convert to ms
        if self.samplingFreq is not None:
            self.samplingFreq /= 1000.

        while self.active:

            if len(self.inputQueue) != 0:

                dp = self.inputQueue.dequeue()

                # last data point
                if dp == 'end':
                    self.outputQueue.enqueue('end')
                    self.active = False
                    return

                window.enqueue(dp)

                # convert unit G to m/s2
                if self.convertG:
                    dp.convertGtoAcc()

                # first data point
                if len(window) == 1:
                    self.outputQueue.enqueue(dp)

                # middle data points
                if len(window) > 1:

                    # convert times from ms to s
                    time1 = window.queue[0].time
                    time2 = window.queue[1].time

                    # if no sampling frequency is given, use first two points to determine frequency
                    if self.samplingFreq is None:
                        self.samplingFreq = 1. / (time2 - time1)

                    # Check how many interpolation points COULD lie in between the timestamps
                    for i in range(int(math.ceil((time2 - time1) * self.samplingFreq))):
                        interp_time = interpolation_count / self.samplingFreq

                        # If the interpolated time lies in this range, create the new data point and add it
                        if time1 <= interp_time < time2:
                            dp = linearInterp(window.queue[0], window.queue[1], interp_time)
                            dp.a_norm = vctr.norm(dp.a)
                            dp.g_norm = vctr.norm(dp.g)
                            self.outputQueue.enqueue(dp)
                            interpolation_count += 1
                    # Pop oldest element
                    window.dequeue()


def linearInterp(dp1, dp2, time):
    time1 = dp1.time
    time2 = dp2.time
    dt = (time2 - time1)

    slope_a = (dp2.a - dp1.a) / dt
    slope_g = (dp2.g - dp1.g) / dt
    slope_m = (dp2.m - dp1.m) / dt

    a = slope_a * (time - time1) + dp1.a
    g = slope_g * (time - time1) + dp1.g
    m = slope_m * (time - time1) + dp1.m

    return dtp(time, a=a, g=g, m=m)