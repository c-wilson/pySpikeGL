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
    
    
    def build_data(self):
        #not implemented yet.
        data = {}
        return data 
    
    def build_window_params(self, acquisition_interface):
        ''' window_n = {channels: (1,2,...n), position =(1,2,3,4) 'grid position'} 
        window_1 = { }'''
        
        #this should return a windows dictionary.
        
        windows = {}
        return windows
    
    def __init__(self, acquisition_interface = 'SpikeGL'):
        self.data = self.build_data()
        self.window_params = self.build_window_params(acquisition_interface)
        
        return



class J_HIRES_4x16(AbstractProbe):
    
    def build_window_params(self, interface):
        window1 = {'channels' :         np.array([49,46,48,47,51,44,50,45,53,43,52,42,55,41,54,40]),
                   'site_numbers'  :    np.array([10, 7, 9, 8,12, 5,11, 6,14, 3,13, 4,16, 1,15, 2]),
                   'grid_position' :    ()
                   }
        window2 = {'channels' :         np.array([29, 7,27,25, 6, 5,25, 4,28, 3,26, 2,24, 1,30, 0]),
                   'site_numbers' :     np.array([26,23,25,24,28,21,27,22,30,19,29,20,32,17,31,18]),
                   'grid_position' :    ()
                   }
        window3 = {'channels' :         np.array([33,35,32,36,59,38,63,56,58,34,62,37,57,39,61,60]),
                   'site_numbers' :     np.array([41,40,42,39,43,38,44,37,45,36,46,35,47,34,48,33]),
                   'grid_position' :    ()
                   }
        window4 = {'channels' :         np.array([23, 9,22,13,21,10,20,14,19,11,18,15,17, 8,12,16]),
                   'site_numbers' :     np.array([57,56,58,55,59,54,60,53,61,52,62,51,63,50,64,49]),
                   'grid_position' :    ()
                   }
        
        window_params = [window1,window2,window3,window4]
        return window_params
        
        
        
        
        
probes ={'J_HIRES_4x16': J_HIRES_4x16()} # we'll import this...
