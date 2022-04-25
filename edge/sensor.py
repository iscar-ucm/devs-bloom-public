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

from edge.file import FileIn,FileOut,FileInVar
from edge.body import SimBody,SimBody2,SimBody3
from util.event import Event,DataEventId,SensorEventId


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


class SimSensor3(Atomic):
  '''Simulated Sensor using a simulated Body3 in NetHFC4 format using sigma and time '''
  def __init__(self,name,simbody,start,delay=0,log=False):       
    super().__init__(name)
    self.log=log
    self.i_in = Port(Event, "i_int")    #Event to aks the mesaurements  
    self.add_in_port(self.i_in)         
    self.o_out = Port(Event, "o_out")   #Event includes the measurements
    self.add_out_port(self.o_out)
    self.simbody=simbody                #Simulated Body in NetHFC4 format
    self.start=start                    #Start DateTime of Simulation
    self.delay=delay                    #The measurement takes delay seconds. 
    self.datetime=start                 
  
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
    #msg = self.i_in.get()
    for bmsg in self.i_in._bag:
      msg=bmsg.get()
      #ACOPLE DE TIEMPOS DE SIMULACIÓN y SIMBODY
      #simtime=msg.timestamp-self.start    #dt.datetime(2021,8,1,0,0,0)
      bodytime=msg.timestamp-self.simbody.vars['dtini']
      myt=bodytime.seconds                 #Seconds of SimBody.   
      mylat=msg.payload['Lat']
      mylon=msg.payload['Lon']
      mydepth=msg.payload['Depth']
      self.myvar=msg.payload['Sensor']
      values=self.simbody.readvar(self.myvar,myt,mylat,mylon,mydepth)
      self.datetime=msg.timestamp+dt.timedelta(seconds=self.delay)
      self.data = {'Time':myt,'Lat':mylat,'Lon':mylon,'Depth':mydepth, self.myvar: values}
    
  def lambdaf(self):
    msg=Event(id=self.myvar,source=self.name,timestamp=self.datetime,payload=self.data)
    self.o_out.add(msg)
    if self.log==True: 
      logger.info("Sensor: %s DateTime: %s Payload: %s" , self.name,self.datetime,self.data)
      #logger.info(msg)




class Test3(Coupled):
  '''Ejemplo para utiliza SimBody3 y SimSensor3:
    *Petición de TMs de O2, N2 y ALG generadas desde ficheros
    *SimSensor3 lee las TMs desde un SimBody3
    *Se guardan TMs con t,lat,lon,depth y valor de la señal
  '''
  def __init__(self, name, simbody, start, log=False):
    super().__init__(name)
    #AskSensor = FileIn("AskMeasurement", './data/LatLonDep.xlsx',start=start, dataid=DataEventId.NITROGEN, log=log)
    AskSensorN = FileInVar("Ask_N", './dataedge/Sensor2008_WQ_N.xlsx',start, log=log)   
    AskSensorO = FileInVar("Ask_O", './dataedge/Sensor2008_WQ_O.xlsx',start, log=log) 
    AskSensorA = FileInVar("Ask_O", './dataedge/Sensor2008_WQ_ALG.xlsx',start, log=log) 
    SensorN = SimSensor3("SimSenN", simbody , start, delay=30, log=log)       
    SensorO = SimSensor3("SimSenO", simbody , start, delay=40, log=log) 
    SensorA = SimSensor3("SimSenA", simbody , start, delay=50, log=log)     
    Outfile = FileOut("Sensors2008Out", './dataedge/Sensors2008out1.xlsx', log=log)     
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
        
class Test4(Coupled):
  '''Barrido durante 5 horas del BodySim a diferentes profundidades, 
    *Petición de TMs de O2, N2 y ALG generadas desde ficheros
    *SimSensor3 lee las TMs desde un SimBody3
    *Se guardan TMs con t,lat,lon,depth y valor de la señal
  '''
  def __init__(self, name, simbody, start, log=False):
    super().__init__(name)
    #AskSensor = FileIn("AskMeasurement", './data/LatLonDep.xlsx',start=start, dataid=DataEventId.NITROGEN, log=log)
    AskSensorN = FileInVar("Ask_N", './dataedge/Sweep2008_WQ_N.xlsx',start, log=log)   
    AskSensorO = FileInVar("Ask_O", './dataedge/Sweep2008_WQ_O.xlsx',start, log=log) 
    AskSensorA = FileInVar("Ask_A", './dataedge/Sweep2008_WQ_ALG.xlsx',start, log=log) 
    SensorN = SimSensor3("SimSenN", simbody , start, delay=0, log=log)       
    SensorO = SimSensor3("SimSenO", simbody , start, delay=0, log=log) 
    SensorA = SimSensor3("SimSenA", simbody , start, delay=0, log=log)     
    Outfile = FileOut("Sweep2008Out", './dataedge/Sweep2008out.xlsx', log=log)     
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
  startdt = dt.datetime(2008,9,12,1,0,0)
  enddt   = dt.datetime(2008,9,12,6,59,59)
  simseconds=(enddt-startdt).total_seconds()
  
  print('Carga BodySim')
  bodyfile = './body/Washington-1d-2008-09-12_compr.nc'
  vars=('WQ_O','WQ_N','WQ_ALG')
  simbody=SimBody3('SimWater',bodyfile,vars)
  
  print('Instancia Modelos')
  #coupled = Test3("SimBodyRead", simbody, startdt, log=True)
  coupled = Test4("SimBodyRead", simbody, startdt, log=False)
  coord = Coordinator(coupled, flatten=True)
  coord.initialize()
  
  print('Simula')
  coord.simulate_time(simseconds)   #En segundos
  coord.exit()
  print('Fin')




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


'''if __name__ == "__main__":
  
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
  print('Fin')'''