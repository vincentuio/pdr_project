from src.structures.queue import Queue
from src.structures.thread import threatStructure
import time

class Deng2015(threatStructure):
    def __init__(self,inputQueue,outputQueue):
        super(Deng2015, self).__init__()
        self.target = self.run

        self.inputQueue = inputQueue
        self.outputQueue = outputQueue
        self.dt_threshold = 0.5 * 1000 # threshold in ms
        self.acc_threshold = 10
        
    def run(self):

        '''two windows: 
        window is regular window that tracks if there are enough points,
        step_window tracks all points since last potential step.
         
        step_window resets if new step is detected'''
        
        window = Queue()
        step_window = Queue()

        while self.active:

            if len(self.inputQueue) != 0:

                dtp = self.inputQueue.dequeue()

                # Last point
                if dtp == 'end':
                    
                    # enqueue remaining part of step_window
                    for ii in range(len(step_window)):
                        pop = step_window.dequeue()
                        self.outputQueue.enqueue(pop)
                    
                    # enqueue last data point of window
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

                    # Check for local peak AND above threshold
                    if window[1].a_norm_smooth > max([window[0].a_norm_smooth, window[2].a_norm_smooth, self.acc_threshold]):

                        # first step identified
                        if not step_window[0].isStep:
                            window[1].isStep = True

                            # enqueue all points in step_window to output queue, empty step_window
                            for ii in range(len(step_window)):
                                pop = step_window.dequeue()
                                self.outputQueue.enqueue(pop)

                        # subsequent steps identified
                        else:
                            
                            # check if dt > threshold
                            if (window[1].time - step_window[0].time) > self.dt_threshold:
                                window[1].isStep = True
                                for ii in range(len(step_window)):
                                    pop = step_window.dequeue()
                                    self.outputQueue.enqueue(pop)
                            
                            # check if new acc norm > acc norm of previous step
                            elif window[1].a_norm_smooth >= step_window[0].a_norm_smooth:
                                window[1].isStep = True
                                step_window[0].isStep = False
                                for ii in range(len(step_window)):
                                    pop = step_window.dequeue()
                                    self.outputQueue.enqueue(pop)
                            
                            # otherwise false positive
                            else:
                                pass

                    # enqueue middle data point to step_window
                    step_window.enqueue(window[1])

                    # remove oldest point from window
                    window.dequeue()
            else:
                time.sleep(0.05)

