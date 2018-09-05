from src.structures.queue import Queue
from src.structures.thread import threatStructure
import numpy as np
import time

class Lee2015(threatStructure):
    def __init__(self, inputQueue, outputQueue):
        super(Lee2015, self).__init__()
        self.target = self.run

        # external parameters
        self.inputQueue = inputQueue
        self.outputQueue = outputQueue
        self.alfa = 10.
        self.beta = 1.
        self.dt_max = 1.5 * 1000. # max time (ms) in between steps (resets mean and std to NONE)
        self.min_dt_points = 5.  # Min nr of points for dt mean and std calculation

        # internal parameters
        self.dtp_peak = None
        self.dtp_valley = None
        self.peaks = []
        self.valleys = []
        self.accList = []
        self.dt_peak = 0
        self.dt_valley = 0
        self.time_last_peak_or_valley = 0
        self.state_prev = 'none'  # 0, 1, 2 (none, peak, valley)
        self.mean = None
        self.std = 0
        self.step = 0

    def run(self):

        window = Queue()
        step_window = Queue()
        step_index = None

        while self.active:

            if len(self.inputQueue) != 0:

                dtp = self.inputQueue.dequeue()

                # last point
                if dtp == 'end':

                    # confirm last step
                    if step_index is not None:
                        step_window[step_index].isStep = True

                    # add remaining data points to queue
                    for ii in range(len(step_window)):
                        pop = step_window.dequeue()
                        self.outputQueue.enqueue(pop)
                    self.outputQueue.enqueue(window[-1])

                    self.outputQueue.enqueue('end')
                    self.active = False
                    return

                window.enqueue(dtp)

                # first point
                if len(window) == 1:
                    self.outputQueue.enqueue(dtp)

                # intermediate points
                if len(window) == 3:

                    self.accList.append(window[1].a_norm_smooth)

                    # INSERT extra statement here to consider points only above a certain 'active' threshold
                    if True:  # window[1].accActive:

                        # state: 'peak', 'valley' or 'none'
                        state = self.detectState(window)

                        if state == 'peak':
                            # initial peak
                            if self.state_prev == 'none':
                                self.updatePeak(window[1])
                                # self.peaks.append(window[1])

                            # previous is valley AND new peak is above minimum time threshold
                            elif (self.state_prev == 'valley') and (window[1].time - self.dtp_peak.time > self.dt_peak):
                                self.updatePeak(window[1])
                                self.updateMean()

                            # previous is peak AND is within time threshold AND new peak has larger acc norm
                            elif (self.state_prev == 'peak') \
                                    and (window[1].time - self.dtp_peak.time <= self.dt_peak) \
                                    and (window[1].a_norm_smooth > self.dtp_peak.a_norm_smooth):
                                self.updatePeak(window[1], replace=True)

                        elif state == 'valley':
                            # previous is peak AND initial valley
                            if (self.state_prev == 'peak') and (self.dtp_valley is None):
                                self.updateValley(window[1])
                                # potential step: store index in step_window
                                step_index = len(step_window)
                                #window[1].isStep = True
                                self.updateMean()

                            # previous is peak AND new valley is above minimum time threshold
                            elif (self.state_prev == 'peak') \
                                    and (window[1].time - self.dtp_valley.time > self.dt_valley):
                                self.updateValley(window[1])
                                # potential step: store index in step_window
                                step_index = len(step_window)
                                #window[1].isStep = True
                                self.updateMean()

                            # previous is valley AND is within time threshold AND new valley has lower acc norm
                            elif (self.state_prev == 'valley') \
                                    and (window[1].time - self.dtp_valley.time <= self.dt_valley) \
                                    and (window[1].a_norm_smooth < self.dtp_valley.a_norm_smooth):
                                # change potential step index:
                                step_index = len(step_window)
                                self.updateValley(window[1], replace=True)

                    # compute standard deviation of acc:
                    self.std = np.std(np.array(self.accList))

                    # add data point to the step window
                    step_window.enqueue(window[1])

                    # if there is a potential step
                    if step_index is not None:

                        # if last valley is > time threshold, confirm step
                        if window[1].time - step_window[step_index].time > self.dt_valley:
                            step_window[step_index].isStep = True

                            # append all data point up to and including step to output queue
                            for ii in range(step_index + 1):
                                pop = step_window.dequeue()
                                self.outputQueue.enqueue(pop)

                            step_index = None
                    # print(self.mean, self.std, self.dt_peak, self.dt_valley)

                    # reset counter if there has been no activity for some time
                    if window[1].time - self.time_last_peak_or_valley > self.dt_max:
                        self.resetParams()

                    window.dequeue()
            else:
                time.sleep(0.05)

    def detectState(self, window):
        a_0 = window[0].a_norm_smooth
        a_1 = window[1].a_norm_smooth
        a_2 = window[2].a_norm_smooth

        # check for local maximum
        if a_1 > max([a_0, a_2]):
            if self.mean is None:
                return 'peak'
            elif a_1 > self.mean + self.std / self.alfa:
                return 'peak'

        elif a_1 < min([a_0, a_2]):
            if self.mean is None:
                return 'valley'
            elif a_1 < self.mean - self.std / self.alfa:
                return 'valley'
        return 'none'

    def updatePeak(self, dtp, replace=False):
        # append new peak to peak list for time threshold calculation
        if replace:
            self.peaks[-1] = dtp
        else:
            self.peaks.append(dtp)

        # update mean_p and std_p and compute dt_peak
        self.dt_peak = self.timeThreshold_update(self.peaks)

        # set last peak and last state
        self.dtp_peak = dtp
        self.time_last_peak_or_valley = dtp.time
        self.state_prev = 'peak'

    def updateValley(self, dtp, replace=False):
        # append new valley to valley list for time threshold calculation
        if replace:
            self.valleys[-1] = dtp
        else:
            self.valleys.append(dtp)

        # update mean_p and std_p and compute dt_peak
        self.dt_valley = self.timeThreshold_update(self.valleys)

        # set last peak and last state
        self.dtp_valley = dtp
        self.time_last_peak_or_valley = dtp.time
        self.state_prev = 'valley'

    def updateMean(self):
        self.mean = (self.dtp_peak.a_norm_smooth + self.dtp_valley.a_norm_smooth) / 2.

    def timeThreshold_update(self, inputlist):
        if len(inputlist) > 1:
            diff = np.diff(np.array([x.time for x in inputlist]))
            return np.average(diff) - np.std(diff) / self.beta
        else:
            return 0

    def resetParams(self):
        self.mean = None
        self.std = 0
        self.dtp_peak = None
        self.dtp_valley = None
        self.peaks.clear()
        self.valleys.clear()
        self.accList.clear()
        self.time_last_peak_or_valley = 0
        self.dt_peak = 0
        self.dt_valley = 0
        self.state_prev = 'none'
        self.step = 0
        return
