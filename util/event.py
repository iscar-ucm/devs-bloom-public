import datetime as dt
from dataclasses import dataclass, field
from enum import Enum

@dataclass
class Event:
  '''A message to model events'''
  id: str
  source: str
  target: str = field(default=None)
  timestamp: dt.datetime = field(default_factory=dt.datetime.now)
  payload: dict = field(default_factory=dict)


class DataEventId(Enum):
  '''Allowed data events'''
  SIMSEN="SimSensor"
  POS3D = "position"
  LATLON = "latlon"
  DEPTH = "depth"
  TEMP = "temperature"
  SUN = "sun"
  BLOOM = "bloom"
  POSBLOOM = "position&bloom"
  DEFAULT = "default"
  MEASUREMENT = "measurement"
  COMMAND = "command"

# TODO: Para las columnas de cada evento:
# Usar un diccionario donde la clave sea el DtaEventId y el valor sea la lista de campos
# Encapsularlo en una clase
# La descripción de los sensores (límites) estarán en SensorInfo
# class DataEventColumns:
#    diccionario
#    get_columns(DataEventId)
#    SensorInfo get_sensor_by_column(column)

class EnergyEventId(Enum):
  '''Allowed energy events'''
  POWER_ON = "power_on"
  POWER_OFF = "power_off"
  POWER_DEMAND = "power_demand"

class SensorEventId(Enum):
  '''Allowed Sensor events acording to BodySim'''
  OXIGEN="WQ_O"
  NITROGEN="WQ_N"
  ALGA="WQ_ALG"


class CommandEventId(Enum):
    """Allowed commands."""

    CMD_START_SIM = "START_SIM"
    CMD_STOP_SIM = "STOP_SIM"
    CMD_FIX_OUTLIERS = "FIX_OUTLIERS"


class CommandEvent:
    """Clase para enviar mensajes del Commander al entorno de simulación."""

    def __init__(self, date: dt.datetime = None, cmd: CommandEventId = None,
                 args: str = ''):
        """Función de instanciación."""
        self.date: dt.datetime = date
        self.cmd: CommandEventId = cmd
        self.args: str = args

    def parse(self, cmdline):
        """Función que transforma una cadena de texto en CommandEvent."""
        parts: list = cmdline.split(';')
        self.date = dt.datetime.strptime(parts[0], '%Y-%m-%d %H:%M:%S')
        self.cmd = CommandEventId[parts[1]]
        if(len(parts) > 2):
            self.args = parts[2]
