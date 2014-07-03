'''
Created on Jul 2, 2014

@author: chris
'''
from PyQt4 import QtCore, QtGui
import pyqtgraph as pg
import numpy as np
import scipy as sp
from probe_definitions import probes
from sgl_interface import SGLInterface, TestInterface



class SpikeGraph(QtGui.QWidget):
    '''
    classdocs
    '''
    
    trigger = QtCore.pyqtSignal()
       
    def __init__(self, probe_type, refresh_period_ms = 1000, trigger_ch = None, acquisition_source = 'SpikeGL', **kwargs):
        self.refresh_period_ms = 1000
        super(SpikeGraph, self).__init__()
        if acquisition_source == 'SpikeGL':
            self.acquisition_interface = SGLInterface()
        elif acquisition_source == 'TEST':
            self.acquisition_interface = TestInterface()
        self.max_window_size = self.acquisition_interface.acquisition_rate * 2 #10 second window.(might be too big)
        probe = probes[probe_type]
        self.init_ui(probe)

        self.samples = np.zeros((probe.data['num_sites'],self.max_window_size))
        self.x = self.make_x(self.max_window_size)
        self.init_timing()
        
        
        self.show()
        
    def init_ui(self, probe):
        
        window = QtGui.QGridLayout()
        self.graph_widgets = [] #list of graph widget objects that we will fill below.
        for window_params in probe.window_params:
            temp_win = GraphWidget(window_params,self)
            self.graph_widgets.append(temp_win)
        for widget in self.graph_widgets:
            position = widget.position
            print position
            print widget
            window.addWidget(widget, position[0],position[1],position[2],position[3])
        self.setLayout(window)
        self.setGeometry(300, 300, 600, 600) 

        
    def init_timing(self):
        #make timer for getting information from acquisition system
        self.timer = QtCore.QTimer()
        self.connect(self.timer,QtCore.SIGNAL('timeout()'),self,QtCore.SLOT("update()") )
        
        # connect graph widgets' update method (slot) to 
        # to global update signal that will be emitted after the acquisition data is loaded
        for widget in self.graph_widgets:
            self.trigger.connect(widget.update_graph_data)
        
        #start global timer for update.
        self.timer.start(self.refresh_period_ms)
        return
    
    def make_x(self, num_samples): #make x-axis with 0 at the far right.
        num_seconds = num_samples / self.acquisition_interface.acquisition_rate
        return np.linspace(-num_seconds,0,num_samples)
    
    @QtCore.pyqtSlot()       
    def update(self):
        print 'updating'
        max_samples = self.acquisition_interface.acquisition_rate * self.refresh_period_ms/1000
#         new_samples = self.acquisition_interface.get_next_data(max_samples = max_samples)
        self.new_samples = np.random.randn(64,self.acquisition_interface.acquisition_rate * self.refresh_period_ms/1000)
        num_new_samples = self.new_samples.shape[1]
        
        self.samples = self.new_samples
#         self.samples = np.roll(self.samples,-num_new_samples) #shift and..
#         self.samples[:,-num_new_samples:] = self.new_samples # write!
        #TODO: take this out:
        print 'updating'
        
        self.x = self.make_x(self.samples.shape[1])
        self.trigger.emit()
        return

class GraphWidget(pg.PlotWidget):
    
    def __init__(self, params,parent_class):
        super(GraphWidget, self).__init__()
        self.channels = params['channels']
        self.sites = params['site_numbers']
        self.position = params['grid_position']
        self.setLabel('left', '', units = 'V')
        self.setLabel('bottom', 'Time', units = 's')
        #TODO: try downsampling:
        #self.setDownsampling(True, True, 'peak')
        #TODO: setYRange appropriately

        self.add_channels()
#         self.useOpenGL()
        self.parent_class = parent_class
        self.disableAutoRange()
        self.YRange = (0, 120)
        self.XRange = (-1,0)
        self.setDownsampling(True,True,'peak')
#         self.useOpenGL()
        
        
        
        
    def add_channels(self):
        self.plots = []
        for chan in self.channels:
            self.plots.append(self.plot())
    
    
    def calculate_offsets(self):
        y_limits = self.viewRange()[1]
        y_range = y_limits[1]- y_limits[0]
        steps = self.channels.size
        end_step_size = float(y_range) / float(steps)+1. / 2.
        self.offsets = np.linspace(end_step_size, (y_range-end_step_size), steps)
        self.offsets.shape = steps, 1
        
        return
        
        
    

    
    @QtCore.pyqtSlot()
    def update_graph_data(self):
        samples = self.parent_class.samples[self.channels]
#         samples = samples * self.interaction_manager.processors['navigation'].scalar + self.multi_plot_offsets
        num_samples = samples.shape[1]
        self.calculate_offsets()
        samples = samples + self.offsets
        for i_ch, plot in enumerate(self.plots):
            plot.setData(x = self.parent_class.x, y = samples[i_ch])
        return
            

app = QtGui.QApplication([])
mw = QtGui.QMainWindow()
a = SpikeGraph('J_HIRES_4x16', acquisition_source = 'TEST') 
mw.setCentralWidget(a)
mw.show()

if __name__ == '__main__':
    import sys
    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        QtGui.QApplication.instance().exec_()