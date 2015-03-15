'''
Created on Jul 16, 2014

@author: chris
'''
from copy import deepcopy
import numpy as np
import numba as nb
class CircularBuffer(object):
    '''
    This is a circular buffer object for use with streaming data input. It has methods to add samples to the 
    
    '''

    def __init__(self, rows, columns, dimension=1):
        self.shape = (rows, columns)
        self.head_idx = np.int64(0)
        self.buffer_len = columns  # we are using row-major order here (python default and C)
        self.samples = np.zeros(self.shape, dtype=np.float64)
        self.sample_count_array = np.zeros(columns, dtype=np.uint64)
        return

    def add_samples(self, new_samples):
        head_idx = self.head_idx
        buffer_len = self.buffer_len
        if new_samples.ndim < 2:
            print 'ERROR: the input is expected as a 2D numpy.array().'
        num_new_samples = new_samples.shape[1]
        # TODO: add functionality for single dimension arrays...

        if num_new_samples >= self.buffer_len:
            print 'Number samples greater than buffer length, clipping new samples to fit buffer!'
            self.samples[:, :] = new_samples[:, -buffer_len:]  # fill the buffer with the newest samples.
            self.head_idx = 0  # start at beginning for next new_samples.
            sample_start = self.sample_count_array[head_idx - 1] + 1
            sample_start += num_new_samples - buffer_len
            self.sample_count_array = np.arange(sample_start, sample_start + buffer_len, dtype=np.uint64)
        else:
            new_head_idx = self.head_idx + num_new_samples

            if new_head_idx >= buffer_len:
                new_head_idx -= buffer_len
                num_initial_samples = buffer_len - head_idx
                self.samples[:, head_idx:] = new_samples[:, :num_initial_samples]
                self.samples[:, :new_head_idx] = new_samples[:, num_initial_samples:]
            else:
                self.samples[:, head_idx: new_head_idx] = new_samples[:, :]
            self.sample_count_array = self.update_sample_count(self.sample_count_array, head_idx, num_new_samples)
            self.head_idx = new_head_idx
        return

    @staticmethod
    @nb.jit(nb.uint64[:](nb.uint64[:], nb.int64, nb.int64), nopython=True)
    def update_sample_count(sample_count_array, buffer_head, num_new_samples):
        buffer_len = sample_count_array.size
        if buffer_head == 0:
            sample = sample_count_array[-1]
        else:
            sample = sample_count_array[buffer_head - 1]

        for i in xrange(buffer_head, buffer_head + num_new_samples):
            sample += 1
            if i >= buffer_len:
                i -= buffer_len
            sample_count_array[i] = sample
        return sample_count_array


    def sample_range(self, num_samples=None, head=None, tail=None, ):
        if num_samples >= self.buffer_len:
            num_samples = self.buffer_len - 1
            print 'More samples requested than present in buffer, returning all available samples.'
        if num_samples and not head and not tail:  # returns the last n samples before the head.
            tail = (self.head_idx - num_samples) % self.buffer_len  # index of first sample to display.
            head = self.head_idx
        elif num_samples and tail and not head:  # returns the next n samples after the specified tail. Returns None if not enough samples exist!
            head = (tail + num_samples) % self.buffer_len  # index of last value to display
            if not ((
                                    self.head_idx > tail and self.head_idx > tail + num_samples) or  # in this case, we have not wrapped around the main buffer, so the head should be absolutely greater.
                        (self.head_idx < tail and self.head_idx > head)):
                return None
        samples = np.zeros((self.shape[0], num_samples), dtype=np.float64)
        if head == 0:
            samples = self.samples[:, tail:]
        elif tail > head:
            samples[:, :-head] = self.samples[:, tail:]
            samples[:, -head:] = self.samples[:, :head]

        else:
            samples = self.samples[:, tail:head]
        return deepcopy(samples)