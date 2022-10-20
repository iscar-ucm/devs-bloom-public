"""
Fichero que implementa las clases principales para la capa Fog.

TODO: Hay un margen de mejora. El Cloud guarda datos de n_offset en n_offset,
lo que significa que el remanente final no queda guardado. Hay que modificar
esta clase para que guarde el remanente de datos final. Una forma sería enviar
una señal stop cuando la simulación termina, de forma que la función de
transición externa de GCS, al detectar este final, guarde los datos
remanentes.
"""
from cmath import sqrt
from tkinter import EventType
import pandas as pd
import numpy as np
import logging
import datetime as dt
from time import strftime, localtime
from xdevs import get_logger, PHASE_ACTIVE
from xdevs.models import Atomic, Coupled, Port
from util.view import Scope
from util.event import CommandEvent, CommandEventId, EnergyEventId, Event, DataEventColumns, SensorEventId

logger = get_logger(__name__, logging.DEBUG)


class GCS(Atomic):
    """Clase para guardar datos en la base de datos."""

    def __init__(self, name: str,usv1, thing_names: list, thing_event_ids: list, n_offset: int = 100):
        """Función de inicialización de atributos."""
        super().__init__(name)
        self.usv1 = usv1
        self.thing_names = thing_names
        self.thing_event_ids = {}
        self.n_offset = n_offset
        
        # Puertos de entrada de comandos
        self.i_cmd = Port(CommandEvent, "i_cmd")
        self.add_in_port(self.i_cmd)

        # Puertos entrada con los datos del barco 
        self.i_usv = Port(Event, "i_usv")
        self.add_in_port(self.i_usv)

        # Puertos salida para el planificador
        self.o_usvp = Port(Event, "o_usvp")
        self.add_out_port(self.o_usvp)

        # Puertos salida para el Servicio de Inferencia
        self.o_isv = Port(Event, "o_isv")
        self.add_out_port(self.o_isv)
        
        for i in range(0, len(self.thing_names)):
            thing_name = thing_names[i]
            self.thing_event_ids[thing_name] = thing_event_ids[i]
            self.add_in_port(Port(Event, "i_" + thing_name))
            self.add_out_port(Port(pd.DataFrame, "o_" + thing_name))

    def initialize(self):
        """Inicialización de la simulación DEVS."""
        self.boolean_1 = False
        self.boolean_2 = False
        self.msgin_usv   = None
        self.msgout_usvp = None
        self.msgout_isv  = None
        self.db       = {}
        self.db_cache = {}
        self.db_path  = {}
        self.counter  = {}
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

        # Enviando el mensaje correspondiente al planificador 
        if self.boolean_1 == True:
            self.o_usvp.add(self.msgout_usvp)
            print(f'GCS: {self.msgin_usv.timestamp}')
            self.boolean_1 = False

        # Enviando el mensaje correspondiente al Servicio de inferencia 
        if self.boolean_2 == True:
            self.o_isv.add(self.msgout_isv)
            self.boolean_2 == False

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
        # Procesamos primero el puerto del barco:
        if self.i_usv.empty() is False:
            self.msgin_usv = self.i_usv.get()
            # bypass temporal entre GCS y el Planificador
            self.boolean_1 = True
            self.datetime=self.msgin_usv.timestamp
            self.msgout_usvp=Event(id=self.msgin_usv.id,source=self.name,timestamp=self.datetime,payload=self.msgin_usv.payload)
            if self.msgin_usv.payload['SensorsOn'] == True:
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
        else:
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


class Usv_Planner(Atomic):

    def __init__(self, name: str, delay:float):    
        """Instancia la clase."""
        super().__init__(name)

        self.delay = delay
        self.input_buffer = []
        self.data_buffer = []

        # Puerto de entrada para el GCS
        self.i_in = Port(Event, "i_in")
        self.add_in_port(self.i_in)

        # Puertos de salida para el FogServer
        self.o_out = Port(Event, "o_out")
        self.add_out_port(self.o_out)
        self.o_info = Port(Event, "o_info")
        self.add_out_port(self.o_info)

        
    def initialize(self):
        """Función de inicialización."""
        # El planificador conoce los parámetros iniciales del barco
        self.count = 0
        self.boolean = False
        self.msgout    = None
        self.xdel      = [0,0,0]
        self.k2d       = 1/100
        self.X         = []
        self.U         = []
        self.P         = []
        self.SensorsOn = False
        self.mybloom   = False
        self.maxspeed  = 0.002
        # Valores del estado del barco:
        #X[0]=power             X[1]=lon            X[2]=lat
        #U(0)=charger           U(1)=eastspeed      U(2)=nordspeed          U(3)=time of actuator activation 
        #P(0)=solarpower        P(1)=eastwaterspeed P(2)=nordwaterspeed
        super().passivate()

    def exit(self):
        """Exit function."""
        pass

    def lambdaf(self):
        """DEVS output function."""
        if self.boolean == True:
            self.o_out.add(self.msgout)
            self.boolean = False


    def deltint(self):
        """DEVS internal transition function."""
        self.passivate()

    def deltext(self, e):
        """Función DEVS de transición externa."""
        self.continuef(e)
        """DEVS external transition function."""
        if (self.i_in.empty() is False):
            self.msgin = self.i_in.get()
            self.boolean = True
            print(f'PLANER: {self.msgin.timestamp}')
            # Se recogen los valores entregados por el GCS               
            self.X         = self.msgin.payload['X']
            self.U         = self.msgin.payload['U']
            self.P         = self.msgin.payload['P']
            self.xdel      = self.msgin.payload['xdel']
            self.SensorsOn = self.msgin.payload['SensorsOn']
            self.Bloom     = self.msgin.payload['Bloom']
            # Si el barco tiene batería:
            if self.X[0] > 0:
                if self.U[1] >  self.maxspeed: self.U[1] =  self.maxspeed
                if self.U[2] >  self.maxspeed: self.U[2] =  self.maxspeed
                if self.U[1] < -self.maxspeed: self.U[1] = -self.maxspeed
                if self.U[2] < -self.maxspeed: self.U[2] = -self.maxspeed
                # Despl      = Electro   + Solar     - Propulsón
                self.xdel[0] = self.U[0] + self.P[0] - 30*sqrt(self.U[1]^2 + self.U[2]^2)
                self.xdel[1] = self.U[1] + self.k2d*self.P[1] 
                self.xdel[2] = self.U[2] + self.k2d*self.P[2] 
            else:
                self.X[0]    = 0
                self.xdel[0] = self.P[0]
                self.xdel[1] = 0
                self.xdel[2] = 0
            
            # El planificador calcula el estado final del barco
            self.X = [self.X[0]+self.xdel[0], self.X[1]+self.xdel[1], self.X[2]+self.xdel[2] ]

            # Se ajusta el valor máximo de la batería
            if self.X[0] > 1:
                self.X[0] = 1
            
            # Se construye la trama de datos a enviar:
            self.datetime=dt.datetime.fromisoformat(self.msgin.timestamp)+dt.timedelta(seconds=self.delay)
            data = {'X':self.X,'U':self.U,'P':self.P,'xdel':self.xdel,'SensorsOn':self.SensorsOn,'Bloom':self.mybloom}
            self.msgout = Event(id=self.msgin.id,source=self.name,timestamp=self.datetime,payload=data)
            super().activate()


class Inference_Service(Atomic):
    PHASE_OFF = "off"         #Standby, wating for a resquet
    PHASE_INIT = "init"       #Send Inference Service Info
    PHASE_ON = "on"           #Initialited, wating for a resquet
    PHASE_WORK = "work"       #Providing Service
    PHASE_DONE = "done"       #Send Service data

    def __init__(self, name: str, usv1, delay:float):    
        super().__init__(name)

        self.i_in = Port(Event, "i_int")    
        self.add_in_port(self.i_in)         
        self.o_out = Port(Event, "o_out")   
        self.add_out_port(self.o_out)
        self.o_info = Port(Event, "o_info")   
        self.add_out_port(self.o_info)

        self.usv1 = usv1
        self.delay = delay
    
    def initialize(self):
        # Wait for a resquet
        self.msgout = None
        self.passivate(self.PHASE_OFF)         
      
    def exit(self):
        self.passivate(self.PHASE_OFF)         
        pass
        
    def deltint(self):
        pass
    def deltext(self, e: any):
        pass
          
    def lambdaf(self):
        pass


class FogServer(Coupled):
    """Clase acoplada FogServer."""    
    def __init__(self, name, usv1, thing_names: list, thing_event_ids: list, n_offset: int = 100):
        """Inicialización de atributos."""
        super().__init__(name)
        self.i_cmd = Port(CommandEvent, "i_cmd")
        self.add_in_port(self.i_cmd)

        # Puerto de entrada de la conexión con el USV
        self.add_in_port(Port(Event, "i_" + usv1.name))
        # Puerto de salida de la conexión con el USV
        self.add_out_port(Port(Event, "o_" + usv1.name))

        # Puerto de entrada-salida de los sensores
        for thing_name in thing_names:
            self.add_in_port(Port(Event, "i_" + thing_name))
            self.add_out_port(Port(pd.DataFrame, "o_" + thing_name))

        gcs = GCS("GCS", usv1, thing_names, thing_event_ids, n_offset)
        self.add_component(gcs)
        self.add_coupling(self.i_cmd, gcs.i_cmd)
        # Conexión del puerto de entrad del USV con la entrada del GCS
        self.add_coupling(self.get_in_port("i_" + usv1.name), gcs.i_usv)

        # Conexiones de entrada-salida de datos
        for thing_name in thing_names:
            # EIC
            self.add_coupling(self.get_in_port("i_" + thing_name), gcs.get_in_port("i_" + thing_name))
            # EOC
            self.add_coupling(gcs.get_out_port("o_" + thing_name), self.get_out_port("o_" + thing_name))

        # USVs planner
        USVp = Usv_Planner("USVs_Planner", delay=0)
        self.add_component(USVp)
        # Conexión de salida del puerto del GCS con el puerto de entrada del planificador
        self.add_coupling(gcs.o_usvp, USVp.i_in)
        # Conexión de salida del planificador con el puerto de salida del FogServer
        self.add_coupling(USVp.o_out, self.get_out_port("o_" + usv1.name))
        self.add_coupling(USVp.o_info, self.get_out_port("o_" + usv1.name))

        '''
        # Nitrates scope
        if SensorEventId.NOX.value in thing_event_ids:
            idx_n = thing_event_ids.index(SensorEventId.NOX.value)
            scope = Scope(thing_names[idx_n], thing_event_ids[idx_n])
            self.add_component(scope)
            # bypass??
            self.add_coupling(self.get_in_port("i_" + thing_names[idx_n]), scope.i_in)

        # Inference Service 
        isv = Inference_Service("Inference_Service", usv1, delay=0)
        self.add_component(isv)
        self.add_coupling(gcs.o_isv, isv.i_in)
        self.add_coupling(isv.o_out, gcs.i_isv)
        '''