from src.structures.thread import threatStructure


class queueCopier(threatStructure):

    def __init__(self, inputQueue, outputQueue1, outputQueue2):
        super(queueCopier, self).__init__()
        self.target = self.run

        self.inputQueue = inputQueue
        self.outputQueue1 = outputQueue1
        self.outputQueue2 = outputQueue2

    def run(self):
        while self.active:
            if len(self.inputQueue) != 0:
                dtp = self.inputQueue.dequeue()
                if dtp == 'end':
                    self.outputQueue1.enqueue('end')
                    self.outputQueue2.enqueue('end')
                    self.active = False
                    return
                self.outputQueue1.enqueue(dtp)
                self.outputQueue2.enqueue(dtp)

