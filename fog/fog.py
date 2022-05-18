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
# import numpy as np
# import sklearn.neighbors as nb
import logging
import datetime as dt
from time import strftime, localtime
from xdevs import get_logger
from xdevs.models import Atomic, Coupled, Port
from util.event import CommandEvent, CommandEventId, Event
# from dataclasses import dataclass, field

logger = get_logger(__name__, logging.DEBUG)


class FogHub(Atomic):
    """Hub de datos del servidor Fog."""

    def __init__(self, name, n_uav=1, n_offset=100):
        """Función de inicialización de atributos."""
        super().__init__(name)
        self.n_uav = n_uav
        self.n_offset = n_offset
        self.i_cmd = Port(CommandEvent, "i_cmd")
        self.add_in_port(self.i_cmd)
        # Puertos con los datos de barco y bloom fusionados.
        for i in range(1, self.n_uav+1):
            uav = "fusion_" + str(i)
            self.add_in_port(Port(Event, "i_" + uav))
            self.add_out_port(Port(Event, "o_" + uav + "_raw"))
            self.add_out_port(Port(Event, "o_" + uav + "_mod"))

    def initialize(self):
        """Incialización de la simulación DEVS."""
        # Memoria cache para ir detectanto los outliers:
        self.msg_raw = {}
        self.msg_mod = {}
        self.cache = {}
        self.counter = {}
        for i in range(1, self.n_uav+1):
            uav = "fusion_" + str(i)
            self.msg_raw[uav] = None
            self.msg_mod[uav] = None
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
        """
        Función DEVS de salida.
        """
        for i in range(1, self.n_uav+1):
            uav = "fusion_" + str(i)
            if self.msg_raw[uav] is not None:
                self.get_out_port("o_" + uav + "_raw").add(self.msg_raw[uav])
            if self.msg_mod[uav] is not None:
                self.get_out_port("o_" + uav + "_mod").add(self.msg_mod[uav])

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
        # Comentamos la detección de outliers, para agilizar la simulación
        # De hecho, la detección de ouliers irá más abajo
        # NOTA. Creo que al final lo mejor es que el detector de OUTLIERS
        # vaya en FogDb. Hablarlo en la reunión.
        for i in range(1, self.n_uav+1):
            uav = "fusion_" + str(i)
            iport = self.get_in_port("i_" + uav)
            if (iport.empty() is False):
                msg = iport.get()
                self.msg_raw[uav] = msg
                self.msg_mod[uav] = msg
                # Añadimos el mensaje al diccionario:
                ## content = pd.Series(list(msg.payload.values()),
                ##                     index=self.cache[uav].columns)
                ## self.cache[uav] = self.cache[uav].append(content, ignore_index=True)
                ## self.counter[uav] += 1
                ## if(self.counter[uav] >= self.n_offset):
                ##     # Para evitar desbordamientos si nos vienen muchos datos:
                ##     self.counter[uav] = self.n_offset
                ##     lof = nb.LocalOutlierFactor()
                ##     wrong_values = lof.fit_predict(self.cache[uav])
                ##     outlier_index = np.where(wrong_values == -1)
                ##     self.cache[uav].iloc[outlier_index, ] = np.nan
                ##     if(np.size(outlier_index) > 0):
                ##         self.cache[uav] = self.cache[uav].interpolate()
                ##         # self.msg_mod tiene que ser el último elemento del DF
                ##         # y hay que eliminar el primer elemento del DF.
                ##         content = list(self.cache[uav].iloc[-1])
                ##         self.msg_mod[uav].payload['Lat'] = content[0]
                ##         self.msg_mod[uav].payload['Lon'] = content[1]
                ##         self.msg_mod[uav].payload['Depth'] = content[2]
                ##         self.msg_mod[uav].payload['DetB'] = content[4]
                ##         self.msg_mod[uav].payload['DetBb'] = content[5]
                ##         # Quitamos el primer elemento de la cache:
                ##         self.cache[uav].drop(index=self.cache[uav].index[0], axis=0, inplace=True)
                super().activate()
        if self.i_cmd.empty() is False:
            cmd: CommandEvent = self.i_cmd.get()
            if cmd.cmd == CommandEventId.CMD_FIX_OUTLIERS:
                # Leemos los argumentos del comando
                args = cmd.args.split(",")
                if args[0] == self.parent.name:
                    init_interval = dt.datetime.strptime(args[1], '%Y-%m-%d %H:%M:%S') 
                    stop_interval = dt.datetime.strptime(args[2], '%Y-%m-%d %H:%M:%S\n') 
                    print("Soy " + self.parent.name + ". Recibo la orden: " + cmd.cmd.name + " en el instante " 
                          + cmd.date.strftime("%Y/%m/%d %H:%M:%S") + " para detectar outliers en el intervalo: (" 
                          + init_interval.strftime("%Y/%m/%d %H:%M:%S") + "-" + stop_interval.strftime("%Y/%m/%d %H:%M:%S") + ")")


class FogDb(Atomic):
    """Clase para guardar datos en la base de datos."""

    def __init__(self, name, n_uav=1, n_offset=100):
        """Función de inicialización de atributos."""
        super().__init__(name)
        self.n_uav = n_uav
        self.n_offset = n_offset
        # Puertos con los datos de barco y bloom fusionados.
        for i in range(1, self.n_uav+1):
            uav = "fusion_" + str(i)
            self.add_in_port(Port(Event, "i_" + uav + "_raw"))
            self.add_in_port(Port(Event, "i_" + uav + "_mod"))
            self.add_out_port(Port(pd.DataFrame, "o_" + uav + "_raw"))
            self.add_out_port(Port(pd.DataFrame, "o_" + uav + "_mod"))

    def initialize(self):
        """Inicialización de la simulación DEVS."""
        self.db_raw = {}
        self.db_mod = {}
        self.pathraw = {}
        self.pathmod = {}
        self.counter = {}
        time_mark = strftime("%Y%m%d%H%M%S", localtime())
        for i in range(1, self.n_uav+1):
            uav = "fusion_" + str(i)
            self.db_raw[uav] = pd.DataFrame(columns=["id", "source",
                                                     "timestamp",
                                                     "Lat", "Lon",
                                                     "Depth", "DetB",
                                                     "DetBb"])
            self.db_mod[uav] = pd.DataFrame(columns=["id", "source",
                                                     "timestamp",
                                                     "Lat", "Lon",
                                                     "Depth", "DetB",
                                                     "DetBb"])
            self.pathraw[uav] = "data/" + self.parent.name + "." + uav + "_" + time_mark + "_raw"
            self.pathmod[uav] = "data/" + self.parent.name + "." + uav + "_" + time_mark + "_mod"
            # Los datos raw y mod deben venir a la vez, por lo que
            # solo hay un contador.
            self.counter[uav] = 0
        self.passivate()

    def exit(self):
        """Función de salida de la simulación."""
        # Aquí tenemos que guardar la base de datos.
        for i in range(1, self.n_uav+1):
            uav = "fusion_" + str(i)
            self.db_raw[uav].to_csv(self.pathraw[uav] + ".csv")
            self.db_mod[uav].to_csv(self.pathmod[uav] + ".csv")

    def lambdaf(self):
        """
        Función DEVS de salida.
        De momento la comentamos para que no vaya trabajo al cloud.
        """
        # for i in range(1, self.n_uav+1):
        #    uav = "fusion_" + str(i)
        #    if self.counter[uav] < 2*self.n_offset:
        #        continue
        #    # Añadir solo las n_offset últimas filas
        #    df = self.db_raw[uav].tail(self.n_offset)
        #    self.get_out_port("o_" + uav + "_raw").add(df)
        #    df = self.db_mod[uav].tail(self.n_offset)
        #    self.get_out_port("o_" + uav + "_mod").add(df)
        pass

    def deltint(self):
        """Función DEVS de transición interna."""
        for i in range(1, self.n_uav+1):
            uav = "fusion_" + str(i)
            if self.counter[uav] == 2*self.n_offset:
                self.counter[uav] = 0
        self.passivate()

    def deltext(self, e):
        """Función DEVS de transición externa."""
        self.continuef(e)
        super().passivate()
        # Procesamos todos los puertos:
        for i in range(1, self.n_uav+1):
            uav = "fusion_" + str(i)
            for dtype in ["raw", "mod"]:
                portname = "i_" + uav + "_" + dtype
                port = self.get_in_port(portname)
                if(port.empty() is False):
                    msg = port.get()
                    msg_list = list()
                    msg_list.append(msg.id)
                    msg_list.append(msg.source)
                    msg_list.append(msg.timestamp)
                    for value in msg.payload.values():
                        msg_list.append(value)
                    if dtype == "raw":
                        self.db_raw[uav].loc[len(self.db_raw[uav])] = msg_list
                    elif dtype == "mod":
                        self.db_mod[uav].loc[len(self.db_mod[uav])] = msg_list
                    self.counter[uav] += 1
            if self.counter[uav] == 2*self.n_offset:
                super().activate()


class FogServer(Coupled):
    """Clase acoplada FogServer."""

    def __init__(self, name, n_uav=1, n_offset=100):
        """Inicialización de atributos."""
        super().__init__(name)
        self.i_cmd = Port(CommandEvent, "i_cmd")
        self.add_in_port(self.i_cmd)
        for i in range(1, n_uav+1):
            uav = "fusion_" + str(i)
            self.add_in_port(Port(Event, "i_" + uav))
            self.add_out_port(Port(pd.DataFrame, "o_" + uav + "_raw"))
            self.add_out_port(Port(pd.DataFrame, "o_" + uav + "_mod"))

        hub = FogHub("FogHub", n_uav, n_offset)
        db = FogDb("FogDb", n_uav, n_offset)
        self.add_component(hub)
        self.add_component(db)
        self.add_coupling(self.i_cmd, hub.i_cmd)
        for i in range(1, n_uav+1):
            uav = "fusion_" + str(i)
            # EIC
            self.add_coupling(self.get_in_port("i_" + uav),
                              hub.get_in_port("i_" + uav))
            # IC
            self.add_coupling(hub.get_out_port("o_" + uav + "_raw"),
                              db.get_in_port("i_" + uav + "_raw"))
            self.add_coupling(hub.get_out_port("o_" + uav + "_mod"),
                              db.get_in_port("i_" + uav + "_mod"))
            # EOC
            self.add_coupling(db.get_out_port("o_" + uav + "_raw"),
                              self.get_out_port("o_" + uav + "_raw"))
            self.add_coupling(db.get_out_port("o_" + uav + "_mod"),
                              self.get_out_port("o_" + uav + "_mod"))
