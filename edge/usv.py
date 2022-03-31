import datetime as dt
import math
from random import random
import numpy as np
from scipy.integrate import solve_ivp
import requests

from edge.file import FileOut
from xdevs.models import Atomic, Port, Coupled
from xdevs.sim import Coordinator
from util.event import EnergyEventId, DataEventId, Event
from pyproj import Transformer, CRS
from edge.usv_controllers import USVController, USVPurePursuitController

PHASE_ON = "on"
PHASE_OFF = "off"
PHASE_TRANSMIT = "transmit"
PHASE_IDLE = "idle"
PHASE_MEASURING = "measure"
PHASE_STARTING = "starting"
PHASE_STOPPING = "stopping"
PHASE_UPDATE = "update"

class PoweredComponent(Atomic):
  '''A base class for components that consume energy'''

  def __init__(self, name: str, period:float=1, mA: float=10,
               start_time: dt.datetime=dt.datetime.now(), debug: bool=False):
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
    self.clock += dt.timedelta(seconds=self.sigma)
    self.hold_in(PHASE_ON, self.period)

  def deltext(self, e: float) -> None:
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
	
  def lambdaf(self) -> None:
    energy = Event(
      id=EnergyEventId.POWER_DEMAND,
      source=f'{self.name}',
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
    self.clock = dt.datetime.now()

  def initialize(self) -> None:
    self.hold_in(PHASE_STARTING, 0)

  def exit(self) -> None:
    pass
		
  def deltint(self) -> None:
    self.clock += dt.timedelta(seconds=self.sigma)
    if self.phase == PHASE_STOPPING:
      self.passivate(PHASE_OFF)
    elif self.phase in [PHASE_STARTING, PHASE_ON]:
      self.hold_in(PHASE_ON, self.period)

  def deltext(self, e: float) -> None:
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

  def lambdaf(self) -> None:
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


class PoweredSensor(PoweredComponent):
  '''A model of a basic sensor that yields a measurement consuming some energy'''

  def __init__(self, name, period=10, mA=2.0e-6, debug: bool=False):
    super().__init__(name, period=period, mA=mA, debug=debug)

  def lambdaf(self) -> None:
    measurement = Event(
      id=DataEventId.MEASUREMENT,
      source=f'{self.name}',
      timestamp=self.clock,
      payload={ 'temperature': [random()] }
    )
    self.o_data.add(measurement)
    if self.debug:
      print(f'SENSOR: {self.clock}->{measurement}')


class PoweredSimSensor(PoweredComponent):
  '''A simulated sensor that reads variables from a file with simulated data.'''

  def __init__(self, name: str, body, period: float=1, mA: float=10,
               start_time: dt.datetime=dt.datetime.now()):
    super().__init__(name, period=period, mA=mA, start_time=start_time)
    self.body = body
    self.buffer = []
    self.delay = 0

  def deltint(self) -> None:
    self.clock += dt.timedelta(seconds=self.sigma)
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
      source=f'{self.name}',
      timestamp=self.clock,
      payload={ 'mAh': [self.mAh] }
    )
    if len(self.buffer):
      info = self.buffer.pop(0)
      measurement = Event(
        id=DataEventId.MEASUREMENT,
        source=f'{self.name}',
        timestamp=self.clock,
        payload=self.body.readvar(*info),
      )
      self.o_pwr.add(energy)
      self.o_data.add(measurement)


class GenericCommunicationModule(PoweredComponent):
  '''A model of a generic communication module that can transmit/receive data'''

  def __init__(self, name, period: float=1, mA: float=100, debug: bool=False):
    super().__init__(name, period=period, mA=mA, debug=debug)
    self.i_rx = Port(Event, "i_rx")
    self.o_tx = Port(Event, "o_tx")
    self.add_in_port(self.i_rx)
    self.add_out_port(self.o_tx)
    self.input_buffer = []
    self.data_buffer = []
    self.transmit_mA = 100
    self.transmit_delay_ms = 10

  def deltint(self) -> None:
    self.clock += dt.timedelta(seconds=self.sigma)
    if len(self.input_buffer) > 0:
      self.hold_in(PHASE_TRANSMIT, self.transmit_delay_ms/1000)
    else:
      self.passivate(PHASE_ON)

  def deltext(self, e: float) -> None:
    super().deltext(e)
    if self.i_data:
      for msg in self.i_data.values:
        self.input_buffer.append(msg)
      if self.phase != PHASE_OFF:
        self.hold_in(PHASE_TRANSMIT, self.transmit_delay_ms/1000)
    if self.i_rx:
      msg = self.i_rx.get()
      self.data_buffer.append(msg)
      print(f'USV receives: {self.clock} -> {msg.source} - {msg.payload}')

  def lambdaf(self) -> None:
    for m in self.data_buffer:
      self.o_data.add(m)
    self.data_buffer.clear()
    if self.phase == PHASE_TRANSMIT:
      msg = self.input_buffer.pop(0)
      if self.debug:
        print(f'USV sends: {self.clock} -> {msg.source} - {msg.payload}')
      self.o_tx.add(msg)
      self.o_pwr.add(Event(
        id=EnergyEventId.POWER_DEMAND,
        source=f'{self.name}',
        timestamp=self.clock,
        payload={ 'mAh': [self.mAh] }
      ))


class Processor(PoweredComponent):
  '''A model of a component that can process incoming data and generate clean/processed data'''

  def __init__(self, name: str, period: float=1.0, debug: bool=False, 
      controller: USVController=USVPurePursuitController()) -> None:
    super().__init__(name, period=period, debug=debug)
    self.input_buffer = []
    self.output_buffer = []
    self.controller = controller
    self.P0_SANTILLANA = (40.706421, -3.87) # Embalse de Santillana
    self.P0_WASHINGTON = (47.58, -122.27) # Embalse de Washington
    crs = CRS.from_epsg(3857)
    self.toCrs = Transformer.from_crs(crs.geodetic_crs, crs)
    self.toGeodetic = Transformer.from_crs(crs, crs.geodetic_crs)
    self.origin = self.toCrs.transform(47.58, -122.27)
    self.u = np.array([0, 0])
    self.x = np.array([0, 0, 0])
    self.measurements = []
    self.energy = []
    self.iter = 0
    self.mA = 10

  def deltint(self) -> None:
    self.clock += dt.timedelta(seconds=self.sigma)
    if self.phase == PHASE_OFF:
      return

    elif self.phase == PHASE_ON:
      self.iter += 1
      if self.iter > 30:
        self.hold_in(PHASE_MEASURING, 0)
        self.iter = 0
      else:
        self.hold_in(PHASE_ON, self.period)

    elif self.phase == PHASE_MEASURING:
      self.hold_in(PHASE_ON, self.period)

    elif self.phase == PHASE_TRANSMIT:
      self.hold_in(PHASE_ON, self.period)
    
    elif self.phase == PHASE_UPDATE:
      self.tic()
      self.hold_in(PHASE_TRANSMIT, 0)

  def tic(self) -> None:
    '''Do the periodic computations'''
    self.u = self.controller.update_control()

  def deltext(self, e: float) -> None:
    super().deltext(e)

    for msg in self.i_data.values:
      if msg.id == DataEventId.MEASUREMENT:
        self.input_buffer.append(msg)
        if msg.source == 'IMU':
          self.x = msg.payload['position']
          self.controller.update_position(self.x)
          self.hold_in(PHASE_UPDATE, 0.0)
        if msg.source == 'sim_sensor':
          self.measurements.append(msg.payload)
        if msg.source == 'pcu':
          self.energy.append(msg)
      if msg.id == DataEventId.COMMAND and 'waypoint' in msg.payload:
        self.controller.add_waypoints(msg.payload['waypoint'])
        if 'set_origin' in msg.payload:
          self.origin = self.toCrs.transform(*(msg.payload['set_origin']))

  def lambdaf(self) -> None:
    energy = Event(
      id=EnergyEventId.POWER_DEMAND,
      source=f'{self.name}',
      timestamp=self.clock,
      payload={ 'mAh': [self.mA*self.period/3600] }
    )
    self.o_pwr.add(energy)
    if self.phase == PHASE_MEASURING:
      self.request_measurement('WQ_O')
    if self.phase == PHASE_TRANSMIT:
      self.send_control()
      self.send_position()
      self.send_measurements()
      self.send_energy()

  def request_measurement(self, var: str) -> None:
    '''Send a measurement command to the sensor'''
    (lat, lon) = self.toGeodetic.transform(*(self.origin + self.x[0:2]))
    time = int(self.clock.timestamp() - self.start_time.timestamp())
    self.o_data.add(Event(
      id=DataEventId.MEASUREMENT,
      source=f'{self.name}',
      timestamp=self.clock,
      target='sim_sensor',
      payload={
        'var': var,
        'time': time,
        'lat': lat,
        'lon': lon,
        'depth':  10
      }
    ))

  def send_control(self) -> None:
    command = Event(
      id=DataEventId.COMMAND,
      source=f'{self.name}',
      target='IMU',
      timestamp=self.clock,
      payload={ 'u': self.u }
    )
    self.o_data.add(command)

  def send_position(self) -> None:
    (lat, lon) = self.toGeodetic.transform(*(self.origin + self.x[0:2]))
    measurement = Event(
      id=DataEventId.MEASUREMENT,
      source=f'IMU',
      target='comms',
      timestamp=self.clock,
      payload={ 'position': self.x, 'lat': lat, 'lon': lon }
    )
    self.o_data.add(measurement)

  def send_measurements(self) -> None:
    for m in self.measurements:
      self.o_data.add(Event(
        id=DataEventId.MEASUREMENT,
        source='sim_sensor',
        target='comms',
        timestamp=self.clock,
        payload=m
      ))
    self.measurements.clear()

  def send_energy(self) -> None:
    for msg in self.energy:
      msg.target = 'comms'
      self.o_data.add(msg)
    self.energy.clear()


class ContinuousModel(Atomic):

  def __init__(self, name: str, period: float=1,
                initial: np.array=np.array((0, 0, 0))) -> None:
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
    self.x = initial
    self.power = 10 # W
    self.mA = 1000
    self.u = [0, 0]

  def differential(t) -> np.array:
    def rates(t, x, u):
      return [
        -u[0]*math.sin(x[2]),
        u[0]*math.cos(x[2]),
        u[1],
      ]
    return rates

  def f(self, t, x) -> np.array:
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

  def initialize(self) -> None:
    self.passivate(PHASE_OFF)

  def deltint(self) -> None:
    self.clock += dt.timedelta(seconds=self.sigma)
    if self.phase == PHASE_OFF:
      return
    elif self.phase == PHASE_UPDATE:
      self.x = self.nextstep()
      self.hold_in(PHASE_TRANSMIT, 0)
    elif self.phase == PHASE_TRANSMIT:
      self.hold_in(PHASE_ON, self.period)
    elif self.phase == PHASE_ON:
      self.hold_in(PHASE_UPDATE, 0)
      return

  def nextstep(self) -> None:
    '''Integrates the USV dynamics within one period'''
    t = self.clock.timestamp()
    sol = solve_ivp(self.differential(), [t, t+self.period], self.x, args=(self.u,))
    return sol.y[:,-1]

  def deltext(self, e: float) -> None:
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

    if self.i_data:
      for msg in self.i_data.values:
        if msg.id == DataEventId.COMMAND and 'u' in msg.payload:
          self.u = msg.payload['u']

  def exit(self) -> None:
    pass

  def lambdaf(self) -> None:
    if self.phase == PHASE_TRANSMIT:
      energy = Event(
        id=EnergyEventId.POWER_DEMAND,
        source=f'{self.name}',
        timestamp=self.clock,
        payload={ 'mAh': [self.mA*2*self.u[0]*self.period/3600] }
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

  def __init__(self, name: str, period: float=1, body=None, 
                initial: np.array=np.array((0, 0, 0))):
    super().__init__(name)

    if period <= 0:
      raise ValueError("period has to be greater than 0")

    self.pcu = PowerControlUnit("pcu", mAh=20000, period=10*period)
    sensor = PoweredSimSensor("sim_sensor", body, period=30*period)
    processor = Processor("processor", period=1*period)
    comms = GenericCommunicationModule("generic_comms")
    model = ContinuousModel("IMU", period=1, initial=initial)
    # Components
    self.add_component(self.pcu)
    self.add_powered_component(comms)
    self.add_powered_component(processor)
    self.add_powered_component(sensor)
    self.add_powered_component(model)
    # Wiring
    self.add_coupling(sensor.o_data, processor.i_data)
    self.add_coupling(self.pcu.o_data, processor.i_data)
    self.add_coupling(model.o_data, processor.i_data)
    self.add_coupling(processor.o_data, sensor.i_data)
    self.add_coupling(processor.o_data, model.i_data)
    # processor - comms
    self.add_coupling(comms.o_data, processor.i_data)
    self.add_coupling(processor.o_data, comms.i_data)
    # I/O
    self.add_in_port(Port(Event, 'i_rx'))
    self.add_out_port(Port(Event, 'o_tx'))
    self.add_coupling(self.get_in_port('i_rx'), comms.i_rx)
    self.add_coupling(comms.o_tx, self.get_out_port('o_tx'))


  def add_powered_component(self, component: PoweredComponent, connectTo: list=[]) -> None:
    super().add_component(component)
    self.add_coupling(self.pcu.o_pwr, component.i_pwr)
    self.add_coupling(component.o_pwr, self.pcu.i_pwr)
    for c in connectTo:
      self.add_coupling(component.i_data, c.o_data)
      self.add_coupling(component.o_data, c.i_data)


# class TestInput(Atomic):
#   '''A test input generator for a single USV'''

#   def __init__(self, name, end_time):
#     super().__init__(name)
#     self.o_data = Port(Event, "o_data")
#     self.add_out_port(self.o_data)
#     self.clock = dt.datetime.now()
#     self.end_time = end_time

#   def initialize(self) -> None:
#     self.hold_in("send_waypoint", 1)

#   def exit(self) -> None:
#     pass

#   def deltint(self) -> None:
#     self.clock += dt.timedelta(seconds=self.sigma)
#     # if self.clock > self.end_time:
#     #   self.passivate(PHASE_OFF)
#     # self.hold_in(PHASE_ON, 1)
#     self.passivate()

#   def deltext(self, e: float) -> None:
#     pass

#   def lambdaf(self) -> None:
#     if self.phase == "send_waypoint":
#       N = 21
#       width, height = 1000, 2000
#       trajectory = [[(width/(N-1))*int((i+1)/2), height*(int((i+2)/2)%2)] for i in range(N)]
#       self.o_data.add(Event(
#         id=DataEventId.COMMAND,
#         source=f'{self.name}',
#         timestamp=self.clock,
#         payload={
#           'waypoint': trajectory,
#           'set_origin': [47.58, -122.27]
#         }
#       ))


class TestInput(Atomic):
  '''A test input generator for two cooperative USV'''

  def __init__(self, name: str, end_time: dt.datetime, 
                offset: np.array=np.array((0, 0)), origin: list=(47.58, -122.27)):
    super().__init__(name)
    self.o_tx = Port(Event, "o_tx")
    self.add_out_port(self.o_tx)
    self.clock = dt.datetime.now()
    self.end_time = end_time
    self.origin = origin
    self.offset = offset

  def initialize(self) -> None:
    self.hold_in("send_waypoint", 1)

  def exit(self) -> None:
    pass

  def deltint(self) -> None:
    self.clock += dt.timedelta(seconds=self.sigma)
    self.passivate()

  def deltext(self, e: float) -> None:
    pass

  def lambdaf(self) -> None:
    if self.phase == "send_waypoint":
      N = 21
      width, height = 1000, 2000
      trajectory = [[(width/(N-1))*int((i)/2), height*(int((i+1)/2)%2)] for i in range(N)]
      self.o_tx.add(Event(
        id=DataEventId.COMMAND,
        source=f'{self.name}',
        timestamp=self.clock,
        payload={
          'waypoint': trajectory + self.offset,
          'set_origin': self.origin
        }
      ))


class TestUSV(Coupled):
  '''A coupled model to test an USV coupled model'''

  def __init__(self, name: str, usv: USV) -> None:
    super().__init__(name)
    test_input = TestInput("GCS", end_time=100)
    test_output = FileOut("FileOut", './data/USVData.xlsx')
    self.add_component(usv)
    self.add_component(test_input)
    self.add_component(test_output)
    self.add_coupling(test_input.get_out_port('o_tx'),
                      usv.get_in_port('i_rx'))
    self.add_coupling(usv.get_out_port('o_tx'),
                      test_output.get_in_port('i_in'))


class TestTwoUSV(Coupled):
  '''A coupled model to test an USV coupled model'''

  def __init__(self, name: str, usv: list[USV], offset: list) -> None:
    super().__init__(name)
    test_input1 = TestInput("GCS", end_time=100, offset=offset[0])
    test_input2 = TestInput("GCS", end_time=100, offset=offset[1])
    test_output = FileOut("FileOut", './data/USVData.xlsx')
    self.add_component(test_input1)
    self.add_component(test_input2)
    self.add_component(test_output)
    self.add_component(usv[0])
    self.add_component(usv[1])
    self.add_coupling(test_input1.get_out_port('o_tx'),
                      usv[0].get_in_port('i_rx'))
    self.add_coupling(test_input2.get_out_port('o_tx'),
                      usv[1].get_in_port('i_rx'))
    self.add_coupling(usv[0].get_out_port('o_tx'),
                      test_output.get_in_port('i_in'))
    self.add_coupling(usv[1].get_out_port('o_tx'),
                      test_output.get_in_port('i_in'))

class RestBody:

  def __init__(self, url):
    self.url = url

  def readvar(self, var: str, time: float, lat: float, lon: float, layer: int) -> dict:
    data = {
      'timestamp': time,
      'payload': {
        'var': var,
        'time': time,
        'lat': lat,
        'lon': lon,
        'depth': layer
      }
    }
    return requests.post(self.url, json=data).json()


def test() -> None:
  body = RestBody('http://127.0.0.1:5000')
  start_dt = dt.datetime(2021, 8, 1, 0, 0, 0)
  end_dt = dt.datetime(2021, 8, 1, 0, 30, 0)
  sim_seconds = (end_dt - start_dt).total_seconds()
  usv1 = USV("Red Leader",
    period=1,
    body=body,
    initial=np.array((-100, 0, 0))
  )
  coupled = TestUSV("Test USV", usv1)
  coord = Coordinator(coupled, flatten=True)
  coord.initialize()
  coord.simulate_time(sim_seconds)
  coord.exit()
  
  
def test_two_USV() -> None:
  body = RestBody('http://127.0.0.1:5000')
  start_dt = dt.datetime(2021, 8, 1, 0, 0, 0)
  end_dt = dt.datetime(2021, 8, 1, 4, 0, 0)
  sim_seconds = (end_dt - start_dt).total_seconds()
  usv1 = USV("Red Leader",
    period=1,
    body=body,
    initial=np.array((-100, 0, 0))
  )
  usv2 = USV("Red Two",
    period=1,
    body=body, 
    initial=np.array((900, 0, 0)),
  )
  coupled = TestTwoUSV("Test USV",
    usv=(usv1, usv2),
    offset=np.array(((0, 0), (1000, 0)))
  )
  coord = Coordinator(coupled, flatten=True)
  coord.initialize()
  coord.simulate_time(sim_seconds)
  coord.exit()