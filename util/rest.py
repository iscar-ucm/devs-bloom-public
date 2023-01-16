import requests
from datetime import datetime
from time import perf_counter 

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

  t_start = perf_counter()    
  measurement = body.readvar('WQ_O', datetime(2008, 9, 12, 5, 28, 49).timestamp(), 47.64, -122.250, 2)
  t_stop = perf_counter()
  print(f'The simulation ran in {t_stop-t_start} seconds')
  print(measurement)
