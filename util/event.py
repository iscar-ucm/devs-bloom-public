"""Fichero que implementa clases de utilidad relacinada con los eventos."""

import datetime as dt
from dataclasses import dataclass, field
from enum import Enum


@dataclass
class Event:
    """A message to model events."""

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


class DataEventColumns:
    """
    Clase dedicada a hacer explícitas las columnas relacionadas con los eventos.

    Tenemos por un lado las columnas que se consideran 'claves',
    como si de una base de datos se tratase.

    TODO: La descripción de los sensores (límites) estarán
    en SensorInfo.
    """

    key_columns = {}
    key_columns[DataEventId.POSBLOOM.value] = ["id", "source", "timestamp"]
    data_columns = {}
    data_columns[DataEventId.POSBLOOM.value] = ["Lat", "Lon", "Depth", "DetB", "DetBb"]

    @staticmethod
    def get_key_columns(data_event_id: str):
        """Devuelve las columnas clave del evento especificado."""
        return DataEventColumns.key_columns[data_event_id]

    @staticmethod
    def get_data_columns(self, data_event_id: str):
        """Devuelve las columnas de datos del evento especificado."""
        return DataEventColumns.data_columns[data_event_id]

    @staticmethod
    def get_all_columns(data_event_id: str):
        """Devuelve todas las columnas del evento especificado."""
        return DataEventColumns.key_columns[data_event_id] + DataEventColumns.data_columns[data_event_id]


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
