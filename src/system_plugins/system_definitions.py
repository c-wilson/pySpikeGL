import numpy as np


class AbstractSystem(object):
    '''
    classdocs
    '''

    data = {}
    window_params = []


    def build_window_params(self):
        ''' window_n = {channels: (1,2,...n), position =(1,2,3,4) 'grid position'} 
        window_1 = { }'''

        # this should return a windows dictionary.

        windows = {}
        return windows

    def build_data(self):
        data = {}
        return data


    def __init__(self):
        self.window_params = self.build_window_params()

        return


class Acute2System(AbstractSystem):
    def build_window_params(self):
        window1 = {'channels': np.array([192, 194, 224]),
                   'channel_fn': ['Sniff', 'Laser', 'FV'],
                   'grid_position': (0, 0, 1, 1),
                   'site_numbers': []
        }

        window_params = [window1]
        return window_params

    def __init__(self):
        self.acquisition_system = 'SpikeGL'
        super(Acute2System, self).__init__()

        return


systems = {'acute2': Acute2System()}
