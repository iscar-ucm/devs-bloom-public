"""
Fichero que implementa la clase que se encarga de enviar comandos al simulador.
"""

import datetime as dt
from xdevs.models import Atomic, Port


class Commander(Atomic):
    """Clase para emular directivas de simulación."""

    def __init__(self, name, commands_path, start, stop):
        super().__init__(name)
        self.commands_path = commands_path
        self.start = start
        self.stop = stop
        self.out = Port("out")
        self.add_out_port(self.out)

    def initialize(self):
        """Inicialización de la simulación DEVS."""
        self.reader = None
        self.current_input = None
        self.next_input = None
        self.update_inputs()
        super().hold_in("active", 0.0)

    def exit(self):
        reader.close

    def deltint(self):
        if(self.next_input is None):
            super().passivate()
        else:
            sigma_aux = (self.next_input - self.current_input).total_seconds()
            super().hold_in("active", sigma_aux)
            self.current_input = self.next_input
            self.next_input = self.get_next_input()

    def deltext(self, e):
        super().passivate()

    def lambdaf(self):
        self.out.add(current_input)

    def update_inputs(self):
        while ((self.current_input is None) || (self.current_input.datetime < self.start)):
            current_input = self.get_next_input()
        self.next_input = self.get_next_input()

    def get_next_input(self):
        input = None
        if(reader is None):
            reader.open
            reader.readline # Nos saltamos la cabecera
        line = reader.readline
        if(line is None): # Fin de fichero
            return None
        input = input.parse(self.name, line)
        if(input.isafter(self.stop)):
            return None
        return input
            
