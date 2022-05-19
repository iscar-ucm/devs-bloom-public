import requests
from datetime import datetime

class RestBody:

  def __init__(self, host: str='http://localhost:5000', file: str=''):
    self.host = host

  def readvar(self, var: str, time: float, lat: float, lon: float, layer: int) -> dict:
    data = {
      'timestamp': time,
      'payload': {
        'var': var,
        'time': time,
        'lat': lat,
        'lon': lon,
        'depth': layer
      }
    }
    return requests.post(self.host, json=data).json()

if __name__ == "__main__":
  body = RestBody(host='http://pc-iscar.dacya.ucm.es:5000', file='Washington....')
  body.readvar('WQ_O', datetime(2008, 9, 12, 5, 28, 49), 47.64, -122.250, 2)
