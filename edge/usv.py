import datetime as dt
import math
from random import random
import numpy as np
from scipy.integrate import solve_ivp

from edge.file import FileOut
from xdevs.models import Atomic, Port, Coupled
from xdevs.sim import Coordinator
from util.view import Scope, ScopeView
from util.event import EnergyEventId, DataEventId, Event


PHASE_ON = "on"
PHASE_OFF = "off"
PHASE_TRANSMIT = "transmit"
PHASE_STARTING = "starting"
PHASE_STOPPING = "stopping"


class Battery(Atomic):
  '''A model of a basic energy supply module'''

  def __init__(self, name, mAh=10000, period=30):
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
        source=f'{self.name}',
        timestamp=self.clock,
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
        timestamp=self.clock,
    ))


class PoweredSensor(Atomic):
  '''A model of a basic sensor that yields a measurement consuming some energy'''

  def __init__(self, name, period=10, current=2.0e-6):
    super().__init__(name)
    self.i_pwr = Port(Event, "i_pwr")
    self.o_pwr = Port(Event, "o_pwr")
    self.o_data = Port(Event, "o_data")
    self.add_in_port(self.i_pwr)
    self.add_out_port(self.o_pwr)
    self.add_out_port(self.o_data)
    self.period = period
    self.mAh = current*period/3600
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
      payload={ 'mAh': [self.mAh] }
    )
    measurement = Event(
      id=DataEventId.MEASUREMENT,
      source=f'{self.name}',
      timestamp=self.clock,
      payload={ 'temperature': [random()] }
    )
    # print(f'SENSOR: {self.clock}->{measurement}')
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
    self.i_rx = Port(Event, "i_rx")
    self.o_tx = Port(Event, "o_tx")
    self.add_in_port(self.i_pwr)
    self.add_out_port(self.o_pwr)
    self.add_in_port(self.i_data)
    self.add_out_port(self.o_data)
    self.add_in_port(self.i_rx)
    self.add_out_port(self.o_tx)
    self.input_buffer = []
    self.data_buffer = []
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
      for msg in self.i_data.values:
        self.input_buffer.append(msg)
      if self.phase != PHASE_OFF:
        self.hold_in(PHASE_TRANSMIT, self.transmit_delay_ms/1000)
    if self.i_rx:
      msg = self.i_rx.get()
      self.data_buffer.append(msg)
      print(f'USV receives: {self.clock} -> {msg.source} - {msg.payload}')


  def lambdaf(self):
    for m in self.data_buffer:
      self.o_data.add(m)
    self.data_buffer.clear()
    if self.phase == PHASE_TRANSMIT:
      msg = self.input_buffer.pop(0)
      if False:
        print(f'USV sends: {self.clock} -> {msg.source} - {msg.payload}')
      self.o_tx.add(msg)
      self.o_pwr.add(Event(
        id=EnergyEventId.POWER_DEMAND,
        source=f'{self.name}',
        timestamp=self.clock,
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
      source=f'{self.name}',
      timestamp=self.clock,
      payload={ 'mAh': [100] }
    )
    self.o_pwr.add(energy)
    for o in self.input_buffer:
      self.o_data.add(o)
    self.input_buffer.clear()


class ContinuousModel(Atomic):

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
    self.waypoint = [[0, 0], [0, 40]]
    self.x = np.array([4, 2, 0])
    self.target = np.array([4, 2])
    self.L = 3
    self.power = 10 # W
    self.mAh = 10

  def differential(t):
    def rates(t, x, u):
      return [
        -u[0]*math.sin(x[2]),
        u[0]*math.cos(x[2]),
        u[1],
      ]
    return rates

  def f(self, t, x):
    u = self.u(x)
    def rates(t, x):
      return [ # x: [x, y, phi, vx, vy, r]
        x[3],
        x[4],
        x[5],
        -u[0]*math.sin(x[2]),
        u[0]*math.cos(x[2]),
        u[1]
      ]
    return rates

  def u(self, x):
    e = self.target - x[0:2]
    e_x = np.dot(e, np.array([math.cos(x[2]), math.sin(x[2])]))
    v = 1
    w = - v*2*e_x / (self.L**2)
    return [v, w]

  def generate_trajectory(self):
    dr = np.array(self.waypoint[1]) - np.array(self.waypoint[0]) 
    v = dr / np.linalg.norm(dr)
    n = np.array([v[1], -v[0]])
    d = np.dot(self.waypoint[1], n) 
    r = np.array(self.x[0:2])
    target = r + (d-np.dot(r, n))*n + self.L*v
    distance = np.linalg.norm(np.array(self.waypoint[1]) - r)
    if distance < self.L and len(self.waypoint) > 2:
      self.waypoint.pop(0)
    return target

  def initialize(self):
    self.passivate(PHASE_OFF)

  def deltint(self):
    self.clock += dt.timedelta(seconds=self.sigma)
    if self.phase == PHASE_OFF:
      return
    
    self.target = self.generate_trajectory()
    self.x = self.nextstep()
    self.hold_in(PHASE_ON, self.period)

  def nextstep(self):
    '''Integrates the USV dynamics within one period'''
    t = self.clock.timestamp()
    sol = solve_ivp(self.differential(), [t, t+self.period], self.x, args=(self.u(self.x),))
    return sol.y[:,-1]

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

    if self.i_data:
      msg = self.i_data.get()
      if msg.id == DataEventId.COMMAND and 'waypoint' in msg.payload: 
        for w in msg.payload['waypoint']:
          self.waypoint.append(list(w))

  def exit(self):
    pass

  def lambdaf(self):
    energy = Event(
      id=EnergyEventId.POWER_DEMAND,
      source=f'{self.name}',
      timestamp=self.clock,
      payload={ 'mAh': [self.mAh*2*self.u(self.x)[0]] }
    )
    measurement = Event(
      id=DataEventId.MEASUREMENT,
      source=f'{self.name}',
      timestamp=self.clock,
      payload={ 'position': self.x }
    )
    self.o_pwr.add(energy)
    self.o_data.add(measurement)
  

class USV(Coupled):
  '''A coupled model of a USV'''

  def __init__(self, name, period):
    super().__init__(name)

    if period <= 0:
      raise ValueError("period has to be greater than 0")

    battery = Battery("main_power_supply", mAh=100000, period=10*period)
    sensor = PoweredSensor("temperature_sensor", period=300*period)
    processor = Processor("processor", period=10*period)
    comms = GenericCommunicationModule("generic_comms")
    model = ContinuousModel("IMU", period=1)
    out = FileOut("FileOut", './data/USVData.xlsx')
    # Components
    self.add_component(battery)
    self.add_component(comms)
    self.add_component(processor)
    self.add_component(sensor)
    self.add_component(model)
    self.add_component(out)
    # Wiring
    self.add_coupling(battery.o_pwr, sensor.i_pwr)
    self.add_coupling(sensor.o_pwr, battery.i_pwr)
    self.add_coupling(battery.o_pwr, comms.i_pwr)
    self.add_coupling(comms.o_pwr, battery.i_pwr)
    self.add_coupling(battery.o_pwr, processor.i_pwr)
    self.add_coupling(processor.o_pwr, battery.i_pwr)
    self.add_coupling(battery.o_pwr, model.i_pwr)
    self.add_coupling(model.o_pwr, battery.i_pwr)
    self.add_coupling(sensor.o_data, comms.i_data)
    self.add_coupling(battery.o_data, comms.i_data)
    self.add_coupling(model.o_data, comms.i_data)
    self.add_coupling(comms.o_data, model.i_data)
    # self.add_coupling(processor.o_data, comms.i_data)
    # self.add_coupling(comms.o_data, processor.i_data)
    self.add_coupling(comms.o_tx, out.i_in)
    self.add_in_port(Port(Event, 'i_data'))
    self.add_out_port(Port(Event, 'o_data'))
    # I/O
    self.add_coupling(self.get_in_port('i_data'), comms.i_rx)
    self.add_coupling(comms.o_tx, self.get_out_port('o_data'))


class TestInput(Atomic):
  '''A model of a simple scope that plots the evolution of a quantity'''

  def __init__(self, name, end_time):
    super().__init__(name)
    self.o_data = Port(Event, "o_data")
    self.add_out_port(self.o_data)
    self.clock = dt.datetime.now()
    self.end_time = end_time

  def initialize(self):
    self.hold_in("send_waypoint", 1)

  def exit(self):
    pass

  def deltint(self):
    self.clock += dt.timedelta(seconds=self.sigma)
    # if self.clock > self.end_time:
    #   self.passivate(PHASE_OFF)
    # self.hold_in(PHASE_ON, 1)
    self.passivate()

  def deltext(self, e: float):
    pass

  def lambdaf(self):
    if self.phase == "send_waypoint":
      trajectory = [
        [5, 40], [5, 0], [10, 0], [10, 40], [15, 40],
        [15, 0], [20, 0], [20, 40], [25, 40], [25, 0],
        [30, 0], [30, 40], [35, 40], [35, 0], [40, 0],
      ]
      self.o_data.add(Event(
        id=DataEventId.COMMAND,
        source=f'{self.name}',
        timestamp=self.clock,
        payload={ 'waypoint': trajectory }
      ))


class TestUSV(Coupled):
  '''A coupled model to test an USV coupled model'''

  def __init__(self, name: str, usv: USV):
    super().__init__(name)

    # scope_batt = Scope("Battery Scope", "mAh", ScopeView())
    # scope_sensor = Scope("Sensor Scope", "temperature", ScopeView())
    test_input = TestInput("GCS", end_time=100)
    scope_position = Scope("Sensor Scope", ScopeView(), "position")
    self.add_component(usv)
    self.add_component(test_input)
    self.add_component(scope_position)
    self.add_coupling(test_input.get_out_port('o_data'),
                      usv.get_in_port('i_data'))
    self.add_coupling(usv.get_out_port('o_data'),
                      scope_position.get_in_port('i_data'))


# Test
def test():
  day = "20210801"
  start_dt = dt.datetime(2021, 8, 1, 0, 0, 0)
  end_dt = dt.datetime(2021, 8, 1, 0, 10, 0)
  sim_seconds = (end_dt-start_dt).total_seconds()
  ScopeView.setFileOutput('output.html')
  usv = USV("Red Leader", period=1)
  coupled = TestUSV("Test USV", usv)
  coord = Coordinator(coupled, flatten=True)
  coord.initialize()
  coord.simulate_time(sim_seconds)
  coord.exit()