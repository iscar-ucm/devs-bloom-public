import datetime as dt
from enum import Enum
from dataclasses import dataclass, field
from random import random

from xdevs.models import Atomic, Port, Coupled
from xdevs.sim import Coordinator

PHASE_ON = "on"
PHASE_OFF = "off"
PHASE_TRANSMIT = "transmit"
PHASE_STARTING = "starting"
PHASE_STOPPING = "stopping"

class DataEventId(Enum):
  '''Allowed data events'''
  MEASUREMENT = "measurement"
  COMMAND = "command"

class EnergyEventId(Enum):
  '''Allowed energy events'''
  POWER_ON = "power_on"
  POWER_OFF = "power_off"
  POWER_DEMAND = "power_demand"

@dataclass
class Event:
  '''A message to model energy consumption events'''
  id: str
  source: str
  timestamp: dt.datetime = field(default_factory=dt.datetime.now)
  payload: dict = field(default_factory=dict)


class Battery(Atomic):
  '''A model of a basic energy supply module'''

  def __init__(self, name, mAh=1000, period=30):
    super().__init__(name)
    self.mAh_left = mAh
    self.i_pwr = Port(Event, "i_pwr")
    self.o_pwr = Port(Event, "o_pwr")
    self.o_data = Port(Event, "o_data")
    self.add_in_port(self.i_pwr)
    self.add_out_port(self.o_data)
    self.add_out_port(self.o_pwr)
    self.period = period
    self.clock = dt.datetime.now()

  def initialize(self):
    self.hold_in(PHASE_STARTING, 0)

  def exit(self):
    pass
		
  def deltint(self):
    self.clock += dt.timedelta(seconds=self.sigma)
    if self.phase == PHASE_STOPPING:
      self.passivate(PHASE_OFF)
    elif self.phase in [PHASE_STARTING, PHASE_ON]:
      self.hold_in(PHASE_ON, self.period)

  def deltext(self, e: float):
    self.continuef(e)
    self.clock += dt.timedelta(seconds=e)
    msg = self.i_pwr.get()
    if self.phase == PHASE_ON:
      if msg.id == EnergyEventId.POWER_DEMAND:
        if self.mAh_left <= msg.payload['mAh'][0]:
          self.mAh_left = 0
          self.activate(PHASE_STOPPING)
          return
        self.mAh_left -= msg.payload['mAh'][0]

  def lambdaf(self):
    if self.phase == PHASE_STARTING:
      self.o_pwr.add(Event(
        id=EnergyEventId.POWER_ON,
        source=f'{self.name}'
      ))
      print(f'POWER ON: {self.name}')
    elif self.phase == PHASE_ON:
      self.o_data.add(Event(
        id=DataEventId.MEASUREMENT,
        source=f'{self.name}',
        timestamp=self.clock,
        payload={ 'mAh': [self.mAh_left] }
      ))
    elif self.phase == PHASE_STOPPING:
      print(f'POWER OFF: {self.name}')
      self.o_pwr.add(Event(
        id=EnergyEventId.POWER_OFF,
        source=f'{self.name}',
      ))


class PoweredSensor(Atomic):
  '''A model of a basic sensor that yields a measurement consuming some energy'''

  def __init__(self, name, period=10):
    super().__init__(name)
    self.i_pwr = Port(Event, "i_pwr")
    self.o_pwr = Port(Event, "o_pwr")
    self.o_data = Port(Event, "o_data")
    self.add_in_port(self.i_pwr)
    self.add_out_port(self.o_pwr)
    self.add_out_port(self.o_data)
    self.period = period
    self.clock = dt.datetime.now()


  def initialize(self):
    self.passivate(PHASE_OFF)

  def exit(self):
    pass
		
  def deltint(self):
    self.clock += dt.timedelta(seconds=self.sigma)
    self.hold_in(PHASE_ON, self.period)

  def deltext(self, e: float):
    self.continuef(e)
    self.clock += dt.timedelta(seconds=e)
    if self.i_pwr:
      msg = self.i_pwr.get()
      if msg.id == EnergyEventId.POWER_ON:
        print(f'POWER ON: {self.name}')
        self.hold_in(PHASE_ON, self.period)
      elif msg.id == EnergyEventId.POWER_OFF:
        print(f'POWER OFF: {self.name}')
        self.passivate(PHASE_OFF)
	
  def lambdaf(self):
    energy = Event(
      id=EnergyEventId.POWER_DEMAND,
      source=f'{self.name}',
      timestamp=self.clock,
      payload={ 'mAh': [10] }
    )
    measurement = Event(
      id=DataEventId.MEASUREMENT,
      source=f'{self.name}',
      timestamp=self.clock,
      payload={ 'temperature': random() }
    )
    print(f'SENSOR: {self.clock}->{measurement}')
    self.o_pwr.add(energy)
    self.o_data.add(measurement)


class GenericCommunicationModule(Atomic):
  '''A model of a generic communication module that can transmit/receive data'''

  def __init__(self, name):
    super().__init__(name)
    self.i_pwr = Port(Event, "i_pwr")
    self.o_pwr = Port(Event, "o_pwr")
    self.i_data = Port(Event, "i_data")
    self.o_data = Port(Event, "o_data")
    self.add_in_port(self.i_pwr)
    self.add_out_port(self.o_pwr)
    self.add_in_port(self.i_data)
    self.add_out_port(self.o_data)
    self.input_buffer = []
    self.transmit_delay_ms = 10
    self.clock = dt.datetime.now()

  def initialize(self):
    self.passivate(PHASE_OFF)

  def exit(self):
    pass

  def deltint(self):
    self.clock += dt.timedelta(seconds=self.sigma)
    if len(self.input_buffer) > 0:
      self.hold_in(PHASE_TRANSMIT, self.transmit_delay_ms/1000)
    else:
      self.passivate(PHASE_ON)

  def deltext(self, e: float):
    self.continuef(e)
    self.clock += dt.timedelta(seconds=e)
    if self.i_pwr:
      msg = self.i_pwr.get()
      if msg.id == EnergyEventId.POWER_ON:
        print(f'POWER ON: {self.name}')
        self.activate(PHASE_ON)
      elif msg.id == EnergyEventId.POWER_OFF:
        print(f'POWER OFF: {self.name}')
        # self.passivate(PHASE_OFF)
    if self.i_data:
      msg = self.i_data.get()
      print(f'COMMS: {self.clock}->{msg}')
      self.input_buffer.append(msg)
      if self.phase != PHASE_OFF:
        self.hold_in(PHASE_TRANSMIT, self.transmit_delay_ms/1000)

  def lambdaf(self):
    if self.phase == PHASE_TRANSMIT:
      msg = self.input_buffer.pop(0)
      print(f'COMMS: {self.clock}->{msg}')
      self.o_data.add(msg)
      self.o_pwr.add(Event(
        id=EnergyEventId.POWER_DEMAND,
        source=f'{self.name}',
        payload={ 'mAh': [100] }
      ))


class Processor(Atomic):
  '''A model of a component that can process incoming data and generate clean/processed data'''

  def __init__(self, name, period=1):
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
    self.clock = dt.datetime.now()

    self.input_buffer = []

  def initialize(self):
    self.passivate(PHASE_OFF)

  def deltint(self):
    self.clock += dt.timedelta(seconds=self.sigma)

    if self.phase == PHASE_OFF:
      return
    self.hold_in(PHASE_ON, self.period)

  def deltext(self, e: float):
    self.continuef(e)
    self.clock += dt.timedelta(seconds=e)
    if not self.i_pwr.empty():
      msg = self.i_pwr.get()
      if msg.id == EnergyEventId.POWER_ON:
        print(f'POWER ON: {self.name}')
        self.hold_in(PHASE_ON, self.period)
      elif msg.id == EnergyEventId.POWER_OFF:
        print(f'POWER OFF: {self.name}')
        self.passivate(PHASE_OFF)

    if not self.i_data.empty():
      msg = self.i_data.get()
      if msg.id == DataEventId.MEASUREMENT:
        self.input_buffer.append(msg)

  def exit(self):
    pass

  def lambdaf(self):
    energy = Event(
      id=EnergyEventId.POWER_DEMAND,
      timestamp=self.clock,
      payload={ 'mAh': [100] }
    )
    self.o_pwr.add(energy)
    for o in self.input_buffer:
      self.o_data.add(o)
    self.input_buffer.clear()


class UAV(Coupled):
  '''A coupled model of a UAV'''

  def __init__(self, name, period):
    super().__init__(name)

    if period <= 0:
      raise ValueError("period has to be greater than 0")

    battery = Battery("main_power_supply", mAh=1000, period=period)
    sensor = PoweredSensor("temperature_sensor", period=period)
    # processor = Processor("processor", period=10)
    comms = GenericCommunicationModule("generic_comms")
    # TO DO: Move to TestUAV {
    # scope_batt = Scope("Battery Scope", "mAh", ScopeView())
    # scope_sensor = Scope("Sensor Scope", "temperature", ScopeView())
    # }
    self.add_component(battery)
    self.add_component(comms)
    # self.add_component(processor)
    self.add_component(sensor)
    # TO DO: Move to TestUAV {
    # self.add_component(scope_batt)
    # self.add_component(scope_sensor)
    # }
    # Power
    self.add_coupling(battery.o_pwr, sensor.i_pwr)
    self.add_coupling(battery.o_pwr, comms.i_pwr)
    # self.add_coupling(battery.o_pwr, processor.i_pwr)
    self.add_coupling(sensor.o_pwr, battery.i_pwr)
    self.add_coupling(comms.o_pwr, battery.i_pwr)
    # self.add_coupling(processor.o_pwr, battery.i_pwr)
    # Data
    self.add_coupling(sensor.o_data, comms.i_data)
    self.add_coupling(battery.o_data, comms.i_data)
    # self.add_coupling(processor.o_data, comms.i_data)
    # self.add_coupling(comms.o_data, processor.i_data)
    # TO DO: Move to TestUAV {
    # self.add_coupling(comms.o_data, scope_batt.i_in)
    # self.add_coupling(comms.o_data, scope_sensor.i_in)
    # }
    # Is this correct?
    # self.add_in_port(comms.i_data)
    # self.add_out_port(comms.o_data)



class TestInput(Atomic):
  '''A model of a simple scope that plots the evolution in time of a quantity'''

  def __init__(self, name, end_time):
    super().__init__(name)
    self.i_out = Port(Event, "i_out")
    self.add_out_port(self.i_in)
    self.clock = dt.datetime.now()
    self.end_time = end_time

  def initialize(self):
    self.hold_in("on", 1)

  def exit(self):
    self.scopeView.show()

  def deltint(self):
    self.clock += dt.timedelta(seconds=self.sigma)
    if self.clock > self.end_time:
      self.passivate(PHASE_OFF)
    self.hold_in(PHASE_ON, 1)

  def deltext(self, e: float):
    pass

  def lambdaf(self):
    self.add(Event(
      id=DataEventId.COMMAND,
      payload={ 'waypoint': { 'x': 10, 'y': 20 }}
    ))

class TestOutput(Atomic):
  '''A model of a simple scope that plots the evolution in time of a quantity'''

  def __init__(self, name, end_time):
    super().__init__(name)
    self.i_in = Port(Event, "i_in")
    self.add_in_port(self.i_in)
    self.clock = dt.datetime.now()
    self.end_time = self.clock + dt.timedelta(seconds=end_time)

  def initialize(self):
    self.hold_in("on", 1)

  def exit(self):
    pass

  def deltint(self):
    self.clock += dt.timedelta(seconds=self.sigma)
    if self.phase == PHASE_ON and self.clock > self.end_time:
      self.passivate(PHASE_OFF)
    elif self.phase == PHASE_OFF:
      self.hold_in(PHASE_ON, 1)

  def deltext(self, e: float):
    self.continuef(e)
    self.clock += dt.timedelta(seconds=e)
    print(self.i_in)

  def lambdaf(self):
    pass

class TestUAV(Coupled):
  '''A coupled model to test an UAV coupled model'''

  def __init__(self, name: str, uav: UAV):
    super().__init__(name)

    # scope_batt = Scope("Battery Scope", "mAh", ScopeView())
    # scope_sensor = Scope("Sensor Scope", "temperature", ScopeView())
    output = TestOutput("", end_time=100)
    self.add_component(uav)
    self.add_component(output)
    # self.add_coupling(uav.get_out_port('o_data'), output.i_in)


# Test
def test():
  # ScopeView.setFileOutput('output.html')
  uav = UAV("Red Leader", period=0.1)
  coupled = TestUAV("Test UAV", uav)
  coord = Coordinator(coupled, flatten=True)
  coord.initialize()
  coord.simulate(300)
  coord.exit()