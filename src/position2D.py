import math
import time
from src.structures.thread import threatStructure

class position2D(threatStructure):

    def __init__(self,inputQueue,outputQueue):
        super(position2D, self).__init__()
        self.target = self.run
        self.inputQueue = inputQueue
        self.outputQueue = outputQueue

        self.x = 0
        self.y = 0

    def run(self):
        while self.active:

            if len(self.inputQueue) != 0:

                dtp = self.inputQueue.dequeue()

                # last point
                if dtp == 'end':
                    self.outputQueue.enqueue('end')
                    self.active = False
                    return

                # update position if datapoint is a step
                if dtp.isStep:
                    self.x += dtp.stepLength * math.cos(dtp.roll_pitch_yaw[2])
                    self.y += dtp.stepLength * math.sin(dtp.roll_pitch_yaw[2])

                # write current position to data point
                dtp.position = [self.x, self.y, 0]

                self.outputQueue.enqueue(dtp)
            else:
                time.sleep(0.05)

