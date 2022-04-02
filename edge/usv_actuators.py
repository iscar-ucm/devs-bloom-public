import datetime as dt
import math
import numpy as np
from scipy.integrate import solve_ivp
from xdevs.models import Atomic, Port
from util.event import EnergyEventId, DataEventId, Event

PHASE_ON = "on"
PHASE_OFF = "off"
PHASE_TRANSMIT = "transmit"
PHASE_UPDATE = "update"

class ContinuousModel(Atomic):

  def __init__(self, name: str, period: float=1,
                initial: np.array=None) -> None:
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
    self.x = np.array((0, 0, 0)) if initial is None else initial
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
        source=self.name,
        timestamp=self.clock,
        payload={ 'mAh': [self.mA*2*self.u[0]*self.period/3600] }
      )
      measurement = Event(
        id=DataEventId.MEASUREMENT,
        source=self.name,
        timestamp=self.clock,
        payload={ 'position': self.x }
      )
      self.o_pwr.add(energy)
      self.o_data.add(measurement)
