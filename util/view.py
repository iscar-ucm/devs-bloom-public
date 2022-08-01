"""
Fichero que define las clases necesariar para representar datos.

Tenemos dos clases: ScopeView y Scope. La última es el modelo atómico DEVS que
se usará dentro del modelo complejo.
"""

from xdevs.models import Atomic, Port
from util.event import Event
from bokeh.io import output_notebook, show, output_file
from bokeh.models import ColumnDataSource
from bokeh.plotting import figure
import math


class ScopeView:
    """A scope."""

    @staticmethod
    def setFileOutput(filename):
        """Documentation."""
        output_file(filename=filename)

    @staticmethod
    def setNotebookOutput():
        """Documentation needed."""
        output_notebook()

    def __init__(self, title="Scope View", x_label="Time (s)", y_label="Value"):
        """Documentation needed."""
        self.data_source = ColumnDataSource(data=dict(x=[0], y=[0]))
        # self.figure = figure(plot_width=400, plot_height=400, x_range=(0, 100), title=title, x_axis_label=x_label, y_axis_label=y_label)
        self.figure = figure(plot_width=400, plot_height=400, title=title, x_axis_label=x_label, y_axis_label=y_label)
        # self.figure.step('x', 'y', source=self.data_source, line_width=2, color='red')
        self.figure.circle(source=self.data_source, size=4, color='red')

    def add(self, x, y):
        """Add a point to the current plot."""
        self.data_source.data['x'].append(x)
        self.data_source.data['y'].append(y)

    def show(self):
        """Show the current figure."""
        show(self.figure)


class Scope(Atomic):
    """A model of a simple scope that plots the evolution in time of a quantity."""

    def __init__(self, name: str, payload_field: str, title="Scope View", x_label="Time (s)", y_label="Value"):
        """Initiliazation function."""
        super().__init__(name)
        self.i_in = Port(Event, "i_in")
        self.add_in_port(self.i_in)
        self.clock = 0
        self.payload_field = payload_field
        self.scopeView = ScopeView("Scope View", "Time (s)", "Value")

    def initialize(self):
        """DEVS initialization function."""
        self.passivate()

    def exit(self):
        """DEVS exit function."""
        self.scopeView.show()

    def deltint(self):
        """DEVS internal transition function."""
        self.passivate()

    def deltext(self, e):
        """DEVS external transition function."""
        self.continuef(e)
        self.clock += e
        msg = self.i_in.get()
        if not math.isnan(msg.payload[self.payload_field]):
            self.scopeView.add(self.clock, msg.payload[self.payload_field])

    def lambdaf(self):
        """DEVS output function."""
        pass
