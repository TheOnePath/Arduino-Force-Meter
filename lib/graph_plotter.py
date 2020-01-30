import csv
import os, sys
import numpy as np

from PyQt5 import QtGui, QtCore, QtWidgets, uic
from matplotlib.backends.backend_qt5agg import (FigureCanvasQTAgg as FigureCanvas, NavigationToolbar2QT as NavigationToolbar)
from matplotlib.figure import Figure

path = os.path.dirname(os.path.realpath(__file__))
Ui_MainWindow, QMainWindow = uic.loadUiType(f'{path}\window.ui')

app = QtWidgets.QApplication(sys.argv)

class PlotGraph(QMainWindow, Ui_MainWindow):
    def __init__(self, parent=None):
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
        main = PlotGraph()

        main.__plot(f)
        main.show()


class Graphs(QMainWindow, Ui_MainWindow):
    def __init__(self, parent=None):
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
        self.canvas = FigureCanvas(figure)
        self.mplvl.addWidget(self.canvas)
        self.canvas.draw()

        # Toolbar
        self.toolbar = NavigationToolbar(self.canvas, self, coordinates=True)
        self.addToolBar(self.toolbar)


    def change_graph(self, item):
        text = item.text()
        self.rm_mpl()
        self.plot(self.figure_dict[text])


    def rm_mpl(self):
        self.mplvl.removeWidget(self.canvas)
        self.canvas.close()
        self.mplvl.removeWidget(self.toolbar)
        self.toolbar.close()


if __name__ == '__main__':
    main = Graphs()
    main.show()

    sys.exit(app.exec())