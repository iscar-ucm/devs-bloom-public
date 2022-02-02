"""Clase que implementa algunos prototipos de modelos."""

from xdevs.models import Coupled
from edge.file import FileIn, FussionPosBloom
from fog.fog import FogServer
from util.event import DataEventId


class Model_01(Coupled):
    """Clase que implementa un modelo simple a tres días."""

    def __init__(self, name, start, day, log=False):
        """Función de inicialización."""
        super().__init__(name)
        file_ship = FileIn("ShipPos", "../data/LatLon"+day+".xlsx",
                           start=start, dataid=DataEventId.POS3D, log=log)
        file_bloom = FileIn("DetBlo", "../data/DetBloom"+day+".xlsx",
                            start=start, dataid=DataEventId.BLOOM, log=log)
        # Fusiona Posición del barco con medida de Sensor de Bloom
        edge_fusion = FussionPosBloom("EdgeFussion")
        # Capa Fog:
        fog_server = FogServer("FogServer", 100)
        self.add_component(file_ship)
        self.add_component(file_bloom)
        self.add_component(edge_fusion)
        self.add_component(fog_server)
        self.add_coupling(file_ship.o_out, edge_fusion.i_Pos)
        self.add_coupling(file_bloom.o_out, edge_fusion.i_Blo)
        self.add_coupling(edge_fusion.o_out, fog_server.i_fusion_01)
