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
    pause = False # pauses graphing updates AND acquisition.
    pause_ui = False #only pauses the ui, not the acquisition.
    
    trigger = QtCore.pyqtSignal()
    acquisition_trigger = QtCore.pyqtSignal(list, int)
    _pause_ui_sig = QtCore.pyqtSignal()
    last_trigger_idx = 0
    _head_idx = 0
    triggering = False
    triggered = False
    buffer_len = 20833*10
    
    def __init__(self, probe_type, system_config, refresh_period_ms = 1000, display_period = 1000, trigger_ch = 1, **kwargs):
        self.refresh_period_ms = refresh_period_ms
        self.display_period = display_period
        super(SpikeGraph, self).__init__()
        self.trigger_ch = trigger_ch
        
        probe = probes[probe_type]
        system = systems[system_config]
        self.init_acquisition(system.acquisition_system)
        self.acquisition_channels = self.combine_channels(probe, system)  
        
        self.samples = np.zeros((len(self.acquisition_channels),self.buffer_len),dtype = np.float32)
        self.disp_samples = np.zeros((len(self.acquisition_channels), self.acquisition_interface.acquisition_rate*display_period/1000),dtype = np.float32)

              
        self.init_ui(probe,system,self.acquisition_channels)
        self.init_timer()
        self._pause_ui_sig.connect(self.pause_update_ui)
    
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
        return


    
    def combine_channels(self, probe, system): #defines a global channel list which will be used to pull data from acquisition source.
        acquisition_channels = []
        channel_idx = []
        for idx, window in enumerate(probe.window_params):
            channels = window['channels'].tolist()
            acquisition_channels.extend(channels)
        for idx, window in enumerate(system.window_params):
            channels = window['channels'].tolist()
            acquisition_channels.extend(channels)
        acquisition_channels.sort() 
        return acquisition_channels
    
    def init_ui(self, probe, system, channel_mapping):
        
        window = QtGui.QGridLayout()
        self.graph_widgets = [] #list of graph widget objects that we will fill below.
        for window_params in probe.window_params:
            temp_win = GraphWidget(window_params,self.acquisition_channels, self)
            self.graph_widgets.append(temp_win)
        for widget in self.graph_widgets:
            position = widget.position
            window.addWidget(widget, position[0],position[1],position[2],position[3])
        
        print system.window_params
        self.system_window = SystemWidget(system.window_params[0], self.acquisition_channels, self)
        
        
        self.setLayout(window)
        
    
    def keyPressEvent(self, event):
#         print 'press'
        if type(event) == QtGui.QKeyEvent:
            if event.key() == QtCore.Qt.Key_P:
                self.pause_acquire()
            if event.key() == QtCore.Qt.Key_T:
                self.set_triggering_mode()
            event.accept()
            
    def set_triggering_mode(self):
        if self.triggering:
            self.triggering = False
            print 'Leaving trigger mode.'
        else:
            self.triggering = True
            print 'Trigger mode set: waiting for trigger on ch: ' + str(self.trigger_ch) + '.'
        return
        
    def pause_acquire(self):
        if self.pause:
            self.pause = False
            print 'Unpausing.'
        else:
            self.pause = True
            self.acquisition_interface.close_connect()
            print 'Pausing.'
    
    @QtCore.pyqtSlot()
    def pause_update_ui(self):
        if self.pause_ui:
            self.pause_ui = False
        else:
            self.pause_ui = True
            
    def init_timer(self):
        #make timer for getting information from acquisition system
        self.timer = QtCore.QTimer()
        self.connect(self.timer,QtCore.SIGNAL('timeout()'),self,QtCore.SLOT("update()") )
        
        # connect graph widgets' update method (slot) to 
        # to global update signal that will be emitted after the acquisition data is loaded
        for widget in self.graph_widgets:
            self.trigger.connect(widget.update_graph_data)
        self.trigger.connect(self.system_window.update_graph_data)

        return
    
    @QtCore.pyqtSlot()       
    def update(self):
        if not self.pause:
            self.acquisition_trigger.emit(self.acquisition_channels, self.acquisition_interface.acquisition_rate * self.refresh_period_ms/1000*3)

#         print 'done '+ str(time_take)
    @QtCore.pyqtSlot()       
    def update_graphs(self):
        self.stime = time.time()
        self.new_samples =  self.acquisition_interface.data
#         start = self.samples.shape[1]-self.new_samples.shape[1]
#         print start
        #roll the sample buffer, this implementation is far faster than rolling the buffer ~4ms, we can probably 
        #make this more efficient by using a ring index.
        
        new_head_idx = (self._head_idx+self.new_samples.shape[1])%self.buffer_len
        if new_head_idx < self._head_idx:
            self.samples[:,(self._head_idx):] = self.new_samples[:,:-new_head_idx]
            self.samples[:,:new_head_idx] = self.new_samples[:,-(new_head_idx):]
        else:        
            self.samples[:,self._head_idx:new_head_idx] = self.new_samples[:,:]       
        
        self._head_idx = new_head_idx
        
        if self.pause_ui: #we don't need to mess with anything else here, so lets get out.
            return
        
        if not self.triggering:
            disp_start_idx = (self._head_idx - (self.acquisition_interface.acquisition_rate * self.display_period/1000))%self.buffer_len
            if disp_start_idx > self._head_idx:
                self.disp_samples[:,:-self._head_idx] = self.samples[:,disp_start_idx:]
                self.disp_samples[:,-self._head_idx:] = self.samples[:,:self._head_idx]
            else:
                self.disp_samples = self.samples[:,disp_start_idx:self._head_idx]
            self.trigger.emit()
        elif self.triggering and not self.triggered:
            self.find_trigger()
            
        if self.triggering and self.triggered:
            if (self._head_idx - self.last_trigger_idx)%self.buffer_len > self.disp_samples:
                self.triggered = False
                # update display
                disp_start_idx = self.last_trigger_idx
                if disp_start_idx > self._head_idx:
                    self.disp_samples[:,:-self._head_idx] = self.samples[:,disp_start_idx:]
                    self.disp_samples[:,-self._head_idx:] = self.samples[:,:self._head_idx]
                else:
                    self.disp_samples = self.samples[:,disp_start_idx:self._head_idx]
            self.trigger.emit()        
        return
        
        
    def find_trigger(self):
        self.th = self.samples[self.trigger_ch,:] > np.float32(3.3) #TTL threshold rounded down.
        if np.any(self.th):
            th_edges = np.convolve([1, -1], self.th, mode='same')
            th_idx = np.where(th_edges == 1)[-1] #THIS IS FOR UPWARD EDGES!
            if self.last_trigger_idx != th_idx: #very very rare that two triggers will happen in the same idx position.
                self.triggered = True
                self.last_trigger_idx
        
                
        
        
        

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
        parent._pause_ui_sig.connect(self.pause_update_ui)
        
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
                triggered=self.pause_acquire))
        self.popMenu.addAction(QtGui.QAction("Reset View", self,
                statusTip="Cut the current selection's contents to the clipboard",
                triggered=self.interaction_manager.processors['navigation'].process_reset_event))

        self.popMenu.exec_(event.globalPos())
        self.pause_update_ui()
        return
    
    def mousePressEvent(self, e):
        self.parent_widget._pause_ui_sig.emit()
        if self.mouse_blocked:
            return
        self.user_action_generator.mousePressEvent(e)
        self.process_interaction()
        
    def mouseReleaseEvent(self, e):
        if self.mouse_blocked:
            return
        self.user_action_generator.mouseReleaseEvent(e)
        self.process_interaction()    
        self.parent_widget._pause_ui_sig.emit()
        
    def keyPressEvent(self, e):
        if e.key() == QtCore.Qt.Key_P: # pause, global, propagate to main widget.
            e.ignore()
        elif e.key() == QtCore.Qt.Key_T:
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
            self.samples = self.parent_widget.disp_samples[self.channel_mapping,:]
#             self.samples = self.parent_widget.samples[self.channel_mapping,:]
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
    def pause_acquire(self):
        if self.pause:
            self.pause = False
            self.pause_label = 'Pause'
        else:
            self.pause = True
            self.pause_label = 'Unpause'
        return
    
    @QtCore.pyqtSlot()
    def pause_update_ui(self): 
        if self._pause_ui:
            self._pause_ui = False
        else:
            self._pause_ui = True
    
    
class SystemWidget(GraphWidget): 
    #to be impletmented
    pass
    
    
    
    
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
        self.scalar = 25
        self.sxl, self.syl = .01, .01
        self.rx, self.ry = 0., 0.
        self.navigation_rectangle = None
        self.parent.zoom_y()
    

app = QtGui.QApplication([])
mw = Main()
a = SpikeGraph('J_HIRES_4x16','acute2', acquisition_source = 'SpikeGL', refresh_period_ms = 1000, display_period = 2000)
palette = QtGui.QPalette()
palette.setColor(QtGui.QPalette.Background,QtCore.Qt.black)
mw.setPalette(palette)
mw.setCentralWidget(a)
mw.setWindowTitle("SPIKESCOPE 3,000,001 by Spike-rosoft")
dim = QtCore.QRect(1700,-650,1000,1800)
mw.setGeometry(dim)
# mw.showFullScreen()
mw.showMaximized()
a.system_window.setWindowTitle('SPIKESCOPE CONTROL')
a.system_window.show()
# p = a.palette()
# p.setColor(a.backgroundRole(), QtCore.Qt.black)
# a.setPalette(p)


mw.show()
a.timer.start(1000)

if __name__ == '__main__':
    import sys
    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        print 'running'
        QtGui.QApplication.instance().exec_()
        print 'done'
        a.acquisition_interface.close_connect()
    
        