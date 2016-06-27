from __future__ import division

__author__ = 'chris'

import galry
import numpy as np
from scipy import signal
from PyQt4 import QtCore, QtGui


class Discriminator(QtGui.QWidget):
    def __init__(self, probe):
        super(Discriminator, self).__init__()

    def build_window(self, probe):
        pass

    @QtCore.pyqtSlot()
    def data_ready(self):
        pass

    def find_spikes(self):
        """

        :return:
        """
        pass

    def plot_spikes(self):
        pass
