"""Módulo creado por Segundo para realizar pruebas."""


# Simulación de un Sensor Simulado que toma los datos de BodySim
from xdevs.sim import Coordinator
from xdevs.models import Coupled
import datetime as dt

from edge.file import FileInVar,FileOut
from edge.body import SimBody3
from edge.sensor import SimSensor3,SensorEventId,SensorInfo


class Test3(Coupled):
  '''Ejemplo para utiliza SimBody3 y SimSensor3:
    *Petición de TMs de O2, N2 y ALG generadas desde ficheros
    *SimSensor3 se inicializa y manda su configuración
    *SimSensor3 lee las TMs desde un SimBody3
    *Se guardan TMs con t,lat,lon,depth y valor de la señal
  '''
  def __init__(self, name, simbody, start, log=False):
    super().__init__(name)
    Nseninf=SensorInfo(id=SensorEventId.NITROGEN,description="Sonda de Nitrogeno",delay=0.4, max= 0.5, min=0,precision=0.01,noisebias=0.001,noisesigma=0.001)
    Oseninf=SensorInfo(id=SensorEventId.OXIGEN,description="Sonda de Oxigeno",delay=0.6, max= 10.0, min=0,precision=0.1,noisebias=0.01,noisesigma=0.01)
    Aseninf=SensorInfo(id=SensorEventId.ALGA,description="Detector de Algas",delay=0.8, max= 0.01, min=0,precision=0.001,noisebias=0.001,noisesigma=0.001)
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
  
  #Simulación Test3, to sweep la zona (Ojo, es larga)
  startdt = dt.datetime(2008,9,12,4,0,0)
  enddt   = dt.datetime(2008,9,12,4,59,59)
  simseconds=(enddt-startdt).total_seconds()
  print('Sim IniDate:',startdt)
  print('Sim EndDate:',enddt)
  #print('BodySim loading...')
  bodyfile = './body/Washington-1d-2008-09-12_compr.nc'
  myvars=('WQ_O','WQ_N','WQ_ALG')
  simbody=SimBody3('SimWater',bodyfile,myvars)
  
  print('Models Initialitation...')
  coupled = Test3("SimBodyRead", simbody, startdt, log=False)
  coord = Coordinator(coupled, flatten=True)
  coord.initialize()
  
  print('Simulating...')
  coord.simulate_time(simseconds)   #En segundos
  coord.exit()
  print('End')