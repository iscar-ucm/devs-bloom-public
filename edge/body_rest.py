from flask import Flask, request, jsonify
from flask.json import JSONEncoder
from edge.body import SimBody4 as Sensor
from datetime import datetime, timedelta
import numpy as np

class CustomJSONEncoder(JSONEncoder):

    def default(self, obj):
      try:
        if isinstance(obj, np.generic):
          return obj.item()
      except TypeError:
          pass
      return JSONEncoder.default(self, obj)


app = Flask(__name__)
app.json_encoder = CustomJSONEncoder

def create_sensor(bodyfile: str, vars:list=('WQ_O','WQ_N','WQ_ALG')):
  print(f'Loading BodySim file: {bodyfile}')
  return Sensor('SimWater', bodyfile, vars)

simbody = create_sensor('/POOL/data/devs-bloom/dataedge/Washington-1d-2008-09-12_compr.nc')
# start_dt = datetime(2008,9,12,5,28,49)

@app.route('/', methods=['POST'])
def sensor():
  try:
    data = request.get_json()
    measure = [data['payload'][k] for k in ('var', 'time', 'lat', 'lon', 'depth')]
    measure[1] = datetime.fromtimestamp(measure[1])
    measurement = data['payload'].copy()
    measurement.update({
      measure[0]: [v for v in simbody.readvar(*measure)],
    })
    result = jsonify(measurement)
  except Exception as e:
    print(e)
    result = jsonify(error='invalid params')
  return result


def test():
  simbody = create_sensor('/POOL/data/devs-bloom/dataedge/Washington-1d-2008-09-12_compr.nc')
  print('Solicitando Datos')
  O2 = simbody.readvar("WQ_O", 50, 47.6, -122.27, 5)
  print("WQ_O: ", O2)
  N = simbody.readvar("WQ_N", 50, 47.6, -122.27, 5)
  print("WQ_N: ", N)
  print('Fin')

  
if __name__ == "__main__":
  test()

# To run as flask application:
#   FLASK_APP=body_rest flask run
