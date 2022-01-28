from xdevs import get_logger,PHASE_ACTIVE
from xdevs.models import Atomic, Port
from xdevs.models import Coupled
from xdevs.sim import Coordinator
import logging
logger = get_logger(__name__, logging.INFO)

from dataclasses import dataclass, field
from enum import Enum
from typing import Any
import pandas as pd
import datetime as dt


class DataEventId(Enum):
  '''Allowed data events'''
  POS3D = "position"
  LATLON ="latlon"
  DEPTH="depth"
  TEMP = "temperature"
  SUN="sun"
  BLOOM="bloom"
  POSBLOOM = "position&bloom"
  DEFAULT="default"

@dataclass
class Event:
  '''A message to model network message'''
  id: str
  source: str
  timestamp: dt.datetime = field(default_factory=dt.datetime.now)
  payload: dict = field(default_factory=dict)


class FileIn(Atomic):
  '''A model to load datetime-values messages from datafile'''
  def __init__(self, name, datafile, start, dataid=DataEventId.DEFAULT, log=False):       
    super().__init__(name)
    self.datafile=datafile
    self.dataid=dataid
    self.start=start
    self.log=log
    self.o_out = Port(Event, "o_out")
    self.add_out_port(self.o_out)
    
  def initialize(self):
    # Let's read a value from excel
    if self.datafile[-1]=='x':
      self.mydata=pd.read_excel(self.datafile)  #Sensor data loading
    if self.datafile[-1]=='v':
        self.mydata=pd.read_csv(self.datafile)  #Sensor data loading
    self.ind=self.mydata[self.mydata.DateTime == self.start].index.values
    #¡Se debe mejorar. No está protegido, debe existir TM para la fecha start!
    self.columns=self.mydata.columns
    self.hold_in(PHASE_ACTIVE, 0)
    
  def exit(self):
    pass
		
  def deltint(self):
    #Calcula delta tiempo hasta siguiente Telemetría
    Actual=self.mydata.iloc[self.ind].DateTime.values
    Futura=self.mydata.iloc[self.ind+1].DateTime.values
    delta=Futura-Actual
    seconds=int(delta)/1e9 #ns->s
    self.hold_in(PHASE_ACTIVE, seconds) 
  
  def deltext(self, e: Any):
    pass 

  def lambdaf(self):
    row=self.mydata.iloc[self.ind]   #Telemetría
    self.ind=self.ind+1              #Actualizo indice a siguiente
    datetime=row.DateTime.values     #Timestamp
    fila=row.iloc[0,:].values     
    #values=row.iloc[0,1:].values    #Payload
    payload={}
    if self.columns.size==2:
      payload={self.columns[1]: fila[1] }
    elif self.columns.size==3:
      payload={self.columns[1]: fila[1],self.columns[2]: fila[2] }
    elif self.columns.size==4:
      payload={self.columns[1]: fila[1],self.columns[2]: fila[2],self.columns[3]: fila[3] }
    else:  #Para más columnas no desgloso
      payload={self.columns[1]: fila[0,1:]}
    #msg=Event(id= self.dataid,source= self.datafile,timestamp=datetime,payload=values[:])
    msg=Event(id= self.dataid.value,source= self.datafile,timestamp=datetime,payload=payload)
    self.o_out.add(msg)
    if self.log==True: 
      #logger.info("FileIn: %s DateTime: %s Payload: %s" , self.name, datetime[0], values)
      logger.info("FileIn: %s DateTime: %s Payload: %s" , self.name, datetime[0], payload)
      #logger.info("FileIn: %s DateTime: %s" , self.name, datetime)
      #logger.info(msg)


class FileOut(Atomic):
  '''A model to store datatime-value-PosX-PosY-PosZ messages on datafile if save=True'''
  def __init__(self, name, datafile=[],save=True,log=False):       
    super().__init__(name)
    self.save=save
    self.log=log
    self.datafile=datafile
    self.i_in = Port(Event, "i_in")
    self.add_in_port(self.i_in)
    
  def initialize(self):
    if self.save==True:           
      self.data =pd.DataFrame(columns=["Id","Source","DateTime","PayLoad"])     
    self.passivate()
  
  def exit(self):
    if self.save==True:
      if self.datafile[-1]=='x':
        self.data.to_excel(self.datafile)
      if self.datafile[-1]=='v':
        self.data.to_csv(self.datafile)
      
  def deltint(self):
    pass
   
  def deltext(self, e: Any):
    msg = self.i_in.get()
    if self.save==True:
      items=msg.payload.items()
      columns=["Id","Source","DateTime","PayLoad"]
      content=[msg.id,msg.source,msg.timestamp[0],msg.payload]
      for it in items:
        columns.append(it[0])
        content.append(it[1])
      newdata =pd.DataFrame(content,columns)
      self.data=self.data.append(newdata.T,ignore_index=True)
    
    if self.log==True: 
        logger.info("FileOut: %s DateTime: %s PayLoad: %s" , self.name, msg.timestamp[0], msg.payload)
	
    self.continuef(e)
  
  def lambdaf(self):
    pass


class FussionPosBloom(Atomic):
  '''A model of edge data fussion'''
   # Este se encarga de fusionar datos de posición y de Detector de Bloom
  def __init__(self, name, log=False):        #Period 1h
    super().__init__(name)
    self.i_Pos = Port(Event, "i_Pos")
    self.add_in_port(self.i_Pos)
    self.i_Blo = Port(Event, "i_Blo")
    self.add_in_port(self.i_Blo)
    self.o_out = Port(Event, "o_out")
    self.add_out_port(self.o_out)
    
    self.log=log
    self.msg1 = None
    self.msg2 = None
    self.msg = None

  def initialize(self):
    self.passivate()
    
  def exit(self):
    pass
		
  def deltint(self):
    self.passivate()

  def deltext(self, e: Any):
    in1 = self.i_Pos.get()
    in2 = self.i_Blo.get()
    if (in1!=None):self.msg1=in1
    if (in2!=None):self.msg2=in2
    #Espero a tener los tres datos
    if (self.msg1!=None) & (self.msg2!=None):
      #Ejemplo de mezcla de mensajes, uno los PayLoads
      newpayload={**self.msg1.payload,**self.msg2.payload}   
      self.msg=Event(id= DataEventId.POSBLOOM.value,source= self.name,timestamp=self.msg1.timestamp,payload=newpayload)
      self.in1=None
      self.in2=None
      self.hold_in(PHASE_ACTIVE,0)
 	
  def lambdaf(self):
      self.o_out.add(self.msg)
      if self.log==True: 
        logger.info("Fussin: %s Time: %s PAyLoad: %s" , self.name, self.msg.DateTime, self.msg.payload)



class Test1(Coupled):
  '''Un ejemplo acoplado que conecta ficheros de entrada y salida'''

  def __init__(self, name, start, log=False):
    super().__init__(name)
    fileT1 = FileIn("FilTem1", './data/SensorTemperatura1.xlsx',start=start, dataid=DataEventId.TEMP, log=log)     
    fileS1 = FileIn("FilSol1", './data/SensorSol1.xlsx', start=start, dataid=DataEventId.SUN,  log=log)     
    fileP1 = FileIn("FilPos1", './data/PosBarco2d1m.xlsx', start=start, dataid=DataEventId.POS3D, log=log)     
    fileOT1 = FileOut("FilOut1", './data/FileOutT1.xlsx', log=log)     
    fileOS1 = FileOut("FilOut2", './data/FileOutS1.xlsx', log=log)
    fileOP1 = FileOut("FilOut2", './data/FileOutP1.xlsx', log=log)     
    self.add_component(fileT1)
    self.add_component(fileS1)
    self.add_component(fileP1)
    self.add_component(fileOT1)
    self.add_component(fileOS1)
    self.add_component(fileOP1)
    self.add_coupling(fileT1.o_out, fileOT1.i_in)
    self.add_coupling(fileS1.o_out, fileOS1.i_in)
    self.add_coupling(fileP1.o_out, fileOP1.i_in)



class Test2(Coupled):
  '''Un ejemplo acoplado que conecta ficheros y hace fusión de datos en Edge'''
  def __init__(self, name, start, log=False):
    super().__init__(name)
    filePi = FileIn("ShipPos", './data/LatLon2d.xlsx', start=start, dataid=DataEventId.POS3D, log=log)     
    fileBi = FileIn("DetBlo", './data/DetBloom2d.xlsx',start=start, dataid=DataEventId.BLOOM, log=log)     
    EdgFus= FussionPosBloom("EdgeFussion") #Fusiona Posición del barco con medida de Sensor de Bloom
    filePB = FileOut("filePB", './data/FileOutPOSBLOOM.xlsx', log=log)     
    self.add_component(filePi)   
    self.add_component(fileBi)
    self.add_component(EdgFus)
    self.add_component(filePB)
    self.add_coupling(filePi.o_out, EdgFus.i_Pos)
    self.add_coupling(fileBi.o_out, EdgFus.i_Blo)
    self.add_coupling(EdgFus.o_out, filePB.i_in)



if __name__ == "__main__":
  #startdt=dt.datetime(2021,8,1,0,0,0)
  #enddt=dt.datetime(2021,8,10,23,0,0)
  startdt=dt.datetime(2021,8,1,0,0,0)
  enddt=dt.datetime(2021,8,2,0,0,0)
  #enddt=dt.datetime(2021,8,3,0,0,0)
 
  #coupled = Test1("ExampleTest1ByPass", start=startdt, log=True)
  coupled = Test2("ExampleBloomDetection", start=startdt, log=True)
  coord = Coordinator(coupled, flatten=True)
  print('Ini Simulación')
  coord.initialize()
  simseconds=(enddt-startdt).total_seconds()
  coord.simulate_time(simseconds)   #En segundos
  coord.exit()
  print('Fin Simulación')
