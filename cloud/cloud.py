"""Fichero que implementa las clases principales de la capa Cloud."""

import pandas as pd
from time import strftime, localtime
from xdevs.models import Atomic, Port


class CloudDb(Atomic):
    """Clase para guardar datos en la base de datos."""

    def __init__(self, name, num_water_bodies=1):
        """Función de inicialización de atributos."""
        super().__init__(name)
        self.num_water_bodies = num_water_bodies
        for i in range(1, num_water_bodies+1):
            port_raw_name = "i_body_" + str(i) + "_raw"
            port_mod_name = "i_body_" + str(i) + "_mod"
            self.add_in_port(Port(pd.DataFrame, port_raw_name))
            self.add_in_port(Port(pd.DataFrame, port_mod_name))

    def initialize(self):
        """Inicialización de la simulación DEVS."""
        self.dfs_raw = {}
        self.dfs_mod = {}
        self.dfs_raw_path = {}
        self.dfs_mod_path = {}
        time_suffix = strftime("%Y%m%d-%H%M%S", localtime())
        for i in range(1, self.num_water_bodies+1):
            port_raw_name = "i_body_" + str(i) + "_raw"
            port_mod_name = "i_body_" + str(i) + "_mod"
            path_row = "data/" + self.name + "_" + port_raw_name + "_"
            path_row += time_suffix
            path_mod = "data/" + self.name + "_" + port_mod_name + "_"
            path_mod += time_suffix
            self.dfs_raw[port_raw_name] = pd.DataFrame(columns=["id", "source",
                                                                "timestamp",
                                                                "Lat", "Lon",
                                                                "Depth",
                                                                "DetB",
                                                                "DetBb"])
            self.dfs_mod[port_mod_name] = pd.DataFrame(columns=["id", "source",
                                                                "timestamp",
                                                                "Lat", "Lon",
                                                                "Depth",
                                                                "DetB",
                                                                "DetBb"])
            self.dfs_raw_path[port_raw_name] = path_row
            self.dfs.mod_path[port_mod_name] = path_mod
        self.passivate()

    def exit(self):
        """Función de salida de la simulación."""
        # Aquí tenemos que actualizar la base de datos.
        for i in range(1, self.num_water_bodies+1):
            port_raw_name = "i_body_" + str(i) + "_raw"
            port_mod_name = "i_body_" + str(i) + "_mod"
            path_raw = self.dfs_raw_path[port_raw_name]
            path_mod = self.dfs_mod_path[port_mod_name]
            self.dfs_raw[port_raw_name].to_csv(path_raw)
            self.dfs_mod[port_mod_name].to_csv(path_mod)

    def lambdaf(self):
        """Función DEVS de salida."""
        pass

    def deltext(self, e):
        """Función DEVS de transición externa."""
        self.continuef(e)
        for i in range(1, self.num_water_bodies+1):
            for type_data in ["raw" "mod"]:
                port_name = "i_body_" + str(i) + "_" + type_data
                port = self.in_ports[port_name]
                if(port.empty() is False):
                    df = port.get()
                    if type_data == "raw":
                        self.dfs_raw[port_name].append(df)
                    elif type_data == "mod":
                        self.dfs_mod[port_name].append(df)
        super().passivate()

    def deltint(self):
        """Función DEVS de transición interna."""
        self.passivate()
