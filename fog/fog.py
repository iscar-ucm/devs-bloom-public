"""
Fichero que implementa las clases principales para la capa Fog.

TODO: Hay un margen de mejora. El Cloud guarda datos de n_offset en n_offset,
lo que significa que el remanente final no queda guardado. Hay que modificar
esta clase para que guarde el remanente de datos final. Una forma sería enviar
una señal stop cuando la simulación termina, de forma que la función de
transición externa de GCS, al detectar este final, guarde los datos
remanentes.
"""

from tkinter import EventType
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


class GCS(Atomic):
    """Clase para guardar datos en la base de datos."""

    def __init__(self, name: str, usv1, thing_names: list, thing_event_ids: list, n_offset: int = 100):
        """Función de inicialización de atributos."""
        super().__init__(name)
        self.thing_names = thing_names
        self.thing_event_ids = {}
        self.n_offset = n_offset
        self.i_cmd = Port(CommandEvent, "i_cmd")
        self.add_in_port(self.i_cmd)

        # Puerto de entrada del USV
        self.i_usv = Port(Event, "i_" + usv1.name)
        self.add_in_port(self.i_usv)
        # Puerto de salida para la Servicio de Inferencia
        self.o_IS = Port(Event, "o_IS")
        self.add_out_port(self.o_IS)
        # Pueto de salida para el USV planner
        self.o_usvp = Port(Event, "o_usvp")
        self.add_out_port(self.o_usvp)

        # Puertos con los datos de barco y bloom fusionados.
        for i in range(0, len(self.thing_names)):
            thing_name = thing_names[i]
            self.thing_event_ids[thing_name] = thing_event_ids[i]
            self.add_in_port(Port(Event, "i_" + thing_name))
            self.add_out_port(Port(pd.DataFrame, "o_" + thing_name))

    def initialize(self):
        """Inicialización de la simulación DEVS."""
        self.msgout = None
        self.gcs = {}
        self.gcs_cache = {}
        self.gcs_path = {}
        self.counter = {}
        time_mark = strftime("%Y%m%d%H%M%S", localtime())
        for thing_name in self.thing_names:
            self.gcs[thing_name] = pd.DataFrame(columns=DataEventColumns.get_all_columns(self.thing_event_ids[thing_name]))
            self.gcs_cache[thing_name] = pd.DataFrame(columns=DataEventColumns.get_all_columns(self.thing_event_ids[thing_name]))
            self.gcs_path[thing_name] = "data/" + self.parent.name + "." + thing_name + "_" + time_mark
            # offset
            self.counter[thing_name] = 0
        self.passivate()

    def exit(self):
        """Función de salida de la simulación."""
        # Aquí tenemos que guardar la base de datos.
        for thing_name in self.thing_names:
            self.gcs[thing_name].to_csv(self.gcs_path[thing_name] + ".csv")

    def lambdaf(self):
        """
        Función DEVS de salida.

        De momento la comentamos para que no vaya trabajo al cloud.
        """
        for thing_name in self.thing_names:
            if self.counter[thing_name] >= self.n_offset:
                df = self.gcs[thing_name].tail(self.n_offset)
                self.get_out_port("o_" + thing_name).add(df)

        self.o_IS.add(self.msgout_IS)
        self.o_usvp.add(self.msgout_usvp)

    def deltint(self):
        """Función DEVS de transición interna."""
        for thing_name in self.thing_names:
            if self.counter[thing_name] == self.n_offset:
                self.counter[thing_name] = 0
            if len(self.gcs_cache[thing_name]) > 0:
                self.gcs_cache[thing_name] = pd.DataFrame(columns=DataEventColumns.get_all_columns(self.edge_data_ids[thing_name]))
         
        # Medidas de los sensores
        myt     = self.msg.payload['Time']                 
        mylat   = self.msg.payload['Lat']
        mylon   = self.msg.payload['Lon']
        mydepth = self.msg.payload['Depth']
        myalg   = self.gcs_cache['SimSenA']
        # Parámetros del barco
        mydelx  = self.msg_usv.payload['xdel']   
        # Procesado del mensaje de salida
        self.datetime=dt.datetime.fromisoformat(self.msg.timestamp)# En principio sin delay +dt.timedelta(seconds=self.sensorinfo.delay)
        data_usvp = {'Time':myt,'Lat':mylat,'Lon':mylon,'Depth':mydepth, 'Xdel': mydelx, 'Algae': myalg}
        data_IS = {'Time':myt,'Lat':mylat,'Lon':mylon,'Depth':mydepth, 'Xdel': mydelx, 'Algae': myalg}
        self.msgout_usvp=Event(id=self.msg_usv.id,source=self.name,timestamp=self.datetime,payload=data_usvp)
        self.msgout_IS=Event(id=self.msg_usv.id,source=self.name,timestamp=self.datetime,payload=data_IS)
        self.passivate()

    def deltext(self, e):
        """Función DEVS de transición externa."""
        self.continuef(e)
        # Procesamos el puerto del barco:
        msg_usv = self.i_usv.get()
        # Procesamos los demás puertos:
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
                self.gcs[thing_name].loc[len(self.gcs[thing_name])] = msg_list
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
                ##     self.gcs_cache[thing_name] = self.gcs_raw[thing_name][(self.gcs_raw[thing_name].timestamp >= init_interval) &
                ##                                                         (self.gcs_raw[thing_name].timestamp <= stop_interval)]
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
        print(self.gcs_cache[edge_device].head(30))
        columns = DataEventColumns.get_data_columns(self.edge_data_ids[edge_device])
        whisker_width = 1.5
        for column in columns:
            q1 = self.gcs_cache[edge_device][column].quantile(0.25)
            q3 = self.gcs_cache[edge_device][column].quantile(0.75)
            iqr = q3 - q1
            lower_whisker = q1 - whisker_width*iqr
            upper_whisker = q3 + whisker_width*iqr
            self.gcs_cache[edge_device][column] = np.where(self.gcs_cache[edge_device][column] > upper_whisker, np.nan, self.gcs_cache[edge_device][column])
            self.gcs_cache[edge_device][column] = np.where(self.gcs_cache[edge_device][column] < lower_whisker, np.nan, self.gcs_cache[edge_device][column])
            self.gcs_cache[edge_device][column] = self.gcs_cache[edge_device][column].interpolate().ffill().bfill()
            print("dcache DESPUÉS de la interpolación de la columna " + column)
            print(self.gcs_cache[edge_device].head(30))
        self.gcs_mod[edge_device] = pd.concat([self.gcs_mod[edge_device], self.gcs_cache[edge_device]], ignore_index=True)


class Usv_Planner(Atomic):
    PHASE_OFF = "off"         #Standby, wating for a resquet
    PHASE_INIT = "init"       #Send SensorInfo
    PHASE_ON = "on"           #Initialited, wating for a resquet
    PHASE_WORK = "work"       #Taking a measurement
    PHASE_DONE = "done"       #Send Measurement

    def __init__(self, name: str, usv1, delay:float):    
        super().__init__(name)
        self.i_in = Port(Event, "i_int")    #Event to aks the mesaurements  
        self.add_in_port(self.i_in)         
        self.o_out = Port(Event, "o_out")   #Event includes the measurements
        self.add_out_port(self.o_out)
        self.o_info = Port(Event, "o_info")   #Event includes the measurements
        self.add_out_port(self.o_info)

        self.usv1 = usv1
        self.delay = delay
    
    def initialize(self):
        # Wait for a resquet
        self.msgout = None
        self.passivate(self.PHASE_OFF)         #SENSOR OFF
      
    def exit(self):
        self.passivate(self.PHASE_OFF)         #SENSOR OFF
        pass
        
    def deltint(self):
        if self.phase==self.PHASE_INIT:
            self.hold_in(self.PHASE_WORK,self.delay)
        elif self.phase==self.PHASE_WORK:   
            # Variables de entrada/saluda = LON, LAT, xdel            
            mylat=self.msgin.payload['Lat']
            mylon=self.msgin.payload['Lon']
            self.xdel=self.msgin.payload['xdel']
            self.datetime=dt.datetime.fromisoformat(self.msgin.timestamp)+dt.timedelta(seconds=self.delay)
            #BYPASS provisional
            data = {'Lat':mylat,'Lon':mylon,'xdel':self.xdel} 
            self.msgout=Event(id=self.msgin.id,source=self.name,timestamp=self.datetime,payload=data) 
            self.hold_in(self.PHASE_DONE,0)
        elif self.phase==self.PHASE_DONE:
            self.passivate(self.PHASE_ON)
      
    def deltext(self, e: Any):
        if self.phase==self.PHASE_OFF:
            self.msgin = self.i_in.get()
            self.msgout=Event(id=self.msgin.id,source=self.name,timestamp=self.msgin.timestamp,payload=vars(self.msgin)) 
            self.hold_in(self.PHASE_INIT,0)
        elif self.phase==self.PHASE_ON:
            self.msgin = self.i_in.get()
            self.hold_in(self.PHASE_WORK,self.sensorinfo.delay)
          
    def lambdaf(self):
        if self.phase==self.PHASE_INIT:
            self.o_info.add(self.msgout)
            if self.log==True:  logger.info(self.msgout)
        if self.phase==self.PHASE_DONE:
            self.o_out.add(self.msgout)
            if self.log==True:  logger.info(self.msgout)


class FogServer(Coupled):
    """Clase acoplada FogServer."""

    def __init__(self, name, usv1, thing_names: list, thing_event_ids: list, n_offset: int = 100):
        """Inicialización de atributos."""
        super().__init__(name)
        self.i_cmd = Port(CommandEvent, "i_cmd")
        self.add_in_port(self.i_cmd)

        # Puerto de entrada para la conexión con el barco
        self.add_in_port(Port(Event, "i_" + usv1.name))
        # Puerto de salida para la conexión con el barco
        self.add_out_port(Port(Event, "o_" + usv1.name))

        # Puerto de entrada-salida de los sensores
        for thing_name in thing_names:
            self.add_in_port(Port(Event, "i_" + thing_name))
            self.add_out_port(Port(pd.DataFrame, "o_" + thing_name))

        gcs = GCS("GCS", usv1, thing_names, thing_event_ids, n_offset)
        self.add_component(gcs)
        self.add_coupling(self.i_cmd, gcs.i_cmd)

        # Conexión del puerto del barco con la entrada del GCS
        self.add_coupling(gcs.get_in_port("i_" + usv1.name), self.get_in_port("i_" + usv1.name))

        # Conexiones de entrada-salida de datos
        for thing_name in thing_names:
            # EIC
            self.add_coupling(self.get_in_port("i_" + thing_name), gcs.get_in_port("i_" + thing_name))
            # EOC
            self.add_coupling(gcs.get_out_port("o_" + thing_name), self.get_out_port("o_" + thing_name))

        # Nitrates scope
        if SensorEventId.NOX.value in thing_event_ids:
            idx_n = thing_event_ids.index(SensorEventId.NOX.value)
            scope = Scope(thing_names[idx_n], thing_event_ids[idx_n])
            self.add_component(scope)
            self.add_coupling(self.get_in_port("i_" + thing_names[idx_n]), scope.i_in)
            # Inference Service    

        # USVs planner
        USVp = Usv_Planner("USVs_Planner",usv1, delay=0)
        self.add_component(USVp)
        self.add_coupling(gcs.o_IS, USVp.i_in)
        self.add_coupling(self.get_out_port("o_" + usv1.name), USVp.o_out)
        self.add_coupling(self.get_out_port("o_" + usv1.name), USVp.o_info)

