from datetime import datetime, timedelta
from xdevs.models import Atomic, Port
from util.event import EnergyEventId, DataEventId, Event

PHASE_ON = "on"
PHASE_OFF = "off"
PHASE_STARTING = "starting"
PHASE_STOPPING = "stopping"

class PoweredComponent(Atomic):
  '''A base class for components that consume energy'''

  def __init__(self, name: str, period:float=1, mA: float=10,
               start_time: datetime=datetime.now(), debug: bool=False):
    super().__init__(name)
    self.i_pwr = Port(Event, "i_pwr")
    self.o_pwr = Port(Event, "o_pwr")
    self.i_data = Port(Event, "i_data")
    self.o_data = Port(Event, "o_data")
    self.add_in_port(self.i_pwr)
    self.add_out_port(self.o_pwr)
    self.add_in_port(self.i_data)
    self.add_out_port(self.o_data)
    self.period = period
    self.clock = start_time
    self.start_time = start_time
    self.debug = debug
    self.mA = mA
    self.mAh = mA*self.period/3600

  def initialize(self) -> None:
    self.passivate(PHASE_OFF)

  def exit(self) -> None:
    pass
		
  def deltint(self) -> None:
    self.clock += timedelta(seconds=self.sigma)
    self.hold_in(PHASE_ON, self.period)

  def deltext(self, e: float) -> None:
    self.continuef(e)
    self.clock += timedelta(seconds=e)
    if self.i_pwr:
      msg = self.i_pwr.get()
      if msg.id == EnergyEventId.POWER_ON:
        print(f'POWER ON: {self.name}')
        self.hold_in(PHASE_ON, self.period)
      elif msg.id == EnergyEventId.POWER_OFF:
        print(f'POWER OFF: {self.name}')
        self.passivate(PHASE_OFF)
	
  def lambdaf(self) -> None:
    energy = Event(
      id=EnergyEventId.POWER_DEMAND,
      source=self.name,
      timestamp=self.clock,
      payload={ 'mAh': [self.mAh] }
    )
    self.o_pwr.add(energy)


class PowerControlUnit(Atomic):
  '''A model of a basic energy supply module'''

  def __init__(self, name: str, mAh: float=10000, period: float=30):
    super().__init__(name)
    self.mAh_left = mAh
    self.i_pwr = Port(Event, "i_pwr")
    self.o_pwr = Port(Event, "o_pwr")
    self.i_data = Port(Event, "i_data")
    self.o_data = Port(Event, "o_data")
    self.add_in_port(self.i_pwr)
    self.add_out_port(self.o_pwr)
    self.add_in_port(self.i_data)
    self.add_out_port(self.o_data)
    self.period = period
    self.clock = datetime.now()

  def initialize(self) -> None:
    self.hold_in(PHASE_STARTING, 0)

  def exit(self) -> None:
    pass
		
  def deltint(self) -> None:
    self.clock += timedelta(seconds=self.sigma)
    if self.phase == PHASE_STOPPING:
      self.passivate(PHASE_OFF)
    elif self.phase in [PHASE_STARTING, PHASE_ON]:
      self.hold_in(PHASE_ON, self.period)

  def deltext(self, e: float) -> None:
    self.continuef(e)
    self.clock += timedelta(seconds=e)
    msg = self.i_pwr.get()
    if self.phase == PHASE_ON:
      if msg.id == EnergyEventId.POWER_DEMAND:
        if self.mAh_left <= msg.payload['mAh'][0]:
          self.mAh_left = 0
          self.activate(PHASE_STOPPING)
          return
        self.mAh_left -= msg.payload['mAh'][0]

  def lambdaf(self) -> None:
    if self.phase == PHASE_STARTING:
      self.o_pwr.add(Event(
        id=EnergyEventId.POWER_ON,
        source=self.name,
        timestamp=self.clock,
      ))
      print(f'POWER ON: {self.name}')
    elif self.phase == PHASE_ON:
      self.o_data.add(Event(
        id=DataEventId.MEASUREMENT,
        source=self.name,
        timestamp=self.clock,
        payload={ 'mAh': [self.mAh_left] }
      ))
    elif self.phase == PHASE_STOPPING:
      print(f'POWER OFF: {self.name}')
      self.o_pwr.add(Event(
        id=EnergyEventId.POWER_OFF,
        source=self.name,
        timestamp=self.clock,
    ))
