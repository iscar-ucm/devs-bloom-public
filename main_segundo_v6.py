"""Módulo creado por Segundo para realizar pruebas."""


# Simulación de un Sensor Simulado que toma los datos de BodySim
from xdevs.sim import Coordinator
from xdevs.models import Coupled
import datetime as dt

from util.file import FileAskVar,FileOut
from util.body import SimBody6
from edge.sensor import SimSensor6,SensorEventId,SensorInfo

from util.util import Generator

class ModelSensor6(Coupled):
    """Clase que implementa un modelo para probar Sensor5 sobre BodySim6."""

    def __init__(self, name: str, commands_path: str, simbody: SimBody6, log_Data=False,log_Time=False):
        """Función de inicialización."""
        super().__init__(name)
        generator = Generator("Commander", commands_path)
        ask_sensor_n = FileAskVar("Ask_N", './dataedge/Sensor2008_NOX.csv', dataid=SensorEventId.NOX)
        ask_sensor_o = FileAskVar("Ask_O", './dataedge/Sensor2008_DOX.csv', dataid=SensorEventId.DOX)
        ask_sensor_a = FileAskVar("Ask_A", './dataedge/Sensor2008_ALG.csv', dataid=SensorEventId.ALG)
        ask_sensor_t = FileAskVar("Ask_T", './dataedge/Sensor2008_temperature.csv', dataid=SensorEventId.WTE)
        ask_sensor_u = FileAskVar("Ask_U", './dataedge/Sensor2008_U.csv', dataid=SensorEventId.WFU)
        ask_sensor_v = FileAskVar("Ask_V", './dataedge/Sensor2008_V.csv', dataid=SensorEventId.WFV)
        ask_sensor_s = FileAskVar("Ask_S", './dataedge/Sensor2008_sun.csv', dataid=SensorEventId.SUN)
        ask_sensor_x = FileAskVar("Ask_X", './dataedge/Sensor2008_wind_x.csv', dataid=SensorEventId.WFX)
        ask_sensor_y = FileAskVar("Ask_Y", './dataedge/Sensor2008_wind_y.csv', dataid=SensorEventId.WFY)
        sensor_info_n = SensorInfo(id=SensorEventId.NOX, description="Nitrogen sensor (mg/L)", delay=6, max=0.5, min=0.0, precision=0.1, noisebias=0.01, noisesigma=0.001)
        sensor_info_o = SensorInfo(id=SensorEventId.DOX, description="Oxigen sensor (mg/L)", delay=5, max=30.0, min=0.0, precision=1.0, noisebias=1.0, noisesigma=0.1)
        sensor_info_a = SensorInfo(id=SensorEventId.ALG, description="Algae detector (mg/L)", delay=7, max=15.0, min=0.0, precision=1.0, noisebias=1.0, noisesigma=0.1)
        sensor_info_t = SensorInfo(id=SensorEventId.WTE, description="Water temperature sensor (ºC)", delay=4, max=30, min=0, precision=0.1, noisebias=0.01, noisesigma=0.1)
        sensor_info_u = SensorInfo(id=SensorEventId.WFU, description="East water flow (m/s)", delay=4, max=0.1, min=-0.1, precision=0.01, noisebias=0.001, noisesigma=0.001)
        sensor_info_v = SensorInfo(id=SensorEventId.WFV, description="Nord water flow (m/s)", delay=4, max=0.1, min=-0.1, precision=0.01, noisebias=0.001, noisesigma=0.001)
        sensor_info_s = SensorInfo(id=SensorEventId.SUN, description="Sun radiation (n.u.)", delay=2, max=1.0, min=0, precision=0.01, noisebias=0.001, noisesigma=0.001)
        sensor_info_x = SensorInfo(id=SensorEventId.WFX, description="East wind flow (m/s)", delay=3, max=0.1, min=-0.1, precision=0.01, noisebias=0.001, noisesigma=0.001)
        sensor_info_y = SensorInfo(id=SensorEventId.WFY, description="Nord wind flow (m/s)", delay=3, max=0.1, min=-0.1, precision=0.01, noisebias=0.001, noisesigma=0.001)
       
        sensor_n = SimSensor6("SimSenN", simbody, sensor_info_n, log_Data=log_Data,log_Time=log_Time)
        sensor_o = SimSensor6("SimSenO", simbody, sensor_info_o, log_Data=log_Data,log_Time=log_Time)
        sensor_a = SimSensor6("SimSenA", simbody, sensor_info_a, log_Data=log_Data,log_Time=log_Time)
        sensor_t = SimSensor6("SimSenT", simbody, sensor_info_t, log_Data=log_Data,log_Time=log_Time)
        sensor_u = SimSensor6("SimSenU", simbody, sensor_info_u, log_Data=log_Data,log_Time=log_Time)
        sensor_v = SimSensor6("SimSenV", simbody, sensor_info_v, log_Data=log_Data,log_Time=log_Time)
        sensor_s = SimSensor6("SimSenS", simbody, sensor_info_s, log_Data=log_Data,log_Time=log_Time)
        sensor_x = SimSensor6("SimSenX", simbody, sensor_info_x, log_Data=log_Data,log_Time=log_Time)
        sensor_y = SimSensor6("SimSenY", simbody, sensor_info_y, log_Data=log_Data,log_Time=log_Time)

        out_file = FileOut("SensorsOut", './dataedge/Sensors2008_out.csv')
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

def test_sensor6():
    """Comprobamos el modelo para el Sensor5 y BodySim5"""
    print('Initialization')
    bodyfile: str = './dataedge/Washington-1m-2008-09_UGRID.nc'
    simfile: str='./data/simulation-sensor5.txt'
    simbody: SimBody6 = SimBody6('SimWater', bodyfile,log=False)
    coupled = ModelSensor6("ModelSensor5", simfile, simbody, log_Data=True,log_Time=True)
    coord = Coordinator(coupled)
    coord.initialize()
    print('Simulation')
    coord.simulate()
    coord.exit()
    print('End of simulation')

         
if __name__ == "__main__":
  
  test_sensor6()