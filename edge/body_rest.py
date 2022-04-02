from re import S

import netCDF4
import numpy as np
from scipy.interpolate import griddata

from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

class SimBody:
  '''Body Simulated in NetHFC4 format. It allows to read simulated data'''
    
  def __init__(self, name, bodyfile, vars):
    self.name = name
    simbody = netCDF4.Dataset(bodyfile)    # Let's open the file or not
    #   Not all variables have the same dimensions, see file info for details
    lat = np.array(simbody['lat'])
    inan = (lat != simbody['lat'].FillValue)
    latflat = lat[inan]
    lon = np.array(simbody['lon'])
    lonflat = lon[lon != simbody['lon'].FillValue]    
    time = np.array(simbody['time'])
    time = time - time[0]
    self.vars = {
      'time': time,
      'latflat': latflat,
      'lonflat': lonflat,
      'inan': inan
    }
    for var in vars:
      tempvar = np.array(simbody[var])
      tempvar[tempvar == simbody[var].FillValue] = np.NaN # Remove fill values
      self.vars[var] = tempvar
    simbody.close()

  def readvar(self, var, time, lat, lon, layer):
    vartl = self.vars[var][time, :, :, layer]
    varflat = vartl[self.vars['inan']]
    varint = griddata(
      (self.vars['lonflat'], self.vars['latflat']),
      varflat,
      (lon, lat),
      method='linear'
    )
    return varint.tolist()

print('Loading BodySim')
bodyfile = '../data/Washington-1d-2008-09-12_compr.nc'
vars = ('WQ_O','WQ_N')
simbody = SimBody('SimWater', bodyfile, vars)

@app.route('/', methods=['POST'])
def sensor():
  try:
    data = request.get_json()
    measure = [data['payload'][k] for k in ('var', 'time', 'lat', 'lon', 'depth')]
    measurement = data['payload'].copy()
    measurement.update({
      data['payload']['var']: simbody.readvar(*measure)
    })
    result = jsonify(measurement)
  except Exception as e:
    print(e)
    print(measurement)
    result = jsonify(error='invalid params')
  return result


def test():
  print('Cargando BodySim')
  bodyfile = './data/Washington-1d-2008-09-12_compr.nc'
  vars = ('WQ_O','WQ_N')
  simbody = SimBody('SimWater', bodyfile, vars)
  print('Solicitando Datos')
  O2 = simbody.readvar("WQ_O", 50, 47.6, -122.27, 5)
  print("WQ_O: ", O2)
  N = simbody.readvar("WQ_N", 50, 47.6, -122.27, 5)
  print("WQ_N: ", N)
  print('Fin')

  
if __name__ == "__main__":
  test()
  # export FLASK_APP=body_rest
  # flask run

