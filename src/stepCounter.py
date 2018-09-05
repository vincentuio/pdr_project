from src.stepdetection.Deng2015 import Deng2015
from src.stepdetection.Lee2015 import Lee2015
from src.stepdetection.zerocrossing import zerocrossing
from src.stepdetection.Brynes2016 import Brynes2016
from src.stepdetection.Kang2018 import Kang2018
from src.structures.thread import threatStructure
class stepCounter(threatStructure):
    def __init__(self,inputQueue,outputQueue,algoType):
        super(stepCounter, self).__init__()
        self.target = self.run

        self.inputQueue = inputQueue
        self.outputQueue = outputQueue
        self.stepcount_algorithm = None
        self.algoName = None

        if algoType == 0:
            self.stepcount_algorithm = Lee2015(self.inputQueue, self.outputQueue)
            self.algoName = 'Lee2015'
        elif algoType == 1:
            self.stepcount_algorithm = Deng2015(self.inputQueue, self.outputQueue)
            self.algoName = 'Deng2015'
        elif algoType == 2:
            self.stepcount_algorithm = Kang2018(self.inputQueue,self.outputQueue)
            self.algoName = 'Kang2018'
        elif algoType == 3:
            self.stepcount_algorithm = zerocrossing(self.inputQueue, self.outputQueue)
            self.algoName = 'zerocrossing'
        elif algoType == 4:
            self.stepcount_algorithm = Brynes2016(self.inputQueue,self.outputQueue)
            self.algoName = 'Brynes2016'
        else:
            print('step counting algorithm not detected. default = Deng2015')
            self.stepcount_algorithm = Deng2015(self.inputQueue, self.outputQueue)
            self.algoName = 'Deng2015'

    def run(self):
        self.stepcount_algorithm.start()



