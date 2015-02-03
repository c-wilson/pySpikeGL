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
        self.data['non_displayed_chans'] = np.array([])
        return


class J_HIRES_4x16(AbstractProbe):
    def build_window_params(self, interface):
        # NOTE: CHANNEL 2 HERE IS ON THE TOP OF THE SHANK.
        window1 = {'site_numbers': np.array([2, 15, 1, 16, 4, 13, 3, 14, 6, 11, 5, 12, 8, 9, 7, 10]),
                   'channels': np.array([24, 38, 23, 40, 25, 39, 22, 31, 26, 16, 21, 17, 27, 18, 28, 19]),
                   'grid_position': (0, 0, 1, 1)  # (row, column, rowSpan, columnSpan)
        }
        window2 = {'site_numbers': np.array([18, 31, 17, 32, 20, 29, 19, 30, 22, 27, 21, 28, 24, 25, 23, 26]),
                   'channels': np.array([41, 20, 37, 29, 42, 30, 36, 32, 43, 47, 35, 33, 44, 46, 34, 45]),
                   'grid_position': (0, 1, 1, 1)
        }
        window3 = {'site_numbers': np.array([33, 48, 34, 47, 35, 46, 36, 45, 37, 44, 38, 43, 39, 42, 40, 41]),
                   'channels': np.array([11, 54, 2, 58, 1, 53, 63, 59, 48, 52, 62, 60, 49, 51, 50, 61]),
                   'grid_position': (1, 1, 1, 1)
        }
        window4 = {'site_numbers': np.array([49, 64, 50, 63, 51, 62, 52, 61, 53, 60, 54, 59, 55, 58, 56, 57]),
                   'channels': np.array([57, 7, 55, 8, 56, 6, 0, 9, 15, 5, 14, 10, 13, 4, 12, 3]),
                   'grid_position': (1, 0, 1, 1)
        }

        window_params = [window1, window2, window3, window4]
        return window_params


class NN_buz_64s(AbstractProbe):
    def build_window_params(self, interface):
        window1 = {'channels': np.array([8, 0, 10, 11, 5, 1, 12, 9, 3, 13]),
                   'site_numbers': np.array([1, 10, 2, 9, 3, 8, 4, 7, 5, 6]),
                   'grid_position': (0, 0, 1, 1,)  # (row, column, rowSpan, columnSpan)
        }
        window2 = {'channels': np.array([2, 51, 55, 57, 14, 52, 54, 56, 15, 53]),
                   'site_numbers': np.array([11, 20, 12, 19, 13, 18, 14, 17, 15, 16]),
                   'grid_position': (0, 1, 1, 1)
        }
        window3 = {'channels': np.array([58, 6, 62, 50, 59, 49, 63, 48, 60, 61]),
                   'site_numbers': np.array([21, 30, 22, 29, 23, 28, 24, 27, 25, 26]),
                   'grid_position': (1, 0, 1, 1)
        }
        window4 = {'channels': np.array([7, 37, 4, 33, 27, 36, 24, 32, 25, 35]),
                   'site_numbers': np.array([31, 44, 32, 43, 33, 42, 34, 41, 35, 40]),
                   'grid_position': (1, 1, 1, 1)
        }
        window5 = {'channels': np.array([44, 29, 38, 40, 43, 17, 39, 41, 42, 16]),
                   'site_numbers': np.array([45, 54, 46, 53, 47, 52, 48, 51, 49, 50]),
                   'grid_position': (2, 0, 1, 1)
        }
        window6 = {'channels': np.array([31, 23, 20, 21, 30, 26, 22, 19, 18, 28]),
                   'site_numbers': np.array([55, 64, 56, 63, 57, 62, 58, 61, 59, 60]),
                   'grid_position': (2, 1, 1, 1),
        }

        window_params = [window1, window2, window3, window4, window5, window6]
        return window_params

    def __init__(self):
        super(NN_buz_64s, self).__init__()
        self.data['non_displayed_chans'] = np.array([45, 34, 47, 46])


probes = {'J_HIRES_4x16': J_HIRES_4x16(),
          'NN_buz_64s': NN_buz_64s()}  # we'll import this...