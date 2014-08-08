'''
Created on Jul 2, 2014

YOU MUST ADD NEW PROBE DEFINITIONS TO THE 'PROBES' DICTIONARY AT THE BOTTOM OF THIS DOCUMENT!

@author: chris
'''

import numpy as np


class AbstractProbe(object):
    '''
    classdocs
    '''

    data = {}
    window_params = []


    def build_window_params(self, acquisition_interface):
        ''' window_n = {channels: (1,2,...n), position =(1,2,3,4) 'grid position'} 
        window_1 = { }'''

        # this should return a windows dictionary.

        windows = {}
        return windows

    def build_data(self):
        data = {}
        return data

    def calculate_sites(self):
        num_sites = 0
        for window in self.window_params:
            num_sites += window['channels'].size
        return num_sites


    def __init__(self, acquisition_interface='SpikeGL'):
        self.window_params = self.build_window_params(acquisition_interface)
        self.data = self.build_data()
        num_sites = self.calculate_sites()
        self.data['num_sites'] = num_sites
        return


class J_HIRES_4x16(AbstractProbe):
    def build_window_params(self, interface):
        window1 = {'channels': np.array([0,31,1,30,2,29,3,28,4,27,5,26,6,25,7,24]),
                   'site_numbers': np.array([10, 7, 9, 8, 12, 5, 11, 6, 14, 3, 13, 4, 16, 1, 15, 2]),
                   'grid_position': (0, 0, 1, 1)
        }
        window2 = {'channels': np.array([16,12,8,17,15,18,11,19,14,20,10,21,13,22,9,23]),
                   'site_numbers': np.array([26, 23, 25, 24, 28, 21, 27, 22, 30, 19, 29, 20, 32, 17, 31, 18]),
                   'grid_position': (0, 1, 1, 1)
        }
        window3 = {'channels': np.array([60,32,33,56,34,63,35,59,36,62,37,58,38,61,39,57]),
                   'site_numbers': np.array([41, 40, 42, 39, 43, 38, 44, 37, 45, 36, 46, 35, 47, 34, 48, 33]),
                   'grid_position': (1, 1, 1, 1)
        }
        window4 = {'channels': np.array([47,48,46,49,45,50,44,51,43,52,4253,41,54,40,55]),
                   'site_numbers': np.array([57, 56, 58, 55, 59, 54, 60, 53, 61, 52, 62, 51, 63, 50, 64, 49]),
                   'grid_position': (1, 0, 1, 1)
        }

        window_params = [window1, window2, window3, window4]
        return window_params


probes = {'J_HIRES_4x16': J_HIRES_4x16()}  # we'll import this...
