from xdevs import PHASE_ACTIVE
from typing import Any
from xdevs.models import Atomic, Port
from data import Message
from extra.view import ScopeView


class Scope(Atomic):
  '''A model of a simple scope that plots the evolution in time of a quantity'''

  def __init__(self, name, scopeView: ScopeView):
    super().__init__(name)
    self.i_in = Port(Message, "i_in")
    self.add_in_port(self.i_in)
    self.clock = 0
    self.scopeView = scopeView

  def initialize(self):
    self.passivate()

  def exit(self):
    self.scopeView.show()

  def deltint(self):
    self.passivate()

  def deltext(self, e: Any):
    self.continuef(e)
    self.clock += e
    msg = self.i_in.get()
    self.scopeView.add(self.clock, msg.value)

  def lambdaf(self):
    pass