'''
Created on Jul 2, 2014

@author: chris
'''
import galry
import numpy as np
import scipy as sp
from probe_definitions import probes
from system_definitions import systems
from sgl_interface import SGLInterface, TestInterface
from PyQt4 import QtCore, QtGui
import time


class Main(QtGui.QMainWindow):
    def keyPressEvent(self, event):
        print 'press'




class SpikeGraph(QtGui.QWidget):
    '''
    classdocs
    '''
    pause = False
    
    trigger = QtCore.pyqtSignal()
    acquisition_trigger = QtCore.pyqtSignal(list, int)
    
    
    def __init__(self, probe_type, system_type, refresh_period_ms = 1000, trigger_ch = None, acquisition_source = 'SpikeGL', **kwargs):
        self.refresh_period_ms = refresh_period_ms
        super(SpikeGraph, self).__init__()

        self.init_acquisition(acquisition_source)
        probe = probes[probe_type]
        system = systems[system_type]
        self.acquisition_channels = self.combine_channels(probe, system)        
        self.init_ui(probe,self.acquisition_channels)
        self.init_timer()
    
    def init_acquisition(self,acquisition_source):
        
        
        self.acquisition_thread = QtCore.QThread()
        if acquisition_source == 'TEST':
            self.acquisition_interface = TestInterface()
        if acquisition_source == 'SpikeGL':
            self.acquisition_interface = SGLInterface()
            
        self.acquisition_interface.moveToThread(self.acquisition_thread)
        self.acquisition_thread.start()
        self.acquisition_trigger.connect(self.acquisition_interface.get_next_data)
        self.acquisition_interface.acquisition_complete.connect(self.update_graphs)


    
    def combine_channels(self, probe, system): #defines a global channel list which will be used to pull data from acquisition source.
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
    
    def keyPressEvent(self, event):
        print 'press'
        if type(event) == QtGui.QKeyEvent:
            print event.key()
            if event.key() == QtCore.Qt.Key_P:
                self.pause_update()
            event.accept()
        
    def pause_update(self):
        if self.pause:
            self.pause = False
        else:
            self.pause = True
            
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
        if not self.pause:
            self.stime = time.time()
            max_samples = self.acquisition_interface.acquisition_rate * self.refresh_period_ms/1000
            self.acquisition_trigger.emit(self.acquisition_channels, self.acquisition_interface.acquisition_rate * self.refresh_period_ms/1000)
            
#             self.new_samples = self.acquisition_interface.get_next_data(self.acquisition_channels,self.acquisition_interface.acquisition_rate * self.refresh_period_ms/1000)
#             print self.new_samples.shape
#             self.new_samples = 0.01* np.random.randn(64,self.acquisition_interface.acquisition_rate * self.refresh_period_ms/1000 )
#             print self.new_samples.shape

#             num_new_samples = self.new_samples.shape[1]
            
    #         print 'trigger'
    #         
    
            
#         time_take = time.time() - stime
#         print 'done '+ str(time_take)
    @QtCore.pyqtSlot()       
    def update_graphs(self):
        self.new_samples = self.acquisition_interface.data
        print time.time() - self.stime
        #TODO: we can probably make this more efficient in not copying this object.
        self.trigger.emit()
        print time.time() - self.stime
        return
        
        

class GraphWidget(galry.GalryWidget):
    pause = False
    _pause_ui = False
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
        self.pause_update_ui()
        self.popMenu = QtGui.QMenu()
        anaction = self.popMenu.addAction(QtGui.QAction(self.pause_label, self,
                statusTip="Cut the current selection's contents to the clipboard",
                triggered=self.pause_update))
        self.popMenu.addAction(QtGui.QAction("Reset View", self,
                statusTip="Cut the current selection's contents to the clipboard",
                triggered=self.interaction_manager.processors['navigation'].process_reset_event))

        self.popMenu.exec_(event.globalPos())
        self.pause_update_ui()
        return
    
    def mousePressEvent(self, e):
        self._pause_ui = True
        if self.mouse_blocked:
            return
        self.user_action_generator.mousePressEvent(e)
        self.process_interaction()
        
    def mouseReleaseEvent(self, e):
        if self.mouse_blocked:
            return
        self.user_action_generator.mouseReleaseEvent(e)
        self.process_interaction()    
        self._pause_ui =  False
        
    def keyPressEvent(self, e):
        if e.key() == QtCore.Qt.Key_P: # pause, global, propagate to main widget.
            e.ignore()
        pass
#         self.user_action_generator.keyPressEvent(e)
#         self.process_interaction()
#         # Close the application when pressing Q
#         if e.key() == QtCore.Qt.Key_Q:
#             if hasattr(self, 'window'):
#                 self.close_widget()

    
    def initialize(self):
        self.set_bindings(galry.PlotBindings)
        self.set_companion_classes(
            paint_manager=MyPaintManager,
            interaction_manager=MyPlotInteractionManager,)
        self.initialize_companion_classes()

    
    @QtCore.pyqtSlot()
    def update_graph_data(self):
        if not self.pause and not self._pause_ui:
            self.samples = self.parent_widget.new_samples[self.channel_mapping]
            self.p_samples = self.samples * self.interaction_manager.processors['navigation'].scalar + self.offsets
            num_samples = self.samples.shape[1]
            if num_samples != self.num_samples:
                self.num_samples = num_samples
                self.x = np.tile(np.linspace(-1., 1., num_samples), (len(self.channels), 1))
                
                self.paint_manager.reinitialize_visual(visual = 'plots', x = self.x, y = self.p_samples, autocolor = True)
                self.updateGL()
            else:
                self.paint_manager.set_data(visual = 'plots',position=np.vstack((self.x.ravel(), self.p_samples.ravel())).T, )
                self.updateGL()
            return
        else:
            pass

    def zoom_y(self):
        if hasattr(self,'samples'):
            self.processed_samples = self.samples * self.interaction_manager.processors['navigation'].scalar + self.offsets
            self.paint_manager.set_data(visual = 'plots', position=np.vstack((self.x.ravel(), self.processed_samples.ravel())).T)
            self.updateGL()   
        else:
            pass


    def calculate_offsets(self):
        y_limits = [-1,1]
        y_range = y_limits[1]- y_limits[0]
        steps = self.channels.size
        end_step_size = float(y_range) / (float(steps)+1.) 
        self.offsets = np.linspace((y_limits[0]+end_step_size), (y_limits[1]-end_step_size), steps)[:,np.newaxis]        
        return self.offsets

    @QtCore.pyqtSlot()
    def pause_update(self):
        if self.pause:
            self.pause = False
            self.pause_label = 'Pause'
        else:
            self.pause = True
            self.pause_label = 'Unpause'
        return
    def pause_update_ui(self): 
        if self._pause_ui:
            self._pause_ui = False
        else:
            self._pause_ui = True
    
class MyPaintManager(galry.PlotPaintManager):
    def initialize(self):
        self.parent.y = .01 * np.random.randn(self.parent.channels.size, 20833) + self.parent.calculate_offsets()
        self.parent.x = np.tile(np.linspace(-1., 1., 20833), (self.parent.channels.size, 1))
        self.add_visual(galry.PlotVisual, x=self.parent.x, y=self.parent.y, autocolor = True, name = 'plots')
        self.parent.num_samples = self.parent.y.shape[1]
        
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
        self.sx, self.sy = .01, .01
        self.scalar = 2.31757045631e-05
        self.sxl, self.syl = .01, .01
        self.rx, self.ry = 0., 0.
        self.navigation_rectangle = None
        self.parent.zoom_y()
    

app = QtGui.QApplication([])
mw = Main()
a = SpikeGraph('J_HIRES_4x16','acute2', acquisition_source = 'SpikeGL') 
palette = QtGui.QPalette()
palette.setColor(QtGui.QPalette.Background,QtCore.Qt.black)
mw.setPalette(palette)
mw.setCentralWidget(a)
mw.setWindowTitle('SPIKES WITH PYTHON!')
dim = QtCore.QRect(1700,-650,1000,1800)
mw.setGeometry(dim)
# mw.showFullScreen()
mw.showMaximized()
# p = a.palette()
# p.setColor(a.backgroundRole(), QtCore.Qt.black)
# a.setPalette(p)


mw.show()
a.timer.start(1000)

if __name__ == '__main__':
    import sys
    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        QtGui.QApplication.instance().exec_()
        