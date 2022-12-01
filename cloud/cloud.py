"""
Fichero que implementa las clases principales de la capa Cloud.

De momento, implementamos la capa Cloud como un modelo atómico.  En el futuro
tendremos que considerarlo como un modelo acoplado.
"""
import logging
import pandas as pd
from time import strftime, localtime
from xdevs.models import Atomic, Port
from xdevs import get_logger
import requests
from datetime import datetime
from time import perf_counter 
from util.event import CommandEvent, CommandEventId, DataEventId, EnergyEventId, Event, DataEventColumns, SensorEventId

logger = get_logger(__name__, logging.DEBUG)

class Cloud(Atomic):
    """Clase para guardar datos en la base de datos."""
    PHASE_REQUEST = "GET and POST petitions"
    #PHASE_GET   = "GET data from server" 
    #PHASE_POST  = "POST data to server"

    def __init__(self, name: str, thing_names:list, thing_event_ids:list, host='http://localhost:80',  log_Time=False, log_Data=False):
        """Función de inicialización de atributos."""
        super().__init__(name)
        # Dirección IP del servidor (Esp32)
        self.timeout         = 0.5
        self.thing_names     = thing_names
        self.thing_event_ids = {}
        self.host            = host
        self.log_Time        = log_Time
        self.log_Data        = log_Data 

        for i in range(0, len(self.thing_names)):
            thing_name = thing_names[i]
            self.thing_event_ids[thing_name] = thing_event_ids[i]
            self.add_in_port(Port(Event, "i_" + thing_name))
            self.add_out_port(Port(Event, "o_" + thing_name))

    def initialize(self):
        """Inicialización de la simulación DEVS."""
        self.max_time    = datetime(1, 1, 1, 0, 0)
        self.msg         = {}
        self.db          = {}
        self.db_cache    = {}
        self.db_path     = {}
        self.counter     = {}
        time_mark        = strftime("%Y%m%d%H%M%S", localtime())
        
        for thing_name in self.thing_names:
            self.db[thing_name]       = pd.DataFrame(columns=DataEventColumns.get_all_columns(self.thing_event_ids[thing_name]))
            self.db_cache[thing_name] = pd.DataFrame(columns=DataEventColumns.get_all_columns(self.thing_event_ids[thing_name]))
            self.db_path[thing_name]  = "datacloud/" + self.parent.name + "." + thing_name + "_" + time_mark
            # offset
            self.counter[thing_name] = pd.DataFrame(columns=DataEventColumns.get_all_columns(self.thing_event_ids[thing_name]))

        self.passivate()

    def exit(self):
        """Función de salida de la simulación."""
        # Aquí tenemos que guardar la base de datos.
        for thing_name in self.thing_names:
            self.db[thing_name].to_csv(self.db_path[thing_name] + ".csv")
        pass

    def lambdaf(self):
        """Función DEVS de salida."""
        if self.phase == self.PHASE_REQUEST:  
            try:
                self.data_out_get  = self.getvar(var="voltage")
                self.pos = round( -1.25*(self.max_time.hour)**2+30*(self.max_time.hour))
                self.data_out_post = self.postvar(type="angle",value=self.pos,unit="degrees")

                if self.log_Time is True: logger.info("CLOUD->{ }: DataTime = %s" %(self.max_time))
                if self.log_Data is True: logger.info("SERVER->CLOUD: Data = %s" %(self.data_out_get))
                if self.log_Data is True: logger.info("CLOUD->SERVER: Data = %s" %(self.data_out_post))

            except requests.exceptions.Timeout:   
                if self.log_Time is True: logger.info("CLOUD->{ }: DataTime = NONE, 'Connection timed out'")
                if self.log_Data is True: logger.info("SERVER->CLOUD: Data = NONE, 'Connection timed out'")
                if self.log_Data is True: logger.info("CLOUD->SERVER: Data = NONE, 'Connection timed out'")

            self.passivate()

    def deltint(self):
        """Función DEVS de transición interna."""
        self.passivate()

    def deltext(self, e):
        """Función DEVS de transición externa."""
        self.continuef(e)
        for thing_name in self.thing_names:
            # Se recoge la información de cada uno de los sensores:
            if self.get_in_port("i_" + thing_name).empty() is False:
                self.msg[thing_name]= self.get_in_port("i_" + thing_name).get()
                self.max_time = max(self.max_time,self.msg[thing_name].timestamp)
            # Una vez se tiene la información de todos los sensores:
            if len(self.msg) == len(self.thing_names):
                for thing_name in self.thing_names:
                    msg_list = list()
                    msg_list.append(self.msg[thing_name].id)
                    msg_list.append(self.msg[thing_name].source)
                    msg_list.append(self.msg[thing_name].timestamp)
                    for value in self.msg[thing_name].payload:
                        msg_list.append(value)
                    self.db[thing_name].loc[len(self.db[thing_name])] = msg_list
                    self.counter[thing_name] += 1
                #self.msgout=Event(id=self.msgin_usv.id,source=self.name,timestamp=self.msg,payload=self.msgin_usv.payload)
                self.msg = {}   
                super().activate(self.PHASE_REQUEST)
                

    # Funciones implementadas con la librería requests
    def getvar(self, var: str)->dict:
        t_start = perf_counter()  
        self.var = var
        params = dict(
            type_in='None',
            value_in='None',
            unit_in='None'
        )
        self.get_petition  = requests.get(self.host+'/'+self.var, params=params, timeout=self.timeout)
        t_stop = perf_counter()
        data_out = {
            'data': self.get_petition.json(),
            'time_request': t_stop-t_start,
            'petition_info': self.get_petition
        }
        return data_out


    def postvar(self, type:str, value:float, unit:str)->dict:
        t_start    = perf_counter()  
        self.type  = type
        self.value = value
        self.unit  = unit
        data_json  = {
            'type' : self.type, 
            'value': self.value, 
            'unit' : self.unit 
        }
        self.post_petition = requests.post(self.host+'/'+self.type, json=data_json,timeout=self.timeout)
        t_stop = perf_counter()
        data_out = {
            'data': data_json,
            'time_request': t_stop-t_start,
            'petition_info': self.post_petition
        }
        return data_out

