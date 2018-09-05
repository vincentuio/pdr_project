from src.dataImporter import dataImporter
from src.preProcessor import preprocessor
from src.smoothingFilter import smoothingFilter
from src.orientation import orientation
from src.stepCounter import stepCounter
from src.stepLength import stepLength
from src.position2D import position2D
from src.simulator import simulator

from src.structures.queue import Queue
from src.functions.plotting import create_plot

class pedestrian_dead_reckoning:

    def __init__(self, filename, realtime = False):

        # user input
        self.filename = filename
        self.sampling_frequency = 20 # type 'None' if frequency should be determined from first two points
        self.realtime = realtime
        self.algoType = 1
        '''
        0 = Lee2015 
        1 = Deng2015 
        2 = Kang2018 (set freq to 20!) 
        3 = zerocrossing 
        4 = Brynes2016 (not working)
        '''
        self.filterType = 'gaussian'
        '''
        moving_average
        gaussian
        hann
        kaiser_bessel
        '''

        # Internal queues for data flow
        self.inputQueue = Queue()
        self.preprocessQueue = Queue()
        self.smoothedQueue = Queue()
        self.orientationQueue = Queue()
        self.stepCountQueue = Queue()
        self.stepLengthQueue = Queue()
        self.positionQueue = Queue()
        self.simulationQueue = Queue()

    def initialize(self):
        self.dataImporterer = dataImporter(self.inputQueue, self.filename, self.realtime)
        self.preprocessor = preprocessor(self.inputQueue, self.preprocessQueue, samplingFreq=self.sampling_frequency)
        self.smoothing_filter = smoothingFilter(self.preprocessQueue, self.smoothedQueue, filterType=self.filterType)
        self.orientation = orientation(self.smoothedQueue, self.orientationQueue)
        self.step_counter = stepCounter(self.orientationQueue, self.stepCountQueue, self.algoType)
        self.step_length = stepLength(self.stepCountQueue, self.stepLengthQueue)
        self.position2D = position2D(self.stepLengthQueue,self.positionQueue)
        self.simulation = simulator(self.positionQueue, self.simulationQueue)

    def run(self):
        self.dataImporterer.start()
        self.preprocessor.start()
        self.smoothing_filter.start()
        self.orientation.start()
        self.step_counter.start()
        self.step_length.start()
        self.position2D.start()
        self.simulation.start()

        self.dataImporterer.dataImport.join()
        self.preprocessor.join()
        self.smoothing_filter.join()
        self.orientation.join()
        self.step_counter.stepcount_algorithm.join()
        self.step_length.join()
        self.position2D.join()
        self.simulation.join()

#pdr = pedestrian_dead_reckoning('data/sonitor_dataset_5_hand_edited/')
# pdr = pedestrian_dead_reckoning('data/bballfield_pocket.csv')
# pdr = pedestrian_dead_reckoning('data/Calibration.csv')
pdr = pedestrian_dead_reckoning('data/bballfield_hand.csv', realtime = False)
pdr.initialize()
pdr.run()

# create plot of acc norm raw, acc norm smooth and steps
create_plot(pdr)
