from xdevs import get_logger
from xdevs.models import Atomic, Port
from xdevs.models import Coupled
from xdevs.sim import Coordinator
import logging
logger = get_logger(__name__, logging.INFO)

from typing import Any
import datetime as dt
from file import FileIn,FileOut
from body import SimBody

PHASE_ON = "on"           #Taking a measurement
PHASE_OFF = "off"         #Wating a resquet

from site import addsitedir   #Para poder realizar pruebas en el directorio.
addsitedir("C:/Users/segu2/OneDrive - Universidad Complutense de Madrid (UCM)/devs-bloom") 

from util.event import Event,DataEventId


class SimSensor(Atomic):
  '''Simulated Sensor using a simulated Body in NetHFC4 format'''
  def __init__(self, name,simbody,delay=0,log=False):       
    super().__init__(name)
    self.log=log
    self.i_in = Port(Event, "i_int")    #Event commads to read  sensors
    self.add_in_port(self.i_in)
    self.o_out = Port(Event, "o_out")   #Event includes the measurements
    self.add_out_port(self.o_out)
    #Simulated Body in NetHFC4 format
    self.simbody=simbody
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
    self.hold_in(PHASE_ON, self.delay)  #1 minute to read the signals
    #Conseguir (t,lat,lon,depth)
    #Lectura desde el fichero de los datos
    #columns=["Id","Source","DateTime","PayLoad"]
    #content=[msg.id,msg.source,msg.timestamp,msg.payload]
    msg = self.i_in.get()

    #myt=50  #Indice del tiempo de prueba    
    #ACOPLO CON NUESTRO TIEMPO DE SIMULACIÓN
    simtime=msg.timestamp-dt.datetime(2021,8,1,0,0,0)
    fdays=simtime.seconds/(24.0*60.0*60.0)
    times=self.simbody.vars['time']
    times0=times-times[0]
    ind=0                     #Indice de tiempo
    while times0[ind]<fdays: #Busco el siguiente tiempo
      ind=ind+1
    myt=ind

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
  '''Un ejemplo acoplado que pide datos a SensorSim'''

  def __init__(self, name, simbody, start, log=False):
    super().__init__(name)
    AskSensor = FileIn("AskMeasurement", './data/LatLonDep.xlsx',start=start, dataid=DataEventId.NITROGEN, log=log)
    #AskSensor = FileIn("AskO&N", './data/LatLonDepWQ_O.xlsx',start=start, dataid=DataEventId.OXIGEN, log=log)   
    Sensor = SimSensor("SimulatedSensor", simbody, delay=60, log=log)     
    Outfile = FileOut("FileOutSimSen", './data/FileOutSensor.xlsx', log=log)     
    self.add_component(AskSensor)
    self.add_component(Sensor)
    self.add_component(Outfile)
    self.add_coupling(AskSensor.o_out, Sensor.i_in)
    self.add_coupling(Sensor.o_out, Outfile.i_in)
    

if __name__ == "__main__":
  
  startdt=dt.datetime(2021,8,1,0,0,0)
  enddt=dt.datetime(2021,8,2,0,0,0)
  simseconds=(enddt-startdt).total_seconds()
  
  print('Cargando BodySim')
  bodyfile = './data/Washington-1d-2008-09-12_compr.nc'
  vars=('WQ_O','WQ_N')
  simbody=SimBody('SimWater',bodyfile,vars)
  
  print('Instanciano Modelos')
  coupled = Test1("SimBodyRead", simbody, startdt, True)
  coord = Coordinator(coupled, flatten=True)
  coord.initialize()
  
  print('Simulando')
  coord.simulate_time(simseconds)   #En segundos
  coord.exit()
  print('Fin')