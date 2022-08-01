# from asyncio.windows_events import NULL
from cmath import inf
from contextlib import nullcontext
from xdevs import get_logger
from xdevs.models import Atomic, Port
from xdevs.models import Coupled
from xdevs.sim import Coordinator
import logging
logger = get_logger(__name__, logging.INFO)

from typing import Any
import datetime as dt
from dataclasses import dataclass

@dataclass 
class SensorInfo:
  '''Info of sesors signals'''
  #def __init__(self, id:str,description:str,delay:float,max:float,min:float,precision:float,noisebias:float,noisesigma:float):       
  id: str           #SensorEventId
  description: str  #Sensor description
  delay:  float     #Sensor latency
  max: float        #Max value 
  min: float        #Min value
  precision: float  #Precission
  noisebias: float  #Bias of Error
  noisesigma: float #Sigma of Error noise
  #pass


#from site import addsitedir
#addsitedir('C:/Users/segu2/OneDrive - Universidad Complutense de Madrid (UCM)/devs-bloom-1')

from edge.file import FileIn,FileOut,FileInVar
from edge.body import SimBody3,SimBody4
from util.event import Event,SensorEventId


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
    AskSensor = FileIn("Ask_O", './data/LatLonDep.xlsx',start=start, dataid=SensorEventId.OXIGEN, log=log)   
    Sensor = SimSensor("SimulatedSensor", simbody, delay=60, log=log)     
    Outfile = FileOut("FileOutSimSen", './data/FileOutSensor.xlsx', log=log)     
    self.add_component(AskSensor)
    self.add_component(Sensor)
    self.add_component(Outfile)
    self.add_coupling(AskSensor.o_out, Sensor.i_in)
    self.add_coupling(Sensor.o_out, Outfile.i_in)


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
    AskSensor = FileIn("Ask_O", './data/LatLonDep.xlsx',start=start, dataid=SensorEventId.OXIGEN, log=log)   
    Sensor = SimSensor2("SimulatedSensor2", simbody, start=start, delay=60, log=log)     
    Outfile = FileOut("FileOutSimSen2", './data/FileOutSensor2.xlsx', log=log)     
    self.add_component(AskSensor)
    self.add_component(Sensor)
    self.add_component(Outfile)
    self.add_coupling(AskSensor.o_out, Sensor.i_in)
    self.add_coupling(Sensor.o_out, Outfile.i_in)


class SimSensor3(Atomic):
  '''Simulated Sensor using a simulated Body3 in NetHFC4 format using sigma and time 
  TBD: Initialitation of SensorInfo'''
  PHASE_OFF = "off"         #Standby, wating for a resquet
  PHASE_INIT = "init"       #Send SensorInfo
  PHASE_ON = "on"           #Initialited, wating for a resquet
  PHASE_WORK = "work"       #Taking a measurement
  PHASE_DONE = "done"       #Send Measurement

  def __init__(self,name,simbody,sensorinfo,log=False):       
    super().__init__(name)
    self.log=log
    self.i_in = Port(Event, "i_int")    #Event to aks the mesaurements  
    self.add_in_port(self.i_in)         
    self.o_out = Port(Event, "o_out")   #Event includes the measurements
    self.add_out_port(self.o_out)
    self.simbody=simbody                #Simulated Body in NetHFC4 format
    self.sensorinfo=sensorinfo          #The measurement takes delay seconds. 
   
  def initialize(self):
    # Wait for a resquet
    self.msgout = None
    self.passivate(self.PHASE_OFF)         #SENSOR OFF
    
  def exit(self):
    self.passivate(self.PHASE_OFF)         #SENSOR OFF
    pass
		
  def deltint(self):
    if self.phase==self.PHASE_INIT:
      self.hold_in(self.PHASE_WORK,self.sensorinfo.delay)
    elif self.phase==self.PHASE_WORK:
      myt=self.msgin.timestamp                   
      mylat=self.msgin.payload['Lat']
      mylon=self.msgin.payload['Lon']
      mydepth=self.msgin.payload['Depth']
      self.myvar=self.msgin.payload['Sensor']
      value,t,i,j,l=self.simbody.readvar(self.myvar,myt,mylat,mylon,mydepth)
      self.datetime=self.msgin.timestamp+dt.timedelta(seconds=self.sensorinfo.delay)
      data = {'Time':myt,'Lat':mylat,'Lon':mylon,'Depth':mydepth, self.myvar: value, 'Bt':t,'Bi':i,'Bj':j,'Bl':l}
      self.msgout=Event(id=self.msgin.id,source=self.name,timestamp=self.datetime,payload=data) 
      self.hold_in(self.PHASE_DONE,0)
    elif self.phase==self.PHASE_DONE:
      self.passivate(self.PHASE_ON)
    
  def deltext(self, e: Any):
    if self.phase==self.PHASE_OFF:
      self.msgin = self.i_in.get()
      self.msgout=Event(id=self.msgin.id,source=self.name,timestamp=self.msgin.timestamp,payload=vars(self.sensorinfo)) 
      self.hold_in(self.PHASE_INIT,0)
    elif self.phase==self.PHASE_ON:
      self.msgin = self.i_in.get()
      self.hold_in(self.PHASE_WORK,self.sensorinfo.delay)
       
  def lambdaf(self):
    if self.phase==self.PHASE_INIT:
      # TODO: (JOSELE) Comento esto porque si se envían dos mensajes distintos por el mismo puerto, tenemos un problema estructural.
      # El FOG no distingue entre mensajes. Lo mejor sería tener un puerto específico destinado a enviar este mensaje.
      # self.o_out.add(self.msgout)
      if self.log==True:  logger.info(self.msgout)
    if self.phase==self.PHASE_DONE:
      self.o_out.add(self.msgout)
      if self.log==True:  logger.info(self.msgout)


class Test3(Coupled):
  '''Ejemplo para utiliza SimBody3 y SimSensor3:
    *Petición de TMs de O2, N2 y ALG generadas desde ficheros
    *SimSensor3 se inicializa y manda su configuración
    *SimSensor3 lee las TMs desde un SimBody3
    *Se guardan TMs con t,lat,lon,depth y valor de la señal
  '''
  def __init__(self, name, simbody, start, log=False):
    super().__init__(name)
    Nseninf=SensorInfo(id=SensorEventId.NITROGEN,description="Sonda de Nitrogeno",delay=0.1, max= 0.5, min=0,precision=0.01,noisebias=0.001,noisesigma=0.001)
    Oseninf=SensorInfo(id=SensorEventId.OXIGEN,description="Sonda de Oxigeno",delay=0.2, max= 10.0, min=0,precision=0.1,noisebias=0.01,noisesigma=0.01)
    Aseninf=SensorInfo(id=SensorEventId.ALGA,description="Detector de Algas",delay=.6, max= 0.01, min=0,precision=0.001,noisebias=0.001,noisesigma=0.001)
    AskSensorN = FileInVar("Ask_N", './dataedge/Sweep2008_WQ_N.xlsx', start, dataid=SensorEventId.NITROGEN,  log=log)   
    AskSensorO = FileInVar("Ask_O", './dataedge/Sweep2008_WQ_O.xlsx', start, dataid=SensorEventId.OXIGEN, log=log) 
    AskSensorA = FileInVar("Ask_A", './dataedge/Sweep2008_WQ_ALG.xlsx', start, dataid=SensorEventId.ALGA, log=log) 
    SensorN = SimSensor3("SimSenN", simbody , Nseninf, log=log)       
    SensorO = SimSensor3("SimSenO", simbody , Oseninf, log=log) 
    SensorA = SimSensor3("SimSenA", simbody , Aseninf, log=log)     
    Outfile = FileOut("Sensors2008Out", './dataedge/Sensors2008out2.xlsx', log=log)     
    self.add_component(AskSensorN)
    self.add_component(AskSensorO)
    self.add_component(AskSensorA)
    self.add_component(SensorN)
    self.add_component(SensorO)
    self.add_component(SensorA)
    self.add_component(Outfile)
    self.add_coupling(AskSensorN.o_out, SensorN.i_in)
    self.add_coupling(AskSensorO.o_out, SensorO.i_in)
    self.add_coupling(AskSensorA.o_out, SensorA.i_in)
    self.add_coupling(SensorN.o_out, Outfile.i_in)
    self.add_coupling(SensorO.o_out, Outfile.i_in)
    self.add_coupling(SensorA.o_out, Outfile.i_in)
        
if __name__ == "__main__":
  
  #Simulación Test3, para mostrar funcionamiento de SimSensor3 y Simbody3 
  #startdt=dt.datetime(2008,9,12,0,29,0)
  #enddt=dt.datetime(2008,9,13,0,29,0)
  
  #Simulación Test4, to sweep la zona (Ojo, es larga)
  startdt = dt.datetime(2008,9,12,4,0,0)
  enddt   = dt.datetime(2008,9,12,4,59,59)
  simseconds=(enddt-startdt).total_seconds()
  print(dt.datetime.now())
  print('Sim IniDate:',startdt)
  print('Sim EndDate:',enddt)
  print('BodySim loading...')
  bodyfile = './body/Washington-1d-2008-09-12_compr.nc'
  myvars=('WQ_O','WQ_N','WQ_ALG')
  simbody=SimBody4('SimWater',bodyfile,myvars)
  print(dt.datetime.now())
  print('Models Init...')
  coupled = Test3("SimBodyRead", simbody, startdt, log=False)
  coord = Coordinator(coupled, flatten=True)
  coord.initialize()
  print(dt.datetime.now())
  print('Simulating...')
  coord.simulate_time(simseconds)   #En segundos
  coord.exit()
  print('End')
  print(dt.datetime.now())





'''
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
'''
