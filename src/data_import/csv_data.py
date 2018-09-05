from src.structures.datapoint import datapoint as dtp
from src.structures.thread import threatStructure
from src.structures.queue import Queue
import src.functions.vector as vctr
import pandas as pd
import numpy as np
import time

class csv_import(threatStructure):

    def __init__(self,outputQueue,filename, realtime = False):

        super(csv_import, self).__init__()
        self.target = self.run

        self.outputQueue = outputQueue
        self.filename = filename
        self.realtime = realtime

        self.column_names_gyro = ['gyroRotationX(rad/s)',
                                  'gyroRotationY(rad/s)',
                                  'gyroRotationZ(rad/s)']
        self.column_names_acc = ['accelerometerAccelerationX(G)',
                                 'accelerometerAccelerationY(G)',
                                 'accelerometerAccelerationZ(G)']
        self.column_names_mag = ['locationHeadingX(µT)',
                                 'locationHeadingY(µT)',
                                 'locationHeadingZ(µT)']

    def run(self):
        df = pd.read_csv(self.filename, delimiter=',')

        # convert absolute time to relative time in ms
        time_array = pd.to_datetime(df['loggingTime(txt)']).values.astype('datetime64[ms]')
        time_array = (time_array - time_array[0]).astype(int)

        # read in columns for gyro, acc and mag
        gyr = df[self.column_names_gyro].values
        acc = df[self.column_names_acc].values
        mag = df[self.column_names_mag].values

        # initial data points
        first_point = True

        a_i = 0
        g_i = 0
        m_i = 0

        window = Queue()

        while self.active:

            for kk in range(time_array.size):

                a = acc[kk]
                g = gyr[kk]
                m = mag[kk]

                dp = dtp(time_array[kk], a, g, m)

                # last data point
                if kk == time_array.size - 1:
                    a_final = window[a_i].a
                    g_final = window[g_i].g
                    m_final = window[m_i].m
                    for dp in window:
                        if pd.isna(dp.a[0]):
                            dp.a = a_final
                        if pd.isna(dp.g[0]):
                            dp.g = g_final
                        if pd.isna(dp.m[0]):
                            dp.m = m_final
                        dp.a_norm = vctr.norm(dp.a)
                        dp.g_norm = vctr.norm(dp.g)
                        self.outputQueue.enqueue(dp)
                    self.outputQueue.enqueue('end')
                    self.active = False
                    break

                # first data point
                if first_point:
                    if pd.isna(dp.a[0]):
                        dp.a = np.array([0., 0., 0.])
                    if pd.isna(dp.g[0]):
                        dp.g = np.array([0., 0., 0.])
                    if pd.isna(dp.m[0]):
                        dp.m = np.array([0., 0., 0.])
                    first_point = False

                # intermediate datapoints
                window.enqueue(dp)

                if len(window) > 1:
                    # per dataype: if latest dp has an updated value, interpolate intermediate dps and update index
                    if not pd.isna(dp.a[0]):
                        slope = (dp.a - window[a_i].a) / (dp.time - window[a_i].time)
                        for ii in range(a_i + 1, len(window)):
                            dt = window[ii].time - window[a_i].time
                            window[ii].a = window[a_i].a + slope * dt
                        a_i = len(window) - 1

                    if not pd.isna(dp.g[0]):
                        slope = (dp.g - window[g_i].g) / (dp.time - window[g_i].time)
                        for ii in range(g_i + 1, len(window)):
                            dt = window[ii].time - window[g_i].time
                            window[ii].g = window[g_i].g + slope * dt
                        g_i = len(window) - 1

                    if not pd.isna(dp.m[0]):
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

                # if realtime = true, wait before next datapoint
                if (kk != 0) and self.realtime:
                    time.sleep((time_array[kk]-time_array[kk-1]) / 1000)

    def run_without_nans(self):

        window = Queue()
        while self.active:
            df = pd.read_csv(self.filename, delimiter=',')

            # convert absolute time to relative time in ms
            time = pd.to_datetime(df['loggingTime(txt)']).values.astype('datetime64[ms]')
            time = (time - time[0]).astype(int)

            # read in columns for gyro, acc and mag
            gyr = df[self.column_names_gyro].values
            acc = df[self.column_names_acc].values
            mag = df[self.column_names_mag].values

            # compute datapoints
            for ii in range(time.size):

                # first point
                if ii == 0:
                    new_dtp = dtp(time[ii], a=acc[ii], g=gyr[ii], m=mag[ii])

                new_dtp = dtp(time[ii], a = acc[ii], g = gyr[ii], m = mag[ii])
                new_dtp.a_norm = vctr.norm(acc[ii])
                new_dtp.g_norm = vctr.norm(gyr[ii])

                self.outputQueue.enqueue(new_dtp)
            self.outputQueue.enqueue('end')

            self.active = False