"""Fichero que implementa las clases principales para la capa Fog."""

import pandas as pd
import numpy as np
import datetime as dt
import random as rnd
import sklearn.neighbors as nb
import logging
from xdevs import PHASE_ACTIVE, get_logger
from xdevs.models import Atomic, Coupled, Port
from xdevs.sim import Coordinator
from util.event import Event
# from dataclasses import dataclass, field

logger = get_logger(__name__, logging.DEBUG)


class TmpGenerator(Atomic):
    """Clase generadora de datos. Es un recurso temporal, para pruebas."""

    def __init__(self, name, num_events):
        """Función de inicialización de atributos."""
        super().__init__(name)
        self.o_out = Port(Event, "o_out")
        self.add_out_port(self.o_out)
        self.num_events = num_events

    def initialize(self):
        self.period = 1
        self.counter = 1
        self.hold_in(PHASE_ACTIVE, self.period)

    def deltext(self, e: float):
        pass

    def exit(self):
        pass

    def deltint(self):
        self.counter += 1
        if (self.counter<=self.num_events):
            self.hold_in(PHASE_ACTIVE, self.period)
        else:
            self.passivate()

    def lambdaf(self):
        value = rnd.randint(35,37)
        if (rnd.random() < 0.01):
            value = -value  # Outlier
        event = Event(id=str(self.counter), source="sensor_temp_01",
                      timestamp=dt.datetime.now, payload={"temp": value})
        self.o_out.add(event)


class FogHub(Atomic):
    """Hub de datos del servidor Fog."""

    def __init__(self, name, n_offset=100):
        """Función de inicialización de atributos."""
        super().__init__(name)
        self.n_offset = n_offset
        # Puertos de ejemplo, sobre los que se hace detección de outliers:
        """
        self.i_sensor_temp_01 = Port(Event, "i_sensor_temp_01")
        self.add_in_port(self.i_sensor_temp_01)
        self.o_sensor_temp_01_raw = Port(pd.DataFrame, "o_sensor_temp_01_raw")
        self.add_out_port(self.o_sensor_temp_01_raw)
        self.o_sensor_temp_01_new = Port(pd.DataFrame, "o_sensor_temp_01_new")
        self.add_out_port(self.o_sensor_temp_01_new)
        """
        # Puerto con los datos de barco y bloom fusionados.
        # Cada n_samples se agrupan los datos en un dataframe y se lanzan al
        # Cloud.
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
        """
        self.sensor_temp_01_raw = pd.DataFrame(columns=["id",
                                                        "timestamp",
                                                        "value"])
        self.sensor_temp_01_new = pd.DataFrame(columns=["id",
                                                        "timestamp",
                                                        "value"])
                                                        """
        # Memoria cache para ir detectanto los outliers:
        self.msg_raw = None
        self.msg_mod = None
        self.fusion_01_cache = pd.DataFrame(columns=["Lat",
                                                     "Lon",
                                                     "Depth",
                                                     "DetB",
                                                     "DetBb"])
        # TODO: Esto lo tengo que pasar a otro modelo atómico, de hecho:
        # 1.- FogServer pasaría a ser FogData.
        # 2.- Nuevo modelo atómico FogDb que almacene datos y detecte outliers.
        # 3.- Nuemo modelo acoplado FogServer que incluya estos dos.
        """
        self.fusion_01_db = pd.DataFrame(columns=["id",
                                                  "source",
                                                  "datetime",
                                                  "payload"])
"""
        # self.sensor_temp_01_counter = 0
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
            content = pd.Series(list(msg.payload.items()),
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
                    self.fusion_01_cache.drop(index=self.fusion_01_cache.index[0], axis=0, inplace=True)
                    # TODO: CONTINÚA AQUÍ
            super().activate()
            """msg = self.i_fusion_01.get()
            items = msg.payload.items()
            columns = ["id", "source", "", "payload"]
            content = [msg.id, msg.source, msg.timestamp, msg.payload]
            for item in items:
                columns.append(item[0])
                content.append(item[1])
            new_data = pd.DataFrame(content, columns)
            self.fusion_01_raw = self.fusion_01_raw.append(new_data.T,
                                                           ignore_index=True)
            self.fusion_01_db = self.fusion_01_db.append(new_data.T,
                                                         ignore_index=True)
            self.fusion_01_counter += 1
            if(self.fusion_01_counter == self.n_samples):
                # De momento, no comprobamos outliers.
                super().activate()
"""
        if (self.i_sensor_temp_01.empty() is False):
            current_input = self.i_sensor_temp_01.get()
            id = current_input.id
            timestamp = current_input.timestamp
            value = current_input.payload["temp"]
            values = {"id": id, "timestamp": timestamp, "value": value}
            self.sensor_temp_01_raw = self.sensor_temp_01_raw.append(
                values, ignore_index=True)
            self.sensor_temp_01_counter = self.sensor_temp_01_counter + 1
            if (self.sensor_temp_01_counter == self.n_offset):
                lof = nb.LocalOutlierFactor()
                wrong_values = lof.fit_predict(self.sensor_temp_01_raw[["value"]])
                outlier_index = np.where(wrong_values == -1)
                self.sensor_temp_01_new = self.sensor_temp_01_raw
                self.sensor_temp_01_new.iloc[outlier_index, 2] = np.nan
                self.sensor_temp_01_new[["value"]] = self.sensor_temp_01_new[["value"]].astype(float)
                if(np.size(outlier_index) > 0):
                    self.sensor_temp_01_new[["value"]] = self.sensor_temp_01_new[["value"]].interpolate()
                super().activate()

    def deltint(self):
        """Función DEVS de transición interna."""
        # Reinicialización del dataframe temporal:
        if(self.fusion_01_counter == self.n_offset):
            self.fusion_01_raw = pd.DataFrame(columns=["id",
                                                       "source",
                                                       "datetime",
                                                       "payload"])
            self.fusion_01_counter = 0

        # Reinicialización del dataframe temporal:
        if(self.sensor_temp_01_counter == self.n_offset):
            self.sensor_temp_01_raw = pd.DataFrame(columns=["id",
                                                            "timestamp",
                                                            "value"])
            self.sensor_temp_01_new = pd.DataFrame(columns=["id",
                                                            "timestamp",
                                                            "value"])
            self.sensor_temp_01_counter = 0
        self.passivate()


class FogDb(Atomic):
    """Clase para guardar datos en la base de datos."""

    def __init__(self, name):
        """Función de inicialización de atributos."""
        super().__init__(name)
        self.i_fusion_01 = Port(Event, "i_fusion_01")
        self.add_in_port(self.i_fusion_01)

    def initialize(self):
        """Inicialización de la simulación DEVS."""
        # TODO: Aquí tenemos que crear el archivo de salida:
        pass

    def exit(self):
        """Función de salida de la simulación."""
        # Aquí tenemos que cerrar el archivo
        pass

    def deltext(self, e):
        """Función DEVS de transición externa."""
        self.continuef(e)
        # Procesamos el puerto i_fusion_01:
        if(self.i_fusion_01.empty() is False):
            msg = self.i_fusion_01.get()
            # Aquí tenemos que escribir en el archivo
            super().passivate()


class TestFogServer(Coupled):
    """Clase para evaluar FogServer."""
    def __init__(self, name, num_events=1000, n_samples=100):
        """Inicialización de atributos."""
        super().__init__(name)
        gen = TmpGenerator("generator", num_events)
        fog = FogHub("fog", n_samples)
        self.add_component(gen)
        self.add_component(fog)
        self.add_coupling(gen.o_out, fog.i_sensor_temp_01)


if __name__ == '__main__':
    test_fog = TestFogServer("test_fog", 1000, 100)
    coord = Coordinator(test_fog)
    coord.initialize()
    coord.simulate()
    coord.exit()
