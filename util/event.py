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
  POS3D = "position"
  LATLON ="latlon"
  DEPTH="depth"
  TEMP = "temperature"
  SUN="sun"
  BLOOM="bloom"
  POSBLOOM = "position&bloom"
  DEFAULT="default"