from src.dataImporter import dataImporter
from src.preProcessor import preprocessor
from src.smoothingFilter import smoothingFilter
from src.orientation import orientation
from src.stepCounter import stepCounter
from src.stepLength import stepLength
from src.position2D import position2D
from src.simulator import simulator
from src.structures.queue import Queue
import matplotlib.pyplot as plt


class pedestrian_dead_reckoning:

    def __init__(self, filename):

        # user input
        self.filename = filename
        self.algoType = 1 # 0 = Lee2015 1 = Deng2015 2 = Kang2018 (set freq to 20!) 3 = zerocrossing 4 = Brynes2016 (not working)
        self.sampling_frequency = 20 # type 'None' if frequency should be determined from first two points

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
        self.dataImporterer = dataImporter(self.inputQueue, self.filename)
        self.preprocessor = preprocessor(self.inputQueue, self.preprocessQueue, samplingFreq=self.sampling_frequency)
        self.smoothing_filter = smoothingFilter(self.preprocessQueue, self.smoothedQueue)
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

        self.dataImporterer.dataImport.thread.join()
        self.preprocessor.thread.join()
        self.smoothing_filter.thread.join()
        self.orientation.thread.join()
        self.step_counter.stepcount_algorithm.thread.join()
        self.step_length.thread.join()
        self.position2D.thread.join()
        self.simulation.thread.join()

# pdr = pedestrian_dead_reckoning('data/sonitor_dataset_2_hand/')
# pdr = pedestrian_dead_reckoning('data/bballfield_pocket.csv')
# pdr = pedestrian_dead_reckoning('data/Calibration.csv')
pdr = pedestrian_dead_reckoning('data/bballfield_hand.csv')
pdr.initialize()
pdr.run()


# plot data (green dots are steps)
a_norm = []
a_norm_smooth = []
a_time = []
step_a = []
step_time = []
for q in pdr.simulationQueue:
    a_time.append(q.time)
    a_norm.append(q.a_norm)
    a_norm_smooth.append(q.a_norm_smooth)
    if q.isStep:
        step_a.append(q.a_norm_smooth)
        step_time.append(q.time)

fig, ax = plt.subplots(1, 1, figsize=(40, 10))
plt.plot(a_time, a_norm)
plt.plot(a_time, a_norm_smooth)
plt.plot(step_time, step_a, 'o')
plt.show()
print('steps / datapoints:', len(step_time), len(a_time))