import numpy as np
from src.structures.thread import threatStructure

class stepLength(threatStructure):
    def __init__(self,inputQueue,outputQueue, algoType = 1):
        super(stepLength, self).__init__()
        self.target = self.run
        self.inputQueue = inputQueue
        self.outputQueue = outputQueue
        self.algoType = algoType

        # parameter for constant steplength
        self.constant_steplength = 0.75

        # parameters for steplength L = a * freq + b * variance + g
        self.a = 0.2
        self.b = 0.2
        self.g = 0.2

    def run(self):

        first_step = True
        step_datapoints = []

        while self.active:
            if len(self.inputQueue) != 0:
                dtp = self.inputQueue.dequeue()

                # last point
                if dtp == 'end':

                    self.outputQueue.enqueue('end')
                    self.active = False
                    return

                # METHOD 1: constant step length
                if self.algoType == 0:
                    if dtp.isStep:
                        dtp.stepLength = self.constant_steplength

                # METHOD 2: L = a * freq + b * variance + g
                elif self.algoType == 1:
                    if dtp.isStep:

                        # first step, assume steplength is 0.75 meter:
                        if first_step:
                            dtp.stepLength = self.constant_steplength
                            first_step = False

                        # additional steps
                        else:
                            # compute time difference between steps to determine frequency
                            dt = step_datapoints[-1].time - step_datapoints[0].time
                            freq = 1 / dt

                            # compute acc variance of all datapoints between current and previous step
                            var = np.std(np.array([x.a_norm for x in step_datapoints]))

                            # use frequency and variance to determine current step length
                            dtp.stepLength = self.a * freq + self.b * var + self.g

                            # clear datapoint list except for the last step
                            step_datapoints.clear()

                    # AFTER first step, start appending datapoints to compute next step length
                    if not first_step:
                        step_datapoints.append(dtp)

                # append each datapoint to the outputQueue
                self.outputQueue.enqueue(dtp)
