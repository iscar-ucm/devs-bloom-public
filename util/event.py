import datetime as dt
from dataclasses import dataclass, field
from enum import Enum

@dataclass
class Event:
  '''A message to model events'''
  id: str
  source: str
  target: str = field(default=None)
  timestamp: dt.datetime = field(default_factory=dt.datetime.now)
  payload: dict = field(default_factory=dict)


class DataEventId(Enum):
  '''Allowed data events'''
  SIMSEN="SimSensor"
  POS3D = "position"
  LATLON = "latlon"
  DEPTH = "depth"
  TEMP = "temperature"
  SUN = "sun"
  BLOOM = "bloom"
  POSBLOOM = "position&bloom"
  DEFAULT = "default"
  MEASUREMENT = "measurement"
  COMMAND = "command"


class EnergyEventId(Enum):
  '''Allowed energy events'''
  POWER_ON = "power_on"
  POWER_OFF = "power_off"
  POWER_DEMAND = "power_demand"

class SensorEventId(Enum):
  '''Allowed Sensor events acording to BodySim'''
  OXIGEN="WQ_O"
  NITROGEN="WQ_N"

@dataclass
class SensorInfo:
  '''Info of sesors signals'''
  id: str           #SensorEventId
  description: str  #Sensor description
  max: float        #Max value 
  min: float        #Min value
  precision: float  #Precission
  noisebias: float  #Bias of Error
  noisesigma: float #Sigma of Error noise

