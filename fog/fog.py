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
from util.event import CommandEvent, CommandEventId, Event, DataEventColumns
# from dataclasses import dataclass, field

logger = get_logger(__name__, logging.DEBUG)


class FogDb(Atomic):
    """Clase para guardar datos en la base de datos."""

    def __init__(self, name: str, edge_devices: list, edge_data_ids: list, n_offset: int = 100):
        """Función de inicialización de atributos."""
        super().__init__(name)
        self.edge_devices = edge_devices
        self.edge_data_ids = {}
        self.n_offset = n_offset
        self.i_cmd = Port(CommandEvent, "i_cmd")
        self.add_in_port(self.i_cmd)
        # Puertos con los datos de barco y bloom fusionados.
        for i in range(0, len(self.edge_devices)):
            edge_device = self.edge_devices[i]
            self.edge_data_ids[edge_device] = edge_data_ids[i]
            self.add_in_port(Port(Event, "i_" + edge_device))
            self.add_out_port(Port(pd.DataFrame, "o_" + edge_device + "_raw"))
            self.add_out_port(Port(pd.DataFrame, "o_" + edge_device + "_mod"))

    def initialize(self):
        """Inicialización de la simulación DEVS."""
        self.db_raw = {}
        self.db_mod = {}
        self.dcache = {}
        self.pathraw = {}
        self.pathmod = {}
        self.counter = {}
        time_mark = strftime("%Y%m%d%H%M%S", localtime())
        for edge_device in self.edge_devices:
            # TODO: Necesitamos almacenar en algún sitio las columnas de cada edge_device. Ahora vale porque
            # todos son iguales, pero en un futuro no valdrá:
            self.db_raw[edge_device] = pd.DataFrame(columns=DataEventColumns.get_all_columns(self.edge_data_ids[edge_device]))
            self.db_mod[edge_device] = pd.DataFrame(columns=DataEventColumns.get_all_columns(self.edge_data_ids[edge_device]))
            self.dcache[edge_device] = pd.DataFrame(columns=DataEventColumns.get_all_columns(self.edge_data_ids[edge_device]))
            self.pathraw[edge_device] = "data/" + self.parent.name + "." + edge_device + "_" + time_mark + "_raw"
            self.pathmod[edge_device] = "data/" + self.parent.name + "." + edge_device + "_" + time_mark + "_mod"
            # offset
            self.counter[edge_device] = 0
        self.passivate()

    def exit(self):
        """Función de salida de la simulación."""
        # Aquí tenemos que guardar la base de datos.
        for edge_device in self.edge_devices:
            self.db_raw[edge_device].to_csv(self.pathraw[edge_device] + ".csv")
            self.db_mod[edge_device].to_csv(self.pathmod[edge_device] + ".csv")

    def lambdaf(self):
        """
        Función DEVS de salida.

        De momento la comentamos para que no vaya trabajo al cloud.
        """
        for edge_device in self.edge_devices:
            if self.counter[edge_device] >= self.n_offset:
                df = self.db_raw[edge_device].tail(self.n_offset)
                self.get_out_port("o_" + edge_device + "_raw").add(df)
            if len(self.dcache[edge_device]) > 0:
                self.get_out_port("o_" + edge_device + "_mod").add(self.dcache[edge_device])

    def deltint(self):
        """Función DEVS de transición interna."""
        for edge_device in self.edge_devices:
            if self.counter[edge_device] == self.n_offset:
                self.counter[edge_device] = 0
            if len(self.dcache[edge_device]) > 0:
                self.dcache[edge_device] = pd.DataFrame(columns=DataEventColumns.get_all_columns(self.edge_data_ids[edge_device]))
        self.passivate()

    def deltext(self, e):
        """Función DEVS de transición externa."""
        self.continuef(e)
        # Procesamos todos los puertos:
        for edge_device in self.edge_devices:
            port = self.get_in_port("i_" + edge_device)
            if(port.empty() is False):
                msg = port.get()
                msg_list = list()
                msg_list.append(msg.id)
                msg_list.append(msg.source)
                msg_list.append(msg.timestamp)
                for value in msg.payload.values():
                    msg_list.append(value)
                self.db_raw[edge_device].loc[len(self.db_raw[edge_device])] = msg_list
                self.counter[edge_device] += 1
            if self.counter[edge_device] == self.n_offset:
                super().activate()
        if self.i_cmd.empty() is False:
            cmd: CommandEvent = self.i_cmd.get()
            if cmd.cmd == CommandEventId.CMD_FIX_OUTLIERS:
                # Leemos los argumentos del comando
                args = cmd.args.split(",")
                if args[0] == self.parent.name:
                    edge_device = args[1]
                    init_interval = dt.datetime.strptime(args[2], '%Y-%m-%d %H:%M:%S')
                    stop_interval = dt.datetime.strptime(args[3], '%Y-%m-%d %H:%M:%S\n')
                    # Tengo que seleccionar los datos en el intervalo especificado:
                    self.dcache[edge_device] = self.db_raw[edge_device][(self.db_raw[edge_device].timestamp >= init_interval) &
                                                                        (self.db_raw[edge_device].timestamp <= stop_interval)]
                    print("Soy " + self.parent.name + ". Recibo la orden: " + cmd.cmd.name + " en el instante " + cmd.date.strftime("%Y/%m/%d %H:%M:%S")
                          + " para detectar outliers de " + edge_device + " en el intervalo: (" + init_interval.strftime("%Y/%m/%d %H:%M:%S") + "-"
                          + stop_interval.strftime("%Y/%m/%d %H:%M:%S") + ")")
                    self.fit_outlayers(edge_device)
                    super().activate()

    def fit_outlayers(self, edge_device):
        """
        Función que se encarga de reparar los outliers.

        Ver el siguiente artículo: https://medium.com/analytics-vidhya/identifying-cleaning-and-replacing-outliers-titanic-dataset-20182a062893

        TODO: De momento el procedimiento no es muy avanzado. Por ejemplo: Lat y Lon se deberían detectar de forma multivariable (simultánea),
        teniendo en cuenta la distancia con los vecinos.
        """
        self.dcache[edge_device].fillna(0, inplace=True)
        # TODO: Estas columnas deberían estar en alguna clase:
        columns = DataEventColumns.get_data_columns(self.edge_data_ids[edge_device])
        whisker_width = 1.5
        for column in columns:
            q1 = self.dcache[edge_device][column].quantile(0.25)
            q3 = self.dcache[edge_device][column].quantile(0.75)
            iqr = q3 - q1
            lower_whisker = q1 - whisker_width*iqr
            upper_whisker = q3 + whisker_width*iqr
            self.dcache[edge_device][column] = np.where(self.dcache[edge_device][column] > upper_whisker, np.nan, self.dcache[edge_device][column])
            self.dcache[edge_device][column] = np.where(self.dcache[edge_device][column] < lower_whisker, np.nan, self.dcache[edge_device][column])
            self.dcache[edge_device][column] = self.dcache[edge_device][column].interpolate().ffill().bfill()
        self.db_mod[edge_device] = pd.concat([self.db_mod[edge_device], self.dcache[edge_device]], ignore_index=True)


class FogServer(Coupled):
    """Clase acoplada FogServer."""

    def __init__(self, name, edge_devices: list, edge_data_ids: list, n_offset: int = 100):
        """Inicialización de atributos."""
        super().__init__(name)
        self.i_cmd = Port(CommandEvent, "i_cmd")
        self.add_in_port(self.i_cmd)
        for edge_device in edge_devices:
            self.add_in_port(Port(Event, "i_" + edge_device))
            self.add_out_port(Port(pd.DataFrame, "o_" + edge_device + "_raw"))
            self.add_out_port(Port(pd.DataFrame, "o_" + edge_device + "_mod"))

        db = FogDb("FogDb", edge_devices, edge_data_ids, n_offset)
        self.add_component(db)
        self.add_coupling(self.i_cmd, db.i_cmd)
        for edge_device in edge_devices:
            # EIC
            self.add_coupling(self.get_in_port("i_" + edge_device), db.get_in_port("i_" + edge_device))
            # EOC
            self.add_coupling(db.get_out_port("o_" + edge_device + "_raw"), self.get_out_port("o_" + edge_device + "_raw"))
            self.add_coupling(db.get_out_port("o_" + edge_device + "_mod"), self.get_out_port("o_" + edge_device + "_mod"))
