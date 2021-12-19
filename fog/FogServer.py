from pandas.core.frame import DataFrame
from sklearn.neighbors import LocalOutlierFactor
from random import randint
from random import random
import pandas as pd
import numpy as np
import logging
from xdevs import PHASE_ACTIVE, PHASE_PASSIVE, get_logger
from xdevs.models import Atomic, Coupled, Port
from xdevs.sim import Coordinator
import datetime as dt
from dataclasses import dataclass, field

logger = get_logger(__name__, logging.DEBUG)

# TODO: Preguntar a Jesús cómo importar util.event
@dataclass
class Event:
  '''A message to model events'''
  id: str
  source: str
  timestamp: dt.datetime = field(default_factory=dt.datetime.now)
  payload: dict = field(default_factory=dict)

class TmpGenerator(Atomic):
    def __init__(self, name, num_events):
        super().__init__(name)
        self.o_out = Port(Event, "o_out")
        self.add_out_port(self.o_out)
        self.num_events = num_events

    def initialize(self):
        self.period = 1
        self.counter = 1
        self.hold_in(PHASE_ACTIVE, self.period)

    def deltext(self, e: float):
        pass

    def exit(self):
        pass

    def deltint(self):
        self.counter += 1
        if (self.counter<=self.num_events):
            self.hold_in(PHASE_ACTIVE, self.period)
        else:
            self.passivate()

    def lambdaf(self):
        value = randint(35,37)
        if (random()<0.01):
            value = -value # Outlier
        event = Event(id=str(self.counter), source="sensor_temp_01", timestamp=dt.datetime.now, payload={"temp": value})
        self.o_out.add(event)


class FogServer(Atomic):
    ''' A model for the fog server.'''

    def __init__(self, name, n_samples):
        super().__init__(name)
        self.n_samples = n_samples
        self.i_sensor_temp_01 = Port(Event, "i_sensor_temp_01")
        self.add_in_port(self.i_sensor_temp_01)
        self.o_sensor_temp_01_raw = Port(DataFrame, "o_sensor_temp_01_raw")
        self.add_out_port(self.o_sensor_temp_01_raw)
        self.o_sensor_temp_01_new = Port(DataFrame, "o_sensor_temp_01_new")
        self.add_out_port(self.o_sensor_temp_01_new)

    def initialize(self):
        self.sensor_temp_01_raw = pd.DataFrame(columns=["id","timestamp","value"])
        self.sensor_temp_01_new = pd.DataFrame(columns=["id","timestamp","value"])
        self.counter = 0
        self.passivate()

    def exit(self):
        pass

    def lambdaf(self):
        self.o_sensor_temp_01_raw.add(self.sensor_temp_01_raw)
        self.o_sensor_temp_01_new.add(self.sensor_temp_01_new)

    def deltext(self, e):
        self.continuef(e)
        if (self.i_sensor_temp_01.empty() == False):
            current_input = self.i_sensor_temp_01.get()
            id = current_input.id
            timestamp = current_input.timestamp
            value = current_input.payload["temp"]
            values = {"id": id, "timestamp": timestamp, "value": value}
            self.sensor_temp_01_raw = self.sensor_temp_01_raw.append(
                values, ignore_index=True)
            self.counter = self.counter + 1
            if (self.counter == self.n_samples):
                lof = LocalOutlierFactor()
                wrong_values = lof.fit_predict(self.sensor_temp_01_raw[["value"]])
                outlier_index = np.where(wrong_values == -1)
                self.sensor_temp_01_new = self.sensor_temp_01_raw
                self.sensor_temp_01_new.iloc[outlier_index, 2] = np.nan
                self.sensor_temp_01_new[["value"]] = self.sensor_temp_01_new[["value"]].astype(float)
                if(np.size(outlier_index)>0):
                    self.sensor_temp_01_new[["value"]] = self.sensor_temp_01_new[["value"]].interpolate()
                super().activate()

    def deltint(self):
        self.sensor_temp_01_raw = pd.DataFrame(columns=["id","timestamp","value"])
        self.sensor_temp_01_new = pd.DataFrame(columns=["id","timestamp","value"])
        self.counter = 0
        self.passivate()

class TestFogServer(Coupled):

	def __init__(self, name, num_events=1000, n_samples=100):
		super().__init__(name)

		gen = TmpGenerator("generator", num_events)
		fog = FogServer("fog", n_samples)

		self.add_component(gen)
		self.add_component(fog)

		self.add_coupling(gen.o_out, fog.i_sensor_temp_01)

if __name__ == '__main__':
    test_fog = TestFogServer("test_fog", 1000, 100)
    coord = Coordinator(test_fog)
    coord.initialize()
    coord.simulate()
    coord.exit()
