"""
Fichero que implementa las clases principales para la capa Fog.

TODO: Hay un margen de mejora. El Cloud guarda datos de n_offset en n_offset,
lo que significa que el remanente final no queda guardado. Hay que modificar
esta clase para que guarde el remanente de datos final. Una forma sería enviar
una señal stop cuando la simulación termina, de forma que la función de
transición externa de GCS, al detectar este final, guarde los datos
remanentes.
"""
import math
from queue import Empty
import pandas as pd
import numpy as np
from typing import Any
import logging
import datetime as dt
from datetime import timedelta
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon
from matplotlib.patches import Circle
from matplotlib.animation import FuncAnimation
from matplotlib.collections import PatchCollection
from scipy.spatial import KDTree
from time import strftime, localtime
from xdevs import get_logger, PHASE_ACTIVE
from xdevs.models import Atomic, Coupled, Port
from edge.sensor import SensorEventId, SensorInfo
from cloud.cloud import Cloud_Sensor
from util.view import Scope
from util.event import CommandEvent, CommandEventId, DataEventId, EnergyEventId, Event, DataEventColumns, SensorEventId

logger = get_logger(__name__, logging.DEBUG)


class GCS(Atomic):
    """Clase para guardar datos en la base de datos."""
    PHASE_ISV     = "sending_to_ISV"           # Sending Data to Inference Service
    PHASE_PLANNER = "sending_to_USV_PLANNER"   # Sending Data to USV planner
    PHASE_SUN     = "sensing_to_sensor_sun"    # Sending Comand to Sun sensor
    PHASE_CLOUD   = "sending_to_cloud"         # Sending Data to Cloud 
    PHASE_INIT    = "delt_int"

    def __init__(self, name: str, usv_name: str, thing_names: list, thing_event_ids: list, log_Time=False, log_Data=False,n_offset: int = 100):
        """Función de inicialización de atributos."""
        super().__init__(name)
        self.thing_names     = thing_names
        self.thing_event_ids = {}

        self.log_Time = log_Time
        self.log_Data = log_Data
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

        # Puerto de entrada para el Servicio de Inferencia
        self.i_isv = Port(Event, "i_isv")
        self.add_in_port(self.i_isv)

        # Puerto de salida para el Servicio de Inferencia
        self.o_isv = Port(Event, "o_isv")
        self.add_out_port(self.o_isv)

        # Puerto de entrada para el sensor Sun
        self.i_sensor_s = Port(Event, "i_sensor_s")
        self.add_in_port(self.i_sensor_s)

        # Puerto de salida para el sensor Sun
        self.o_sensor_s = Port(Event, "o_sensor_s")
        self.add_out_port(self.o_sensor_s)
        
        for i in range(0, len(self.thing_names)):
            thing_name = thing_names[i]
            self.thing_event_ids[thing_name] = thing_event_ids[i]
            self.add_in_port(Port(Event, "i_" + thing_name))
            self.add_out_port(Port(Event, "o_" + thing_name))

    def initialize(self):
        """Inicialización de la simulación DEVS."""
        self.mydata = {}
        self.datetimes = {}
        self.mydata  = pd.read_csv('./dataedge/'+'Sensor2008_sun.csv', parse_dates=True)  # Sensor data loading
        self.datetimes = [dt.datetime.fromisoformat(s) for s in self.mydata['DateTime']] #Para CSV
        self.N = self.mydata.DateTime.count() # N = 721
        self.ind = -1

        delta = self.datetimes[0] - self.datetimes[-1]
        row = self.mydata.iloc[0]   # Telemetría
        payload = row.to_dict() #{'DateTime': '', 'Lat': , 'Lon': , 'Depth': , 'Sensor': ''}
        self.datetime = payload.pop('DateTime')
        self.dataid = SensorEventId.SUN
        self.msgout_sensor = Event(id=self.dataid.value, source=self.name, timestamp=self.datetime, payload=payload)
        
        self.msgin_usv   = None
        self.msg         = {}
        self.db          = {}
        self.db_cache    = {}
        self.db_path     = {}
        self.counter     = {}
        time_mark        = strftime("%Y%m%d%H%M%S", localtime())
        for thing_name in self.thing_names:
            self.db[thing_name]       = pd.DataFrame(columns=DataEventColumns.get_all_columns(self.thing_event_ids[thing_name]))
            self.db_cache[thing_name] = pd.DataFrame(columns=DataEventColumns.get_all_columns(self.thing_event_ids[thing_name]))
            self.db_path[thing_name]  = "datafog/" + self.parent.name + "." + thing_name + "_" + time_mark
            # offset
            self.counter[thing_name] = pd.DataFrame(columns=DataEventColumns.get_all_columns(self.thing_event_ids[thing_name]))

        self.db["ExtSenS"] = pd.DataFrame(columns=DataEventColumns.get_all_columns(self.thing_event_ids["SimSenS"]))
        self.db_path["ExtSenS"]  = "datafog/" + self.parent.name + "." + "ExtSenS" + "_" + time_mark
        self.passivate()

    def exit(self):
        """Función de salida de la simulación."""
        # Aquí tenemos que guardar la base de datos.
        for thing_name in self.thing_names:
            self.db[thing_name].to_csv(self.db_path[thing_name] + ".csv")

        self.db["ExtSenS"].to_csv(self.db_path["ExtSenS"] + ".csv")
        pass

    def lambdaf(self):
        # Enviando el mensaje correspondiente al planificador o a los servicios necesarios
        if self.phase == self.PHASE_SUN and self.ind < self.N:
            self.o_sensor_s.add(self.msgout_sensor)
            self.passivate()

        if self.phase == self.PHASE_ISV and self.ind < self.N:
            self.o_isv.add(self.msgout_isv)
            cloud_body = Cloud_Sensor(host='http://192.168.137.167')
            self.data_out_get  = cloud_body.getvar(var="voltage")
            self.pos = round( -1.25*(self.msgout_isv.timestamp.hour-12)**2+180)
            self.data_out_post = cloud_body.postvar(type="angle",value=self.pos,unit="degrees")

            if self.log_Time is True: logger.info("GCS->ISV: DataTime = %s" %(self.msgout_isv.timestamp))
            if self.log_Data is True: logger.info("GCS->ISV: Data = Sensors + msg_usv" )
            self.passivate()

        if self.phase == self.PHASE_PLANNER and self.ind < self.N:
            self.o_usvp.add(self.msgout_usvp)
            if self.log_Time is True: logger.info("GCS->USV_P: DataTime = %s" %(self.msgout_usvp.timestamp))
            if self.log_Data is True: logger.info("GCS->ISV: Data = %s" %(self.msgout_usvp.payload))
            self.passivate()

        if self.phase == self.PHASE_CLOUD:    
            for thing_name in self.thing_names:
                if self.counter[thing_name] >= self.n_offset:
                    df = self.db[thing_name].tail(self.n_offset)
                    self.get_out_port("o_" + thing_name).add(df)
            self.passivate()

    def deltint(self):
        """DEVS internal transition function."""
        # Calcula delta tiempo hasta siguiente Telemetría
        self.passivate()

    def deltext(self, e: Any):
        """Función DEVS de transición externa."""
        self.continuef(e)
        # Procesamos primero el puerto del barco:
        if self.i_usv: 
           self.msgin_usv = self.i_usv.get()
           self.max_time = self.msgin_usv.timestamp
        if (self.msgin_usv!=None):
            if self.msgin_usv.payload['SensorsOn'] == True:
                # Se comprueban si todos los puertos de los sensores tienen mensajes de entrada:
                for thing_name in self.thing_names:
                    if self.get_in_port("i_" + thing_name).empty() is False:
                        self.msg[thing_name]= self.get_in_port("i_" + thing_name).get()
                        self.max_time = max(self.max_time,self.msg[thing_name].timestamp)
                # Si falta únicamente el valor del sensor SUN
                if len(self.msg) == len(self.thing_names)-1:
                    self.ind = self.ind + 1              # Actualizo indice a siguiente
                    if self.ind >= self.N:
                        self.passivate()
                    else:
                        self.datetime = self.max_time.strftime("%Y-%m-%d %H:%M:%S")
                        row = self.mydata.iloc[self.ind]   # Telemetría
                        payload = row.to_dict() #{'DateTime': '', 'Lat': , 'Lon': , 'Depth': , 'Sensor': ''}
                        self.dataid = SensorEventId.SUN
                        self.msgout_sensor = Event(id=self.dataid.value, source=self.name, timestamp=self.datetime, payload=payload)
                        self.activate(self.PHASE_SUN)
                        
                # Cuando se tiene la información de todos los sensores:
                if len(self.msg) == len(self.thing_names):
                    for thing_name in self.thing_names:
                        msg_list = list()
                        msg_list.append(self.msg[thing_name].id)
                        msg_list.append(self.msg[thing_name].source)
                        msg_list.append(self.msg[thing_name].timestamp)
                        for value in self.msg[thing_name].payload.values():
                            msg_list.append(value)
                        self.db[thing_name].loc[len(self.db[thing_name])] = msg_list
                        self.counter[thing_name] += 1
                        # Envío de los datos hacia la capa CLOUD cada self.n_offset 
                        #if self.counter[thing_name] == self.n_offset:
                        #    super().activate(self.PHASE_CLOUD)
                    self.data = self.msg
                    # Se activa la salida del módulo GCS, se actualizan los mensajes de salida(bypass temporal) y se eliminan todos los mensajes de entrada:
                    self.msgin_usv.payload.update({'db':self.data})
                    self.msgout_isv=Event(id=self.msgin_usv.id,source=self.name,timestamp=self.max_time,payload=self.msgin_usv.payload)
                    self.msg = {}   
                    super().activate(self.PHASE_ISV)
            else:           
                self.msgout_isv=Event(id=self.msgin_usv.id,source=self.name,timestamp=self.msgin_usv.timestamp,payload=self.msgin_usv.payload)
                super().activate(self.PHASE_ISV)  

        if self.i_isv.empty() is False:
            self.msgin_isv = self.i_isv.get()
            self.msgout_usvp=Event(id=self.msgin_usv.id,source=self.name,timestamp=self.max_time,payload=self.msgin_isv.payload)
            super().activate(self.PHASE_PLANNER)

        if self.i_cmd.empty() is False:
            cmd: CommandEvent = self.i_cmd.get()
            if cmd.cmd == CommandEventId.CMD_FIX_OUTLIERS:
                if self.log == True: logger.info("Command %s has been retired temporarily.", cmd.cmd.value)

            if cmd.cmd == CommandEventId.CMD_START_SIM:
                start: np.datetime = cmd.date
                delstart = [s-start for s in self.datetimes]
                self.ind = round(np.nanargmin(np.absolute(delstart)))  # Nearest time index
                delta = (self.datetimes[self.ind] - start).total_seconds()
                self.datetime = self.datetimes[self.ind]
                if (delta >= 0):
                    super().passivate()

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
    ''' Fases útiles para futuras implementaciones
        PHASE_OFF = "off"         #Standby, wating for a resquet
        PHASE_INIT = "init"       #Send Inference Service Info
        PHASE_ON = "on"           #Initialited, wating for a resquet
        PHASE_WORK = "work"       #Providing Service
        PHASE_DONE = "done"       #Send Service data
    '''
    PHASE_SENDING = "sending" # Sending Data

    def __init__(self, name: str, delay:float, log_Time=False, log_Data=False):    
        """Instancia la clase."""
        super().__init__(name)

        self.delay = delay
        self.log_Time=log_Time
        self.log_Data=log_Data
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
        self.k_2d_dis_usv        = 1/100   # USV 2D displacement
        self.maxspeed            = 0.002   # USV max speed
        self.electronic_consume  = -0.003  # USV electronic consume
        self.SensorsOn           = False   # Sensors boolean
        self.msgout              = None    # Message out
        super().passivate()

    def exit(self):
        """Exit function."""
        pass

    def lambdaf(self):
        """DEVS output function."""
        #if self.boolean == True:
        if self.phase == self.PHASE_SENDING:
            self.o_out.add(self.msgout)
            if self.log_Time is True: logger.info("PLANNER->USV: datetime = %s" % (self.msgout.timestamp))
            if self.log_Data is True: logger.info("PLANNER->USV: Data = %s" % (self.msgout.payload))
            self.passivate()

    def deltint(self):
        """DEVS internal transition function."""
        self.passivate()

    def deltext(self, e):
        """Función DEVS de transición externa."""
        self.continuef(e)
        """DEVS external transition function."""
        if (self.i_in.empty() is False):
            self.msgin = self.i_in.get()
            self.datetime=self.msgin.timestamp+dt.timedelta(seconds=self.delay)
            #bypass temporal
            self.msgout = Event(id=self.msgin.id,source=self.name,timestamp=self.datetime,payload=self.msgin.payload)
            super().activate(self.PHASE_SENDING)


class Inference_Service(Atomic):
    ''' Fases útiles para futuras implementaciones
        PHASE_OFF = "off"         #Standby, wating for a resquet
        PHASE_INIT = "init"       #Send Inference Service Info
        PHASE_ON = "on"           #Initialited, wating for a resquet
        PHASE_WORK = "work"       #Providing Service
        PHASE_DONE = "done"       #Send Service data
    '''
    PHASE_SENDING = "sending"     # Sending Data

    def __init__(self, name: str, usv_name: str,thing_names, delay:float, log_Time=False, log_Data=False):    
        super().__init__(name)
        self.thing_names = thing_names
        self.delay = delay
        self.log_Time=log_Time
        self.log_Data=log_Data

        # Puerto de entrada de comandos(desde el Generador)
        self.i_cmd = Port(CommandEvent, "i_cmd")    
        self.add_in_port(self.i_cmd)      

        # Puerto de entrada de datos(desde el GCS)
        self.i_in = Port(Event, "i_int")    
        self.add_in_port(self.i_in)      

        # Puerto de salida de datos(hacia el GCS)   
        self.o_out = Port(Event, "o_out")   
        self.add_out_port(self.o_out)

        # Puerto de salida de info(hacia el GCS)  
        self.o_info = Port(Event, "o_info")   
        self.add_out_port(self.o_info)

    def initialize(self):
        # Wait for a resquet

        self.tau             = 100       # Time
        self.lyr             = 54        # Depth layers (54 = surface)
        self.ip              = 9         # Bloom particle position index on map
        self.k_breath        = 0.05      # Breath
        self.k_photo         = 5         # Photosynthesis
        self.k_decrease      = 1/6       # Decrease
        self.k_growth        = 1         # Growth
        self.k_2d_dis_bloom  = 1/60      # Bloom 2D displacement

        self.nox             = list()    # Nitrate
        self.dox             = list()    # Dissolved oxygen
        self.algae           = list()    # Algae
        self.water_temp      = list()    # Water temperature
        self.water_x         = list()    # Water speed x axis
        self.water_y         = list()    # Water speed y axis
        self.wind_x          = list()    # Wind speed x axis
        self.wind_y          = list()    # Wind speed y axis  
        self.sun             = list()    # Sun radiation
        self.frame           = 0         # Frame
        self.msgout          = None      # Message out
        self.passivate()         
      
    def exit(self):
        self.passivate()         
        pass
        
    def deltext(self, e: any):
        """Función DEVS de transición externa."""
        self.continuef(e)
        if (self.i_in.empty() is False):
            # Load the payload data into variables
            self.msgin          = self.i_in.get()                         # Message recieved
            self.db             = self.msgin.payload['db']                # Sensors data
            self.datetime       = self.msgin.timestamp                    # Date
            self.SensorsOn      = self.msgin.payload['SensorsOn']         # Sensors boolean

            # The first message contains all the initial information
            if self.msgin.id == 'USV_Init':
                # Load the initial payload data into variables
                self.zonal_lon      = self.msgin.payload['zonal_lon']      # Zonal longitude
                self.zonal_lat      = self.msgin.payload['zonal_lat']      # Zonal latitude
                self.nodal_lon      = self.msgin.payload['nodal_lon']      # Nonal longitude
                self.nodal_lat      = self.msgin.payload['nodal_lat']      # Nonal latitude
                self.bottom_elev    = self.msgin.payload['bottom_elev']    # Bottom elevation
                self.w_surf_elev    = self.msgin.payload['w_surf_elev']    # Water surface elevation
                self.nodes          = self.msgin.payload['nodes']          # Nodes surrounding element
                self.time           = self.msgin.payload['time']           # Time
                self.sigma          = self.msgin.payload['sigma']          # Sigma at layer midpoints
                self.bloom          = self.msgin.payload['bloom']          # Bloom boolean
                self.maptree        = self.msgin.payload['maptree']        # Map

                # Variable initialization
                self.depth             = self.w_surf_elev[self.tau-1, :] - self.bottom_elev[0, :] + np.transpose(self.sigma) * (self.w_surf_elev[self.tau-1, :] - self.bottom_elev[0, :])
                self.ini_bloom_size    = 0
                self.ini_bloom_lon     = self.zonal_lon[self.ip]
                self.ini_bloom_lat     = self.zonal_lat[self.ip]
                self.bloom_size        = self.ini_bloom_size
                self.bloom_lon         = self.ini_bloom_lon
                self.bloom_lat         = self.ini_bloom_lat
                self.usv_power         = 0.5
                self.usv_lon           = self.ini_bloom_lon
                self.usv_lat           = self.ini_bloom_lat  

                # Load the sensors data into variables
                for thing_name in self.thing_names:
                    if self.db[thing_name].id == 'NOX':
                        self.nox         = self.db[thing_name].payload['Value']
                    if self.db[thing_name].id == 'DOX':
                        self.dox         = self.db[thing_name].payload['Value']
                    if self.db[thing_name].id == 'ALG':
                        self.algae       = self.db[thing_name].payload['Value']
                    if self.db[thing_name].id == 'WTE':
                        self.water_temp  = self.db[thing_name].payload['Value']
                    if self.db[thing_name].id == 'WFU':
                        self.water_x     = self.db[thing_name].payload['Value']
                    if self.db[thing_name].id == 'WFV':
                        self.water_y     = self.db[thing_name].payload['Value']
                    if self.db[thing_name].id == 'WFX':
                        self.wind_x      = self.db[thing_name].payload['Value']
                    if self.db[thing_name].id == 'WFY':
                        self.wind_y      = self.db[thing_name].payload['Value']
                    if self.db[thing_name].id == 'SUN':
                        self.sun         = self.db[thing_name].payload['Value']
            
                # When the day begins it restarts
                if self.datetime.hour == 0 and self.datetime.minute == 0:
                    self.bloom_size = self.ini_bloom_size
                    self.bloom_lon  = self.ini_bloom_lon
                    self.bloom_lat  = self.ini_bloom_lat
                    self.bloom      = False

                # Recalculate USV ip
                _, self.ip = self.maptree.query([self.usv_lon, self.usv_lat])

                # Variable calculations
                self.breath          = self.nox * self.dox
                self.photosynthesis  = self.nox * self.sun
                self.food            = self.k_breath * self.breath + self.k_photo * self.photosynthesis
                self.sun_radiation   = 0.04 * self.sun

                # Bloom logic
                if self.dox > 20:
                    self.bloom = True
                if self.dox < 15:
                    self.bloom = False

                # Bloom dynamic
                self.bloom_size = self.bloom_size + self.k_growth * self.food - self.k_decrease * self.bloom_size
                if self.bloom:
                    self.bloom_lon = self.bloom_lon + self.k_2d_dis_bloom * self.water_x
                    self.bloom_lat = self.bloom_lat + self.k_2d_dis_bloom * self.water_y
                else:
                    self.bloom_lon = self.ini_bloom_lon
                    self.bloom_lat = self.ini_bloom_lat
                # Size control
                if self.bloom_size > 10:
                    self.bloom_size = 10

                # USV position error
                self.lon_usv_error = self.bloom_lon - self.usv_lon
                self.lat_usv_error = self.bloom_lat - self.usv_lat

                # Se construye la trama de datos a enviar:
                self.datetime+=dt.timedelta(seconds=self.delay)    
                data = {'usv_power':self.usv_power,'usv_lon':self.usv_lon,'usv_lat':self.usv_lat,'lon_usv_error':self.lon_usv_error,'lat_usv_error':self.lat_usv_error,'sun_radiation':self.sun_radiation,'water_x':self.water_x,'water_y':self.water_y,'SensorsOn':self.SensorsOn}
                self.msgout = Event(id=self.msgin.id,source=self.name,timestamp=self.datetime,payload=data)
                self.frame+=1
                super().activate(self.PHASE_SENDING)

            # The other messages only contain the USV and sensors info
            if self.msgin.id == 'USV':
                # Load the payload data into variables
                self.usv_power  = self.msgin.payload['usv_power']   # USV power
                self.usv_lon    = self.msgin.payload['usv_lon']     # USV longitude
                self.usv_lat    = self.msgin.payload['usv_lat']     # USV latitude

                # Load the sensors data into variables
                for thing_name in self.thing_names:
                    if self.db[thing_name].id == 'NOX':
                        self.nox         = self.db[thing_name].payload['Value']
                    if self.db[thing_name].id == 'DOX':
                        self.dox         = self.db[thing_name].payload['Value']
                    if self.db[thing_name].id == 'ALG':
                        self.algae       = self.db[thing_name].payload['Value']
                    if self.db[thing_name].id == 'WTE':
                        self.water_temp  = self.db[thing_name].payload['Value']
                    if self.db[thing_name].id == 'WFU':
                        self.water_x     = self.db[thing_name].payload['Value']
                    if self.db[thing_name].id == 'WFV':
                        self.water_y     = self.db[thing_name].payload['Value']
                    if self.db[thing_name].id == 'WFX':
                        self.wind_x      = self.db[thing_name].payload['Value']
                    if self.db[thing_name].id == 'WFY':
                        self.wind_y      = self.db[thing_name].payload['Value']
                    if self.db[thing_name].id == 'SUN':
                        self.sun         = self.db[thing_name].payload['Value']

                # When the day begins it restarts
                if self.datetime.hour == 0 and self.datetime.minute == 0:
                    self.bloom_size = self.ini_bloom_size
                    self.bloom_lon  = self.ini_bloom_lon
                    self.bloom_lat  = self.ini_bloom_lat
                    self.bloom      = False

                # Recalculate USV ip
                _, self.ip = self.maptree.query([self.usv_lon, self.usv_lat])

                # Variable calculations
                self.breath          = self.nox * self.dox
                self.photosynthesis  = self.nox * self.sun
                self.food            = self.k_breath * self.breath + self.k_photo * self.photosynthesis
                self.sun_radiation   = 0.04 * self.sun

                # Bloom logic
                if self.dox > 20:
                    self.bloom = True
                if self.dox < 15:
                    self.bloom = False

                # Bloom dynamic
                self.bloom_size = self.bloom_size + self.k_growth * self.food - self.k_decrease * self.bloom_size
                if self.bloom:
                    self.bloom_lon = self.bloom_lon + self.k_2d_dis_bloom * self.water_x
                    self.bloom_lat = self.bloom_lat + self.k_2d_dis_bloom * self.water_y
                else:
                    self.bloom_lon = self.ini_bloom_lon
                    self.bloom_lat = self.ini_bloom_lat
                # Size control
                if self.bloom_size > 10:
                    self.bloom_size = 10

                # USV position error
                self.lon_usv_error = self.bloom_lon - self.usv_lon
                self.lat_usv_error = self.bloom_lat - self.usv_lat

                # Se construye la trama de datos a enviar:
                self.datetime+=dt.timedelta(seconds=self.delay)    
                data = {'usv_power':self.usv_power,'usv_lon':self.usv_lon,'usv_lat':self.usv_lat,'lon_usv_error':self.lon_usv_error,'lat_usv_error':self.lat_usv_error,'sun_radiation':self.sun_radiation,'water_x':self.water_x,'water_y':self.water_y,'SensorsOn':self.SensorsOn}
                self.msgout = Event(id=self.msgin.id,source=self.name,timestamp=self.datetime,payload=data)
                self.frame+=1
                super().activate(self.PHASE_SENDING)


    def lambdaf(self):
        """DEVS output function."""
        if self.phase == self.PHASE_SENDING:
            self.o_out.add(self.msgout)
            if self.log_Time is True: logger.info("ISV->GCS: datetime = %s" % (self.msgout.timestamp))
            if self.log_Data is True: logger.info("ISV->GC: Data = %s" % (self.msgout.payload))
            self.passivate()
            
    def deltint(self):
        pass

        
class FogServer(Coupled):
    """Clase acoplada FogServer."""    
    def __init__(self, name, usv_name:str, thing_names: list, thing_event_ids: list, sensor_s, log_Data=False, log_Time=False, n_offset: int = 100):
        """Inicialización de atributos."""
        super().__init__(name)
        self.i_cmd = Port(CommandEvent, "i_cmd")
        self.add_in_port(self.i_cmd)

        # Puerto de entrada de la conexión con el USV
        self.add_in_port(Port(Event, "i_" + usv_name))
        # Puerto de salida de la conexión con el USV
        self.add_out_port(Port(Event, "o_" + usv_name))
        # Puerto de salida de la conexión con el sensor S
        self.o_sensor = Port(Event, "o_sensor")
        self.add_out_port(self.o_sensor)


        # Puerto de entrada-salida de los sensores
        for thing_name in thing_names:
            self.add_in_port(Port(Event, "i_" + thing_name))
            self.add_out_port(Port(Event, "o_" + thing_name))

        gcs = GCS("GCS", usv_name, thing_names, thing_event_ids, log_Time=log_Time, log_Data = log_Data, n_offset=n_offset)
        self.add_component(gcs)
        self.add_coupling(self.i_cmd, gcs.i_cmd)
        # Conexión del puerto de entrad del USV con la entrada del GCS
        self.add_coupling(self.get_in_port("i_" + usv_name), gcs.i_usv)
        # Conexión del puerto de salida del GCS con el puerto de salida del sensor Sun
        self.add_coupling(gcs.o_sensor_s,self.o_sensor)
        

        # Conexiones de entrada-salida de datos
        for thing_name in thing_names:
            # EIC
            self.add_coupling(self.get_in_port("i_" + thing_name), gcs.get_in_port("i_" + thing_name))
            # EOC
            self.add_coupling(gcs.get_out_port("o_" + thing_name), self.get_out_port("o_" + thing_name))

        # USVs planner
        USVp = Usv_Planner("USVs_Planner", delay=0, log_Time=log_Time, log_Data = log_Data)
        self.add_component(USVp)
        # Conexión de salida del puerto del GCS con el puerto de entrada del planificador
        self.add_coupling(gcs.o_usvp, USVp.i_in)
        # Conexión de salida del planificador con el puerto de salida del FogServer
        self.add_coupling(USVp.o_out, self.get_out_port("o_" + usv_name))
        self.add_coupling(USVp.o_info, self.get_out_port("o_" + usv_name)) 

        # Inference Service 
        isv = Inference_Service("Inference_Service", usv_name, thing_names, delay=0, log_Time=log_Time, log_Data = log_Data)
        self.add_component(isv)
        self.add_coupling(self.i_cmd, isv.i_cmd)
        self.add_coupling(gcs.o_isv, isv.i_in)
        self.add_coupling(isv.o_out, gcs.i_isv)

        '''
        # Nitrates scope
        if SensorEventId.NOX.value in thing_event_ids:
            idx_n = thing_event_ids.index(SensorEventId.NOX.value)
            scope = Scope(thing_names[idx_n], thing_event_ids[idx_n])
            self.add_component(scope)
            # bypass??
            self.add_coupling(self.get_in_port("i_" + thing_names[idx_n]), scope.i_in)

        '''       