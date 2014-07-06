'''
Created on Jul 2, 2014

@author: chris
'''
import galry
import numpy as np
import scipy as sp
from probe_definitions import probes
from sgl_interface import SGLInterface, TestInterface
from PyQt4 import QtCore, QtGui



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
        self.init_ui(probe)
        self.init_timer()

        
        
        
    
    def init_ui(self, probe):
        
        window = QtGui.QGridLayout()
        self.graph_widgets = [] #list of graph widget objects that we will fill below.
        for window_params in probe.window_params:
            temp_win = GraphWidget(window_params, self)
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
        
        self.timer.setInterval(50000)
        #start global timer for update.
        self.timer.start()

        return
    
    @QtCore.pyqtSlot()       
    def update(self):
        max_samples = self.acquisition_interface.acquisition_rate * self.refresh_period_ms/1000
#         new_samples = self.acquisition_interface.get_next_data(max_samples = max_samples)
        self.new_samples = 0.01* np.random.randn(64,self.acquisition_interface.acquisition_rate * self.refresh_period_ms/1000)
        num_new_samples = self.new_samples.shape[1]
        
        print 'trigger'
        self.trigger.emit()
        
        

class GraphWidget(galry.GalryWidget):
    
    
    def __init__(self, params, parent):
        self.parent_widget = parent
        self.channels = params['channels']
        self.sites = params['site_numbers']
        self.position = params['grid_position']
        self.num_samples = 0
        super(GraphWidget,self).__init__()
    
    def initialize(self):
        self.set_bindings(galry.PlotBindings)
        self.set_companion_classes(
            paint_manager=MyPaintManager,
            interaction_manager=MyPlotInteractionManager,)
        self.initialize_companion_classes()

    
    @QtCore.pyqtSlot()
    def update_graph_data(self):
        self.samples = self.parent_widget.new_samples[self.channels]
        self.processed_samples = self.samples * self.interaction_manager.processors['navigation'].scalar + self.offsets
        num_samples = self.samples.shape[1]
#         if num_samples != self.num_samples:
#             self.num_samples = num_samples
#             self.x = np.tile(np.linspace(-1., 1., num_samples), (len(self.channels), 1))
        position = np.vstack((self.x.flatten(), self.processed_samples.flatten())).T
        self.paint_manager.set_data(position=position)
        self.updateGL()

    def zoom_y(self):
        self.processed_samples = self.samples * self.interaction_manager.processors['navigation'].scalar + self.offsets
        position = np.vstack((self.x.flatten(), self.processed_samples.flatten())).T      
        self.paint_manager.set_data(position=position)
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
        self.parent.y = .01 * np.random.randn(self.parent.channels.size, 20833) + self.parent.calculate_offsets()
        self.parent.x = np.tile(np.linspace(-1., 1., 20833), (self.parent.channels.size, 1))
        self.add_visual(galry.PlotVisual, x=self.parent.x, y=self.parent.y, autocolor = True)
        
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
        