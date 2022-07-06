"""Clase que implementa algunos prototipos de modelos."""

from xdevs.models import Coupled
import datetime as dt
from xdevs.sim import Coordinator
from edge.file import FileIn, FussionPosBloom
from fog.fog import FogServer
from cloud.cloud import Cloud
from util.event import DataEventId
from util.commander import Commander


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
        commander = Commander("Commander", commands_path)
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
        commander = Commander("Commander", commands_path)
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
