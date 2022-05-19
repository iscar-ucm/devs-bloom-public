from datetime import datetime, timedelta
from random import random
from edge.usv import PoweredComponent
from util.event import EnergyEventId, DataEventId, Event

PHASE_ON = "on"
PHASE_OFF = "off"
PHASE_TRANSMIT = "transmit"
PHASE_IDLE = "idle"
PHASE_MEASURING = "measure"
PHASE_STARTING = "starting"
PHASE_STOPPING = "stopping"
PHASE_UPDATE = "update"

class PoweredSensor(PoweredComponent):
  '''A model of a basic sensor that yields a measurement consuming some energy'''

  def __init__(self, name, period=10, mA=2.0e-6, debug: bool=False):
    super().__init__(name, period=period, mA=mA, debug=debug)

  def lambdaf(self) -> None:
    measurement = Event(
      id=DataEventId.MEASUREMENT,
      source=self.name,
      timestamp=self.clock,
      payload={ 'temperature': [random()] }
    )
    self.o_data.add(measurement)
    if self.debug:
      print(f'SENSOR: {self.clock}->{measurement}')


class PoweredSimSensor(PoweredComponent):
  '''A simulated sensor that reads variables from a file with simulated data.'''

  def __init__(self, name: str, body, period: float=1, mA: float=10,
               start_time: datetime=datetime.now()):
    super().__init__(name, period=period, mA=mA, start_time=start_time)
    self.body = body
    self.buffer = []
    self.delay = 0

  def deltint(self) -> None:
    self.clock += timedelta(seconds=self.sigma)
    if self.phase == PHASE_MEASURING:
      self.passivate(PHASE_ON)

  def deltext(self, e: float) -> None:
    super().deltext(e)
    if self.phase == PHASE_MEASURING or self.phase == PHASE_ON:
      for msg in self.i_data.values:
        if msg.target != self.name: continue
        self.buffer.append([
          msg.payload['var'],
          msg.payload['time'],
          msg.payload['lat'],
          msg.payload['lon'],
          msg.payload['depth'],
        ])
        self.hold_in(PHASE_MEASURING, self.delay)
 
  def lambdaf(self) -> None:
    energy = Event(
      id=EnergyEventId.POWER_DEMAND,
      source=self.name,
      timestamp=self.clock,
      payload={ 'mAh': [self.mAh] }
    )
    if len(self.buffer):
      info = self.buffer.pop(0)
      measurement = Event(
        id=DataEventId.MEASUREMENT,
        source=self.name,
        timestamp=self.clock,
        payload=self.body.readvar(*info),
      )
      print(measurement)
      self.o_pwr.add(energy)
      self.o_data.add(measurement)
