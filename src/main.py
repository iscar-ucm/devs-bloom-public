from xdevs.models import Coupled
from xdevs.sim import Coordinator
from sensors import SensorExample
from view import Scope
from extra.view import ScopeView


class CoupledExample(Coupled):
  '''A simple coupled model that connect a Sensor with a Scope'''

  def __init__(self, name, period, scopeView):
    super().__init__(name)

    if period <= 0:
      raise ValueError("period has to be greater than 0")

    sensor = SensorExample("Sensor", 0, period)
    scope = Scope("Scope", scopeView)
    self.add_component(sensor)
    self.add_component(scope)
    self.add_coupling(sensor.o_out, scope.i_in)


if __name__ == "__main__":
  ScopeView.setFileOutput('output.html')
  coupled = CoupledExample("Example", 1, ScopeView())
  coord = Coordinator(coupled, flatten=True)
  coord.initialize()
  coord.simulate(100)
  coord.exit()