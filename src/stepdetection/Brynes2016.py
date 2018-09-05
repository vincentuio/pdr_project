from src.structures.queue import Queue
from src.structures.thread import threatStructure
import math

# NOT WORKING YET!!
class Brynes2016(threatStructure):
    def __init__(self,inputQueue,outputQueue):
        super(Brynes2016, self).__init__()
        self.target = self.run

        self.inputQueue = inputQueue
        self.outputQueue = outputQueue
        self.typ = 999 #max_diff
        self.windowSize = 5
        self.threshold = 0
        self.minNrOfPoints = 10
        self.timeThreshold = 1 * 1000 # ms

        self.n = 0
        self.mean = 0
        self.std = 0
        self.intermediateQueue = Queue()
        self.intermediateQueue2 = Queue()

    def run(self):
        # Part A: peak function:
        if self.typ == 'max_diff':
            self.maxDiff()
        elif self.typ == 'mean_diff':
            self.meanDiff()
        elif self.typ == 'pan_tompkins':
            self.panTompkins()
        else:
            raise Exception('Unknown peak scorer type: ' + self.typ)

        # Part B: Scoring function:
        self.peakDetect()

        # Part C: Post-processing
        self.postProcess()

    def maxDiff(self):
        window = Queue()

        while True:
            if len(self.inputQueue) != 0:

                # Get next data point
                dp = self.inputQueue.dequeue()

                # Special case handling for end data point.
                if dp == 'end':
                    self.intermediateQueue.enqueue('end')
                    return

                # Add data point to list and queue
                window.enqueue(dp)

                # Once we reach the window size, do some processing!
                if len(window) == self.windowSize:

                    # Calculate peak score
                    midPoint = int(self.windowSize / 2)
                    maxDiffLeft = -100
                    maxDiffRight = -100

                    # Find max difference on left
                    for i in range(0, midPoint):
                        value = window[midPoint].a_norm_smooth - window[i].a_norm_smooth
                        if value > maxDiffLeft:
                            maxDiffLeft = value

                    # Find max difference on right
                    for i in range(midPoint + 1, len(window)):
                        value = window[midPoint].a_norm_smooth - window[i].a_norm_smooth
                        if value > maxDiffRight:
                            maxDiffRight = value

                    # Calculate peak score and create a new point
                    avg = (maxDiffRight + maxDiffLeft) / 2
                    window[midPoint].accNormNew = avg
                    self.intermediateQueue.enqueue(window[midPoint])
                    window.dequeue()

    def meanDiff(self):
        window = Queue()

        while True:
            if len(self.inputQueue) != 0:

                # Get next data point
                dp = self.inputQueue.dequeue()

                # Special case handling for end data point.
                if dp == 'end':
                    self.intermediateQueue.enqueue('end')
                    return

                # Add data point to list and queue
                window.enqueue(dp)

                # Once we reach the window size, do some processing!
                if len(window) == self.windowSize:

                    # Calculate peak score
                    midPoint = int(self.windowSize / 2)
                    diffLeft = 0
                    diffRight = 0

                    # Find total difference on left
                    for i in range(0, midPoint):
                        value = window[midPoint].a_norm_smooth - window[i].a_norm_smooth
                        diffLeft += value

                    # Find total difference on right
                    for i in range(midPoint + 1, len(window)):
                        value = window[midPoint].a_norm_smooth - window[i].a_norm_smooth
                        diffRight += value

                    # Calculate peak score and create a new point
                    avg = (diffLeft + diffRight) / (self.windowSize - 1)
                    window[midPoint].accNormNew = avg
                    self.intermediateQueue.enqueue(window[midPoint])
                    window.dequeue()


    def panTompkins(self):
        window = Queue()

        while True:
            if len(self.inputQueue) != 0:

                # Get next data point
                dp = self.inputQueue.dequeue()

                # Special case handling for end data point.
                if dp == 'end':
                    self.intermediateQueue.enqueue('end')
                    return

                # Add data point to list and queue
                window.enqueue(dp)

                # Once we reach the window size, do some processing!
                if len(window) == self.windowSize:

                    midPoint = int(self.windowSize / 2)

                    # Calculate mean of window
                    ssum = 0
                    for i in range(0,self.windowSize):
                        ssum += window[i].a_norm_smooth
                    mean = ssum / self.windowSize

                    new_mag = 0 if window[midPoint].a_norm_smooth - mean < 0 else window[midPoint].a_norm_smooth - mean
                    # Square it.
                    new_mag *= new_mag

                    # Calculate peak score and create a new point
                    window[midPoint].accNormNew=new_mag
                    self.intermediateQueue.enqueue(window[midPoint])
                    window.dequeue()

    def peakDetect(self):
        while True:
            if len(self.intermediateQueue) != 0:

                # Get next data point
                dp = self.intermediateQueue.dequeue()

                # Special case handling for end data point.
                if dp == 'end':
                    self.intermediateQueue2.enqueue('end')
                    return

                # Update statistics
                self.n += 1
                if self.n == 1:
                    # First data point
                    self.mean = dp.a_norm_smooth
                    self.std = 0
                elif self.n == 2:
                    # Second data point
                    o_mean = self.mean
                    self.mean = (dp.a_norm_smooth + self.mean) / 2.
                    self.std = math.sqrt((math.pow(dp.a_norm_smooth - self.mean, 2) + math.pow(o_mean - self.mean, 2)) / 2)
                else:
                    # Iteratively update mean and standard deviation
                    o_mean = self.mean
                    self.mean = (dp.a_norm_smooth + (self.n - 1) * self.mean) / self.n
                    self.std = math.sqrt(((self.n - 2) * math.pow(self.std, 2) / (self.n - 1)) + math.pow(o_mean - self.mean,2) +  math.pow(dp.a_norm_smooth - self.mean, 2) / self.n)
                if self.n > self.minNrOfPoints:
                    # Check if we are above the threshold
                    if (dp.a_norm_smooth - self.mean) > self.std * self.threshold:
                        # Declare this a peak
                        dp.isStep = True
                self.intermediateQueue2.enqueue(dp)



    def postProcess(self):

        self.windowQueue = Queue()

        while True:
            if len(self.intermediateQueue2) != 0:

                # Get next data point
                dp = self.intermediateQueue2.dequeue()

                # Special case handling for end data point.
                if dp == 'end':
                    self.lastPoint(self.intermediateQueue2)
                    return

                # If we have less than 2 points in the queue, just enqueue
                if dp.isStep:
                    if len(self.windowQueue) == 0:
                        self.windowQueue.enqueue(dp)
 #                       self.enqueue(dp)
                    else:
                        if (self.windowQueue[0].isStep):
                            if (dp.time - self.windowQueue[0].time) > self.timeThreshold:
                                for ii in range(len(self.windowQueue)):
                                    pop = self.windowQueue.dequeue()
                                    self.outputQueue.enqueue(pop)
                            elif dp.a_norm_smooth >= self.windowQueue[0].a_norm_smooth:
                                self.windowQueue[0].isStep = False
                                for ii in range(len(self.windowQueue)):
                                    pop = self.windowQueue.dequeue()
                                    self.outputQueue.enqueue(pop)
                            else:
                                dp.isStep = False
                        else:
                            for ii in range(len(self.windowQueue)):
                                pop = self.windowQueue.dequeue()
                                self.outputQueue.enqueue(pop)
                self.windowQueue.enqueue(dp)

    def lastPoint(self, window):
        # add remaining data points to queue
        for ii in range(len(window)):
            pop = window.dequeue()
            if pop.time > self.outputQueue[-1].time:
                self.outputQueue.enqueue(pop)
        self.outputQueue.enqueue('end')