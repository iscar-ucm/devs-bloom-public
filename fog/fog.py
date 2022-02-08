"""Fichero que implementa las clases principales para la capa Fog."""

import pandas as pd
import numpy as np
import sklearn.neighbors as nb
import logging
from time import strftime, localtime
from xdevs import get_logger
from xdevs.models import Atomic, Coupled, Port
from util.event import Event
# from dataclasses import dataclass, field

logger = get_logger(__name__, logging.DEBUG)


class FogHub(Atomic):
    """Hub de datos del servidor Fog."""

    def __init__(self, name, n_uav=1, n_offset=100):
        """Función de inicialización de atributos."""
        super().__init__(name)
        self.n_uav = n_uav
        self.n_offset = n_offset
        # Puertos con los datos de barco y bloom fusionados.
        for i in range(1, self.n_uav+1):
            port_suf = "fusion_" + str(i)
            self.add_in_port(Port(Event, "i_" + port_suf))
            self.add_out_port(Port(Event, "o_" + port_suf + "_raw"))
            self.add_out_port(Port(Event, "o_" + port_suf + "_mod"))

    def initialize(self):
        """Incialización de la simulación DEVS."""
        # Memoria cache para ir detectanto los outliers:
        self.msg_raw = {}
        self.msg_mod = {}
        self.cache = {}
        self.counter = {}
        for i in range(1, self.n_uav+1):
            uav = "fusion_" + str(i)
            self.msg_raw[uav + "_raw"] = None
            self.msg_mod[uav + "_mod"] = None
            self.cache[uav] = pd.DataFrame(columns=["Lat",
                                                    "Lon",
                                                    "Depth",
                                                    "DetB",
                                                    "DetBb"])
            self.counter[uav] = 0
        self.passivate()

    def exit(self):
        """Función de salida de la simulación."""
        pass

    def lambdaf(self):
        """Función DEVS de salida."""
        for i in range(1, self.n_uav+1):
            uav = "fusion_" + str(i)
            if self.msg_raw[uav] is not None:
                self.out_ports["o_" + uav + "_raw"].add(self.msg_raw[uav])
            if self.msg_mod[uav] is not None:
                self.out_ports["o_" + uav + "_mod"].add(self.msg_mod[uav])

    def deltint(self):
        """Función DEVS de transición interna."""
        for i in range(1, self.n_uav+1):
            uav = "fusion_" + str(i)
            self.msg_raw[uav] = None
            self.msg_mod[uav] = None
        self.passivate()

    def deltext(self, e):
        """Función DEVS de transición externa."""
        self.continuef(e)

        # Procesamos los puertos de entrada:
        for i in range(1, self.n_uav+1):
            uav = "fusion_" + str(i)
            iport = self.in_ports["i_" + uav]
            if (iport.empty() is False):
                msg = iport.get()
                self.msg_raw[uav] = msg
                self.msg_mod[uav] = msg
                # Añadimos el mensaje al diccionario:
                content = pd.Series(list(msg.payload.values()),
                                    index=self.cache[uav].columns)
                self.cache[uav] = self.cache[uav].append(content, ignore_index=True)
                self.counter[uav] += 1
                if(self.counter[uav] >= self.n_offset):
                    # Para evitar desbordamientos si nos vienen muchos datos:
                    self.counter[uav] = self.n_offset
                    lof = nb.LocalOutlierFactor()
                    wrong_values = lof.fit_predict(self.cache[uav])
                    outlier_index = np.where(wrong_values == -1)
                    self.cache[uav].iloc[outlier_index, ] = np.nan
                    if(np.size(outlier_index) > 0):
                        self.cache[uav] = self.cache[uav].interpolate()
                        # self.msg_mod tiene que ser el último elemento del DF
                        # y hay que eliminar el primer elemento del DF.
                        content = list(self.cache[uav].iloc[-1])
                        self.msg_mod[uav].payload['Lat'] = content[0]
                        self.msg_mod[uav].payload['Lon'] = content[1]
                        self.msg_mod[uav].payload['Depth'] = content[2]
                        self.msg_mod[uav].payload['DetB'] = content[4]
                        self.msg_mod[uav].payload['DetBb'] = content[5]
                        # Quitamos el primer elemento de la cache:
                        self.cache[uav].drop(index=self.cache[uav].index[0], axis=0, inplace=True)
                super().activate()


class FogDb(Atomic):
    """Clase para guardar datos en la base de datos."""

    def __init__(self, name):
        """Función de inicialización de atributos."""
        super().__init__(name)
        self.i_fusion_01_raw = Port(Event, "i_fusion_01_raw")
        self.i_fusion_01_mod = Port(Event, "i_fusion_01_mod")
        self.add_in_port(self.i_fusion_01_raw)
        self.add_in_port(self.i_fusion_01_mod)

    def initialize(self):
        """Inicialización de la simulación DEVS."""
        # Al final lo hacemos con data_frames:
        self.db_raw = pd.DataFrame(columns=["id", "source",
                                            "timestamp", "Lat",
                                            "Lon", "Depth",
                                            "DetB", "DetBb"])
        self.db_mod = pd.DataFrame(columns=["id", "source",
                                            "timestamp", "Lat",
                                            "Lon", "Depth",
                                            "DetB", "DetBb"])
        self.db_base_name = "data/" + self.name + "_"
        self.db_base_name += strftime("%Y%m%d-%H%M%S", localtime()) + "_"
        self.passivate()

    def exit(self):
        """Función de salida de la simulación."""
        # Aquí tenemos que actualizar la base de datos.
        self.db_raw.to_csv(self.db_base_name + "raw.csv")
        self.db_mod.to_csv(self.db_base_name + "mod.csv")

    def lambdaf(self):
        """Función DEVS de salida."""
        pass

    def deltext(self, e):
        """Función DEVS de transición externa."""
        self.continuef(e)
        # Procesamos el puerto i_fusion_01_raw:
        if(self.i_fusion_01_raw.empty() is False):
            msg = self.i_fusion_01_raw.get()
            msg_list = list()
            msg_list.append(msg.id)
            msg_list.append(msg.source)
            msg_list.append(msg.timestamp)
            for value in msg.payload.values():
                msg_list.append(value)
            content = pd.Series(msg_list, index=self.db_raw.columns)
            self.db_raw = self.db_raw.append(content, ignore_index=True)
        if(self.i_fusion_01_mod.empty() is False):
            msg = self.i_fusion_01_mod.get()
            msg_list = list()
            msg_list.append(msg.id)
            msg_list.append(msg.source)
            msg_list.append(msg.timestamp)
            for value in msg.payload.values():
                msg_list.append(value)
            content = pd.Series(msg_list, index=self.db_mod.columns)
            self.db_mod = self.db_mod.append(content, ignore_index=True)
        super().passivate()

    def deltint(self):
        """Función DEVS de transición interna."""
        self.passivate()


class FogServer(Coupled):
    """Clase acoplada FogServer."""

    def __init__(self, name, n_uvs=1, n_offset=100):
        """Inicialización de atributos."""
        super().__init__(name)
        for i in range(1, n_uvs+1):
            port_name = "i_fusion_" + str(i)
            self.add_in_port(Port(Event, port_name))
        hub = FogHub("FogHub", n_uvs, n_offset)
        db = FogDb("FogDb", n_uvs, n_offset)
        self.add_component(hub)
        self.add_component(db)
        for i in range(1, n_uvs+1):
            port_suf = "fusion_" + str(i)
            # EIC
            self.add_coupling(self.in_ports["i_" + port_suf],
                              hub.in_ports["i_" + port_suf])
            # IC
            self.add_coupling(hub.out_ports["o_" + port_suf + "_raw"],
                              db.in_ports["i_" + port_suf + "_raw"])
            self.add_coupling(hub.out_ports["o_" + port_suf + "_mod"],
                              db.in_ports["i_" + port_suf + "_mod"])
