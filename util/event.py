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
    """Allowed data events."""

    SIMSEN = "SimSensor"
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


class EnergyEventId(Enum):
    """Allowed energy events."""

    POWER_ON = "power_on"
    POWER_OFF = "power_off"
    POWER_DEMAND = "power_demand"


class SensorEventId(Enum):
    """Allowed Sensor events acording to BodySim."""
    #Id: Old EEMS version
    OXIGEN = "WQ_O"
    NITROGEN = "WQ_N"
    ALGA = "WQ_ALG"
    #Id: New EEMS-UGRID version
    DOX = "DOX"     #Dissolved oxygen
    NOX = "NOX"     #Nitrate nitrogen
    ALG = "ALG"     #Algae 2 
    SUN = "SUN"     #Sun radiation
    WTE = "WTE"     #Water temperature
    WFU = "WFU"     #Water East Flow
    WFV = "WFV"     #Wind Nord Flow
    WFX = "WFX"     #Wind East Flow 
    WFY = "WFY"     #Wind East Flow 


class CommandEventId(Enum):
    """Allowed commands."""

    CMD_START_SIM = "START_SIM"
    CMD_STOP_SIM = "STOP_SIM"
    CMD_FIX_OUTLIERS = "FIX_OUTLIERS"
    CMD_SAVE_DATA = "SAVE_DATA"
    CMD_FOG_REPORT = "FOG_REPORT"


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
    key_columns[SensorEventId.OXIGEN.value] = ["id", "source", "timestamp"]
    key_columns[SensorEventId.NITROGEN.value] = ["id", "source", "timestamp"]
    key_columns[SensorEventId.ALGA.value] = ["id", "source", "timestamp"]
    key_columns[SensorEventId.NOX.value] = ["id", "source", "timestamp"]
    key_columns[SensorEventId.DOX.value] = ["id", "source", "timestamp"]
    key_columns[SensorEventId.ALG.value] = ["id", "source", "timestamp"]
    key_columns[SensorEventId.WTE.value] = ["id", "source", "timestamp"]
    key_columns[SensorEventId.WFU.value] = ["id", "source", "timestamp"]
    key_columns[SensorEventId.WFV.value] = ["id", "source", "timestamp"]
    key_columns[SensorEventId.SUN.value] = ["id", "source", "timestamp"]
    key_columns[SensorEventId.WFX.value] = ["id", "source", "timestamp"]
    key_columns[SensorEventId.WFY.value] = ["id", "source", "timestamp"]
    data_columns = {}
    data_columns[DataEventId.POSBLOOM.value] = ["Lat", "Lon", "Depth", "DetB", "DetBb"]
    data_columns[SensorEventId.OXIGEN.value] = ["Time", "Lat", "Lon", "Depth", SensorEventId.OXIGEN.value, "Bt", "Bi", "Bj", "Bl"]
    data_columns[SensorEventId.NITROGEN.value] = ["Time", "Lat", "Lon", "Depth", SensorEventId.NITROGEN.value, "Bt", "Bi", "Bj", "Bl"]
    data_columns[SensorEventId.ALGA.value] = ["Time", "Lat", "Lon", "Depth", SensorEventId.ALGA.value, "Bt", "Bi", "Bj", "Bl"]
    data_columns[SensorEventId.NOX.value] = ["Time", "Lat", "Lon", "Depth", SensorEventId.NOX.value, "Bt", "Bij", "Bl"]
    data_columns[SensorEventId.DOX.value] = ["Time", "Lat", "Lon", "Depth", SensorEventId.DOX.value, "Bt", "Bij", "Bl"]
    data_columns[SensorEventId.ALG.value] = ["Time", "Lat", "Lon", "Depth", SensorEventId.ALG.value, "Bt", "Bij", "Bl"]
    data_columns[SensorEventId.WTE.value] = ["Time", "Lat", "Lon", "Depth", SensorEventId.WTE.value, "Bt", "Bij", "Bl"]
    data_columns[SensorEventId.WFU.value] = ["Time", "Lat", "Lon", "Depth", SensorEventId.WFU.value, "Bt", "Bij", "Bl"]
    data_columns[SensorEventId.WFV.value] = ["Time", "Lat", "Lon", "Depth", SensorEventId.WFV.value, "Bt", "Bij", "Bl"]
    data_columns[SensorEventId.SUN.value] = ["Time", "Lat", "Lon", "Depth", SensorEventId.SUN.value, "Bt", "Bij", "Bl"]
    data_columns[SensorEventId.WFX.value] = ["Time", "Lat", "Lon", "Depth", SensorEventId.WFX.value, "Bt", "Bij", "Bl"]
    data_columns[SensorEventId.WFY.value] = ["Time", "Lat", "Lon", "Depth", SensorEventId.WFY.value, "Bt", "Bij", "Bl"]

    @staticmethod
    def get_key_columns(data_event_id: str):
        """Devuelve las columnas clave del evento especificado."""
        return DataEventColumns.key_columns[data_event_id]

    @staticmethod
    def get_data_columns(data_event_id: str):
        """Devuelve las columnas de datos del evento especificado."""
        return DataEventColumns.data_columns[data_event_id]

    @staticmethod
    def get_all_columns(data_event_id: str):
        """Devuelve todas las columnas del evento especificado."""
        return DataEventColumns.key_columns[data_event_id] + DataEventColumns.data_columns[data_event_id]


class CommandEvent:
    """Clase para enviar mensajes del Generator al entorno de simulación."""

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

    def str(self):
        """Return a string representation of this object."""
        return self.date.strftime('%Y-%m-%d %H:%M:%S') + ";" + self.cmd.value
