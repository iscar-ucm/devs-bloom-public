"""Clase que implementa algunos prototipos de modelos."""

from xdevs.models import Coupled
import datetime as dt
from xdevs.sim import Coordinator
from edge.file import FileIn, FileAskVar, FileOut, FussionPosBloom
from fog.fog import FogServer
from cloud.cloud import Cloud
from util.event import DataEventId
from util.commander import Generator
from edge.body import SimBody5
from edge.sensor import SimSensor5, SimSensor6, SensorEventId, SensorInfo
from edge.usv import USV_Simple

class Model_01(Coupled):
    """Clase que implementa un modelo simple con un único UAV."""

    def __init__(self, name, start, day, log=False):
        """Función de inicialización."""
        super().__init__(name)
        file_ship = FileIn("ShipPos1", "data/LatLon"+day+".xlsx",
                           start=start, dataid=DataEventId.POS3D, log=log)
        file_bloom = FileIn("DetBlo1", "data/DetBloom"+day+".xlsx",
                            start=start, dataid=DataEventId.BLOOM, log=log)
        # Fusiona Posición del barco con medida de Sensor de Bloom
        edge_fusion = FussionPosBloom("EdgeFussion1")
        # Capa Fog:
        fog_server = FogServer("FogServer1")
        # Capa Cloud:
        cloud = Cloud("Cloud")
        self.add_component(file_ship)
        self.add_component(file_bloom)
        self.add_component(edge_fusion)
        self.add_component(fog_server)
        self.add_component(cloud)
        self.add_coupling(file_ship.o_out, edge_fusion.i_Pos)
        self.add_coupling(file_bloom.o_out, edge_fusion.i_Blo)
        self.add_coupling(edge_fusion.o_out,
                          fog_server.get_in_port("i_fusion_1"))
        self.add_coupling(fog_server.get_out_port("o_fusion_1_raw"),
                          cloud.get_in_port("i_body_1_raw"))
        self.add_coupling(fog_server.get_out_port("o_fusion_1_mod"),
                          cloud.get_in_port("i_body_1_mod"))


class Model_02(Coupled):
    """Clase que implementa un modelo simple con dos UAV."""

    def __init__(self, name, start, day, log=False):
        """Función de inicialización."""
        super().__init__(name)
        # UAV 1
        ship1 = FileIn("ShipPos1", "data/LatLon"+day+".xlsx",
                       start=start, dataid=DataEventId.POS3D, log=log)
        bloom1 = FileIn("DetBlo1", "data/DetBloom"+day+".xlsx",
                        start=start, dataid=DataEventId.BLOOM, log=log)
        fusion1 = FussionPosBloom("EdgeFussion1")
        # UAV 2
        ship2 = FileIn("ShipPos2", "data/LatLon"+day+".xlsx",
                       start=start, dataid=DataEventId.POS3D, log=log)
        bloom2 = FileIn("DetBlo2", "data/DetBloom"+day+".xlsx",
                        start=start, dataid=DataEventId.BLOOM, log=log)
        fusion2 = FussionPosBloom("EdgeFussion2")
        # FOG SEVER 1: Masa de agua 1
        fog1 = FogServer("FogServer1", n_uav=2)
        # Capa Cloud:
        cloud = Cloud("Cloud")
        self.add_component(ship1)
        self.add_component(bloom1)
        self.add_component(fusion1)
        self.add_component(ship2)
        self.add_component(bloom2)
        self.add_component(fusion2)
        self.add_component(fog1)
        self.add_component(cloud)
        self.add_coupling(ship1.o_out, fusion1.i_Pos)
        self.add_coupling(bloom1.o_out, fusion1.i_Blo)
        self.add_coupling(ship2.o_out, fusion2.i_Pos)
        self.add_coupling(bloom2.o_out, fusion2.i_Blo)
        self.add_coupling(fusion1.o_out, fog1.get_in_port("i_fusion_1"))
        self.add_coupling(fusion2.o_out, fog1.get_in_port("i_fusion_2"))
        self.add_coupling(fog1.get_out_port("o_fusion_1_raw"),
                          cloud.get_in_port("i_body_1_raw"))
        self.add_coupling(fog1.get_out_port("o_fusion_2_raw"),
                          cloud.get_in_port("i_body_1_raw"))
        self.add_coupling(fog1.get_out_port("o_fusion_1_mod"),
                          cloud.get_in_port("i_body_1_mod"))
        self.add_coupling(fog1.get_out_port("o_fusion_2_mod"),
                          cloud.get_in_port("i_body_1_mod"))


class Model_03(Coupled):
    """Clase que implementa un modelo con dos UAV x 2 masas de agua."""

    def __init__(self, name, start, day, log=False):
        """Función de inicialización."""
        super().__init__(name)
        # FOG SEVER 1: Masa de agua 1
        fog1 = FogServer("FogServer1", n_uav=2)
        # UAV 11
        ship11 = FileIn("ShipPos11", "data/LatLon"+day+".xlsx",
                        start=start, dataid=DataEventId.POS3D, log=log)
        bloom11 = FileIn("DetBlo11", "data/DetBloom"+day+".xlsx",
                         start=start, dataid=DataEventId.BLOOM, log=log)
        fusion11 = FussionPosBloom("EdgeFussion11")
        # UAV 12
        ship12 = FileIn("ShipPos12", "data/LatLon"+day+".xlsx",
                        start=start, dataid=DataEventId.POS3D, log=log)
        bloom12 = FileIn("DetBlo12", "data/DetBloom"+day+".xlsx",
                         start=start, dataid=DataEventId.BLOOM, log=log)
        fusion12 = FussionPosBloom("EdgeFussion12")
        # FOG SEVER 2: Masa de agua 2
        fog2 = FogServer("FogServer2", n_uav=2)
        # UAV 21
        ship21 = FileIn("ShipPos21", "data/LatLon"+day+".xlsx",
                        start=start, dataid=DataEventId.POS3D, log=log)
        bloom21 = FileIn("DetBlo21", "data/DetBloom"+day+".xlsx",
                         start=start, dataid=DataEventId.BLOOM, log=log)
        fusion21 = FussionPosBloom("EdgeFussion21")
        # UAV 22
        ship22 = FileIn("ShipPos22", "data/LatLon"+day+".xlsx",
                        start=start, dataid=DataEventId.POS3D, log=log)
        bloom22 = FileIn("DetBlo22", "data/DetBloom"+day+".xlsx",
                         start=start, dataid=DataEventId.BLOOM, log=log)
        fusion22 = FussionPosBloom("EdgeFussion22")
        # Capa Cloud:
        cloud = Cloud("Cloud", num_water_bodies=2)
        self.add_component(fog1)
        self.add_component(ship11)
        self.add_component(bloom11)
        self.add_component(fusion11)
        self.add_component(ship12)
        self.add_component(bloom12)
        self.add_component(fusion12)
        self.add_component(fog2)
        self.add_component(ship21)
        self.add_component(bloom21)
        self.add_component(fusion21)
        self.add_component(ship22)
        self.add_component(bloom22)
        self.add_component(fusion22)
        self.add_component(cloud)
        self.add_coupling(ship11.o_out, fusion11.i_Pos)
        self.add_coupling(bloom11.o_out, fusion11.i_Blo)
        self.add_coupling(ship12.o_out, fusion12.i_Pos)
        self.add_coupling(bloom12.o_out, fusion12.i_Blo)
        self.add_coupling(fusion11.o_out, fog1.get_in_port("i_fusion_1"))
        self.add_coupling(fusion12.o_out, fog1.get_in_port("i_fusion_2"))
        self.add_coupling(fog1.get_out_port("o_fusion_1_raw"),
                          cloud.get_in_port("i_body_1_raw"))
        self.add_coupling(fog1.get_out_port("o_fusion_2_raw"),
                          cloud.get_in_port("i_body_1_raw"))
        self.add_coupling(fog1.get_out_port("o_fusion_1_mod"),
                          cloud.get_in_port("i_body_1_mod"))
        self.add_coupling(fog1.get_out_port("o_fusion_2_mod"),
                          cloud.get_in_port("i_body_1_mod"))
        self.add_coupling(ship21.o_out, fusion21.i_Pos)
        self.add_coupling(bloom21.o_out, fusion21.i_Blo)
        self.add_coupling(ship22.o_out, fusion22.i_Pos)
        self.add_coupling(bloom22.o_out, fusion22.i_Blo)
        self.add_coupling(fusion21.o_out, fog2.get_in_port("i_fusion_1"))
        self.add_coupling(fusion22.o_out, fog2.get_in_port("i_fusion_2"))
        self.add_coupling(fog2.get_out_port("o_fusion_1_raw"),
                          cloud.get_in_port("i_body_2_raw"))
        self.add_coupling(fog2.get_out_port("o_fusion_2_raw"),
                          cloud.get_in_port("i_body_2_raw"))
        self.add_coupling(fog2.get_out_port("o_fusion_1_mod"),
                          cloud.get_in_port("i_body_2_mod"))
        self.add_coupling(fog2.get_out_port("o_fusion_2_mod"),
                          cloud.get_in_port("i_body_2_mod"))


class Model_04(Coupled):
    """
    Clase que implementa un 2 masas de agua.

    Body1 con UAV11
    Body2 con UAV21 y UAV22
    """

    def __init__(self, name, start, day, log=False):
        """Función de inicialización."""
        super().__init__(name)
        # FOG SEVER 1: Masa de agua 1
        fog1 = FogServer("FogServer1", n_uav=1)
        # UAV 1
        ship11 = FileIn("ShipPos11", "data/B1S1LatLon"+day+".xlsx",
                        start=start, dataid=DataEventId.POS3D, log=log)
        bloom11 = FileIn("DetBlo11", "data/B1S1DetBloom"+day+".xlsx",
                         start=start, dataid=DataEventId.BLOOM, log=log)
        fusion11 = FussionPosBloom("EdgeFussion11")

        # FOG SEVER 2: Masa de agua 2
        fog2 = FogServer("FogServer2", n_uav=2)
        # UAV 21
        ship21 = FileIn("ShipPos21", "data/B2S1LatLon"+day+".xlsx",
                        start=start, dataid=DataEventId.POS3D, log=log)
        bloom21 = FileIn("DetBlo21", "data/B2S1DetBloom"+day+".xlsx",
                         start=start, dataid=DataEventId.BLOOM, log=log)
        fusion21 = FussionPosBloom("EdgeFussion21")
        # UAV 22
        ship22 = FileIn("ShipPos22", "data/B2S2LatLon"+day+".xlsx",
                        start=start, dataid=DataEventId.POS3D, log=log)
        bloom22 = FileIn("DetBlo22", "data/B2S2DetBloom"+day+".xlsx",
                         start=start, dataid=DataEventId.BLOOM, log=log)
        fusion22 = FussionPosBloom("EdgeFussion22")

        # Capa Cloud:
        cloud = Cloud("Cloud", num_water_bodies=2)

        self.add_component(fog1)
        self.add_component(ship11)
        self.add_component(bloom11)
        self.add_component(fusion11)
        self.add_component(fog2)
        self.add_component(ship21)
        self.add_component(bloom21)
        self.add_component(fusion21)
        self.add_component(ship22)
        self.add_component(bloom22)
        self.add_component(fusion22)
        self.add_component(cloud)
        self.add_coupling(ship11.o_out, fusion11.i_Pos)
        self.add_coupling(bloom11.o_out, fusion11.i_Blo)
        self.add_coupling(ship21.o_out, fusion21.i_Pos)
        self.add_coupling(bloom21.o_out, fusion21.i_Blo)
        self.add_coupling(ship22.o_out, fusion22.i_Pos)
        self.add_coupling(bloom22.o_out, fusion22.i_Blo)
        self.add_coupling(fusion11.o_out, fog1.get_in_port("i_fusion_1"))
        self.add_coupling(fusion21.o_out, fog2.get_in_port("i_fusion_1"))
        self.add_coupling(fusion22.o_out, fog2.get_in_port("i_fusion_2"))
        self.add_coupling(fog1.get_out_port("o_fusion_1_raw"),
                          cloud.get_in_port("i_body_1_raw"))
        self.add_coupling(fog1.get_out_port("o_fusion_1_mod"),
                          cloud.get_in_port("i_body_1_mod"))
        self.add_coupling(fog2.get_out_port("o_fusion_1_raw"),
                          cloud.get_in_port("i_body_2_raw"))
        self.add_coupling(fog2.get_out_port("o_fusion_1_mod"),
                          cloud.get_in_port("i_body_2_mod"))
        self.add_coupling(fog2.get_out_port("o_fusion_2_raw"),
                          cloud.get_in_port("i_body_2_raw"))
        self.add_coupling(fog2.get_out_port("o_fusion_2_mod"),
                          cloud.get_in_port("i_body_2_mod"))


class ModelCommander(Coupled):
    """
    Clase que implementa un modelo con dos UAV x 2 masas de agua.

    Además, introduce el Commander, para introducir eventos de simulación.
    """

    def __init__(self, name, commands_path: str, day: str, log=False):
        """Función de inicialización."""
        super().__init__(name)
        # Commander
        commander = Generator("Commander", commands_path)
        # FOG SEVER 1: Masa de agua 1
        fog1 = FogServer("FogServer1", n_uav=2)
        # UAV 11
        ship11 = FileIn("ShipPos11", "data/LatLon"+day+".xlsx",
                        dataid=DataEventId.POS3D, log=log)
        bloom11 = FileIn("DetBlo11", "data/DetBloom"+day+".xlsx",
                         dataid=DataEventId.BLOOM, log=log)
        fusion11 = FussionPosBloom("EdgeFussion11")
        # UAV 12
        ship12 = FileIn("ShipPos12", "data/LatLon"+day+".xlsx",
                        dataid=DataEventId.POS3D, log=log)
        bloom12 = FileIn("DetBlo12", "data/DetBloom"+day+".xlsx",
                         dataid=DataEventId.BLOOM, log=log)
        fusion12 = FussionPosBloom("EdgeFussion12")
        # FOG SEVER 2: Masa de agua 2
        fog2 = FogServer("FogServer2", n_uav=2)
        # UAV 21
        ship21 = FileIn("ShipPos21", "data/LatLon"+day+".xlsx",
                        dataid=DataEventId.POS3D, log=log)
        bloom21 = FileIn("DetBlo21", "data/DetBloom"+day+".xlsx",
                         dataid=DataEventId.BLOOM, log=log)
        fusion21 = FussionPosBloom("EdgeFussion21")
        # UAV 22
        ship22 = FileIn("ShipPos22", "data/LatLon"+day+".xlsx",
                        dataid=DataEventId.POS3D, log=log)
        bloom22 = FileIn("DetBlo22", "data/DetBloom"+day+".xlsx",
                         dataid=DataEventId.BLOOM, log=log)
        fusion22 = FussionPosBloom("EdgeFussion22")
        # Capa Cloud:
        cloud = Cloud("Cloud", num_water_bodies=2)
        self.add_component(commander)
        self.add_component(fog1)
        self.add_component(ship11)
        self.add_component(bloom11)
        self.add_component(fusion11)
        self.add_component(ship12)
        self.add_component(bloom12)
        self.add_component(fusion12)
        self.add_component(fog2)
        self.add_component(ship21)
        self.add_component(bloom21)
        self.add_component(fusion21)
        self.add_component(ship22)
        self.add_component(bloom22)
        self.add_component(fusion22)
        self.add_component(cloud)
        self.add_coupling(commander.o_cmd, ship11.i_cmd)
        self.add_coupling(commander.o_cmd, bloom11.i_cmd)
        self.add_coupling(commander.o_cmd, ship12.i_cmd)
        self.add_coupling(commander.o_cmd, bloom12.i_cmd)
        self.add_coupling(commander.o_cmd, ship21.i_cmd)
        self.add_coupling(commander.o_cmd, bloom21.i_cmd)
        self.add_coupling(commander.o_cmd, ship22.i_cmd)
        self.add_coupling(commander.o_cmd, bloom22.i_cmd)
        self.add_coupling(commander.o_cmd, fog1.i_cmd)
        self.add_coupling(commander.o_cmd, fog2.i_cmd)
        self.add_coupling(ship11.o_out, fusion11.i_Pos)
        self.add_coupling(bloom11.o_out, fusion11.i_Blo)
        self.add_coupling(ship12.o_out, fusion12.i_Pos)
        self.add_coupling(bloom12.o_out, fusion12.i_Blo)
        self.add_coupling(fusion11.o_out, fog1.get_in_port("i_fusion_1"))
        self.add_coupling(fusion12.o_out, fog1.get_in_port("i_fusion_2"))
        self.add_coupling(fog1.get_out_port("o_fusion_1_raw"),
                          cloud.get_in_port("i_body_1_raw"))
        self.add_coupling(fog1.get_out_port("o_fusion_2_raw"),
                          cloud.get_in_port("i_body_1_raw"))
        self.add_coupling(fog1.get_out_port("o_fusion_1_mod"),
                          cloud.get_in_port("i_body_1_mod"))
        self.add_coupling(fog1.get_out_port("o_fusion_2_mod"),
                          cloud.get_in_port("i_body_1_mod"))
        self.add_coupling(ship21.o_out, fusion21.i_Pos)
        self.add_coupling(bloom21.o_out, fusion21.i_Blo)
        self.add_coupling(ship22.o_out, fusion22.i_Pos)
        self.add_coupling(bloom22.o_out, fusion22.i_Blo)
        self.add_coupling(fusion21.o_out, fog2.get_in_port("i_fusion_1"))
        self.add_coupling(fusion22.o_out, fog2.get_in_port("i_fusion_2"))
        self.add_coupling(fog2.get_out_port("o_fusion_1_raw"),
                          cloud.get_in_port("i_body_2_raw"))
        self.add_coupling(fog2.get_out_port("o_fusion_2_raw"),
                          cloud.get_in_port("i_body_2_raw"))
        self.add_coupling(fog2.get_out_port("o_fusion_1_mod"),
                          cloud.get_in_port("i_body_2_mod"))
        self.add_coupling(fog2.get_out_port("o_fusion_2_mod"),
                          cloud.get_in_port("i_body_2_mod"))


class ModelOutliers(Coupled):
    """Clase que implementa un modelo con dos UAV x 2 masas de agua."""

    def __init__(self, name: str, commands_path: str, day: str, log=False):
        """Función de inicialización."""
        super().__init__(name)
        # Commander
        commander = Generator("Commander", commands_path)
        # FOG SEVER 1: Masa de agua 1
        # UAV 11
        ship11 = FileIn("ShipPos11", "data/LatLon"+day+".xlsx", dataid=DataEventId.POS3D, log=log)
        bloom11 = FileIn("DetBlo11", "data/DetBloom"+day+".xlsx", dataid=DataEventId.BLOOM, log=log)
        fusion11 = FussionPosBloom("EdgeFussion11")
        # UAV 12
        ship12 = FileIn("ShipPos12", "data/LatLon"+day+".xlsx", dataid=DataEventId.POS3D, log=log)
        bloom12 = FileIn("DetBlo12", "data/DetBloom"+day+".xlsx", dataid=DataEventId.BLOOM, log=log)
        fusion12 = FussionPosBloom("EdgeFussion12")
        fog1 = FogServer("FogServer1", [fusion11.name, fusion12.name], [FussionPosBloom.data_id.value, FussionPosBloom.data_id.value])
        # FOG SEVER 2: Masa de agua 2
        # UAV 21
        ship21 = FileIn("ShipPos21", "data/LatLon"+day+".xlsx", dataid=DataEventId.POS3D, log=log)
        bloom21 = FileIn("DetBlo21", "data/DetBloom"+day+".xlsx", dataid=DataEventId.BLOOM, log=log)
        fusion21 = FussionPosBloom("EdgeFussion21")
        # UAV 22
        ship22 = FileIn("ShipPos22", "data/LatLon"+day+".xlsx", dataid=DataEventId.POS3D, log=log)
        bloom22 = FileIn("DetBlo22", "data/DetBloom"+day+".xlsx", dataid=DataEventId.BLOOM, log=log)
        fusion22 = FussionPosBloom("EdgeFussion22")
        fog2 = FogServer("FogServer2", [fusion21.name, fusion22.name], [FussionPosBloom.data_id.value, FussionPosBloom.data_id.value])
        # Capa Cloud:
        cloud = Cloud("Cloud", [DataEventId.POSBLOOM.name])
        self.add_component(commander)
        self.add_component(fog1)
        self.add_component(ship11)
        self.add_component(bloom11)
        self.add_component(fusion11)
        self.add_component(ship12)
        self.add_component(bloom12)
        self.add_component(fusion12)
        self.add_component(fog2)
        self.add_component(ship21)
        self.add_component(bloom21)
        self.add_component(fusion21)
        self.add_component(ship22)
        self.add_component(bloom22)
        self.add_component(fusion22)
        self.add_component(cloud)
        self.add_coupling(commander.o_cmd, ship11.i_cmd)
        self.add_coupling(commander.o_cmd, bloom11.i_cmd)
        self.add_coupling(commander.o_cmd, ship12.i_cmd)
        self.add_coupling(commander.o_cmd, bloom12.i_cmd)
        self.add_coupling(commander.o_cmd, ship21.i_cmd)
        self.add_coupling(commander.o_cmd, bloom21.i_cmd)
        self.add_coupling(commander.o_cmd, ship22.i_cmd)
        self.add_coupling(commander.o_cmd, bloom22.i_cmd)
        self.add_coupling(commander.o_cmd, fog1.i_cmd)
        self.add_coupling(commander.o_cmd, fog2.i_cmd)
        self.add_coupling(ship11.o_out, fusion11.i_Pos)
        self.add_coupling(bloom11.o_out, fusion11.i_Blo)
        self.add_coupling(ship12.o_out, fusion12.i_Pos)
        self.add_coupling(bloom12.o_out, fusion12.i_Blo)
        self.add_coupling(fusion11.o_out, fog1.get_in_port("i_" + fusion11.name))
        self.add_coupling(fusion12.o_out, fog1.get_in_port("i_" + fusion12.name))
        self.add_coupling(fog1.get_out_port("o_" + fusion11.name + "_raw"), cloud.get_in_port("i_" + DataEventId.POSBLOOM.name + "_raw"))
        self.add_coupling(fog1.get_out_port("o_" + fusion12.name + "_raw"), cloud.get_in_port("i_" + DataEventId.POSBLOOM.name + "_raw"))
        self.add_coupling(fog1.get_out_port("o_" + fusion11.name + "_mod"), cloud.get_in_port("i_" + DataEventId.POSBLOOM.name + "_mod"))
        self.add_coupling(fog1.get_out_port("o_" + fusion12.name + "_mod"), cloud.get_in_port("i_" + DataEventId.POSBLOOM.name + "_mod"))
        self.add_coupling(ship21.o_out, fusion21.i_Pos)
        self.add_coupling(bloom21.o_out, fusion21.i_Blo)
        self.add_coupling(ship22.o_out, fusion22.i_Pos)
        self.add_coupling(bloom22.o_out, fusion22.i_Blo)
        self.add_coupling(fusion21.o_out, fog2.get_in_port("i_" + fusion21.name))
        self.add_coupling(fusion22.o_out, fog2.get_in_port("i_" + fusion22.name))
        self.add_coupling(fog2.get_out_port("o_" + fusion21.name + "_raw"), cloud.get_in_port("i_" + DataEventId.POSBLOOM.name + "_raw"))
        self.add_coupling(fog2.get_out_port("o_" + fusion22.name + "_raw"), cloud.get_in_port("i_" + DataEventId.POSBLOOM.name + "_raw"))
        self.add_coupling(fog2.get_out_port("o_" + fusion21.name + "_mod"), cloud.get_in_port("i_" + DataEventId.POSBLOOM.name + "_mod"))
        self.add_coupling(fog2.get_out_port("o_" + fusion22.name + "_mod"), cloud.get_in_port("i_" + DataEventId.POSBLOOM.name + "_mod"))


class ModelJournal(Coupled):
    """Clase que implementa un modelo de la pila IoT como entidad virtual."""

    def __init__(self, name: str, commands_path: str, simbody: SimBody5, log=False):
        """Función de inicialización."""
        super().__init__(name)
        # Simulation file
        generator = Generator("Commander", commands_path)
        # FOG SEVER 1: Masa de agua 1
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
        sensor_n = SimSensor5("SimSenN", simbody, sensor_info_n, log=log)
        sensor_o = SimSensor5("SimSenO", simbody, sensor_info_o, log=log)
        sensor_a = SimSensor5("SimSenA", simbody, sensor_info_a, log=log)
        sensor_t = SimSensor5("SimSenT", simbody, sensor_info_t, log=log)
        sensor_u = SimSensor5("SimSenU", simbody, sensor_info_u, log=log)
        sensor_v = SimSensor5("SimSenV", simbody, sensor_info_v, log=log)
        sensor_s = SimSensor5("SimSenS", simbody, sensor_info_s, log=log)
        sensor_x = SimSensor5("SimSenX", simbody, sensor_info_x, log=log)
        sensor_y = SimSensor5("SimSenY", simbody, sensor_info_y, log=log)
        thing_names = [sensor_n.name, sensor_o.name, sensor_a.name, sensor_t.name, sensor_u.name,
                       sensor_v.name, sensor_s.name, sensor_x.name, sensor_y.name]
        thing_event_ids = [sensor_info_n.id.value, sensor_info_o.id.value, sensor_info_a.id.value,
                           sensor_info_t.id.value, sensor_info_u.id.value, sensor_info_v.id.value,
                           sensor_info_s.id.value, sensor_info_x.id.value, sensor_info_y.id.value]

        # TODO: Complete the FogServer definition
        fog = FogServer("FogServer", thing_names, thing_event_ids)
        # Capa Cloud:
        # cloud = Cloud("Cloud", [SensorEventId.POSBLOOM.name])
        # Components:
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
        self.add_component(fog)
        # Coupling relations:
        self.add_coupling(generator.o_cmd, ask_sensor_n.i_cmd)
        self.add_coupling(generator.o_cmd, ask_sensor_o.i_cmd)
        self.add_coupling(generator.o_cmd, ask_sensor_a.i_cmd)
        self.add_coupling(generator.o_cmd, ask_sensor_t.i_cmd)
        self.add_coupling(generator.o_cmd, ask_sensor_u.i_cmd)
        self.add_coupling(generator.o_cmd, ask_sensor_v.i_cmd)
        self.add_coupling(generator.o_cmd, ask_sensor_s.i_cmd)
        self.add_coupling(generator.o_cmd, ask_sensor_x.i_cmd)
        self.add_coupling(generator.o_cmd, ask_sensor_y.i_cmd)
        self.add_coupling(generator.o_cmd, fog.i_cmd)
        self.add_coupling(ask_sensor_n.o_out, sensor_n.i_in)
        self.add_coupling(ask_sensor_o.o_out, sensor_o.i_in)
        self.add_coupling(ask_sensor_a.o_out, sensor_a.i_in)
        self.add_coupling(ask_sensor_t.o_out, sensor_t.i_in)
        self.add_coupling(ask_sensor_u.o_out, sensor_u.i_in)
        self.add_coupling(ask_sensor_v.o_out, sensor_v.i_in)
        self.add_coupling(ask_sensor_s.o_out, sensor_s.i_in)
        self.add_coupling(ask_sensor_x.o_out, sensor_x.i_in)
        self.add_coupling(ask_sensor_y.o_out, sensor_y.i_in)
        self.add_coupling(sensor_n.o_out, fog.get_in_port("i_" + sensor_n.name))
        self.add_coupling(sensor_o.o_out, fog.get_in_port("i_" + sensor_o.name))
        self.add_coupling(sensor_a.o_out, fog.get_in_port("i_" + sensor_a.name))
        self.add_coupling(sensor_t.o_out, fog.get_in_port("i_" + sensor_t.name))
        self.add_coupling(sensor_u.o_out, fog.get_in_port("i_" + sensor_u.name))
        self.add_coupling(sensor_v.o_out, fog.get_in_port("i_" + sensor_v.name))
        self.add_coupling(sensor_s.o_out, fog.get_in_port("i_" + sensor_s.name))
        self.add_coupling(sensor_x.o_out, fog.get_in_port("i_" + sensor_x.name))
        self.add_coupling(sensor_y.o_out, fog.get_in_port("i_" + sensor_y.name))
        ## self.add_component(cloud)
        ## self.add_coupling(fog1.get_out_port("o_" + fusion11.name + "_raw"), cloud.get_in_port("i_" + DataEventId.POSBLOOM.name + "_raw"))
        ## self.add_coupling(fog1.get_out_port("o_" + fusion12.name + "_raw"), cloud.get_in_port("i_" + DataEventId.POSBLOOM.name + "_raw"))
        ## self.add_coupling(fog1.get_out_port("o_" + fusion11.name + "_mod"), cloud.get_in_port("i_" + DataEventId.POSBLOOM.name + "_mod"))
        ## self.add_coupling(fog1.get_out_port("o_" + fusion12.name + "_mod"), cloud.get_in_port("i_" + DataEventId.POSBLOOM.name + "_mod"))
        ## self.add_coupling(fog2.get_out_port("o_" + fusion22.name + "_mod"), cloud.get_in_port("i_" + DataEventId.POSBLOOM.name + "_mod"))


class ModelJournal_V2(Coupled):
    """Clase que implementa un modelo de la pila IoT como entidad virtual."""
    
    def __init__(self, name: str, commands_path: str, simbody: SimBody5, log=False):
        """Función de inicialización."""
        super().__init__(name)
        # Simulation file
        generator = Generator("Commander", commands_path)

        # FOG SEVER 1: Masa de agua 1
        ''' #ELIMINAMOS EL FILEASKVAR 
        '''
        sensor_info_n = SensorInfo(id=SensorEventId.NOX, description="Nitrogen sensor (mg/L)", delay=6, max=0.5, min=0.0, precision=0.1, noisebias=0.01, noisesigma=0.001)
        sensor_info_o = SensorInfo(id=SensorEventId.DOX, description="Oxigen sensor (mg/L)", delay=5, max=30.0, min=0.0, precision=1.0, noisebias=1.0, noisesigma=0.1)
        sensor_info_a = SensorInfo(id=SensorEventId.ALG, description="Algae detector (mg/L)", delay=7, max=15.0, min=0.0, precision=1.0, noisebias=1.0, noisesigma=0.1)
        sensor_info_t = SensorInfo(id=SensorEventId.WTE, description="Water temperature sensor (ºC)", delay=4, max=30, min=0, precision=0.1, noisebias=0.01, noisesigma=0.1)
        sensor_info_u = SensorInfo(id=SensorEventId.WFU, description="East water flow (m/s)", delay=4, max=0.1, min=-0.1, precision=0.01, noisebias=0.001, noisesigma=0.001)
        sensor_info_v = SensorInfo(id=SensorEventId.WFV, description="Nord water flow (m/s)", delay=4, max=0.1, min=-0.1, precision=0.01, noisebias=0.001, noisesigma=0.001)
        sensor_info_s = SensorInfo(id=SensorEventId.SUN, description="Sun radiation (n.u.)", delay=2, max=1.0, min=0, precision=0.01, noisebias=0.001, noisesigma=0.001)
        sensor_info_x = SensorInfo(id=SensorEventId.WFX, description="East wind flow (m/s)", delay=3, max=0.1, min=-0.1, precision=0.01, noisebias=0.001, noisesigma=0.001)
        sensor_info_y = SensorInfo(id=SensorEventId.WFY, description="Nord wind flow (m/s)", delay=3, max=0.1, min=-0.1, precision=0.01, noisebias=0.001, noisesigma=0.001)
        sensor_n = SimSensor6("SimSenN", simbody, sensor_info_n, log=log)
        sensor_o = SimSensor6("SimSenO", simbody, sensor_info_o, log=log)
        sensor_a = SimSensor6("SimSenA", simbody, sensor_info_a, log=log)
        sensor_t = SimSensor6("SimSenT", simbody, sensor_info_t, log=log)
        sensor_u = SimSensor6("SimSenU", simbody, sensor_info_u, log=log)
        sensor_v = SimSensor6("SimSenV", simbody, sensor_info_v, log=log)
        sensor_s = SimSensor6("SimSenS", simbody, sensor_info_s, log=log)
        sensor_x = SimSensor6("SimSenX", simbody, sensor_info_x, log=log)
        sensor_y = SimSensor6("SimSenY", simbody, sensor_info_y, log=log)

        thing_names = [sensor_n.name, sensor_o.name, sensor_a.name, sensor_t.name, sensor_u.name,
                       sensor_v.name, sensor_s.name, sensor_x.name, sensor_y.name]
        thing_event_ids = [sensor_info_n.id.value, sensor_info_o.id.value, sensor_info_a.id.value,
                           sensor_info_t.id.value, sensor_info_u.id.value, sensor_info_v.id.value,
                           sensor_info_s.id.value, sensor_info_x.id.value, sensor_info_y.id.value]

                           
        # Complete the USV definition (simbody to get the Sensor files)     
        # INCLUIR EL BODYSIM COMO PARÁMETRO DE ENTRADA PARA CALCULAR LAS PERTURBACIONES
        usv1 = USV_Simple("USV_1",'./dataedge/', simbody, thing_names, thing_event_ids, delay=0)
        
        # TODO: Complete the FogServer definition
        fog = FogServer("FogServer", usv1, thing_names, thing_event_ids)
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
        self.add_coupling(usv1.o_sensor, sensor_s.i_in)
        self.add_coupling(usv1.o_sensor, sensor_x.i_in)
        self.add_coupling(usv1.o_sensor, sensor_y.i_in)
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


def test_01():
    """Comprobamos el funcionamiento de alguno de los modelos."""
    day = "20210801"
    start_dt = dt.datetime(2021, 8, 1, 0, 0, 0)
    end_dt = dt.datetime(2021, 8, 2, 0, 0, 0)
    sim_seconds = (end_dt-start_dt).total_seconds()
    coupled = Model_01("day_" + day, start=start_dt, day=day, log=False)
    coord = Coordinator(coupled)
    coord.initialize()
    coord.simulate_time(sim_seconds)
    coord.exit()


def test_02():
    """Comprobamos el funcionamiento de alguno de los modelos."""
    day = "20210801"
    start_dt = dt.datetime(2021, 8, 1, 0, 0, 0)
    end_dt = dt.datetime(2021, 8, 2, 0, 0, 0)
    sim_seconds = (end_dt-start_dt).total_seconds()
    coupled = Model_02("day_" + day, start=start_dt, day=day, log=False)
    coord = Coordinator(coupled)
    coord.initialize()
    coord.simulate_time(sim_seconds)
    coord.exit()


def test_03():
    """Comprobamos el funcionamiento de alguno de los modelos."""
    day = "20210801"
    start_dt = dt.datetime(2021, 8, 1, 0, 0, 0)
    end_dt = dt.datetime(2021, 8, 2, 0, 0, 0)
    sim_seconds = (end_dt-start_dt).total_seconds()
    coupled = Model_03("day_" + day, start=start_dt, day=day, log=False)
    coord = Coordinator(coupled)
    coord.initialize()
    coord.simulate_time(sim_seconds)
    coord.exit()


def test_04():
    """Comprobamos el funcionamiento de alguno de los modelos."""
    day = "20210801"
    start_dt = dt.datetime(2021, 8, 1, 0, 0, 0)
    end_dt = dt.datetime(2021, 8, 2, 0, 0, 0)
    sim_seconds = (end_dt-start_dt).total_seconds()
    coupled = Model_04("day_" + day, start=start_dt, day=day, log=False)
    coord = Coordinator(coupled)
    coord.initialize()
    coord.simulate_time(sim_seconds)
    coord.exit()


def test_commander():
    """Comprobamos el funcionamiento de alguno de los modelos."""
    day = "20210801"
    coupled = ModelCommander("day_" + day, 'data/simulation-example.txt',
                             day=day, log=False)
    coord = Coordinator(coupled)
    coord.initialize()
    coord.simulate()
    coord.exit()


def test_outliers():
    """Comprobamos el funcionamiento de los outliers."""
    day = "20210801"
    coupled = ModelOutliers("day_" + day, 'data/simulation-example.txt', day=day, log=False)
    coord = Coordinator(coupled)
    coord.initialize()
    coord.simulate()
    coord.exit()


def test_journal():
    """Comprobamos el modelo para el journal."""
    bodyfile: str = './dataedge/Washington-1m-2008-09_UGRID.nc'
    simbody: SimBody5 = SimBody5('SimWater', bodyfile)
    coupled = ModelJournal("ModelJournal", 'data/simulation-journal.txt', simbody, log=False)
    coord = Coordinator(coupled)
    coord.initialize()
    coord.simulate()
    coord.exit()

def test_journal_Giordy():
    """Comprobamos el modelo para el journal."""
    bodyfile: str = './dataedge/Washington-1m-2008-09_UGRID.nc'
    simbody: SimBody5 = SimBody5('SimWater', bodyfile)
    coupled = ModelJournal_V2("ModelJournal", 'data/simulation-journal-Giordy.txt', simbody, log=False)
    coord = Coordinator(coupled)
    coord.initialize()
    coord.simulate()
    coord.exit()
