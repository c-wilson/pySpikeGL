__author__ = 'labadmin'

# import multiprocessing
import numpy as np
from scipy.signal import filtfilt
from functools import partial
import time
# import numpy.sharedmem
# import num

# CPUS = multiprocessing.cpu_count()
# USE_CPUS = CPUS - 3
# if USE_CPUS < 1:
# USE_CPUS = 1


# mp = multiprocessing.Pool(8)

def the_filter(filt_val1, filt_val2, dat):
    return filtfilt(filt_val1, filt_val2, dat)


def filter_signal(disp_samples, e_phys_channel_number, filter):
    # shared_array_base = multiprocessing.Array(ctypes.c_double, 10*10)


    # s = time.time()
    a = disp_samples[:e_phys_channel_number, :]
    # sha = np.array([])
    # b = map(lambda x: signal.filtfilt(self.signal_filter[0], self.signal_filter[1], x), a)
    # f = partial(the_filter, filter[0], filter[1])
    # b = np.zeros(a.shape)
    # print len(a)
    # print a.shape
    # b = mp.map(f, a)

    b = filtfilt(filter[0],
                 filter[1],
                 a)
    a[:] = b
    # print time.time()-s
    return disp_samples

