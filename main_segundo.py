"""Módulo creado por Segundo para realizar pruebas."""


# Simulación de un Sensor Simulado que toma los datos de BodySim
from xdevs.sim import Coordinator
from xdevs.models import Coupled
import datetime as dt

from edge.file import FileIn,FileOut
from edge.body import SimBody2
from edge.sensor import SimSensor2
from util.event import DataEventId,SimSenId

class Test1(Coupled):
  '''Ejemplo acoplado que:
    *desde un fichero pide TM de O2 a SimSensor
    *SimSensor lee las TM de O2 desde un SimBody
    *SimSensor genera la TM deO2 60s más tarde
    *La TM de O2 se guardan en un fichero con t,lat,lon,dep
  '''

  def __init__(self, name, simbody, start, log=False):
    super().__init__(name)
    #AskSensor = FileIn("AskN", './data/LatLonDep.xlsx',start=start, dataid=SimSenId.NITROGEN, log=log)
    AskSensor = FileIn("AskO", './data/LatLonDep.xlsx',start=start, dataid=SimSenId.OXIGEN, log=log)   
    #Sensor = SimSensor("SimulatedSensor", simbody, delay=60, log=log)  
    Sensor = SimSensor2("SimulatedSensor", simbody, start=start, delay=60, log=log)     
    Outfile = FileOut("FileOutSimSen", './data/FileOutSensor.xlsx', log=log)     
    self.add_component(AskSensor)
    self.add_component(Sensor)
    self.add_component(Outfile)
    self.add_coupling(AskSensor.o_out, Sensor.i_in)
    self.add_coupling(Sensor.o_out, Outfile.i_in)
  

startdt = dt.datetime(2021, 8, 1, 0, 0, 0)
enddt = dt.datetime(2021, 8, 2, 0, 0, 0)
simseconds = (enddt-startdt).total_seconds()

print('Loading BodySim...')
bodyfile = './body/Washington-1d-2008-09-12_compr.nc'
#bodyfile= 'D:/Unidades compartidas/ia-ges-bloom-cm/IoT/Washington-1d-2008-09-12_compr.nc'
vars = ('WQ_O', 'WQ_N')
#simbody = SimBody('SimWater', bodyfile, vars)
simbody = SimBody2('SimWater', bodyfile, vars)

print('Loading Models...')
coupled = Test1("SimBodyRead", simbody, startdt, True)
coord = Coordinator(coupled, flatten=True)
coord.initialize()

print('Start Simulation.')
coord.simulate_time(simseconds)  # En segundos
coord.exit()
print('End Simulation.')
