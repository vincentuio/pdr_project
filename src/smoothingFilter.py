from src.structures.queue import Queue
from src.structures.thread import threatStructure
from scipy import special
import math


class smoothingFilter(threatStructure):

    def __init__(self, inputQueue, outputQueue, filterType = 'gaussian', filterWindowSize = 10):
        super(smoothingFilter, self).__init__()
        self.target = self.run

        self.inputQueue = inputQueue
        self.outputQueue = outputQueue
        self.filterWindowSize = filterWindowSize
        self.midpoint = int(self.filterWindowSize / 2)

        self.filter_window = self.filterCoeffs(filterType, filterWindowSize)
        self.filter_sum = sum(self.filter_window)

    def run(self):

        window = Queue()

        while self.active:

            if len(self.inputQueue.queue) != 0:
                dtp = self.inputQueue.dequeue()

                # last point in queue
                if dtp == 'end':

                    # add remaining data points to queue (these are not filtered)
                    for ii in range(len(window)):
                        pop = window.dequeue()
                        pop.a_norm_smooth = pop.a_norm
                        pop.g_norm_smooth = pop.g_norm
                        self.outputQueue.enqueue(pop)

                    self.outputQueue.enqueue('end')
                    self.active = False

                    return

                window.enqueue(dtp)

                # if window size is reached:
                if len(window.queue) == self.filterWindowSize:

                    # Compute average of filter window and store in midpoint
                    ssumAcc = 0
                    ssumGyr = 0
                    for i in range(self.filterWindowSize):
                        ssumAcc += window[i].a_norm * self.filter_window[i]
                        ssumGyr += window[i].g_norm * self.filter_window[i]
                    window[self.midpoint].a_norm_smooth = ssumAcc / self.filter_sum
                    window[self.midpoint].g_norm_smooth = ssumGyr / self.filter_sum

                    # store midpoint in output queue
                    self.outputQueue.enqueue(window[self.midpoint])

                    # dequeue oldest point in filter window
                    window.dequeue()

    # determine filter type and compute coefficients
    def filterCoeffs(self, filterType, filterWindowSize):
        if filterType == 'hann':
            filterCoeffs = hannCoeffs(filterWindowSize)
        elif filterType == 'kaiser_bessel':
            filterCoeffs = kaiserBesselCoeffs(filterWindowSize)
        elif filterType == 'gaussian':
            filterCoeffs = gaussianCoeffs(filterWindowSize)
        elif filterType == 'moving_average':
            filterCoeffs = [1] * filterWindowSize
        else:
            self.filterWindowSize = 1
            self.midpoint = 0
            filterCoeffs = [1]
            filterType = 'filter not found. No smoothing'
        print('Filter = ', filterType)
        return filterCoeffs


# filter coeffs functions
def gaussianCoeffs(windowSize, std = 1):
    window = []
    for n in range(windowSize):
        value = math.exp(-0.5 * math.pow((n - (windowSize - 1) / 2) / (std * (windowSize - 1) / 2), 2))
        window.append(value)

    return window

def hannCoeffs(windowSize):
    window = []
    for n in range(windowSize):
        value = 0.5 * (1 - math.cos(2*math.pi * n / (windowSize - 1)))
        window.append(value)
    return window

def kaiserBesselCoeffs(windowSize, cutoff_f = 6, sampling_f = 20):
    coeffs = []
    Np = (windowSize - 1) / 2

    # Assume we always want a attenuation of 60dB at cutoff frequency
    alpha = 5.65326
    Io_alpha = special.iv(0, alpha)

    # Calculate Kaiser-Bessel window coefficients
    window = []
    for i in range(0, windowSize):
        val = alpha * math.sqrt(1 - math.pow((i - Np) / Np, 2))
        window.append(special.iv(0, val) / Io_alpha)

    # Sinc function coefficients
    sinc = []
    for i in range(0, windowSize):
        val = 2 * (i - Np) * cutoff_f / sampling_f
        sinc.append(sinc(val))

    # Multiple the coeffs together
    for i in range(0, windowSize):
        coeffs.append(window[i] * sinc[i])

    return coeffs

# Implementation of the sinc(x) function in Python
# @return:
#   1. value - result of the sinc operator.
def sinc(x):
    if x == 0:
        return 1
    else:
        return math.sin(math.pi * x) / (math.pi * x)