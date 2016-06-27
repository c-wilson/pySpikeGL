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


class NN_A2x32_poly5(AbstractProbe):
    def build_window_params(self, acquisition_interface):
        window1 = {'site_numbers': np.array([7, 26, 1, 14, 32, 8, 25, 2, 19, 31, 9, 24, 3, 15, 30, 10, 23, 4, 18, 29,
                                             11, 22, 5, 16, 28, 12, 21, 6, 17, 27, 13, 20]),
                   'channels': np.array([25, 61, 24, 54, 20, 17, 60, 26, 57, 23, 27, 63, 21, 31, 22, 16, 59, 28, 52,
                                         50, 18, 62, 19, 53, 49, 55, 58, 29, 56, 48, 30, 51]),
                   'grid_position': (0, 0, 1, 1)  # (row, column, rowSpan, columnSpan)
                   }

        window2 = {'site_numbers': np.array([39, 58, 33, 46, 64, 40, 57, 34, 51, 63, 41, 56, 35, 47, 62, 42, 55, 36,
                                             50, 61, 43, 54, 37, 48, 60, 44, 53, 38, 49, 59, 45, 52]),
                   'channels': np.array([34, 6, 11, 38, 7, 35, 14, 8, 41, 5, 32, 4, 9, 43, 10, 36, 15, 45, 0, 3, 33,
                                         13, 46, 39, 12, 37, 40, 47, 42, 2, 44, 1]),
                   'grid_position': (0, 1, 1, 1)
                   }
        return (window1, window2)


class J_HIRES_4x16(AbstractProbe):
    def build_window_params(self, interface):
        # NOTE: CHANNEL 2 HERE IS ON THE TOP OF THE SHANK.
        window1 = {'site_numbers': np.array([16,  1, 15,  2, 14,  3, 13,  4, 12,  5, 11,  6, 10,  7,  9,  8]),
                   'channels': np.array([39, 32, 40, 47, 38, 33, 41, 46, 37, 45, 42, 34, 36, 44, 43, 35]),
                   'grid_position': (0, 0, 1, 1)  # (row, column, rowSpan, columnSpan)
        }
        window2 = {'site_numbers': np.array([31, 17, 27, 18, 30, 19, 26, 20, 29, 21, 25, 22, 32, 23, 24, 28]),
                   'channels': np.array([24, 31, 23, 16, 25, 30, 22, 17, 26, 18, 21, 29, 27, 19, 20, 28]),
                   'grid_position': (0, 1, 1, 1)
        }
        window3 = {'site_numbers': np.array([48, 34, 47, 38, 46, 35, 45, 39, 44, 36, 43, 40, 42, 33, 37, 41]),
                   'channels': np.array([ 0,  7, 15,  8,  1,  6, 14,  9, 13,  5,  2, 10, 12,  4,  3, 11]),
                   'grid_position': (1, 1, 1, 1)
        }
        window4 = {'site_numbers': np.array([64, 49, 63, 50, 62, 51, 61, 52, 60, 53, 59, 54, 58, 55, 57, 56]),
                   'channels': np.array([63, 56, 48, 55, 62, 57, 49, 54, 50, 58, 61, 53, 51, 59, 60, 52]),
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
          'NN_buz_64s': NN_buz_64s(),
          'NN_A2x32_poly5': NN_A2x32_poly5()}  # we'll import this...
