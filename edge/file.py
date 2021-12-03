from xdevs import get_logger,PHASE_ACTIVE
from typing import Any
from xdevs.models import Atomic, Port
from xdevs.models import Coupled
from xdevs.sim import Coordinator

from dataclasses import dataclass
import pandas as pd
import datetime as dt
import logging
logger = get_logger(__name__, logging.INFO)

@dataclass
class DTVMessage:
  '''A simple message to transport DataTim+Values'''
  DateTime:  dt.datetime    #FechaHora como formato de tiempo 
  Value:     float          #Valor del sensor


@dataclass
class DTPMessage:
  '''A simple message to transport DataTime+Positions'''
  DateTime:  dt.datetime    #FechaHora como formato de tiempo 
  PosX:      float
  PosY:      float
  PosZ:      float


@dataclass
class DTVPMessage:
  '''A simple message to transport DataTime+Value+Positions'''
  DateTime:  dt.datetime    #FechaHora como formato de tiempo 
  Value:     float          #Valor del sensor
  PosX:      float
  PosY:      float
  PosZ:      float



class FileInPos(Atomic):
  '''A model to load datetime-PosX-PosY-PosZ values from datafile'''

  def __init__(self, name, datafile=[], period=1,  log=False):       
    super().__init__(name)
    self.datafile=datafile
    self.period=period
    self.log=log
    self.o_out = Port(DTPMessage, "o_out")
    self.add_out_port(self.o_out)

  def initialize(self):
    # Let's read a value from excel
    # Se podría comprobar el tipo de fichero y utilizar su cargador
    if self.datafile[-1]=='x':
      self.mydata=pd.read_excel(self.datafile)  #Sensor data loading
    if self.datafile[-1]=='v':
        self.mydata=pd.read_csv(self.datafile)  #Sensor data loading
    self.indice=0                                        #Initial Inicio primer elemento del fichero
    self.hold_in(PHASE_ACTIVE, 0)
    #self.passivate()
    
  def exit(self):
    pass
		
  def deltint(self):
    self.hold_in(PHASE_ACTIVE, self.period)  
    self.indice=self.indice+self.period
    pass
  
  def deltext(self, e: Any):
    pass 

  def lambdaf(self):
    datetime=self.mydata.DateTime[self.indice]      #Timestamp
    PosX=self.mydata.PosX[self.indice]             
    PosY=self.mydata.PosY[self.indice]  
    PosZ=self.mydata.PosZ[self.indice]  
    mes = DTPMessage(datetime,PosX,PosY,PosZ)
    self.o_out.add(mes)
    #self.indice=self.indice+1                         #actualizo indice
    if self.log==True: 
      logger.info("FileIn: %s DateTime: %s PosXYZ: %f %f %f" , self.name, datetime, PosX,PosY,PosZ)


class FileInSen(Atomic):
  '''A model to load datetime-value messages from datafile'''

  def __init__(self, name, datafile=[], period=1, log=False):       
    super().__init__(name)
    self.datafile=datafile
    self.period=period
    self.log=log
    self.o_out = Port(DTVMessage, "o_out")
    self.add_out_port(self.o_out)

  def initialize(self):
    # Let's read a value from excel
    # Se podría comprobar el tipo de fichero y utilizar su cargador
    if self.datafile[-1]=='x':
      self.mydata=pd.read_excel(self.datafile)  #Sensor data loading
    if self.datafile[-1]=='v':
        self.mydata=pd.read_csv(self.datafile)  #Sensor data loading
    self.indice=0                                        #Initial Inicio primer elemento del fichero
    self.hold_in(PHASE_ACTIVE, 0)
    #self.passivate()
    
  def exit(self):
    pass
		
  def deltint(self):
    self.hold_in(PHASE_ACTIVE, self.period)  
    self.indice=self.indice+self.period                      #Pido lectura de dato y actualizo indice o tiempo
  
  def deltext(self, e: Any):
    pass 

  def lambdaf(self):
    datetime=self.mydata.DateTime[self.indice]      #Timestamp
    value=self.mydata.Value[self.indice]              #Valor del Sensor
    mes = DTVMessage(datetime,value)
    self.o_out.add(mes)
    #self.indice=self.indice+1   
    #self.indice=self.indice+1                         #actualizo indice
    if self.log==True: 
      logger.info("FileIn: %s DateTime: %s Value: %f" , self.name, datetime, value)
	

class FileOutDTVP(Atomic):
  '''A model to store datatime-value-PosX-PosY-PosZ messages on datafile if save=True'''

  def __init__(self, name, datafile=[],  save=True, log=False):
    super().__init__(name)
    self.save=save
    self.log=log
    self.datafile=datafile
    self.i_in = Port(DTVPMessage, "i_in")
    self.add_in_port(self.i_in)
    
  def initialize(self):
    if self.save==True:          #Si 
      self.data =pd.DataFrame(columns=["DateTime","Value","PosX","PosY","PosZ"])     
    #self.passivate()

  def exit(self):
    if self.save==True:
      if self.datafile[-1]=='x':
        self.data.to_excel(self.datafile)

      if self.datafile[-1]=='v':
        self.data.to_csv(self.datafile)

      
  def deltint(self):
    pass
    #self.passivate()

  def deltext(self, e: Any):
    msg = self.i_in.get()
    if self.save==True:
      newdata =pd.DataFrame([[msg.DateTime,msg.Value,msg.PosX,msg.PosY,msg.PosZ]],columns=["DateTime","Value","PosX","PosY","PosZ"])
      self.data=self.data.append(newdata,ignore_index=True)
      if self.log==True: 
        logger.info("FileOut: %s DateTime: %s Value: %f %f %f %f" , self.name, msg.DateTime, msg.Value,msg.PosX,msg.PosY,msg.PosZ)
	
    self.continuef(e)
  
  def lambdaf(self):
    pass


class EdgeComp(Atomic):
  '''A model of edge computation'''
   # Habrá que definir estados, de momentos es una máquina combinacional.

  def __init__(self, name, start=0, log=False):        #Period 1h
    super().__init__(name)
    self.i_in1 = Port(DTVMessage, "i_in1")
    self.add_in_port(self.i_in1)
    self.i_in2 = Port(DTVMessage, "i_in2")
    self.add_in_port(self.i_in2)
    self.i_in3 = Port(DTPMessage, "i_in3")
    self.add_in_port(self.i_in3)
    self.o_out = Port(DTVPMessage, "o_out")
    self.add_out_port(self.o_out)
    
    self.start = start
    self.log=log
    self.in1 = None
    self.in2 = None
    self.in3 = None
    self.out = None
    self.msg = None
    self.message=None 

  def initialize(self):
    #self.hold_in(PHASE_ACTIVE, self.start)     
    self.passivate()
    
  def exit(self):
    pass
		
  def deltint(self):
    #self.hold_in(PHASE_ACTIVE, self.period)
    #self.time=self.time+self.period 
      self.passivate()

  def deltext(self, e: Any):
    in1 = self.i_in1.get()
    in2 = self.i_in2.get()
    in3 = self.i_in3.get()
    if (in1!=None):self.in1=in1
    if (in2!=None):self.in2=in2
    if (in3!=None):self.in3=in3
    if (self.in1!=None) & (self.in2!=None) &(self.in3!=None):
      #Ejemplo de Calculo en Edge
      value=self.in1.Value*self.in2.Value       
      #Ejemplo de mezcla de ficheros
      self.message = DTVPMessage(self.in1.DateTime,value,self.in3.PosX,self.in3.PosY,self.in3.PosZ)
      #Espero a tener los tres datos
      self.in1=None
      self.in2=None
      self.in3=None
      self.hold_in(PHASE_ACTIVE,0)
  
	
  def lambdaf(self):
      self.o_out.add(self.message)
      if self.log==True: 
        logger.info("EdgeComp: %s Time: %s Valor: %f Pos: %f %f %f" , self.name, self.message.DateTime, self.message.Value,self.message.PosX,self.message.PosY,self.message.PosZ )


class CoupledEdgeComp(Coupled):
  '''Un ejemplo acoplado que conecta ficheros y hace cálculo en Edge'''
  
  def __init__(self, name, period=1, log=False):
    super().__init__(name)
    if period <= 0: raise ValueError("period has to be greater than 0")
    
    fileT1 = FileInSen("FilTem1",'./data/SensorTemperatura1.xlsx',period, log)
    fileS1 = FileInSen("FilSun1", './data/SensorSol1.xlsx',period,log)
    fileP1 = FileInPos("FilPos1", './data/Posicion1.xlsx',period,log)
    edgecomp = EdgeComp("EdgeComputation", 0, log)
    file3 = FileOutDTVP("FilSal3",'./data/Salida3.xlsx',True,log)
    
    self.add_component(fileT1)
    self.add_component(fileS1)
    self.add_component(fileP1)
    self.add_component(edgecomp)
    self.add_component(file3) 
    self.add_coupling(fileT1.o_out, edgecomp.i_in1)
    self.add_coupling(fileS1.o_out, edgecomp.i_in2)
    self.add_coupling(fileP1.o_out, edgecomp.i_in3)
    
    self.add_coupling(edgecomp.o_out, file3.i_in)

if __name__ == "__main__":
  
  #coupled = CoupledExample("ExampleSensorFichero", period=1, log=True)
  #coupled = CoupledSenFogFil("ExampleSensorFogFichero", period=1, log=True)
  coupled = CoupledEdgeComp("ExampleFicheroASVFichero", period=1, log=True)
  coord = Coordinator(coupled, flatten=True)
  print('Ini Simulación')
  coord.initialize()
  coord.simulate_time(10*24)   #De momento en Horas
  coord.exit()
  print('Fin Simulación')
