"""
Fichero que implementa las clases principales de la capa Cloud.

De momento, implementamos la capa Cloud como un modelo atómico.  En el futuro
tendremos que considerarlo como un modelo acoplado.
"""

import pandas as pd
from time import strftime, localtime
from xdevs.models import Atomic, Port


class Cloud(Atomic):
    """Clase para guardar datos en la base de datos."""

    def __init__(self, name: str, edge_data_types: list):
        """Función de inicialización de atributos."""
        super().__init__(name)
        self.edge_data_types = edge_data_types
        for edge_data_type in edge_data_types:
            self.add_in_port(Port(pd.DataFrame, "i_" + edge_data_type + "_raw"))
            self.add_in_port(Port(pd.DataFrame, "i_" + edge_data_type + "_mod"))

    def initialize(self):
        """Inicialización de la simulación DEVS."""
        self.dfs_raw = {}
        self.dfs_mod = {}
        self.pathraw = {}
        self.pathmod = {}
        time_mark = strftime("%Y%m%d%H%M%S", localtime())
        for edge_data_type in self.edge_data_types:
            self.dfs_raw[edge_data_type] = pd.DataFrame(columns=["id", "source", "timestamp", "Lat", "Lon", "Depth", "DetB", "DetBb"])
            self.dfs_mod[edge_data_type] = pd.DataFrame(columns=["id", "source", "timestamp", "Lat", "Lon", "Depth", "DetB", "DetBb"])
            self.pathraw[edge_data_type] = "data/" + self.name + "." + edge_data_type + "_" + time_mark + "_raw"
            self.pathmod[edge_data_type] = "data/" + self.name + "." + edge_data_type + "_" + time_mark + "_mod"
        self.passivate()

    def exit(self):
        """Función de salida de la simulación."""
        # Aquí tenemos que actualizar la base de datos.
        for edge_data_type in self.edge_data_types:
            self.dfs_raw[edge_data_type].to_csv(self.pathraw[edge_data_type] + ".csv")
            self.dfs_mod[edge_data_type].to_csv(self.pathmod[edge_data_type] + ".csv")

    def lambdaf(self):
        """Función DEVS de salida."""
        pass

    def deltint(self):
        """Función DEVS de transición interna."""
        self.passivate()

    def deltext(self, e):
        """Función DEVS de transición externa."""
        self.continuef(e)
        for edge_data_type in self.edge_data_types:
            port = self.get_in_port("i_" + edge_data_type + "_raw")
            if(port.empty() is False):
                for item in port.values:
                    self.dfs_raw[edge_data_type] = pd.concat([self.dfs_raw[edge_data_type], item], ignore_index=True)
            port = self.get_in_port("i_" + edge_data_type + "_mod")
            if(port.empty() is False):
                for item in port.values:
                    self.dfs_mod[edge_data_type] = pd.concat([self.dfs_mod[edge_data_type], item], ignore_index=True)
        super().passivate()
