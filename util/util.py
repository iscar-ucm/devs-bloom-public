"""Fichero con varias clases de utilidad."""

import logging
import math
from bokeh.io import output_notebook, show, output_file
from bokeh.models import ColumnDataSource
from bokeh.plotting import figure
from xdevs import get_logger
from xdevs.models import Atomic, Port
from util.event import CommandEvent, CommandEventId, Event

logger = get_logger(__name__, logging.DEBUG)


class Generator(Atomic):
    """Clase para emular directivas de simulación."""

    def __init__(self, name: str, commands_path: str):
        """Inicialización de la clase."""
        super().__init__(name)
        self.commands_path: str = commands_path
        self.commands: list = []
        self.cmd_counter: int = -1
        self.curr_input: CommandEvent = None
        self.next_input: CommandEvent = None
        self.o_cmd = Port(CommandEvent, "o_cmd")
        self.add_out_port(self.o_cmd)

    def initialize(self):
        """Inicialización de la simulación DEVS."""
        reader = open(self.commands_path, mode='r')
        self.commands = reader.readlines()[1:]
        self.commands = [x for x in self.commands if not x.startswith('#')]
        super().passivate()
        if (len(self.commands) > 0):  # At least we must have two commands
            self.cmd_counter = 0
            self.curr_input = self.get_next_input()
            self.next_input = None
            super().hold_in("active", 0.0)

    def exit(self):
        """Función de salida."""
        pass

    def deltint(self):
        """Función de transición interna."""
        self.next_input = self.get_next_input()
        if(self.next_input is None):
            super().passivate()
        else:
            sigma_aux = (self.next_input.date - self.curr_input.date).total_seconds()
            self.curr_input = self.next_input
            super().hold_in("active", sigma_aux)

    def deltext(self, e):
        """Función de transición externa."""
        super().passivate()

    def lambdaf(self):
        """Función de salida."""
        logger.info("%s::%s -> %s", self.name, self.o_cmd.name, self.curr_input.str())
        self.o_cmd.add(self.curr_input)

    def get_next_input(self):
        """Función que toma la siguiente entrada del archivo de comandos."""
        input: CommandEvent = None
        if (self.cmd_counter < len(self.commands)):
            input = CommandEvent()
            input.parse(self.commands[self.cmd_counter])
            self.cmd_counter += 1
        return input


class DevsCsvFile(Atomic):
    """Class to save data in csv file."""
    PHASE_WRITING:str = "WRITING"

    def __init__(self, name: str, source_name: str, fields: list, base_folder: str):
        """Class constructor"""
        super().__init__(name)
        self.source_name: str = source_name
        self.fields: list = fields
        self.base_folder: str = base_folder
        self.iport_data: Port = Port(Event, "data")
        self.add_in_port(self.iport_data)
        self.iport_cmd = Port(CommandEvent, "cmd")
        self.add_in_port(self.iport_cmd)

    def initialize(self):
        """DEVS initialize function."""
        super().passivate()

    def exit(self):
        """DEVS exit function."""
        pass

    def lambdaf(self):
        """DEVS lambda function."""
        pass

    def deltint(self):
        """DEVS deltint function."""
        super().passivate()

    def deltext(self, e):
        """DEVS deltext function."""
        self.continuef(e)
        # Command input port                
        if self.iport_cmd.empty() is False:
            cmd: CommandEvent = self.iport_cmd.get()
            if cmd.cmd == CommandEventId.CMD_START_SIM:
                self.base_file = open(self.base_folder + "/" + self.name + ".csv", "w")    
                for pos, field in enumerate(self.fields):
                    if(pos > 0):
                        self.base_file.write(",")
                    self.base_file.write(field)
                self.base_file.write("\n")
                super().passivate(DevsCsvFile.PHASE_WRITING)
            if cmd.cmd == CommandEventId.CMD_STOP_SIM:
                if(self.base_folder is not None):
                    self.base_file.close()
                super().passivate()
        if (self.iport_data.empty() is False and self.phase == DevsCsvFile.PHASE_WRITING):
            data: Event = self.iport_data.get()
            self.base_file.write(data.to_string() + "\n")
            super().passivate(DevsCsvFile.PHASE_WRITING)


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
