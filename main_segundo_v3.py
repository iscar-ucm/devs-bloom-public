"""Módulo creado por Segundo para realizar pruebas."""


# Simulación de un Sensor Simulado que toma los datos de BodySim
from xdevs.sim import Coordinator
from xdevs.models import Coupled
import datetime as dt

from edge.file import FileInVar,FileOut
from edge.body import SimBody3
from edge.sensor import SimSensor3


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
  

if __name__ == "__main__":
  
  #Simulación de Test3 para mostrar funcionamiento de SimSensor3 y Simbody3 
  startdt=dt.datetime(2008,9,12,0,29,0)
  enddt=dt.datetime(2008,9,13,0,29,0)
  simseconds=(enddt-startdt).total_seconds()

  print('Carga BodySim')
  bodyfile = './body/Washington-1d-2008-09-12_compr.nc'
  vars=('WQ_O','WQ_N','WQ_ALG')
  simbody=SimBody3('SimWater',bodyfile,vars)
  
  print('Instancia Modelos')
  coupled = Test3("SimBodyRead", simbody, startdt, log=True)
  coord = Coordinator(coupled, flatten=True)
  coord.initialize()
  
  print('Simulando')
  coord.simulate_time(simseconds)   #En segundos
  coord.exit()
  print('Fin')
