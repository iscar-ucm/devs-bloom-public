from datetime import timedelta
from xdevs.models import Port
from edge.usv import PoweredComponent
from util.event import EnergyEventId, Event

PHASE_ON = "on"
PHASE_OFF = "off"
PHASE_TRANSMIT = "transmit"

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
    self.clock += timedelta(seconds=self.sigma)
    if len(self.input_buffer) > 0:
      self.hold_in(PHASE_TRANSMIT, self.transmit_delay_ms/1000)
    else:
      self.passivate(PHASE_ON)

  def deltext(self, e: float) -> None:
    super().deltext(e)
    if self.i_data:
      for msg in self.i_data.values:
        if not msg.target == self.name: continue
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
    if self.phase == PHASE_TRANSMIT and self.input_buffer:
      msg = self.input_buffer.pop(0)
      if self.debug:
        print(f'USV sends: {self.clock} -> {msg.source} - {msg.payload}')
      self.o_tx.add(msg)
      self.o_pwr.add(Event(
        id=EnergyEventId.POWER_DEMAND,
        source=self.name,
        timestamp=self.clock,
        payload={ 'mAh': [self.mAh] }
      ))

