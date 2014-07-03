'''
Created on Jul 2, 2014

@author: chris
'''
from PyQt4 import QtCore, QtGui
import galry
import numpy as np
import scipy as sp
from probe_definitions import probes
from sgl_interface import SGLInterface


class SpikeGraph(QtGui.QWidget):
    '''
    classdocs
    '''
    
    trigger = QtCore.pyqtSignal(np.ndarray)
    
    def __init__(self, probe_type, refresh_period_ms = 1000, trigger_ch = None, acquisition_source = 'SpikeGL', **kwargs):
        self.refresh_period_ms = 1000
        super(SpikeGraph, self).__init__()
        if acquisition_source == 'SpikeGL':
            self.acquisition_interface = SGLInterface()
        
        probe = probes[probe_type]
        self.init_ui(probe)
        self.init_timing()

        
        
        
        self.show()
        
    
    def init_ui(self, probe):
        
        window = QtGui.QGridLayout()
        self.graph_widgets = [] #list of graph widget objects that we will fill below.
        for window_params in probe.window_params:
            temp_win = GraphWidget(window_params)
            self.graph_widgets.append(temp_win)
        for widget in self.graph_widgets:
            position = widget.position
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
    
    @QtCore.pyqtSlot()       
    def update(self):
        y = .01 * np.random.randn(64, self.refresh_period_ms)
        
        print 'updating'
        
        self.trigger.emit(y)

class GraphWidget(galry.GalryWidget):
    
    
    def __init__(self, params,parent):
        self.channels = params['channels']
        self.sites = params['sites']
        self.position = params['grid_position']
    
    def initialize(self):
        self.set_bindings(galry.PlotBindings)
        self.set_companion_classes(
            paint_manager=MyPaintManager,
            interaction_manager=MyPlotInteractionManager,)
        self.initialize_companion_classes()
        self.y = .01 * np.random.randn(5, 1000) + np.linspace(-.75, .75, 5)[:,np.newaxis]
        self.x = np.tile(np.linspace(-1., 1., 1000), (5, 1))
        self.multi_plot_offsets = np.linspace(-.75, .75, 5)[:,np.newaxis]
        for key,val in self.interaction_manager.processors.iteritems():
            print key    
    
    @QtCore.pyqtSlot(np.ndarray)
    def update_graph_data(self, samples):
        samples = samples[self.channels]
        samples = samples * self.interaction_manager.processors['navigation'].scalar + self.multi_plot_offsets
        num_samples = samples.shape[1]
        if num_samples != self.num_samples:
            self.num_samples = num_samples
            self.x = np.linspace(start, stop, num, endpoint, retstep)
            viewbox = self.interaction_manager.processors['navigation'].get_viewbox()
            self.interaction_manager.processors['navigation'].set_viewbox(0,viewbox[1],x_max_ms,viewbox[3])
            
        
        position = np.vstack((self.x.flatten))















    
    
    
class MyPaintManager(galry.PlotPaintManager):
    def initialize(self):
        self.x = np.tile(np.linspace(-1., 1., 1000), (5, 1))
        self.y = .01 * np.random.randn(5, 1000) + np.linspace(-.75, .75, 5)[:,np.newaxis]
        self.add_visual(galry.PlotVisual, x=self.x, y=self.y, autocolor = True)
        
class MyPlotInteractionManager(galry.DefaultInteractionManager):
    def initialize_default(self, constrain_navigation=None,
        momentum=False,
        # normalization_viewbox=None
        ):
        super(MyPlotInteractionManager, self).initialize_default()
        self.add_processor(MyNavigationEventProcessor,
            constrain_navigation=constrain_navigation, 
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
        #self.sx *= np.exp(dx)
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
        
    def reset(self):
        """Reset the navigation."""
        self.tx, self.ty, self.tz = 0., 0., 0.
        self.sx, self.sy = 1., 1.
        self.scalar = 1.
        self.sxl, self.syl = 1., 1.
        self.rx, self.ry = 0., 0.
        self.navigation_rectangle = None
    

        