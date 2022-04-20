from xdevs import get_logger
from xdevs.models import Atomic, Port
from xdevs.models import Coupled
from xdevs.sim import Coordinator
import logging
logger = get_logger(__name__, logging.INFO)

from typing import Any
import datetime as dt

PHASE_ON = "on"           #Taking a measurement
PHASE_OFF = "off"         #Wating a resquet


#from site import addsitedir
#addsitedir('C:/Users/segu2/OneDrive - Universidad Complutense de Madrid (UCM)/devs-bloom-1')

from edge.file import FileIn,FileOut
from edge.body import SimBody,SimBody2
from util.event import Event,DataEventId,SimSenId


class SimSensor(Atomic):
  '''Simulated Sensor using a simulated Body in NetHFC4 format (no sigma)'''
  def __init__(self, name,simbody,delay=0,log=False):       
    super().__init__(name)
    self.log=log
    self.i_in = Port(Event, "i_int")    #Event commads to read  sensors
    self.add_in_port(self.i_in)
    self.o_out = Port(Event, "o_out")   #Event includes the measurements
    self.add_out_port(self.o_out)
    #Simulated Body in NetHFC4 format
    self.simbody=simbody                #A simulated Body object
    self.delay=delay                    #The measurement takes delay seconds. 
  
  def initialize(self):
    # Wait for a resquet
    self.passivate()

  def exit(self):
    pass
		
  def deltint(self):
    self.hold_in(PHASE_OFF, 0)
    self.passivate()
    pass

  def deltext(self, e: Any):
    self.hold_in(PHASE_ON, self.delay)  #seconds to read the signals
    msg = self.i_in.get()
   
    #ACOPLO CON NUESTRO TIEMPO DE SIMULACIÓN con el de SIMBODY
    #Hago coincidir el inicio de nuestra Simulación con el inicio de SimBody
    simtime=msg.timestamp-dt.datetime(2021,8,1,0,0,0)
    fdays=simtime.seconds/(24.0*60.0*60.0)
    times=self.simbody.vars['time']
    #times0=times -times[0]   #Lo he restado en SimBody     
    ind=0                     #Indice de tiempo
    while times[ind]<fdays:  #Busco el siguiente tiempo
      ind=ind+1
    myt=ind
    #myt=50  #Indice del tiempo de prueba    
    self.myvar=msg.id
    #Asumimos que la profundidad es layer. Realmente habrá que hacer alguna corrección con Sigma.
    mylayer=round(msg.payload['Depth'])
    mylat=msg.payload['Lat']
    mylon=msg.payload['Lon']
    varint=self.simbody.readvar(self.myvar,myt,mylat,mylon,mylayer)
    self.datetime=msg.timestamp+dt.timedelta(seconds=self.delay)
    self.data = {'Time':myt,'Lat':mylat,'Lon':mylon,'Depth':mylayer, self.myvar: varint}
  
  def lambdaf(self):
    msg=Event(id=self.myvar,source=self.name,timestamp=self.datetime,payload=self.data)
    self.o_out.add(msg)
    if self.log==True: 
      logger.info("Sensor: %s DateTime: %s Payload: %s" , self.name,self.datetime,self.data)
      #logger.info(msg)


class SimSensor2(Atomic):
  '''Simulated Sensor using a simulated Body in NetHFC4 format using sigma (virtual time) '''
  def __init__(self, name,simbody,start,delay=0,log=False):       
    super().__init__(name)
    self.log=log
    self.i_in = Port(Event, "i_int")    #Event commads to read  sensors
    self.add_in_port(self.i_in)
    self.o_out = Port(Event, "o_out")   #Event includes the measurements
    self.add_out_port(self.o_out)
    
    self.simbody=simbody                #Simulated Body in NetHFC4 format
    self.start=start                    #Start DateTime of Simulation
    self.delay=delay                    #The measurement takes delay seconds. 
  
  def initialize(self):
    # Wait for a resquet
    self.passivate()

  def exit(self):
    pass
		
  def deltint(self):
    self.hold_in(PHASE_OFF, 0)
    self.passivate()
    pass

  def deltext(self, e: Any):
    self.hold_in(PHASE_ON, self.delay)  #seconds to read the signals
    msg = self.i_in.get()

    #ACOPLE DE TIEMPOS DE SIMULACIÓN y SIMBODY
    #Hago coincidir el Tiempo de Simulación con el Tiempo de SimBody
    simtime=msg.timestamp-self.start    #dt.datetime(2021,8,1,0,0,0)
    myt=simtime.seconds                 #Seconds of the simulations.   
    mylat=msg.payload['Lat']
    mylon=msg.payload['Lon']
    mydepth=msg.payload['Depth']
    self.myvar=msg.id
    value=self.simbody.readvar(self.myvar,myt,mylat,mylon,mydepth)
    self.datetime=msg.timestamp+dt.timedelta(seconds=self.delay)
    self.data = {'Time':myt,'Lat':mylat,'Lon':mylon,'Depth':mydepth, self.myvar: value}
  
  def lambdaf(self):
    msg=Event(id=self.myvar,source=self.name,timestamp=self.datetime,payload=self.data)
    self.o_out.add(msg)
    if self.log==True: 
      logger.info("Sensor: %s DateTime: %s Payload: %s" , self.name,self.datetime,self.data)
      #logger.info(msg)


class Test1(Coupled):
  '''Ejemplo acoplado que:
    *desde un fichero pide TM de O2 a SimSensor
    *SimSensor lee las TM de O2 desde un SimBody
    *SimSensor genera la TM deO2 60s más tarde
    *La TM de O2 se guardan en un fichero con t,lat,lon,dep
  '''
  def __init__(self, name, simbody, start, log=False):
    super().__init__(name)
    #AskSensor = FileIn("Ask_N", './data/LatLonDep.xlsx',start=start, dataid=SimSenId.NITROGEN, log=log)
    AskSensor = FileIn("Ask_O", './data/LatLonDep.xlsx',start=start, dataid=SimSenId.OXIGEN, log=log)   
    Sensor = SimSensor("SimulatedSensor", simbody, delay=60, log=log)     
    Outfile = FileOut("FileOutSimSen", './data/FileOutSensor.xlsx', log=log)     
    self.add_component(AskSensor)
    self.add_component(Sensor)
    self.add_component(Outfile)
    self.add_coupling(AskSensor.o_out, Sensor.i_in)
    self.add_coupling(Sensor.o_out, Outfile.i_in)

class Test2(Coupled):
  '''Ejemplo acoplado que:
    *desde un fichero pide TM de O2 a SimSensor
    *SimSensor lee las TM de O2 desde un SimBody
    *SimSensor genera la TM deO2 60s más tarde
    *La TM de O2 se guardan en un fichero con t,lat,lon,dep
  '''
  def __init__(self, name, simbody, start, log=False):
    super().__init__(name)
    #AskSensor = FileIn("AskMeasurement", './data/LatLonDep.xlsx',start=start, dataid=DataEventId.NITROGEN, log=log)
    AskSensor = FileIn("Ask_O", './data/LatLonDep.xlsx',start=start, dataid=SimSenId.OXIGEN, log=log)   
    Sensor = SimSensor2("SimulatedSensor2", simbody, start=start, delay=60, log=log)     
    Outfile = FileOut("FileOutSimSen2", './data/FileOutSensor2.xlsx', log=log)     
    self.add_component(AskSensor)
    self.add_component(Sensor)
    self.add_component(Outfile)
    self.add_coupling(AskSensor.o_out, Sensor.i_in)
    self.add_coupling(Sensor.o_out, Outfile.i_in)
    

if __name__ == "__main__":
  
  startdt=dt.datetime(2021,8,1,0,0,0)
  enddt=dt.datetime(2021,8,2,0,0,0)
  simseconds=(enddt-startdt).total_seconds()
  
  print('Carga BodySim')
  bodyfile = './body/Washington-1d-2008-09-12_compr.nc'
  #bodyfile= 'D:/Unidades compartidas/ia-ges-bloom-cm/IoT/Washington-1d-2008-09-12_compr.nc'
  vars=('WQ_O','WQ_N')
  simbody=SimBody2('SimWater',bodyfile,vars)
  
  print('Instancia Modelos')
  coupled = Test2("SimBodyRead", simbody, startdt, True)
  coord = Coordinator(coupled, flatten=True)
  coord.initialize()
  
  print('Simula')
  coord.simulate_time(simseconds)   #En segundos
  coord.exit()
  print('Fin')