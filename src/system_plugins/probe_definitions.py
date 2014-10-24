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
        window1 = {'channels': np.array([0, 31, 1, 30, 2, 29, 3, 28, 4, 27, 5, 26, 6, 25, 7, 24]),
                   'site_numbers': np.array([10, 7, 9, 8, 12, 5, 11, 6, 14, 3, 13, 4, 16, 1, 15, 2]),
                   'grid_position': (0, 0, 1, 1)  # (row, column, rowSpan, columnSpan)
        }
        window2 = {'channels': np.array([16, 12, 8, 17, 15, 18, 11, 19, 14, 20, 10, 21, 13, 22, 9, 23]),
                   'site_numbers': np.array([26, 23, 25, 24, 28, 21, 27, 22, 30, 19, 29, 20, 32, 17, 31, 18]),
                   'grid_position': (0, 1, 1, 1)
        }
        window3 = {'channels': np.array([60, 32, 33, 56, 34, 63, 35, 59, 36, 62, 37, 58, 38, 61, 39, 57]),
                   'site_numbers': np.array([41, 40, 42, 39, 43, 38, 44, 37, 45, 36, 46, 35, 47, 34, 48, 33]),
                   'grid_position': (1, 1, 1, 1)
        }
        window4 = {'channels': np.array([47, 48, 46, 49, 45, 50, 44, 51, 43, 52, 42, 53, 41, 54, 40, 55]),
                   'site_numbers': np.array([57, 56, 58, 55, 59, 54, 60, 53, 61, 52, 62, 51, 63, 50, 64, 49]),
                   'grid_position': (1, 0, 1, 1)
        }

        window_params = [window1, window2, window3, window4]
        return window_params


class NN_buz_64s(AbstractProbe):
    def build_window_params(self, interface):
        window1 = {'channels': np.array([35, 60, 62, 33, 37, 59, 32, 63, 39, 61]),
                   'site_numbers': np.array([6, 5, 7, 4, 8, 3, 9, 2, 10, 1]),
                   'grid_position': (0, 0, 1, 1,)  # (row, column, rowSpan, columnSpan)
        }
        window2 = {'channels': np.array([50, 38, 55, 52, 48, 36, 53, 54, 46, 34]),
                   'site_numbers': np.array([16, 15, 17, 14, 18, 13, 19, 12, 20, 11]),
                   'grid_position': (0, 1, 1, 1)
        }
        window3 = {'channels': np.array([45, 47, 41, 40, 43, 49, 44, 42, 58, 51]),
                   'site_numbers': np.array([26, 25, 27, 24, 28, 23, 29, 22, 30, 21]),
                   'grid_position': (1, 0, 1, 1)
        }
        window4 = {'channels': np.array([31, 10, 24, 9, 1, 8, 26, 56, 3, 57]),
                   'site_numbers': np.array([40, 35, 41, 34, 42, 33, 43, 32, 44, 31]),
                   'grid_position': (1, 1, 1, 1)
        }
        window5 = {'channels': np.array([22, 2, 4, 7, 20, 0, 6, 5, 18, 30]),
                   'site_numbers': np.array([50, 49, 51, 48, 52, 47, 53, 46, 54, 45]),
                   'grid_position': (2, 0, 1, 1)
        }
        window6 = {'channels': np.array([12, 19, 17, 14, 11, 21, 15, 16, 13, 23]),
                   'site_numbers': np.array([60, 59, 61, 58, 62, 57, 63, 56, 64, 55]),
                   'grid_position': (2, 1, 1, 1),
        }

        window_params = [window1, window2, window3, window4, window5, window6]
        return window_params

    def __init__(self):
        super(NN_buz_64s, self).__init__()
        self.data['non_displayed_chans'] = np.array([27, 25, 29, 28])


probes = {'J_HIRES_4x16': J_HIRES_4x16(),
          'NN_buz_64s': NN_buz_64s()}  # we'll import this...