"""Módulo creado para el TFM de Beatriz."""

from xdevs.models import Coupled
from edge.body import SimBody5
from util.commander import Generator
from edge.sensor import SimSensor5, SensorEventId, SensorInfo
from edge.usv import USV_Simple
from fog.fog import FogServer
from xdevs.sim import Coordinator
from time import strftime, localtime
import os

class ModelBeatrizTFM(Coupled):
    """Clase que implementa un modelo de la pila IoT como entidad virtual."""
    
    def __init__(self, name: str, commands_path: str, simbody: SimBody5, base_folder: str, log_Time=False, log_Data=False):
        """Función de inicialización."""
        super().__init__(name)
        # Simulation file
        generator = Generator("Commander", commands_path)

        # FOG SEVER 1: Masa de agua 1
        # Sensores Internos
        sensor_info_n = SensorInfo(id=SensorEventId.NOX, description="Nitrogen sensor (mg/L)", delay=6, max=0.5, min=0.0, precision=0.1, noisebias=0.01, noisesigma=0.001)
        sensor_info_o = SensorInfo(id=SensorEventId.DOX, description="Oxigen sensor (mg/L)", delay=5, max=30.0, min=0.0, precision=1.0, noisebias=1.0, noisesigma=0.1)
        sensor_info_a = SensorInfo(id=SensorEventId.ALG, description="Algae detector (mg/L)", delay=7, max=15.0, min=0.0, precision=1.0, noisebias=1.0, noisesigma=0.1)
        sensor_info_t = SensorInfo(id=SensorEventId.WTE, description="Water temperature sensor (ºC)", delay=4, max=30, min=0, precision=0.1, noisebias=0.01, noisesigma=0.1)
        sensor_info_u = SensorInfo(id=SensorEventId.WFU, description="East water flow (m/s)", delay=4, max=0.1, min=-0.1, precision=0.01, noisebias=0.001, noisesigma=0.001)
        sensor_info_v = SensorInfo(id=SensorEventId.WFV, description="Nord water flow (m/s)", delay=4, max=0.1, min=-0.1, precision=0.01, noisebias=0.001, noisesigma=0.001)
        sensor_info_s = SensorInfo(id=SensorEventId.SUN, description="Sun radiation (n.u.)", delay=2, max=1.0, min=0, precision=0.01, noisebias=0.001, noisesigma=0.001)
        sensor_info_x = SensorInfo(id=SensorEventId.WFX, description="East wind flow (m/s)", delay=3, max=0.1, min=-0.1, precision=0.01, noisebias=0.001, noisesigma=0.001)
        sensor_info_y = SensorInfo(id=SensorEventId.WFY, description="Nord wind flow (m/s)", delay=3, max=0.1, min=-0.1, precision=0.01, noisebias=0.001, noisesigma=0.001)
        sensor_n = SimSensor5("SimSenN", simbody, sensor_info_n, log_Time=log_Time, log_Data=log_Data)
        sensor_o = SimSensor5("SimSenO", simbody, sensor_info_o, log_Time=log_Time, log_Data=log_Data)
        sensor_a = SimSensor5("SimSenA", simbody, sensor_info_a, log_Time=log_Time, log_Data=log_Data)
        sensor_t = SimSensor5("SimSenT", simbody, sensor_info_t, log_Time=log_Time, log_Data=log_Data)
        sensor_u = SimSensor5("SimSenU", simbody, sensor_info_u, log_Time=log_Time, log_Data=log_Data)
        sensor_v = SimSensor5("SimSenV", simbody, sensor_info_v, log_Time=log_Time, log_Data=log_Data)
        sensor_s = SimSensor5("SimSenS", simbody, sensor_info_s, log_Time=log_Time, log_Data=log_Data)
        sensor_x = SimSensor5("SimSenX", simbody, sensor_info_x, log_Time=log_Time, log_Data=log_Data)
        sensor_y = SimSensor5("SimSenY", simbody, sensor_info_y, log_Time=log_Time, log_Data=log_Data)

        thing_names = [sensor_n.name, sensor_o.name, sensor_a.name, sensor_t.name, sensor_u.name,
                       sensor_v.name, sensor_s.name, sensor_x.name, sensor_y.name]
        thing_event_ids = [sensor_info_n.id.value, sensor_info_o.id.value, sensor_info_a.id.value,
                           sensor_info_t.id.value, sensor_info_u.id.value, sensor_info_v.id.value,
                           sensor_info_s.id.value, sensor_info_x.id.value, sensor_info_y.id.value]
         
        # Se crea la clase provisionar del barco
        usv1 = USV_Simple("USV_1",'./dataedge/', simbody, delay=0, log_Time=log_Time, log_Data=log_Data)
        
        # TODO: Complete the FogServer definition
        fog = FogServer("FogServer", usv1.name, thing_names, thing_event_ids, sensor_s, base_folder=base_folder, log_Time=log_Time, log_Data=log_Data)
        # Capa Cloud:
        # cloud = Cloud("Cloud", [SensorEventId.POSBLOOM.name])
        # Components:
        self.add_component(generator)
        self.add_component(sensor_n)
        self.add_component(sensor_o)
        self.add_component(sensor_a)
        self.add_component(sensor_t)
        self.add_component(sensor_u)
        self.add_component(sensor_v)
        self.add_component(sensor_s)
        self.add_component(sensor_x)
        self.add_component(sensor_y)
        self.add_component(usv1)
        self.add_component(fog)
        # Coupling relations:
        self.add_coupling(generator.o_cmd, fog.i_cmd)
        self.add_coupling(generator.o_cmd, usv1.i_cmd)
        self.add_coupling(usv1.o_sensor, sensor_n.i_in)
        self.add_coupling(usv1.o_sensor, sensor_o.i_in)
        self.add_coupling(usv1.o_sensor, sensor_a.i_in)
        self.add_coupling(usv1.o_sensor, sensor_t.i_in)
        self.add_coupling(usv1.o_sensor, sensor_u.i_in)
        self.add_coupling(usv1.o_sensor, sensor_v.i_in)
        self.add_coupling(usv1.o_sensor, sensor_x.i_in)
        self.add_coupling(usv1.o_sensor, sensor_y.i_in)
        self.add_coupling(fog.o_sensor, sensor_s.i_in)
        self.add_coupling(usv1.o_out,  fog.get_in_port("i_" + usv1.name))
        #self.add_coupling(usv1.o_info, fog.get_in_port("i_" + usv1.name))
        self.add_coupling(sensor_n.o_out, fog.get_in_port("i_" + sensor_n.name))
        self.add_coupling(sensor_o.o_out, fog.get_in_port("i_" + sensor_o.name))
        self.add_coupling(sensor_a.o_out, fog.get_in_port("i_" + sensor_a.name))
        self.add_coupling(sensor_t.o_out, fog.get_in_port("i_" + sensor_t.name))
        self.add_coupling(sensor_u.o_out, fog.get_in_port("i_" + sensor_u.name))
        self.add_coupling(sensor_v.o_out, fog.get_in_port("i_" + sensor_v.name))
        self.add_coupling(sensor_s.o_out, fog.get_in_port("i_" + sensor_s.name))
        self.add_coupling(sensor_x.o_out, fog.get_in_port("i_" + sensor_x.name))
        self.add_coupling(sensor_y.o_out, fog.get_in_port("i_" + sensor_y.name))
        self.add_coupling(fog.get_out_port("o_" + usv1.name), usv1.i_in)


        ## self.add_component(cloud)
        ## self.add_coupling(fog1.get_out_port("o_" + fusion11.name + "_raw"), cloud.get_in_port("i_" + DataEventId.POSBLOOM.name + "_raw"))
        ## self.add_coupling(fog1.get_out_port("o_" + fusion12.name + "_raw"), cloud.get_in_port("i_" + DataEventId.POSBLOOM.name + "_raw"))
        ## self.add_coupling(fog1.get_out_port("o_" + fusion11.name + "_mod"), cloud.get_in_port("i_" + DataEventId.POSBLOOM.name + "_mod"))
        ## self.add_coupling(fog1.get_out_port("o_" + fusion12.name + "_mod"), cloud.get_in_port("i_" + DataEventId.POSBLOOM.name + "_mod"))
        ## self.add_coupling(fog2.get_out_port("o_" + fusion22.name + "_mod"), cloud.get_in_port("i_" + DataEventId.POSBLOOM.name + "_mod"))


if __name__ == "__main__":
    # Create the output directory:
    model_name: str = "ModelBeatrizTFM"
    # base_folder: str = "output" + "/" + model_name + "_" + strftime("%Y%m%d%H%M%S", localtime())
    base_folder: str = "output" + "/" + model_name + "_reports"
    os.makedirs(base_folder, exist_ok=True)
    simbody: SimBody5 = SimBody5('SimWater', './dataedge/Washington-1m-2008-09_UGRID.nc')
    coupled = ModelBeatrizTFM(model_name, 'data/main-beatriz-tfm.txt', simbody, base_folder=base_folder, log_Time=True, log_Data=False)
    coord = Coordinator(coupled)
    coord.initialize()
    coord.simulate()
    coord.exit()
