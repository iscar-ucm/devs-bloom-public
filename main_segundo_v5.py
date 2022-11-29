"""Módulo creado por Segundo para realizar pruebas."""


# Simulación de un Sensor Simulado que toma los datos de BodySim
from xdevs.sim import Coordinator
from xdevs.models import Coupled
import datetime as dt

from edge.file import FileAskVar,FileOut
from edge.body import SimBody5
from edge.sensor import SimSensor5,SensorEventId,SensorInfo

from util.commander import Generator

class ModelSensor5(Coupled):
    """Clase que implementa un modelo para probar Sensor5 sobre BodySim5."""

    def __init__(self, name: str, commands_path: str, simbody: SimBody5, log=False):
        """Función de inicialización."""
        super().__init__(name)
        generator = Generator("Commander", commands_path)
        ask_sensor_n = FileAskVar("Ask_N", './dataedge/Sensor2008_NOX.csv', dataid=SensorEventId.NOX, log=log)
        ask_sensor_o = FileAskVar("Ask_O", './dataedge/Sensor2008_DOX.csv', dataid=SensorEventId.DOX, log=log)
        ask_sensor_a = FileAskVar("Ask_A", './dataedge/Sensor2008_ALG.csv', dataid=SensorEventId.ALG, log=log)
        ask_sensor_t = FileAskVar("Ask_T", './dataedge/Sensor2008_temperature.csv', dataid=SensorEventId.WTE, log=log)
        ask_sensor_u = FileAskVar("Ask_U", './dataedge/Sensor2008_U.csv', dataid=SensorEventId.WFU, log=log)
        ask_sensor_v = FileAskVar("Ask_V", './dataedge/Sensor2008_V.csv', dataid=SensorEventId.WFV, log=log)
        ask_sensor_s = FileAskVar("Ask_S", './dataedge/Sensor2008_sun.csv', dataid=SensorEventId.SUN, log=log)
        ask_sensor_x = FileAskVar("Ask_X", './dataedge/Sensor2008_wind_x.csv', dataid=SensorEventId.WFX, log=log)
        ask_sensor_y = FileAskVar("Ask_Y", './dataedge/Sensor2008_wind_y.csv', dataid=SensorEventId.WFY, log=log)
        sensor_info_n = SensorInfo(id=SensorEventId.NOX, description="Nitrogen sensor (mg/L)", delay=6, max=0.5, min=0.0, precision=0.1, noisebias=0.01, noisesigma=0.001)
        sensor_info_o = SensorInfo(id=SensorEventId.DOX, description="Oxigen sensor (mg/L)", delay=5, max=30.0, min=0.0, precision=1.0, noisebias=1.0, noisesigma=0.1)
        sensor_info_a = SensorInfo(id=SensorEventId.ALG, description="Algae detector (mg/L)", delay=7, max=15.0, min=0.0, precision=1.0, noisebias=1.0, noisesigma=0.1)
        sensor_info_t = SensorInfo(id=SensorEventId.WTE, description="Water temperature sensor (ºC)", delay=4, max=30, min=0, precision=0.1, noisebias=0.01, noisesigma=0.1)
        sensor_info_u = SensorInfo(id=SensorEventId.WFU, description="East water flow (m/s)", delay=4, max=0.1, min=-0.1, precision=0.01, noisebias=0.001, noisesigma=0.001)
        sensor_info_v = SensorInfo(id=SensorEventId.WFV, description="Nord water flow (m/s)", delay=4, max=0.1, min=-0.1, precision=0.01, noisebias=0.001, noisesigma=0.001)
        sensor_info_s = SensorInfo(id=SensorEventId.SUN, description="Sun radiation (n.u.)", delay=2, max=1.0, min=0, precision=0.01, noisebias=0.001, noisesigma=0.001)
        sensor_info_x = SensorInfo(id=SensorEventId.WFX, description="East wind flow (m/s)", delay=3, max=0.1, min=-0.1, precision=0.01, noisebias=0.001, noisesigma=0.001)
        sensor_info_y = SensorInfo(id=SensorEventId.WFY, description="Nord wind flow (m/s)", delay=3, max=0.1, min=-0.1, precision=0.01, noisebias=0.001, noisesigma=0.001)
       
        sensor_n = SimSensor5("SimSenN", simbody, sensor_info_n, log_Data=False,log_Time=True)
        sensor_o = SimSensor5("SimSenO", simbody, sensor_info_o, log_Data=False,log_Time=True)
        sensor_a = SimSensor5("SimSenA", simbody, sensor_info_a, log_Data=False,log_Time=True)
        sensor_t = SimSensor5("SimSenT", simbody, sensor_info_t, log_Data=False,log_Time=True)
        sensor_u = SimSensor5("SimSenU", simbody, sensor_info_u, log_Data=False,log_Time=True)
        sensor_v = SimSensor5("SimSenV", simbody, sensor_info_v, log_Data=False,log_Time=True)
        sensor_s = SimSensor5("SimSenS", simbody, sensor_info_s, log_Data=False,log_Time=True)
        sensor_x = SimSensor5("SimSenX", simbody, sensor_info_x, log_Data=False,log_Time=True)
        sensor_y = SimSensor5("SimSenY", simbody, sensor_info_y, log_Data=False,log_Time=True)

        out_file = FileOut("SensorsOut", './dataedge/Sensors2008_out.csv', log=log)
        print('OutputFile:','./dataedge/Sensors2008_out.csv')
        self.add_component(generator)
        self.add_component(ask_sensor_n)
        self.add_component(ask_sensor_o)
        self.add_component(ask_sensor_a)
        self.add_component(ask_sensor_t)
        self.add_component(ask_sensor_u)
        self.add_component(ask_sensor_v)
        self.add_component(ask_sensor_s)
        self.add_component(ask_sensor_x)
        self.add_component(ask_sensor_y)
        self.add_component(sensor_n)
        self.add_component(sensor_o)
        self.add_component(sensor_a)
        self.add_component(sensor_t)
        self.add_component(sensor_u)
        self.add_component(sensor_v)
        self.add_component(sensor_s)
        self.add_component(sensor_x)
        self.add_component(sensor_y)
        self.add_component(out_file)
        
        self.add_coupling(generator.o_cmd, ask_sensor_n.i_cmd)
        self.add_coupling(generator.o_cmd, ask_sensor_o.i_cmd)
        self.add_coupling(generator.o_cmd, ask_sensor_a.i_cmd)
        self.add_coupling(generator.o_cmd, ask_sensor_t.i_cmd)
        self.add_coupling(generator.o_cmd, ask_sensor_u.i_cmd)
        self.add_coupling(generator.o_cmd, ask_sensor_v.i_cmd)
        self.add_coupling(generator.o_cmd, ask_sensor_s.i_cmd)
        self.add_coupling(generator.o_cmd, ask_sensor_x.i_cmd)
        self.add_coupling(generator.o_cmd, ask_sensor_y.i_cmd)
        self.add_coupling(ask_sensor_n.o_out, sensor_n.i_in)
        self.add_coupling(ask_sensor_o.o_out, sensor_o.i_in)
        self.add_coupling(ask_sensor_a.o_out, sensor_a.i_in)
        self.add_coupling(ask_sensor_t.o_out, sensor_t.i_in)
        self.add_coupling(ask_sensor_u.o_out, sensor_u.i_in)
        self.add_coupling(ask_sensor_v.o_out, sensor_v.i_in)
        self.add_coupling(ask_sensor_s.o_out, sensor_s.i_in)
        self.add_coupling(ask_sensor_x.o_out, sensor_x.i_in)
        self.add_coupling(ask_sensor_y.o_out, sensor_y.i_in)
        self.add_coupling(sensor_n.o_out, out_file.i_in)
        self.add_coupling(sensor_o.o_out, out_file.i_in)
        self.add_coupling(sensor_a.o_out, out_file.i_in)
        self.add_coupling(sensor_t.o_out, out_file.i_in)
        self.add_coupling(sensor_u.o_out, out_file.i_in)
        self.add_coupling(sensor_v.o_out, out_file.i_in)
        self.add_coupling(sensor_s.o_out, out_file.i_in)
        self.add_coupling(sensor_x.o_out, out_file.i_in)
        self.add_coupling(sensor_y.o_out, out_file.i_in)

def test_sensor5():
    """Comprobamos el modelo para el Sensor5 y BodySim5"""
    print('Initialization')
    bodyfile: str = './dataedge/Washington-1m-2008-09_UGRID.nc'
    simfile: str='./data/simulation-sensor5.txt'
    simbody: SimBody5 = SimBody5('SimWater', bodyfile,log=False)
    coupled = ModelSensor5("ModelSensor5", simfile, simbody, log=False)
    coord = Coordinator(coupled)
    coord.initialize()
    print('Simulation')
    coord.simulate()
    coord.exit()
    print('End of simulation')

         
if __name__ == "__main__":
  
  test_sensor5()