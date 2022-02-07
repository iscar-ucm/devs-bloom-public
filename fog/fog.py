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

    def __init__(self, name, n_offset=100):
        """Función de inicialización de atributos."""
        super().__init__(name)
        self.n_offset = n_offset
        # Puerto con los datos de barco y bloom fusionados.
        self.i_fusion_01 = Port(Event, "i_fusion_01")
        # Se transmiten los datos tal cual llegan:
        self.o_fusion_01_raw = Port(Event, "o_fusion_01_raw")
        # Se transmiten los datos tras la detección de outliers:
        self.o_fusion_01_mod = Port(Event, "o_fusion_01_mod")
        self.add_in_port(self.i_fusion_01)
        self.add_out_port(self.o_fusion_01_raw)
        self.add_out_port(self.o_fusion_01_mod)

    def initialize(self):
        """Incialización de la simulación DEVS."""
        # Memoria cache para ir detectanto los outliers:
        self.msg_raw = None
        self.msg_mod = None
        self.fusion_01_cache = pd.DataFrame(columns=["Lat",
                                                     "Lon",
                                                     "Depth",
                                                     "DetB",
                                                     "DetBb"])
        self.fusion_01_counter = 0
        self.passivate()

    def exit(self):
        """Función de salida de la simulación."""
        # self.fusion_01_db.to_csv("data/FogData.csv")
        pass

    def lambdaf(self):
        """Función DEVS de salida."""
        self.o_fusion_01_raw.add(self.msg_raw)
        self.o_fusion_01_mod.add(self.msg_mod)

    def deltext(self, e):
        """Función DEVS de transición externa."""
        self.continuef(e)

        # Procesamos el puerto i_fusion_01:
        if (self.i_fusion_01.empty() is False):
            msg = self.i_fusion_01.get()
            self.msg_raw = msg
            self.msg_mod = msg
            # Añadimos el mensaje al diccionario:
            content = pd.Series(list(msg.payload.values()),
                                index=self.fusion_01_cache.columns)
            self.fusion_01_cache = self.fusion_01_cache.append(content, ignore_index=True)
            self.fusion_01_counter += 1
            if(self.fusion_01_counter >= self.n_offset):
                # Para evitar desbordamientos si nos vienen muchos datos:
                self.fusion_01_counter = self.n_offset
                lof = nb.LocalOutlierFactor()
                wrong_values = lof.fit_predict(self.fusion_01_cache)
                outlier_index = np.where(wrong_values == -1)
                self.fusion_01_cache.iloc[outlier_index, ] = np.nan
                if(np.size(outlier_index) > 0):
                    self.fusion_01_cache = self.fusion_01_cache.interpolate()
                    # self.msg_mod tiene que ser el último elemento del DF y
                    # hay que eliminar el primer elemento del DF.
                    content = list(self.fusion_01_cache.iloc[-1])
                    self.msg_mod.payload['Lat'] = content[0]
                    self.msg_mod.payload['Lon'] = content[1]
                    self.msg_mod.payload['Depth'] = content[2]
                    self.msg_mod.payload['DetB'] = content[4]
                    self.msg_mod.payload['DetBb'] = content[5]
                    # Quitamos el primer elemento de la cache:
                self.fusion_01_cache.drop(index=self.fusion_01_cache.index[0], axis=0, inplace=True)
            super().activate()

    def deltint(self):
        """Función DEVS de transición interna."""
        self.passivate()


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

    def __init__(self, name, n_offset=100):
        """Inicialización de atributos."""
        super().__init__(name)
        self.i_fusion_01 = Port(Event, "i_fusion_01")
        self.add_in_port(self.i_fusion_01)
        hub = FogHub("FogHub_01", n_offset)
        db = FogDb("FogDb_01")
        self.add_component(hub)
        self.add_component(db)
        # EIC
        self.add_coupling(self.i_fusion_01, hub.i_fusion_01)
        # IC
        self.add_coupling(hub.o_fusion_01_raw, db.i_fusion_01_raw)
        self.add_coupling(hub.o_fusion_01_mod, db.i_fusion_01_mod)
