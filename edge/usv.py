import logging
import datetime as dt
import numpy as np
import pandas as pd
import os
from xdevs import get_logger, PHASE_ACTIVE
from xdevs.models import Atomic, Port, Coupled
from xdevs.sim import Coordinator
from util.event import EnergyEventId, DataEventId, Event
from pyproj import Transformer, CRS
from edge.file import FileOut
from edge.sensor import SensorEventId
from edge.usv_power import PoweredComponent, PowerControlUnit
from edge.usv_control import USVController, USVPurePursuitController
from edge.usv_sensors import PoweredSimSensor
from edge.usv_comms import GenericCommunicationModule
from edge.usv_actuators import ContinuousModel
from util.rest import RestBody
from util.event import Event, DataEventId, CommandEvent, CommandEventId

logger = get_logger(__name__, logging.INFO)

PHASE_ON = "on"
PHASE_OFF = "off"
PHASE_TRANSMIT = "transmit"
PHASE_IDLE = "idle"
PHASE_MEASURING = "measure"
PHASE_STARTING = "starting"
PHASE_STOPPING = "stopping"
PHASE_UPDATE = "update"


class Processor(PoweredComponent):
  '''A model of a component that can process incoming data and generate clean/processed data'''

  def __init__(self, name: str, period: float=1.0, debug: bool=False, 
      controller: USVController=None) -> None:
    super().__init__(name, period=period, debug=debug)
    self.input_buffer = []
    self.output_buffer = []
    self.controller = USVPurePursuitController() if not controller else controller
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
    self.prefix = ''

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
        if msg.source == self.toFullName('IMU'):
          self.x = msg.payload['position']
          self.controller.update_position(self.x)
          self.hold_in(PHASE_UPDATE, 0.0)
        if msg.source == self.toFullName('sim_sensor'):
          self.measurements.append(msg.payload)
        if msg.source == self.toFullName('pcu'):
          self.energy.append(msg)
      if msg.id == DataEventId.COMMAND and 'waypoint' in msg.payload:
        self.controller.add_waypoints(msg.payload['waypoint'])
        if 'set_origin' in msg.payload:
          self.origin = self.toCrs.transform(*(msg.payload['set_origin']))

  def lambdaf(self) -> None:
    energy = Event(
      id=EnergyEventId.POWER_DEMAND,
      source=self.toFullName(self.name),
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
      source=self.name,
      timestamp=self.clock,
      target=self.toFullName('sim_sensor'),
      payload={
        'var': var,
        'time': time,
        'lat': lat,
        'lon': lon,
        'depth':  2
      }
    ))

  def send_control(self) -> None:
    command = Event(
      id=DataEventId.COMMAND,
      source=self.name,
      target=self.toFullName('IMU'),
      timestamp=self.clock,
      payload={ 'u': self.u }
    )
    self.o_data.add(command)

  def send_position(self) -> None:
    (lat, lon) = self.toGeodetic.transform(*(self.origin + self.x[0:2]))
    measurement = Event(
      id=DataEventId.MEASUREMENT,
      source=self.toFullName('IMU'),
      target=self.toFullName('generic_comms'),
      timestamp=self.clock,
      payload={ 'position': self.x, 'lat': lat, 'lon': lon }
    )
    self.o_data.add(measurement)

  def send_measurements(self) -> None:
    for m in self.measurements:
      self.o_data.add(Event(
        id=DataEventId.MEASUREMENT,
        source=self.toFullName('sim_sensor'),
        target=self.toFullName('generic_comms'),
        timestamp=self.clock,
        payload=m
      ))
    self.measurements.clear()

  def send_energy(self) -> None:
    for msg in self.energy:
      msg.target = self.toFullName('generic_comms')
      self.o_data.add(msg)
    self.energy.clear()

  def toFullName(self, name):
    return f'{self.prefix}.{name}' if self.prefix else name

  def setPrefix(self, prefix):
    self.prefix = prefix


class USV(Coupled):
  '''A coupled model of a USV'''

  def __init__(self, name: str, period: float=1):
    super().__init__(name)

    if period <= 0:
      raise ValueError("period has to be greater than 0")

    self.sensors = []
    self.actuators = []
    self.comms = []
 
  def add_power_control_unit(self, pcu):
    '''Add a Power Control Unit (PCU)
    
      The PCU is the component responsible of handling the power supply of the USV,
      including, but not limited to:
      - Measure and report energy consumption
      - Enable or disable other components

      The current model only support one PCU, which means that if the USV already 
      has one it will be replaced.
    '''
    self.pcu = pcu
    self.add_powered_component(pcu)

  def add_processor(self, processor):
    '''Add a Processor
    
      The Processor is the component responsible of doing the onboard computations,
      which includes, but is not limited to:
      - USV Guidance
      - Gather measurements from sensors
      - Control the actuators
      - Decide when to communicate

      The current model only support one processor, which means that if the USV already 
      has one it will be replaced.
    '''
    self.processor = processor
    self.processor.setPrefix(self.name)
    self.add_powered_component(processor)

  def add_sensor(self, sensor):
    '''Add a sensor
    
      The onboard sensors can measure and report to the processor different magnitudes of interest:
      - Environmental variables: temperature, PH, oxygen/nitrogen concentration...
      - Propioceptive variables: USV attitude, component temperatures, ...

      Each sensor is connected to the processor through the bus.
    '''
    self.sensors.append(sensor)
    self.add_powered_component(sensor, connectTo=[self.processor])

  def add_actuator(self, actuator):
    '''Add an actuator
    
      The onboard actuator can propel the USV, control the location of sensors, and so on.
      Each actuator is connected to the processor through the bus.
    '''
    self.actuators.append(actuator)
    self.add_powered_component(actuator, connectTo=[self.processor])

  def add_comms(self, module):
    '''Add a communication module
    
      The USV has one or more comminucation module such as WiFi, LTE, Ethernet or whatever.

      Each module is connected to the processor through a dedicated bus.
    '''
    self.comms.append(module)
    self.add_powered_component(module, connectTo=[self.processor])

  def add_powered_component(self, component: PoweredComponent, connectTo: list=[]) -> None:
    self.add_component(component)
    self.add_coupling(self.pcu.o_pwr, component.i_pwr)
    self.add_coupling(component.o_pwr, self.pcu.i_pwr)
    for c in connectTo:
      print(f'{component}->{c}')
      self.add_coupling(component.o_data, c.i_data)
      self.add_coupling(c.o_data, component.i_data)


class USVFactory:
  '''A factory that creates USV'''

  def create_USV(self, name: str="USV", period: float=1, initial: np.array=np.array((0,0,0)), body =None) -> USV:
    usv = USV(name)
    period = 1
    pcu = PowerControlUnit(f'{name}.pcu', mAh=20000, period=10*period)
    sensor = PoweredSimSensor(f'{name}.sim_sensor', body, period=30*period)
    processor = Processor(f'{name}.processor', period=1*period)
    comms = GenericCommunicationModule(f'{name}.generic_comms', debug=False)
    model = ContinuousModel(f'{name}.IMU', period=1, initial=initial)
    # Components
    usv.add_power_control_unit(pcu)
    usv.add_processor(processor)
    usv.add_comms(comms)
    usv.add_sensor(sensor)
    usv.add_actuator(model)
    # I/O
    usv.add_in_port(Port(Event, 'i_rx'))
    usv.add_out_port(Port(Event, 'o_tx'))
    usv.add_coupling(usv.get_in_port('i_rx'), comms.i_rx)
    usv.add_coupling(comms.o_tx, usv.get_out_port('o_tx'))
    return usv



class USV_Simple(Atomic):
    """
    A model to load a file to ask SimSensor telemetries.
    File example
    DateTime	          Lat	        Lon	          Depth	        Sensor
    2008-09-12 00:30:30	47,5	      -122,3	      0	            DOX
    2008-09-12 00:31:30	47,50015983	-122,2999521	-0,010423905	NOX
    """

    def __init__(self, name, datapath,  thing_names, thing_event_ids, delay):
        """Instancia la clase."""
        super().__init__(name)
        
        self.datapath = datapath
        self.thing_names = thing_names
        self.thing_event_ids = thing_event_ids
        self.delay = delay
        self.input_buffer = []
        self.data_buffer = []

        #Lectura de los ficheros correspondientes al datapath 
        self.files = [f for f in os.listdir(self.datapath) if (f.startswith('Sensor2008_') and f.endswith(".csv"))]
        self.file_name:str

        # Puerto de entrada para el uso de comandos
        self.i_cmd = Port(CommandEvent, "i_cmd")
        self.add_in_port(self.i_cmd)

        # Puertos de salida de control de los sensores
        self.o_sensor = Port(Event, "o_sensor")
        self.add_out_port(self.o_sensor)
        
        # Puertos de entrada/salida del USV
        self.i_in = Port(Event, "i_in")
        self.add_in_port(self.i_in)

        self.o_out = Port(Event, "o_out")
        self.add_out_port(self.o_out)

        self.o_info = Port(Event, "o_info")
        self.add_out_port(self.o_info)

        
    def initialize(self):
        """Función de inicialización."""
        # Let's read a value from alls sensor files
        self.mydata={}
        self.datetimes={}  

        for self.file_name in self.files:   
          if (self.file_name[-1]) == 'x':
              self.mydata[self.file_name] = pd.read_excel(self.datapath+self.file_name, parse_dates=True)
              self.datetimes[self.file_name]=(self.mydata[self.file_name])['DateTime']

          if (self.file_name[-1]) == 'v':
              self.mydata[self.file_name]  = pd.read_csv(self.datapath+self.file_name, parse_dates=True)  # Sensor data loading
              self.datetimes[self.file_name] = [dt.datetime.fromisoformat(s) for s in (self.mydata[self.file_name])['DateTime']] #Para CSV

        # Al tener archivos con las mismas dimensiones, se puede simplificar las siguientes definiciones,
        # (tener en cuenta en futuras versiones):
        self.N = self.mydata[self.file_name].DateTime.count()
        self.ind = -1

        # Estado inicial del USV:
        '''
        self.tau=100
        self.lyr=55
        self.seccion = range(1,200,1)
        self.latc= self.mydata[self.file_name]['Lat']
        self.lonc = self.mydata[self.file_name]['Lon']
        self.map = [self.lonc[self.seccion],self.latc[self.seccion]]
        self.ip=10
        self.x0=[0,self.lonc(self.ip),self.latc(self.ip)]
        self.x = self.x0
        self.initial: bool = True
        self.msgout = None
        '''
        super().passivate()

    def exit(self):
        """Exit function."""
        pass

    def deltint(self):
        """DEVS internal transition function."""
        # Calcula delta tiempo hasta siguiente Telemetría
        self.ind = self.ind + 1              # Actualizo indice a siguiente
        if self.ind >= self.N:
            self.passivate()
        else:
            #Refrencia del último fichero:
            delta = self.datetimes[self.file_name][self.ind] - self.datetimes[self.file_name][self.ind-1]

            # Implementación del comportamiento del barco 
            # DIVIDIR VALORES ENTRE 30 MINS
            '''
            myt     = self.msgin.payload['Time']                 
            mylat   = self.msgin.payload['Lat']
            mylon   = self.msgin.payload['Lon']
            mydepth = self.msgin.payload['Depth']
            mydelx  = self.msgin.payload['Xdel']   
            myalg   = self.msgin.payload['Algae'] 
            myx     = self.msgin.payload['x'] 
            mybloom = self.msgin.payload['Bloom']
            # BLOOM inicial
            if (self.delt == 0):
              myx = self.x0
              mybloom = False
              self.vtemp = []
              self.vhour = []

            self.datetime=dt.datetime.fromisoformat(self.msgin.timestamp)+dt.timedelta(seconds=self.delay)
            data = {'Time':myt,'Lat':mylat,'Lon':mylon,'Depth':mydepth, 'Xdel': mydelx,'Algae': myalg, 'x': myx, 'Bloom':mybloom}
            self.msgout=Event(id=self.msgin.id,source=self.name,timestamp=self.datetime,payload=data)
            '''
            self.hold_in(PHASE_ACTIVE, delta.seconds)

    def deltext(self, e: any):
        """DEVS external transition function."""
        if (self.i_cmd.empty() is False):
            cmd: CommandEvent = self.i_cmd.get()
            if cmd.cmd == CommandEventId.CMD_START_SIM:
                start: np.datetime = cmd.date
                delstart = [s-start for s in self.datetimes[self.file_name]]
                self.ind = round(np.nanargmin(np.absolute(delstart)))  # Nearest time index
                delta = (self.datetimes[self.file_name][self.ind] - start).total_seconds()
                if (delta >= 0):
                    super().hold_in(PHASE_ACTIVE, delta)
                elif (delta < 0)& (self.ind>0):
                    self.ind = self.ind-1
                    delta = (self.datetimes[self.file_name][self.ind] - start).total_seconds()
                    super().hold_in(PHASE_ACTIVE, delta)
                else:
                    print('Error Start Time does not agree with FileInVar Times')
                    super().passivate()
                    
            if cmd.cmd == CommandEventId.CMD_STOP_SIM:
                super().passivate()
            '''
            if self.phase==self.PHASE_OFF:
                self.msgin = self.i_in.get()
                self.msgout=Event(id=self.msgin.id,source=self.name,timestamp=self.msgin.timestamp,payload=vars(self.sensorinfo)) 
                self.hold_in(self.PHASE_INIT,0)
            elif self.phase==self.PHASE_ON:
                self.msgin = self.i_in.get()
                self.hold_in(self.PHASE_WORK,self.delay)
            '''
    def lambdaf(self):
        """DEVS output function."""
        for self.file_name in self.files:
            row = self.mydata[self.file_name].iloc[self.ind]   # Telemetría
            payload = row.to_dict() #{'DateTime': '', 'Lat': , 'Lon': , 'Depth': , 'Sensor': ''}
            datetime = payload.pop('DateTime')
            match(payload['Sensor']):
              case 'ALG':
                  self.dataid = SensorEventId.ALG
              case 'DOX':
                  self.dataid = SensorEventId.DOX
              case 'NOX':
                  self.dataid = SensorEventId.NOX
              case 'sun':
                  self.dataid = SensorEventId.SUN
              case 'temperature':
                  self.dataid = SensorEventId.WTE
              case 'U':
                  self.dataid = SensorEventId.WFU
              case 'V':
                  self.dataid = SensorEventId.WFV
              case 'wind_x':
                  self.dataid = SensorEventId.WFX
              case 'wind_y':
                  self.dataid = SensorEventId.WFY
              case _:
                  continue  
            self.o_sensor.add(Event(id=self.dataid.value, source=self.datapath+self.file_name, timestamp=datetime, payload=payload))

        '''
          if self.phase==self.PHASE_INIT:
              self.o_info.add(self.msgout)
              if self.log==True:  logger.info(self.msgout)
          if self.phase==self.PHASE_DONE:
              self.o_out.add(self.msgout)
              if self.log==True:  logger.info(self.msgout)
          #Enviar el mensaje inicial del USV
          if ((self.phase==self.PHASE_OFF) and (self.initial == True)):
              data_init = {'Time':0,'Lat':0,'Lon':0,'Depth':0, 'Xdel': 0,'Algae': 0, 'x': 0, 'Bloom': False}
              self.msgout=Event(id='0',source=self.name,timestamp=self.simbody.dtini,payload=data_init)
              self.o_out.add(self.msgout) 
              print('Envio inicial')
              self.initial = False
        '''

class TestInput(Atomic):
  '''A test input generator to test USV'''

  def __init__(self, name: str, offset: np.array=np.array((0, 0)),
                origin: list=(47.58, -122.27),
                trajectory: str='rectangular'):
    super().__init__(name)
    self.o_tx = Port(Event, "o_tx")
    self.add_out_port(self.o_tx)
    self.clock = dt.datetime.now()
    self.origin = origin
    self.offset = offset
    self.generators = {
      'triangle': self._generate_triangle,
      'rectangle': self._generate_rect,
    }
    if not trajectory in self.generators:
      raise ValueError('Invalid trajectory type')
    self.trajectory = trajectory

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
      N, width, height = 21, 1000, 2000
      trajectory = self.generators[self.trajectory](N, width, height)
      self.o_tx.add(Event(
        id=DataEventId.COMMAND,
        source=f'{self.name}',
        timestamp=self.clock,
        payload={
          'waypoint': trajectory + self.offset,
          'set_origin': self.origin
        }
      ))

  def _generate_triangle(self, N, width, height):
    return [
      [i*width/(N-1), height*(i%2)] for i in range(N)
    ]

  def _generate_rect(self, N, width, height):
    return [
      [(width/(N-1))*int((i)/2), height*(int((i+1)/2)%2)] for i in range(N)
    ]



class TestOneUSV(Coupled):
  '''A coupled model to test an USV coupled model'''

  def __init__(self, name: str, usv: USV, trajectory: str='triangle') -> None:
    super().__init__(name)
    test_input = TestInput("GCS", trajectory=trajectory)
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

  def __init__(self, name: str, usv: list[USV], offset: list, trajectory: str='triangle') -> None:
    super().__init__(name)
    test_input1 = TestInput("GCS_1", trajectory=trajectory, offset=offset[0])
    test_input2 = TestInput("GCS_2", trajectory=trajectory, offset=offset[1])
    test_output = FileOut("FileOut", './data/TwoUSVData.xlsx')
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




def test_one_USV(trajectory: str='triangle', host: str='http://127.0.0.1:5000') -> None:
  body = RestBody(host)
  start_dt = dt.datetime(2021, 8, 1, 0, 0, 0)
  end_dt = dt.datetime(2021, 8, 1, 0, 30, 0)
  sim_seconds = (end_dt - start_dt).total_seconds()
  usv = USVFactory().create_USV(
    name='Red Leader',
    period=1,
    body=body,
    initial=np.array((-100, 0, 0))
  )
  coupled = TestOneUSV("Test USV", usv, trajectory)
  coord = Coordinator(coupled, flatten=True)
  coord.initialize()
  coord.simulate_time(sim_seconds)
  coord.exit()
  
  
def test_two_USV(trajectory: str='triangle', host: str='http://127.0.0.1:5000') -> None:
  body = RestBody(host)
  start_dt = dt.datetime(2021, 8, 1, 0, 0, 0)
  end_dt = dt.datetime(2021, 8, 1, 0, 30, 0)
  sim_seconds = (end_dt - start_dt).total_seconds()
  builder = USVFactory()
  usv1 = builder.create_USV(
    name='Red Leader',
    period=1,
    body=body,
    initial=np.array((-100, 0, 0))
  )
  usv2 = builder.create_USV(
    name='Red Two',
    period=1,
    body=body,
    initial=np.array((550, -50, 0))
  )
  coupled = TestTwoUSV("Test USV",
    usv=(usv1, usv2),
    offset=np.array(((0, 0), (500, 0))),
    trajectory=trajectory
  )
  coord = Coordinator(coupled, flatten=True)
  coord.initialize()
  coord.simulate_time(sim_seconds)
  coord.exit()