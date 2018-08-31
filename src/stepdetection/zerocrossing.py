from src.structures.queue import Queue
from src.structures.thread import threatStructure

GLOBAL_GRAVITY = 9.80655

class zerocrossing(threatStructure):
    
    # ! returns a new Queue with non-equidistant datapoints (only zero crossings)
    def __init__(self,inputQueue,outputQueue):
        super(zerocrossing, self).__init__()
        self.target = self.run

        self.inputQueue = inputQueue
        self.outputQueue = outputQueue
        self.windowSize = 3
        self.sensorType = 'acc'

        self.midPoint = int(self.windowSize / 2)

    def run(self):

        window = Queue()

        while self.active:

            if len(self.inputQueue) != 0:

                dtp = self.inputQueue.dequeue()

                # Last point
                if dtp == 'end':
                    # remove points left from midpoint
                    for ii in range(len(window)):
                        pop = window.dequeue()
                        if pop.time > self.outputQueue[-1].time:
                            self.outputQueue.enqueue(pop)
                    self.outputQueue.enqueue('end')
                    self.active = False
                    return

                # remove GLOBAL_GRAVITY from acc_norm_smooth
                dtp.a_norm_smooth -= GLOBAL_GRAVITY

                window.enqueue(dtp)

                # enqueue first points to output
                if len(window) <= self.midPoint:
                    self.outputQueue.enqueue(dtp)

                # compute if window midpoint is step
                if len(window) == self.windowSize:
                    left = []
                    right = []
                    
                    # divide the window in pre- and post datapoints
                    for i in range(self.midPoint):
                        left.append(window[i])                        
                    for i in range(self.midPoint,self.windowSize):
                        right.append(window[i])
                    
                    # check if window has a zero crossing in the middle
                    if all(x.a_norm_smooth <= 0 for x in left) and all(x.a_norm_smooth > 0 for x in right):

                        # datapoint directly AFTER zero crossing is step
                        window[self.midPoint].isStep = True

                    # enqueue midpoint to output queue
                    self.outputQueue.enqueue(window[self.midPoint])
                    left.clear()
                    right.clear()
                    window.dequeue()
