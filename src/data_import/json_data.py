from src.structures.datapoint import datapoint as dtp
from src.structures.queue import Queue as Queue
from src.structures.thread import threatStructure
import src.functions.vector as vctr

import time

import json
import numpy as np
import time


class json_import(threatStructure):

    def __init__(self, outputQueue,pathname, realtime):
        super(json_import, self).__init__()

        # external references
        self.outputQueue = outputQueue
        self.path = pathname

        # internal references
        self.gyrQueue = Queue()
        self.accQueue = Queue()
        self.magQueue = Queue()
        self.sortedQueue = Queue()

        # internal objects
        self.gyrReader = json_reader(self.path + 'motion_gyro.json', 'gyroData', self.gyrQueue, realtime)
        self.accReader = json_reader(self.path + 'motion_accel.json', 'accelData', self.accQueue, realtime)
        self.magReader = json_reader(self.path + 'motion_magnet.json', 'magneticData', self.magQueue, realtime)
        self.dtpSorter = dtp_sorter(self.gyrQueue, self.accQueue, self.magQueue, self.sortedQueue)
        self.dtpInterpolator = dtp_interpolator(self.sortedQueue, self.outputQueue)

        self.target = self.run()

    def run(self):
        '''
        self.gyrReader.run()
        self.accReader.run()
        self.magReader.run()
        self.dtpSorter.run()
        self.dtpInterpolator.run()
        '''
        self.gyrReader.start()
        self.accReader.start()
        self.magReader.start()
        self.dtpSorter.start()
        self.dtpInterpolator.start()

        self.active = False

class json_reader(threatStructure):

    def __init__(self, filename, datatype, outputQueue, realtime):
        super(json_reader, self).__init__()
        self.target = self.run

        self.realtime = realtime
        self.outputQueue = outputQueue
        self.filename = open(filename)
        self.datatype = datatype

    def run(self):

        while self.active:

            t0 = None
            for line in self.filename:

                dataset = json.loads(line)['motion'][self.datatype]

                for m in dataset:

                    # get timestamp in ms
                    t = m[0]/1000

                    # compute new datapoint and append to queue
                    if self.datatype == 'gyroData':
                        self.outputQueue.enqueue(dtp(t, g=np.array(m[1:])))
                    elif self.datatype == 'accelData':
                        self.outputQueue.enqueue(dtp(t, a=np.array(m[1:])))
                    elif self.datatype == 'magneticData':
                        self.outputQueue.enqueue(dtp(t, m=np.array(m[1:])))

                    # if realtime = true, wait before next datapoint
                    if t0 is None:
                        t0 = t
                    elif self.realtime:
                        time.sleep((t - t0) / 1000000)
                        t0 = t

            self.outputQueue.enqueue('end')
            self.active = False


class dtp_sorter(threatStructure):

    def __init__(self, gyrQueue, accQueue, magQueue, outputQueue):
        super(dtp_sorter, self).__init__()
        self.target = self.run

        self.outputQueue = outputQueue
        self.q1 = gyrQueue
        self.q2 = accQueue
        self.q3 = magQueue
        self.q_list = [self.q1, self.q2, self.q3]

        self.dt = None

    def run(self):
        

        #  initial datapoints
        current_dtpts = [None, None, None]
        current_times = [0,0,0]
        stop_counter = 3

        while self.active:

            # update most recent data point per data type
            for ii in range(3):
                if (len(self.q_list[ii]) != 0) and (current_dtpts[ii] is None):
                    dp = self.q_list[ii].dequeue()
                    if dp == 'end':
                        current_times[ii] = 0
                        current_dtpts[ii] = None
                        stop_counter -= 1
                    else:
                        current_times[ii] = dp.time
                        current_dtpts[ii] = dp

            # stop if all queues are done (stop counter reaches 0)
            if stop_counter == 0:
                self.outputQueue.enqueue('end')
                self.active = False
                break

            # continue only if all available data types have a value
            if sum(x is not None for x in current_dtpts) == stop_counter:

                # determine earliest timestamp
                t_min = min([t for t in current_times if t != 0])

                # set initial time to t=0
                if self.dt is None:
                    self.dt = t_min
    
                # create new data point
                dtp_new = dtp(0)
                
                # enqueue earliest datapoint
                for ii in range(3):
                    dp = current_dtpts[ii]
                    if current_times[ii] == t_min:
                        dtp_new.time = dp.time - self.dt
                        if ii == 0:
                            dtp_new.g = dp.g
                        elif ii == 1:
                            dtp_new.a = dp.a
                        elif ii == 2:
                            dtp_new.m = dp.m
                        current_dtpts[ii] = None
                    
                self.outputQueue.enqueue(dtp_new)
                        

class dtp_interpolator(threatStructure):

    def __init__(self, inputQueue, outputQueue):
        super(dtp_interpolator, self).__init__()
        self.target = self.run

        self.outputQueue = outputQueue
        self.inputQueue = inputQueue

    def run(self):
        

        # initial data points
        first_point = True

        a_i = 0
        g_i = 0
        m_i = 0

        window = Queue()

        while self.active:

            if len(self.inputQueue) != 0:

                dp = self.inputQueue.dequeue()

                # last data point
                if dp == 'end':
                    a_final = window[a_i].a
                    g_final = window[g_i].g
                    m_final = window[m_i].m
                    for dp in window:
                        if dp.a is None:
                            dp.a = a_final
                        if dp.g is None:
                            dp.g = g_final
                        if dp.m is None:
                            dp.m = m_final
                        dp.a_norm = vctr.norm(dp.a)
                        dp.g_norm = vctr.norm(dp.g)
                        self.outputQueue.enqueue(dp)

                    self.outputQueue.enqueue('end')
                    self.active = False
                    break

                # first data point
                if first_point:
                    if dp.a is None:
                        dp.a = np.array([0., 0., 0.])
                    if dp.g is None:
                        dp.g = np.array([0., 0., 0.])
                    if dp.m is None:
                        dp.m = np.array([0., 0., 0.])
                    first_point = False

                # intermediate datapoints
                window.enqueue(dp)

                if len(window) > 1:
                    # per dataype: if latest dp has an updated value, interpolate intermediate dps and update index
                    if dp.a is not None:
                        slope = (dp.a - window[a_i].a) / (dp.time - window[a_i].time)
                        for ii in range(a_i + 1, len(window)):
                            dt = window[ii].time - window[a_i].time
                            window[ii].a = window[a_i].a + slope * dt
                        a_i = len(window) - 1

                    if dp.g is not None:
                        slope = (dp.g - window[g_i].g) / (dp.time - window[g_i].time)
                        for ii in range(g_i + 1, len(window)):
                            dt = window[ii].time - window[g_i].time
                            window[ii].g = window[g_i].g + slope * dt
                        g_i = len(window) - 1

                    if dp.m is not None:
                        slope = (dp.m - window[m_i].m) / (dp.time - window[m_i].time)
                        for ii in range(m_i + 1, len(window)):
                            dt = window[ii].time - window[m_i].time
                            window[ii].m = window[m_i].m + slope * dt
                        m_i = len(window) - 1

                    # enqueue all datapoints below min index in window to the output queue
                    min_i = min([a_i, g_i, m_i])
                    for _ in range(min_i):
                        pop = window.dequeue()
                        pop.a_norm = vctr.norm(pop.a)
                        pop.g_norm = vctr.norm(pop.g)
                        self.outputQueue.enqueue(pop)

                    # recompute min indexes of window
                    a_i -= min_i
                    g_i -= min_i
                    m_i -= min_i
'''
q = Queue()
tester = json_import(q, '../../data/sonitor_dataset_2_hand/')
tester.start()
time.sleep(3)
for x in q:
    if x == 'end':
        break
    print(x.time, x.a[1], x.g[1], x.m[1])
print(len(q))
'''



