class AbstractSystem(object):
    '''
    classdocs
    '''

    data = {}
    window_params = []
    
    

    
    def build_window_params(self, acquisition_interface):
        ''' window_n = {channels: (1,2,...n), position =(1,2,3,4) 'grid position'} 
        window_1 = { }'''
        
        #this should return a windows dictionary.
        
        windows = {}
        return windows
    
    def build_data(self):
        data = {}
        return data 
    
        
        
    
    def __init__(self, acquisition_interface = 'SpikeGL'):
        self.window_params = self.build_window_params(acquisition_interface)
        self.data = self.build_data()        
        num_sites = self.calculate_sites()
        self.data['num_sites'] = num_sites
        return
    
class Acute2System(AbstractSystem):
    pass


systems = {'acute2' : Acute2System}
