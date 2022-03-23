import datetime as dt
from re import S

import netCDF4
import numpy as np
from scipy.interpolate import griddata



#from site import addsitedir   #Para añadir la ruta del proyecto
#addsitedir("C:/Users/segu2/OneDrive - Universidad Complutense de Madrid (UCM)/devs-bloom") 

class SimBody:
  '''Body Simulated in NetHFC4 format.
    It allow to read simulated data'''
    
  def __init__(self, name, bodyfile, vars):       
    simbody = netCDF4.Dataset(bodyfile)    # Let's open the file or not
    #   Not all variables have the same dimensions, see file info for details
    lat = np.array(simbody['lat'])
    inan= (lat != simbody['lat'].FillValue)
    latflat=lat[inan]
    lon = np.array(simbody['lon'])
    lonflat=lon[lon != simbody['lon'].FillValue]
    
    #POR HACER para que encaje con el tiempo de nuestras simulaciones
    #BodyRef=dt.datetime(2005,1,1,0,0,0)
    time= np.array(simbody['time'])
    #timeflat= time[time != simbody['time'].FillValue]
    time=time-time[0]

    
    #self.layers= np.array(simbody['layers'])
    #self.layers[self.layers == simbody['layers'].FillValue] = np.NaN
    #self.vars=dict({'latfalt':latflat,'lonfalt':lonflat,'inan':inan})

    self.vars={'time':time,'latflat':latflat,'lonflat':lonflat,'inan':inan}
    for var in vars:
      tempvar=np.array(simbody[var])
      tempvar[tempvar == simbody[var].FillValue]= np.NaN # Remove fill values
      self.vars[var]= tempvar
    simbody.close()


  def readvar(self,myvar,mytime,mylat,mylon,mylayer):
    #  To read a value of myvar
        
    vartl=self.vars[myvar][mytime,:,:,mylayer]
    #latflat = self.vars['lat'][np.logical_not(np.isnan(self.vars['lat']))]
    #lonflat = self.lon[np.logical_not(np.isnan(self.lat))]
    varflat=vartl[self.vars['inan']]
    varint=griddata((self.vars['lonflat'], self.vars['latflat']), varflat,(mylon,mylat), method='linear')
    value=varint.tolist()
    return value
    #self.datetime=msg.timestamp+dt.timedelta(seconds=60)
    #self.data = {self.id.value: varint}
 
 

if __name__ == "__main__":
  
  print('Cargando BodySim')
  bodyfile='./data/Washington-1d-2008-09-12_compr.nc'
  vars=('WQ_O','WQ_N')
  simbody=SimBody('SimWater',bodyfile,vars)
  print('Solicitando Datos')
  O2=simbody.readvar("WQ_O",50,47.6,-122.27,5)
  print("WQ_O: ",O2)
  N=simbody.readvar("WQ_N",50,47.6,-122.27,5)
  print("WQ_N: ",N)
  print('Fin')
  