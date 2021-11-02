from typing import Any
from xdevs import PHASE_ACTIVE
from xdevs.models import Atomic, Port
import random as rnd
from data import Message

class SensorExample(Atomic):
  '''A model of a basic sensor that yields a random measurement with a fixed time basis'''

  def __init__(self, name, start=0, period=1):
    super().__init__(name)
    self.o_out = Port(Message, "o_out")
    self.add_out_port(self.o_out)
    self.start = start
    self.period = period

  def initialize(self):
    self.hold_in(PHASE_ACTIVE, self.start)

  def exit(self):
    pass
		
  def deltint(self):
    self.hold_in(PHASE_ACTIVE, self.period)

  def deltext(self, e: Any):
    pass
	
  def lambdaf(self):
    # Let's send a random number, that's all:
    value = Message(rnd.random())
    self.o_out.add(value)