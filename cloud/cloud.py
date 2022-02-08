"""
Fichero que implementa las clases principales de la capa Cloud.

De momento, implementamos la capa Cloud como un modelo atómico.
En el futuro tendremos que considerarlo como un modelo acoplado.
"""

import pandas as pd
from time import strftime, localtime
from xdevs.models import Atomic, Port


class Cloud(Atomic):
    """Clase para guardar datos en la base de datos."""

    def __init__(self, name, num_water_bodies=1):
        """Función de inicialización de atributos."""
        super().__init__(name)
        self.num_water_bodies = num_water_bodies
        for i in range(1, num_water_bodies+1):
            body = "body_" + str(i)
            self.add_in_port(Port(pd.DataFrame, "i_" + body + "_raw"))
            self.add_in_port(Port(pd.DataFrame, "i_" + body + "_mod"))

    def initialize(self):
        """Inicialización de la simulación DEVS."""
        self.dfs_raw = {}
        self.dfs_mod = {}
        self.pathraw = {}
        self.pathmod = {}
        time_mark = strftime("%Y%m%d%H%M%S", localtime())
        for i in range(1, self.num_water_bodies+1):
            body = "body_" + str(i)
            self.dfs_raw[body] = pd.DataFrame(columns=["id", "source",
                                                       "timestamp",
                                                       "Lat", "Lon",
                                                       "Depth", "DetB",
                                                       "DetBb"])
            self.dfs_mod[body] = pd.DataFrame(columns=["id", "source",
                                                       "timestamp",
                                                       "Lat", "Lon",
                                                       "Depth", "DetB",
                                                       "DetBb"])
            self.pathraw[body] = "data/" + body + "_" + time_mark + "_raw"
            self.pathmod[body] = "data/" + body + "_" + time_mark + "_mod"
        self.passivate()

    def exit(self):
        """Función de salida de la simulación."""
        # Aquí tenemos que actualizar la base de datos.
        for i in range(1, self.num_water_bodies+1):
            body = "body_" + str(i)
            self.dfs_raw[body].to_csv(self.pathraw[body] + ".csv")
            self.dfs_mod[body].to_csv(self.pathmod[body] + ".csv")

    def lambdaf(self):
        """Función DEVS de salida."""
        pass

    def deltint(self):
        """Función DEVS de transición interna."""
        self.passivate()

    def deltext(self, e):
        """Función DEVS de transición externa."""
        self.continuef(e)
        for i in range(1, self.num_water_bodies+1):
            body = "body_" + str(i)
            port = self.get_in_port("i_" + body + "_raw")
            if(port.empty() is False):
                self.dfs_raw[body] = self.dfs_raw[body].append(port.get(), ignore_index=True)
            port = self.get_in_port("i_" + body + "_mod")
            if(port.empty() is False):
                self.dfs_mod[body] = self.dfs_mod[body].append(port.get(), ignore_index=True)
        super().passivate()
