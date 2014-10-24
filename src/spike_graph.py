'''
Created on Jul 2, 2014

@author: chris
'''
import time

import galry
import numpy as np
from scipy import signal
from PyQt4 import QtCore, QtGui
from acq_interfaces.sgl_interface import SGLInterface256ch, TestInterface

from system_plugins.probe_definitions import probes
from system_plugins.system_definitions import systems
from buffers import CircularBuffer


class Main(QtGui.QMainWindow):
    def keyPressEvent(self, event):
        print 'press'

    def closeEvent(self, e):
        app.quit()


# TODO: implement unified zooming of widgets to be an option.
# TODO: implement mutex for acquisition system - graphing system shared variables or move them into signals
# TODO: move acquisition into multiprocessing process?
# TODO: execute filtering in multiprocessing.


class SpikeGraph(QtGui.QWidget):
    '''
    classdocs
    '''

    graph_trigger = QtCore.pyqtSignal(np.ndarray)
    acquisition_trigger = QtCore.pyqtSignal(list, int)
    _pause_ui_sig = QtCore.pyqtSignal()
    QUIT_TRIGGER = QtCore.pyqtSignal()

    def __init__(self, probe_type, system_config,
                 refresh_period_ms=1000, display_period=1000,
                 trigger_ch=66, q_app=None, **kwargs):

        self.filtering = True
        self.buffer_len = 20833 * 6
        self.triggering = False
        self.last_trigger_idx = 0
        self.triggered = False
        self.trigger_offset_ms = 300  # time before the trigger that you want to display
        self.pause = False  # pauses graphing updates AND acquisition.
        self.pause_ui = False  # only pauses the ui, not the acquisition.
        self.updating = False
        self.qApp = q_app
        self.refresh_period_ms = refresh_period_ms
        self.display_period = display_period
        super(SpikeGraph, self).__init__()
        self.trigger_ch = trigger_ch
        probe = probes[probe_type]
        system = systems[system_config]
        self.init_acquisition(system.acquisition_system)
        self.all_channels = self.build_channel_list(probe, system)
        self.buffer = CircularBuffer(len(self.all_channels), self.buffer_len)
        self.disp_samples = np.zeros((len(self.all_channels), self.source.fs * display_period / 1000), dtype=np.float64)
        self.init_ui(probe, system, self.all_channels)
        self.init_timer()
        self._pause_ui_sig.connect(self.pause_update_ui)
        self.build_filter()


    def closeEvent(self, e):
        print' close event'
        if self.qApp:
            self.qApp.quit()

    def init_acquisition(self, acquisition_source):


        self.acquisition_thread = QtCore.QThread()
        if acquisition_source == 'TEST':
            self.source = TestInterface()
        if acquisition_source == 'SpikeGL':
            self.source = SGLInterface256ch()

        #TODO: Get acquisition params from spikeGL to inform ADC gain value

        self.source.moveToThread(self.acquisition_thread)
        self.acquisition_thread.start()
        self.acquisition_trigger.connect(self.source.get_next_data)
        self.source.acquisition_complete.connect(self.update_graphs)
        return


    def build_channel_list(self, probe,
                           system):  #defines a global channel list which will be used to pull data from acquisition source.
        acquisition_channels = []
        channel_idx = []
        for idx, window in enumerate(probe.window_params):
            channels = window['channels'].tolist()
            acquisition_channels.extend(channels)
        acquisition_channels.extend(probe.data['non_displayed_chans'])
        if len(np.unique(acquisition_channels)) != len(acquisition_channels):
            tmp = np.array(acquisition_channels)
            for i in np.unique(tmp):
                if np.sum(tmp == i) > 1:
                    print 'duplicate of channel ' + str(i) + ' found!'
            raise ValueError('Duplicate channels found in probe definition.')
        self.e_phys_channel_number = len(acquisition_channels)
        for idx, window in enumerate(system.window_params):
            channels = window['channels'].tolist()
            acquisition_channels.extend(channels)
        acquisition_channels.sort()

        return acquisition_channels

    def init_ui(self, probe, system, channel_mapping):

        window = QtGui.QGridLayout()
        self.graph_widgets = []  #list of graph widget objects that we will fill below.
        for window_params in probe.window_params:
            temp_win = GraphWidget(window_params, self.all_channels, self)
            self.graph_widgets.append(temp_win)
        for widget in self.graph_widgets:
            position = widget.position
            window.addWidget(widget, position[0], position[1], position[2], position[3])

        self.system_window = SystemWidget(system.window_params[0], self.all_channels, self)

        self.setLayout(window)


    def keyPressEvent(self, event):
        #         print 'press'
        if type(event) == QtGui.QKeyEvent:
            if event.key() == QtCore.Qt.Key_P:
                self.pause_acquire()
            if event.key() == QtCore.Qt.Key_T:
                self.toggle_trigger()
            event.accept()

    @QtCore.pyqtSlot(int)
    def toggle_trigger(self, checked=None):
        if checked is not None:
            if checked == 2:
                self.triggering = True
            elif checked == 0:
                self.triggering = False
        else:
            if self.triggering:
                self.triggering = False
                self.triggering_checkbox.setChecked(False)
                print 'Leaving graph_trigger mode.'
            else:
                self.triggering_checkbox.setChecked(True)
                self.triggering = True
                print 'Trigger mode set: waiting for graph_trigger on ch: ' + str(self.trigger_ch) + '.'
        return

    def pause_acquire(self):
        if self.pause:
            self.pause = False
            print 'Unpausing.'
        else:
            self.pause = True
            self.source.close_connect()
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
        self.connect(self.timer, QtCore.SIGNAL('timeout()'), self, QtCore.SLOT("update()"))

        # connect graph widgets' update method (slot) to 
        # to global update signal that will be emitted after the acquisition data is loaded
        for widget in self.graph_widgets:
            self.graph_trigger.connect(widget.update_graph_data)
        self.graph_trigger.connect(self.system_window.update_graph_data)

        return

    @QtCore.pyqtSlot()
    def update(self):
        self.stime = time.time()

        if not self.pause:
            self.acquisition_trigger.emit(self.all_channels, self.source.fs * self.refresh_period_ms / 1000 * 3)

            # print 'done '+ str(time_take)

    @QtCore.pyqtSlot(np.ndarray)
    def update_graphs(self, source_data):
        # print time.time()-self.stime
        self.buffer.add_samples(source_data)
        #         self.buffer.add_samples(np.random.rand(67,20000))
        # print time.time() - self.stime
        #         print self.new_samples[:,64]
        #         self.filter_signal()

        if self.pause_ui or self.updating:  #we don't need to mess with anything else here, so lets get out.
            return
        self.updating = True
        disp_period_sample_num = self.source.fs * self.display_period / 1000

        if not self.triggering:
            disp_samples = self.buffer.sample_range(disp_period_sample_num)
        elif self.triggering and not self.triggered:
            disp_samples = None
            self.find_trigger()
        if self.triggering and self.triggered:
            trigger_offset_samples = self.source.fs * self.trigger_offset_ms / 1000
            disp_tail_idx = (
                                self.last_trigger_idx - trigger_offset_samples) % self.buffer.buffer_len  # index of first sample to display.
            disp_samples = self.buffer.sample_range(disp_period_sample_num,
                                                         tail=disp_tail_idx)  # returns false if the number of samples is not there.
        if disp_samples is not None:
            self.triggered = False  # we've acted on the trigger, so we will start looking for new triggers next time.
            if self.filtering:
                disp_samples[:] = self.filter_signal(disp_samples[:])  # bandpass filter.
            # print 'final' + str(time.time() - self.stime)
            self.graph_trigger.emit(disp_samples)
        print time.time() - self.stime
        self.updating = False
        return


    def build_filter(self, lp=5000., hp=300.):
        hp_rad = float(hp) / (float(self.source.fs) / 2)
        lp_rad = float(lp) / (float(self.source.fs) / 2)
        hp_rad = np.float64(hp_rad)
        lp_rad = np.float64(lp_rad)
        self.signal_filter = signal.butter(2, [hp_rad, lp_rad], 'bandpass', output='ba')
        return


    def filter_signal(self, disp_samples):
        if self.filtering:
            # s = time.time()
            a = disp_samples[:self.e_phys_channel_number, :]
            # b = map(lambda x: signal.filtfilt(self.signal_filter[0], self.signal_filter[1], x), a)
            b = signal.filtfilt(self.signal_filter[0],
                                self.signal_filter[1],
                                a)
            a[:] = b
            # print time.time()-s
        return disp_samples

    def find_trigger(self):
        self.th = self.buffer.samples[self.trigger_ch, :] > np.float64(.04)  # TTL threshold rounded down.
        if np.any(self.th):
            th_edges = np.convolve([1, -1], self.th, mode='same')
            th_idx = np.where(th_edges == 1)  # THIS IS FOR UPWARD EDGES!
            th_idx = th_idx[0][-1]
            if not (
                                self.last_trigger_idx == th_idx or th_idx == 0 or th_idx == self.buffer.head_idx):  # very very rare that two triggers will happen in the same idx position.
                # dont want the trigger to be 0 or to be == to the head_idx.
                self.triggered = True
                self.last_trigger_idx = th_idx
            else:
                print 'trigger reject'

    @QtCore.pyqtSlot(int)
    def toggle_filter(self, state):
        print state
        if state == 0:
            self.filtering = False
        elif state == 2:
            self.filtering = True
        return

    @QtCore.pyqtSlot(int)
    def change_display_period(self, new_val):
        print new_val
        self.display_period = new_val
        if self.display_period >= 3000:
            self.refresh_period_ms = self.display_period / 2
        else:
            self.refresh_period_ms = 1000
        self.timer.setInterval(self.refresh_period_ms)
        print self.refresh_period_ms
        for widget in self.graph_widgets:
            widget.interaction_manager.processors['navigation'].sx = 1.
            widget.interaction_manager.processors['navigation'].transform_view()

    @QtCore.pyqtSlot(QtCore.QEvent)
    def reset_all_views(self, event):
        for widget in self.graph_widgets:
            widget.interaction_manager.processors['navigation'].process_reset_event(event)

    @QtCore.pyqtSlot(int)
    def set_trigger_offset(self, new_val):
        self.trigger_offset_ms = new_val


    def build_parent_menu(self):
        self.parent_menu_items = QtGui.QWidget()
        self.parent_menu_items_layout = QtGui.QGridLayout(self.parent_menu_items)
        self.parent_menu_items_layout.setMargin(0)
        self.parent_menu_items_layout.setSpacing(0)
        self.filter_check = QtGui.QCheckBox('Apply filter', self.parent_menu_items)
        self.filter_check.setChecked(self.filtering)
        self.filter_check.stateChanged.connect(self.toggle_filter)
        self.pause_checked = QtGui.QCheckBox('Pause All', self.parent_menu_items)
        self.pause_checked.setChecked(self.pause)
        self.pause_checked.stateChanged.connect(self.pause_acquire)

        self.display_period_label = QtGui.QLabel('Display Period:')

        self.display_period_spinbox = QtGui.QSpinBox(self.parent_menu_items)
        self.display_period_spinbox.setRange(100, 5000)
        self.display_period_spinbox.setSuffix(' ms')
        self.display_period_spinbox.setValue(self.display_period)
        self.display_period_spinbox.setSingleStep(100)
        self.display_period_spinbox.valueChanged.connect(self.change_display_period)
        self.line = QtGui.QFrame()
        self.line.setFrameStyle(QtGui.QFrame.HLine)
        self.line2 = QtGui.QFrame()
        self.line2.setFrameStyle(QtGui.QFrame.HLine)

        self.triggering_checkbox = QtGui.QCheckBox('Wait for trigger', self.parent_menu_items)
        self.triggering_checkbox.setChecked(self.triggering)
        self.triggering_checkbox.stateChanged.connect(self.toggle_trigger)
        self.triggering_label = QtGui.QLabel('Trigger offset:')

        self.trigger_offset_spinbox = QtGui.QSpinBox(self.parent_menu_items)
        self.trigger_offset_spinbox.setMinimum(0)
        self.trigger_offset_spinbox.setMaximum(self.display_period)
        self.trigger_offset_spinbox.setValue(self.trigger_offset_ms)
        self.trigger_offset_spinbox.setSingleStep(10)
        self.trigger_offset_spinbox.setSuffix(' ms')
        self.trigger_offset_spinbox.valueChanged.connect(self.set_trigger_offset)

        self.parent_menu_items_layout.addWidget(self.filter_check, 1, 0, 1, 1)
        self.parent_menu_items_layout.addWidget(self.pause_checked, 0, 0, 1, 1)
        self.parent_menu_items_layout.addWidget(self.line, 2, 0, 1, 1)
        self.parent_menu_items_layout.addWidget(self.display_period_label, 3, 0, 1, 1)
        self.parent_menu_items_layout.addWidget(self.display_period_spinbox, 4, 0, 1, 1)
        self.parent_menu_items_layout.addWidget(self.line2, 5, 0, 1, 1)
        self.parent_menu_items_layout.addWidget(self.triggering_checkbox, 6, 0, 1, 1)
        self.parent_menu_items_layout.addWidget(self.triggering_label, 7, 0)
        self.parent_menu_items_layout.addWidget(self.trigger_offset_spinbox, 8, 0, 1, 1)


class GraphWidget(galry.GalryWidget):
    def closeEvent(self, e):
        app.quit()

    def __init__(self, params=None, global_channel_mapping=None, parent=SpikeGraph):
        self.parent_widget = parent
        self.channels = params['channels']
        self.channel_mapping = self.calculate_channel_mapping(global_channel_mapping)
        self.sites = params['site_numbers']
        self.position = params['grid_position']
        self.num_samples = 0
        self.pause_label = 'Pause widget'
        self.pause = False
        self._pause_ui = False
        super(GraphWidget, self).__init__()
        parent._pause_ui_sig.connect(self.pause_update_ui)

    def calculate_channel_mapping(self,
                                  channel_mapping):  # calculate where each channel is within the acquisition matrix. This will be used to pull data from the acquisition source matrix.
        channel_map_array = np.array([], dtype=int)
        for chan in self.channels:
            chan_map = channel_mapping.index(chan)
            channel_map_array = np.append(channel_map_array, chan_map)

        print channel_map_array
        return channel_map_array

    def mouseDoubleClickEvent(self, event):

        self.popMenu = QtGui.QMenu()
        self.pause_widget_checkbox = QtGui.QCheckBox('Pause widget')
        self.pause_widget_checkbox.setChecked(self.pause)
        self.pause_widget_checkbox.stateChanged.connect(self.pause_acquire)
        act0 = QtGui.QWidgetAction(self)
        act0.setDefaultWidget(self.pause_widget_checkbox)
        self.popMenu.addAction(act0)
        self.parent_widget.build_parent_menu()
        act = QtGui.QWidgetAction(self)
        act.setDefaultWidget(self.parent_widget.parent_menu_items)
        self.popMenu.addAction(act)
        self.popMenu.addSeparator()
        self.popMenu.addAction(QtGui.QAction("Reset widget view", self,
                                             statusTip="Cut the current selection's contents to the clipboard",
                                             triggered=self.interaction_manager.processors[
                                                 'navigation'].process_reset_event))
        self.popMenu.addAction(QtGui.QAction("Reset all views", self,
                                             statusTip="Cut the current selection's contents to the clipboard",
                                             triggered=self.parent_widget.reset_all_views))
        self.popMenu.exec_(event.globalPos())
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
        if e.key() == QtCore.Qt.Key_P:  # pause, global, propagate to main widget.
            e.ignore()
        elif e.key() == QtCore.Qt.Key_T:
            e.ignore()
        pass

    #         self.user_action_generator.keyPressEvent(e)
    # self.process_interaction()
    #         # Close the application when pressing Q
    #         if e.key() == QtCore.Qt.Key_Q:
    #             if hasattr(self, 'window'):
    #                 self.close_widget()


    def initialize(self):
        self.set_bindings(galry.PlotBindings)
        self.set_companion_classes(
            paint_manager=MyPaintManager,
            interaction_manager=MyPlotInteractionManager, )
        self.initialize_companion_classes()


    @QtCore.pyqtSlot(np.ndarray)
    def update_graph_data(self, all_chan_samples):
        if not self.pause and not self._pause_ui:
            #TODO: make the widgets use a view of the parent.display_samples array.
            samples = all_chan_samples[self.channel_mapping, :]
            # self.samples = self.parent_widget.samples[self.channel_mapping,:]
            p_samples = samples * self.interaction_manager.processors['navigation'].scalar
            p_samples += self.offsets
            num_samples = samples.shape[1]
            if num_samples != self.num_samples:
                self.num_samples = num_samples
                self.x = np.tile(np.linspace(-1., 1., num_samples), (len(self.channels), 1))
                self.paint_manager.reinitialize_visual(visual='plots', x=self.x, y=p_samples, autocolor=True)
                self.updateGL()
            else:
                self.paint_manager.set_data(visual='plots',
                                            position=np.vstack((self.x.ravel(), p_samples.ravel())).T, )
                self.updateGL()
            self.samples = samples
            return
        else:
            pass

    def zoom_y(self):
        if hasattr(self, 'samples'):
            p_samples = self.samples * self.interaction_manager.processors[
                'navigation'].scalar
            p_samples += self.offsets
            self.paint_manager.set_data(visual='plots',
                                        position=np.vstack((self.x.ravel(), p_samples.ravel())).T)
            self.updateGL()
        else:
            pass


    def calculate_offsets(self):
        y_limits = [-1, 1]
        y_range = y_limits[1] - y_limits[0]
        steps = self.channels.size
        end_step_size = float(y_range) / (float(steps) + 1.)
        self.offsets = np.linspace((y_limits[0] + end_step_size), (y_limits[1] - end_step_size), steps)[:, np.newaxis]
        return self.offsets

    @QtCore.pyqtSlot(int)
    def pause_acquire(self, val=None):
        if val == 2:
            self.pause = True
        elif val == 0:
            self.pause = False


    @QtCore.pyqtSlot()
    def pause_update_ui(self):
        if self._pause_ui:
            self._pause_ui = False
        else:
            self._pause_ui = True


class SystemWidget(GraphWidget):
    #to be impletmented, currently is just a graphwidget...
    pass


class MyPaintManager(galry.PlotPaintManager):
    def initialize(self):
        self.parent.y = .01 * np.random.randn(self.parent.channels.size, 20833) + self.parent.calculate_offsets()
        self.parent.x = np.tile(np.linspace(-1., 1., 20833), (self.parent.channels.size, 1))
        self.add_visual(galry.PlotVisual, x=self.parent.x, y=self.parent.y, autocolor=True, name='plots')
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
        self.add_processor(galry.GridEventProcessor, name='grid')  # , activated=False)


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
        self.scalar *= np.exp(
            dy)  # this allows us to change the scaling on the y axis outside of the zoom function.
        # self.sy *= np.exp(dy)

        # constrain scaling
        if self.constrain_navigation:
            self.sx = np.clip(self.sx, self.sxmin, self.sxmax)
            self.sy = np.clip(self.sy, self.symin, self.symax)

        self.tx += -px * (1. / self.sxl - 1. / self.sx)
        self.ty += -py * (1. / self.syl - 1. / self.sy)
        self.sxl = self.sx
        self.syl = self.sy
        self.constrain_navigation = True
        self.parent.zoom_y()


    def reset(self):
        """Reset the navigation."""
        self.tx, self.ty, self.tz = 0., 0., 0.
        self.sx, self.sy = .01, .01
        self.scalar = .001
        self.sxl, self.syl = .01, .01
        self.rx, self.ry = 0., 0.
        self.navigation_rectangle = None
        self.parent.zoom_y()


app = QtGui.QApplication([])
mw = Main()
a = SpikeGraph('NN_buz_64s', 'acute2', acquisition_source='SpikeGL', refresh_period_ms=1000, display_period=2000,
               q_app=app)
# J_HIRES_4x16

palette = QtGui.QPalette()
palette.setColor(QtGui.QPalette.Background, QtCore.Qt.black)
mw.setPalette(palette)
mw.setCentralWidget(a)
mw.setWindowTitle("Spike-rosoft SPIKESCOPE Viewer")
dim_mw = QtCore.QRect(1700, -650, 1000, 1800)
mw.setGeometry(dim_mw)
# mw.showFullScreen()
mw.showMaximized()
dim_sw = QtCore.QRect(1150, 200, 400, 600)
a.system_window.setGeometry(dim_sw)
a.system_window.setWindowTitle('Spike-rosoft SPIKESCOPE Control')
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

        app = QtGui.QApplication.exec_()
        a.source.close_connect()
    
        