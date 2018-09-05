from src.structures.queue import Queue
from src.structures.thread import threatStructure
from scipy.optimize import minimize_scalar
import numpy as np
import math
import time

class Kang2018(threatStructure):
    def __init__(self, inputQueue, outputQueue):
        super(Kang2018, self).__init__()
        self.target = self.run

        # external parameters
        self.inputQueue = inputQueue
        self.outputQueue = outputQueue
        self.sampling_freq = 20
        self.freq_min = 0.6
        self.freq_max = 2
        self.window_size = 64
        self.sliding_distance = 25
        self.moving_window_time = 64
        self.smoothing_weight = 0.8
        self.w_threshold = 0.1
        self.max_non_walking_windows = 0

        # internal parameters
        self.moving_window_time = (self.moving_window_time - 1) / self.sampling_freq
        self.sliding_distance_time = (self.sliding_distance - 1) / self.sampling_freq
        self.dt = 1./self.sampling_freq

    def run(self):

        window = Queue()
        walking_frequency = None
        non_walking_windows = 0
        walking_time = 0
        step_residual = 0

        while self.active:

            if len(self.inputQueue) != 0:
                dtp = self.inputQueue.dequeue()

                # last point
                if dtp == 'end':
                    # add remaining data points to queue
                    for ii in range(len(window)):
                        pop = window.dequeue()
                        self.outputQueue.enqueue(pop)
                    self.outputQueue.enqueue('end')

                    self.active = False
                    return

                window.enqueue(dtp)

                if len(window.queue) == self.window_size:

                    # get most sensitive gyro axis:
                    g_x = [x.g[0] for x in window]
                    g_y = [x.g[1] for x in window]
                    g_z = [x.g[2] for x in window]
                    g_sum = [sum(abs(x) for x in g_x),sum(abs(x) for x in g_y),sum(abs(x) for x in g_z)]
                    g_index = g_sum.index(max(g_sum))
                    g_target = [g_x, g_y, g_z][g_index]

                    # FFT of target gyro and separate into w_0 (below min freq) and w_c (within range)
                    f, w = self.fft(g_target)
                    w_0 = w[f < self.freq_min]
                    w_c = w[(f >= self.freq_min) & (f <= self.freq_max)]
                    f_c = f[(f >= self.freq_min) & (f <= self.freq_max)]

                    # First test: is there a higher average amplitude within range than below, and is this above 10
                    if np.average(w_c) > np.average([np.sum(w_0), self.w_threshold]):

                        p, r = self.get_max_freq(f_c,w_c)
                        if r.success:

                            # update total time walked
                            walking_time += self.sliding_distance_time

                            # get/update walking frequency for current time window
                            if walking_frequency is None:
                                walking_frequency = r.x
                            else:
                                walking_frequency = self.smoothing_weight * walking_frequency + (1 - self.smoothing_weight) * r.x

                            # determine steps within sliding distance interval
                            step_residual, nr_of_steps = math.modf(2 * walking_frequency * self.sliding_distance_time + step_residual)
                            step_position = int(self.sliding_distance / (2 * nr_of_steps))
                            for ii in range(int(nr_of_steps)):
                                window[2*ii*step_position].isStep = True

                        # else:
                           # print('no walking freq found')
                    else:
                        if walking_frequency is not None:

                            # MAX 1 windows without frequency to continue walking. After that, assume stop walking
                            if non_walking_windows < self.max_non_walking_windows:

                                # determine steps within sliding distance interval
                                step_residual, nr_of_steps = math.modf(2 * walking_frequency * self.sliding_distance_time + step_residual)
                                step_position = int(self.sliding_distance / (2 * nr_of_steps))
                                for ii in range(int(nr_of_steps)):
                                    window[2 * ii * step_position].isStep = True
                                non_walking_windows += 1

                            else:
                                walking_frequency = None
                                step_residual = 0
                                non_walking_windows = 0
                        else:
                            step_residual = 0
                            non_walking_windows = 0

                    for ii in range(self.sliding_distance):
                        pop = window.dequeue()
                        pop.g_norm = g_target[ii]
                        pop.g_norm_smooth = g_target[ii]
                        self.outputQueue.enqueue(pop)
            else:
                time.sleep(0.05)

    def fft(self,g_data):
        a = np.fft.fft(g_data) # * self.dt
        a = np.abs(a[:self.window_size // 2])
        f = np.fft.fftfreq(self.window_size, self.dt)
        f = f[:self.window_size // 2]
        return f, a

    def get_max_freq(self, f, a):
        z = np.polyfit(f, a, f.size-1)
        p = np.poly1d(z)
        r = minimize_scalar(p, bounds=(self.freq_min,self.freq_max), method='bounded')
        return p, r

