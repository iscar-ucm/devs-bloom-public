import datetime as dt
from dataclasses import dataclass, field
from enum import Enum

@dataclass
class Event:
  '''A message to model events'''
  id: str
  source: str
  timestamp: dt.datetime = field(default_factory=dt.datetime.now)
  payload: dict = field(default_factory=dict)


class DataEventId(Enum):
  '''Allowed data events'''
  OXIGEN="WQ_O"
  NITROGEN="WQ_N"
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
