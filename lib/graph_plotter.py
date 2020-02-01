"""A graph plotting module using Matplotlib to generate graphs from 
collected data stored in CSV files and PyQt5 to create the window framework.\n
NOTE: Module is in beta stage and will require redevelopment for improved efficiency at a later date."""

import csv
import os, sys
import numpy as np

from PyQt5 import QtGui, QtCore, QtWidgets, uic
from matplotlib.backends.backend_qt5agg import (FigureCanvasQTAgg as FigureCanvas, NavigationToolbar2QT as NavigationToolbar)
from matplotlib.figure import Figure


path = os.path.dirname(os.path.realpath(__file__))
Ui_MainWindow, QMainWindow = uic.loadUiType(f'{path}\\window.ui')

app = QtWidgets.QApplication(sys.argv)

class PlotGraph(QMainWindow, Ui_MainWindow):
    """A class to plot a single selected graph.\n
    This module is to be called externally through plot() and is referenced by plot_graph() in arduino_main.py"""

    def __init__(self, parent=None):
        """Setup initialisation."""

        super(PlotGraph, self).__init__()
        self.setupUi(self)

        # Lists for data records
        self.time = []
        self.newtons = []

        # Graph setup
        self.figure = Figure()
        self.canvas = FigureCanvas(self.figure)
        self.mplvl.addWidget(self.canvas)
        self.canvas.draw()

        # Toolbar
        self.toolbar = NavigationToolbar(self.canvas, self, coordinates=True)
        self.addToolBar(self.toolbar)


    def __plot(self, datafile):
        """Plot the graph of recorded data."""

        with open(datafile, newline='') as datafile:
                reader = csv.DictReader(datafile)
                for row in reader:
                    self.time.append(row['time'])
                    self.newtons.append(row['newtons'])

        self.time.remove(''); self.newtons.remove('')
        self.time = [float(x) for x in self.time]; self.newtons = [float(x) for x in self.newtons]

        ax = self.figure.add_subplot(111)
        ax.plot(self.time, self.newtons)

        #print(xfit, yfit)
        peak_index = self.newtons.index(max(self.newtons))
        ax.plot(self.time[peak_index], self.newtons[peak_index], '.')


    def plot(self, f):
        """Called externally and calls PlotGraph() then __plot() passing f."""

        main = PlotGraph()

        main.__plot(f)
        main.show()


class Graphs(QMainWindow, Ui_MainWindow):
    """A local class to plot every single recorded event saved in 'results' directory.\n
    This class should only ever be called when _\\__name___ is equal to _\\__main___"""

    def __init__(self, parent=None):
        """Setup initialisation."""
        super(Graphs, self).__init__()
        self.setupUi(self)
        self.mplfigs.itemClicked.connect(self.change_graph)
        self.figure_dict = {}

        # Lists for data records
        self.time = []
        self.newtons = []

        # Loop over all result records generated
        file_in_dir = [name for name in os.listdir('../results')]
        for i in range(0, len(file_in_dir)):
            name = file_in_dir[i][:-4]

            self.figure_dict[name] = file_in_dir[i]
            self.mplfigs.addItem(name)


        self.plot(self.figure_dict[name])


    def plot(self, datafile):
        """Local function called internally. Plot the selected graph chosen from the records dictionary (right-panel)."""

        self.time.clear(); self.newtons.clear()
        with open(f"../results/{datafile}", newline='') as datafile:
                reader = csv.DictReader(datafile)
                for row in reader:
                    self.time.append(row['time'])
                    self.newtons.append(row['newtons'])

        self.time.remove(''); self.newtons.remove('')
        self.time = [float(x) for x in self.time]; self.newtons = [float(x) for x in self.newtons]

        self.figure = Figure()
        self.ax = self.figure.add_subplot(111)
        self.ax.plot(self.time, self.newtons)

        peak_index = self.newtons.index(max(self.newtons))
        self.ax.plot(self.time[peak_index], self.newtons[peak_index], '.')

        self.add_graph(self.figure)


    def add_graph(self, figure):
        """Local function called internally. Draw new canvas and create new navigation toolbar."""

        self.canvas = FigureCanvas(figure)
        self.mplvl.addWidget(self.canvas)
        self.canvas.draw()

        # Toolbar
        self.toolbar = NavigationToolbar(self.canvas, self, coordinates=True)
        self.addToolBar(self.toolbar)


    def change_graph(self, item):
        """Local function called internally. Load the chosen graph from the records dictionary.\n
        Function will call rm_mpl() and then plot() passing the selected record."""

        text = item.text()
        self.rm_mpl()
        self.plot(self.figure_dict[text])


    def rm_mpl(self):
        """Local function called internally. Remove the canvas and navigation toolbar to be recreated."""

        self.mplvl.removeWidget(self.canvas)
        self.canvas.close()
        self.mplvl.removeWidget(self.toolbar)
        self.toolbar.close()


if __name__ == '__main__':
    main = Graphs()
    main.show()

    sys.exit(app.exec())