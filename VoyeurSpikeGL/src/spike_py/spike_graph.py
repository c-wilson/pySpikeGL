'''
Created on Jul 2, 2014

@author: chris
'''
import galry
import numpy as np
import scipy as sp
from probe_definitions import probes
from system_definition import systems
from sgl_interface import SGLInterface, TestInterface
from PyQt4 import QtCore, QtGui
import time


class SpikeGraph(QtGui.QWidget):
    '''
    classdocs
    '''
    
    trigger = QtCore.pyqtSignal()
    def __init__(self, probe_type, refresh_period_ms = 1000, trigger_ch = None, acquisition_source = 'SpikeGL', **kwargs):
        self.refresh_period_ms = 1000
        super(SpikeGraph, self).__init__()
        if acquisition_source == 'TEST':
            self.acquisition_interface = TestInterface
        if acquisition_source == 'SpikeGL':
            self.acquisition_interface = SGLInterface()
        
        probe = probes[probe_type]
        system = system_definition[system]
        self.acquisition_channels = self.combine_channels(probe,system)        
        self.init_ui(probe,self.acquisition_channels)
        self.init_timer()

    
    
    def combine_channels(self, probe): #defines a global channel list which will be used to pull data from acquisition source.
        acquisition_channels = []
        channel_idx = []
        for idx, window in enumerate(probe.window_params):
            channels = window['channels'].tolist()
            acquisition_channels.extend(channels)
        acquisition_channels.sort() 
        return acquisition_channels
    
    def init_ui(self, probe, channel_mapping):
        
        window = QtGui.QGridLayout()
        self.graph_widgets = [] #list of graph widget objects that we will fill below.
        for window_params in probe.window_params:
            temp_win = GraphWidget(window_params,self.acquisition_channels, self)
            self.graph_widgets.append(temp_win)
        for widget in self.graph_widgets:
            position = widget.position
            window.addWidget(widget, position[0],position[1],position[2],position[3])
        
        self.setLayout(window)      
        
        self.setGeometry(300, 300, 600, 600)  
        
    def init_timer(self):
        #make timer for getting information from acquisition system
        self.timer = QtCore.QTimer()
        self.connect(self.timer,QtCore.SIGNAL('timeout()'),self,QtCore.SLOT("update()") )
        
        # connect graph widgets' update method (slot) to 
        # to global update signal that will be emitted after the acquisition data is loaded
        for widget in self.graph_widgets:
            self.trigger.connect(widget.update_graph_data)

        return
    
    @QtCore.pyqtSlot()       
    def update(self):
        max_samples = self.acquisition_interface.acquisition_rate * self.refresh_period_ms/1000
#         new_samples = self.acquisition_interface.get_next_data(max_samples = max_samples)
        self.new_samples = 0.01* np.random.randn(64,self.acquisition_interface.acquisition_rate * self.refresh_period_ms/1000 *2)
        num_new_samples = self.new_samples.shape[1]
        
#         print 'trigger'
#         stime = time.time()
        self.trigger.emit()
#         time_take = time.time() - stime
#         print 'done '+ str(time_take)
        
        

class GraphWidget(galry.GalryWidget):
    pause = False
    pause_label = 'Pause'
    
    def __init__(self, params, global_channel_mapping, parent):
        self.parent_widget = parent
        self.channels = params['channels']
        self.channel_mapping = self.calculate_channel_mapping(global_channel_mapping) 
        self.sites = params['site_numbers']
        self.position = params['grid_position']
        self.num_samples = 0
        super(GraphWidget,self).__init__()
        
    def calculate_channel_mapping(self, channel_mapping): #calculate where each channel is within the acquisition matrix. This will be used to pull data from the acquisition source matrix.
        channel_map_array = np.array([], dtype = int)
        for chan in self.channels:
            chan_map = channel_mapping.index(chan)
            channel_map_array = np.append(channel_map_array,chan_map)
        return channel_map_array
        
    def mouseDoubleClickEvent(self,event):
        print 'CME!'
        self.popMenu = QtGui.QMenu()
        anaction = self.popMenu.addAction(QtGui.QAction(self.pause_label, self,
                statusTip="Cut the current selection's contents to the clipboard",
                triggered=self.pause_update))
        self.popMenu.addAction(QtGui.QAction("Reset View", self,
                statusTip="Cut the current selection's contents to the clipboard",
                triggered=self.interaction_manager.processors['navigation'].process_reset_event))

        self.popMenu.exec_(event.globalPos())
        
        return
    
    def pause_update(self):
        if self.pause:
            self.pause = False
            self.pause_label = 'Pause'
        else:
            self.pause = True
            self.pause_label = 'Unpause'
    
    
    def initialize(self):
        self.set_bindings(galry.PlotBindings)
        self.set_companion_classes(
            paint_manager=MyPaintManager,
            interaction_manager=MyPlotInteractionManager,)
        self.initialize_companion_classes()

    
    @QtCore.pyqtSlot()
    def update_graph_data(self):
        if not self.pause:
            self.samples = self.parent_widget.new_samples[self.channel_mapping]
            self.p_samples = self.samples * self.interaction_manager.processors['navigation'].scalar + self.offsets
            #num_samples = self.samples.shape[1]
    #         if num_samples != self.num_samples:
    #             self.num_samples = num_samples
    #             self.x = np.tile(np.linspace(-1., 1., num_samples), (len(self.channels), 1))
    
            self.paint_manager.set_data(position=np.vstack((self.x.ravel(), self.p_samples.ravel())).T)
            self.updateGL()

    def zoom_y(self):
        self.processed_samples = self.samples * self.interaction_manager.processors['navigation'].scalar + self.offsets
        self.paint_manager.set_data(position=np.vstack((self.x.ravel(), self.processed_samples.ravel())).T)
        self.updateGL()          


    def calculate_offsets(self):
        y_limits = [-1,1]
        y_range = y_limits[1]- y_limits[0]
        steps = self.channels.size
        end_step_size = float(y_range) / (float(steps)+1.) 
        self.offsets = np.linspace((y_limits[0]+end_step_size), (y_limits[1]-end_step_size), steps)[:,np.newaxis]        
        return self.offsets

    
class MyPaintManager(galry.PlotPaintManager):
    def initialize(self):
        self.parent.y = .01 * np.random.randn(self.parent.channels.size, 20833*2) + self.parent.calculate_offsets()
        self.parent.x = np.tile(np.linspace(-1., 1., 20833*2), (self.parent.channels.size, 1))
        self.add_visual(galry.PlotVisual, x=self.parent.x, y=self.parent.y, autocolor = True,)
        
class MyPlotInteractionManager(galry.DefaultInteractionManager):
    def initialize_default(self, constrain_navigation=True,
        momentum=False,
        # normalization_viewbox=None
        ):
        super(MyPlotInteractionManager, self).initialize_default()
        self.add_processor(MyNavigationEventProcessor,
            constrain_navigation=True, 
            # normalization_viewbox=normalization_viewbox,
            momentum=momentum,
            name='navigation')
        self.add_processor(galry.GridEventProcessor, name='grid')#, activated=False)
        
class MyNavigationEventProcessor(galry.NavigationEventProcessor):   
    def zoom(self, parameter):
        """Zoom along the x,y coordinates.
        
        Arguments:
          * parameter: (dx, px, dy, py)
        
        """
        dx, px, dy, py = parameter
        
        
        if self.parent.constrain_ratio:
            if (dx >= 0) and (dy >= 0):
                dx, dy = (max(dx, dy),) * 2
            elif (dx <= 0) and (dy <= 0):
                dx, dy = (min(dx, dy),) * 2
            else:
                dx = dy = 0
        self.sx *= np.exp(dx)
        self.scalar *= np.exp(dy) # this allows us to change the scaling on the y axis outside of the zoom function.        
        #self.sy *= np.exp(dy)
        
        # constrain scaling
        if self.constrain_navigation:
            self.sx = np.clip(self.sx, self.sxmin, self.sxmax)
            self.sy = np.clip(self.sy, self.symin, self.symax)
        
        self.tx += -px * (1./self.sxl - 1./self.sx)
        self.ty += -py * (1./self.syl - 1./self.sy)
        self.sxl = self.sx
        self.syl = self.sy
        self.constrain_navigation = True
        self.parent.zoom_y()
        
                
    def reset(self):
        """Reset the navigation."""
        self.tx, self.ty, self.tz = 0., 0., 0.
        self.sx, self.sy = 1., 1.
        self.scalar = 1.
        self.sxl, self.syl = 1., 1.
        self.rx, self.ry = 0., 0.
        self.navigation_rectangle = None
    

app = QtGui.QApplication([])
mw = QtGui.QMainWindow()
a = SpikeGraph('J_HIRES_4x16', acquisition_source = 'TEST') 
palette = QtGui.QPalette()
palette.setColor(QtGui.QPalette.Background,QtCore.Qt.black)
mw.setPalette(palette)
mw.setCentralWidget(a)

# p = a.palette()
# p.setColor(a.backgroundRole(), QtCore.Qt.black)
# a.setPalette(p)


mw.show()
a.timer.start(1000)

if __name__ == '__main__':
    import sys
    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        QtGui.QApplication.instance().exec_()
        