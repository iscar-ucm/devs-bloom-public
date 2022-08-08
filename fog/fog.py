"""
Fichero que implementa las clases principales para la capa Fog.

TODO: Hay un margen de mejora. El Cloud guarda datos de n_offset en n_offset,
lo que significa que el remanente final no queda guardado. Hay que modificar
esta clase para que guarde el remanente de datos final. Una forma sería enviar
una señal stop cuando la simulación termina, de forma que la función de
transición externa de FogDb, al detectar este final, guarde los datos
remanentes.
"""

import pandas as pd
import numpy as np
import logging
import datetime as dt
from time import strftime, localtime
from xdevs import get_logger
from xdevs.models import Atomic, Coupled, Port
from util.view import Scope
from util.event import CommandEvent, CommandEventId, Event, DataEventColumns, SensorEventId

logger = get_logger(__name__, logging.DEBUG)


class FogDb(Atomic):
    """Clase para guardar datos en la base de datos."""

    def __init__(self, name: str, thing_names: list, thing_event_ids: list, n_offset: int = 100):
        """Función de inicialización de atributos."""
        super().__init__(name)
        self.thing_names = thing_names
        self.thing_event_ids = {}
        self.n_offset = n_offset
        self.i_cmd = Port(CommandEvent, "i_cmd")
        self.add_in_port(self.i_cmd)
        # Puertos con los datos de barco y bloom fusionados.
        for i in range(0, len(self.thing_names)):
            thing_name = thing_names[i]
            self.thing_event_ids[thing_name] = thing_event_ids[i]
            self.add_in_port(Port(Event, "i_" + thing_name))
            self.add_out_port(Port(pd.DataFrame, "o_" + thing_name))

    def initialize(self):
        """Inicialización de la simulación DEVS."""
        self.db = {}
        self.db_cache = {}
        self.db_path = {}
        self.counter = {}
        time_mark = strftime("%Y%m%d%H%M%S", localtime())
        for thing_name in self.thing_names:
            self.db[thing_name] = pd.DataFrame(columns=DataEventColumns.get_all_columns(self.thing_event_ids[thing_name]))
            self.db_cache[thing_name] = pd.DataFrame(columns=DataEventColumns.get_all_columns(self.thing_event_ids[thing_name]))
            self.db_path[thing_name] = "data/" + self.parent.name + "." + thing_name + "_" + time_mark
            # offset
            self.counter[thing_name] = 0
        self.passivate()

    def exit(self):
        """Función de salida de la simulación."""
        # Aquí tenemos que guardar la base de datos.
        for thing_name in self.thing_names:
            self.db[thing_name].to_csv(self.db_path[thing_name] + ".csv")

    def lambdaf(self):
        """
        Función DEVS de salida.

        De momento la comentamos para que no vaya trabajo al cloud.
        """
        for thing_name in self.thing_names:
            if self.counter[thing_name] >= self.n_offset:
                df = self.db[thing_name].tail(self.n_offset)
                self.get_out_port("o_" + thing_name).add(df)

    def deltint(self):
        """Función DEVS de transición interna."""
        for thing_name in self.thing_names:
            if self.counter[thing_name] == self.n_offset:
                self.counter[thing_name] = 0
            if len(self.db_cache[thing_name]) > 0:
                self.db_cache[thing_name] = pd.DataFrame(columns=DataEventColumns.get_all_columns(self.edge_data_ids[thing_name]))
        self.passivate()

    def deltext(self, e):
        """Función DEVS de transición externa."""
        self.continuef(e)
        # Procesamos todos los puertos:
        for thing_name in self.thing_names:
            port = self.get_in_port("i_" + thing_name)
            if(port.empty() is False):
                msg = port.get()
                msg_list = list()
                msg_list.append(msg.id)
                msg_list.append(msg.source)
                msg_list.append(msg.timestamp)
                for value in msg.payload.values():
                    msg_list.append(value)
                self.db[thing_name].loc[len(self.db[thing_name])] = msg_list
                self.counter[thing_name] += 1
            if self.counter[thing_name] == self.n_offset:
                super().activate()
        if self.i_cmd.empty() is False:
            cmd: CommandEvent = self.i_cmd.get()
            if cmd.cmd == CommandEventId.CMD_FIX_OUTLIERS:
                logger.info("Command %s has been retired temporarily.", cmd.cmd.value)
                ## # Leemos los argumentos del comando
                ## args = cmd.args.split(",")
                ## if args[0] == self.parent.name:
                ##     thing_name = args[1]
                ##     init_interval = dt.datetime.strptime(args[2], '%Y-%m-%d %H:%M:%S')
                ##     stop_interval = dt.datetime.strptime(args[3], '%Y-%m-%d %H:%M:%S\n')
                ##     # Tengo que seleccionar los datos en el intervalo especificado:
                ##     self.db_cache[thing_name] = self.db_raw[thing_name][(self.db_raw[thing_name].timestamp >= init_interval) &
                ##                                                         (self.db_raw[thing_name].timestamp <= stop_interval)]
                ##     print("Soy " + self.parent.name + ". Recibo la orden: " + cmd.cmd.name + " en el instante " + cmd.date.strftime("%Y/%m/%d %H:%M:%S")
                ##           + " para detectar outliers de " + thing_name + " en el intervalo: (" + init_interval.strftime("%Y/%m/%d %H:%M:%S") + "-"
                ##           + stop_interval.strftime("%Y/%m/%d %H:%M:%S") + ")")
                ##     self.fit_outlayers(thing_name)
                ##     super().activate()

    def fit_outlayers(self, edge_device):
        """
        Función que se encarga de reparar los outliers.

        Ver el siguiente artículo: https://medium.com/analytics-vidhya/identifying-cleaning-and-replacing-outliers-titanic-dataset-20182a062893

        TODO: De momento el procedimiento no es muy avanzado. Por ejemplo: Lat y Lon se deberían detectar de forma multivariable (simultánea), teniendo en cuenta la distancia con los vecinos.
        """
        # self.dcache[edge_device].fillna(0, inplace=True)
        # La llamada anterior no funciona bien, porque al poner un 0 en los NaN, muchas veces no lo
        # toma como un outlier.
        print("dcache ANTES de la interpolación:")
        print(self.db_cache[edge_device].head(30))
        columns = DataEventColumns.get_data_columns(self.edge_data_ids[edge_device])
        whisker_width = 1.5
        for column in columns:
            q1 = self.db_cache[edge_device][column].quantile(0.25)
            q3 = self.db_cache[edge_device][column].quantile(0.75)
            iqr = q3 - q1
            lower_whisker = q1 - whisker_width*iqr
            upper_whisker = q3 + whisker_width*iqr
            self.db_cache[edge_device][column] = np.where(self.db_cache[edge_device][column] > upper_whisker, np.nan, self.db_cache[edge_device][column])
            self.db_cache[edge_device][column] = np.where(self.db_cache[edge_device][column] < lower_whisker, np.nan, self.db_cache[edge_device][column])
            self.db_cache[edge_device][column] = self.db_cache[edge_device][column].interpolate().ffill().bfill()
            print("dcache DESPUÉS de la interpolación de la columna " + column)
            print(self.db_cache[edge_device].head(30))
        self.db_mod[edge_device] = pd.concat([self.db_mod[edge_device], self.db_cache[edge_device]], ignore_index=True)


class FogServer(Coupled):
    """Clase acoplada FogServer."""

    def __init__(self, name, thing_names: list, thing_event_ids: list, n_offset: int = 100):
        """Inicialización de atributos."""
        super().__init__(name)
        self.i_cmd = Port(CommandEvent, "i_cmd")
        self.add_in_port(self.i_cmd)
        for thing_name in thing_names:
            self.add_in_port(Port(Event, "i_" + thing_name))
            self.add_out_port(Port(pd.DataFrame, "o_" + thing_name))

        db = FogDb("FogDb", thing_names, thing_event_ids, n_offset)
        self.add_component(db)
        self.add_coupling(self.i_cmd, db.i_cmd)
        for thing_name in thing_names:
            # EIC
            self.add_coupling(self.get_in_port("i_" + thing_name), db.get_in_port("i_" + thing_name))
            # EOC
            self.add_coupling(db.get_out_port("o_" + thing_name), self.get_out_port("o_" + thing_name))
        # Nitrates scope
        if SensorEventId.NOX.value in thing_event_ids:
            idx_n = thing_event_ids.index(SensorEventId.NOX.value)
            scope = Scope(thing_names[idx_n], thing_event_ids[idx_n])
            self.add_component(scope)
            self.add_coupling(self.get_in_port("i_" + thing_names[idx_n]), scope.i_in)
