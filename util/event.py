import datetime as dt
from dataclasses import dataclass, field

@dataclass
class Event:
  '''A message to model events'''
  id: str
  source: str
  timestamp: dt.datetime = field(default_factory=dt.datetime.now)
  payload: dict = field(default_factory=dict)
