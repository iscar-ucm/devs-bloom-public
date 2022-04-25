import datetime as dt
import netCDF4
import numpy as np
from scipy.interpolate import griddata

#from site import addsitedir   #Para añadir la ruta del proyecto
#addsitedir("C:/Users/segu2/OneDrive - Universidad Complutense de Madrid (UCM)/devs-bloom") 

class SimBody:
  '''Body Simulated in NetHFC4 format.
    It allow to read simulated data at a layer'''
    
  def __init__(self, name, bodyfile, vars):       
    simbody = netCDF4.Dataset(bodyfile)    # Let's open the file or not
    #   Not all variables have the same dimensions, see file info for details
    lat = np.array(simbody['lat'])
    inan= (lat != simbody['lat'].FillValue)
    latflat=lat[inan]   #Lo utilizaré para limpiar las variables
    lon = np.array(simbody['lon'])
    lonflat=lon[lon != simbody['lon'].FillValue]
    
    #POR HACER para que encaje con el tiempo de nuestras simulaciones
    #BodyRef=dt.datetime(2005,1,1,0,0,0)
    time= np.array(simbody['time'])
    #timeflat= time[time != simbody['time'].FillValue]
    time=time-time[0]   #Tiempo en días desde 0

    
    #self.layers= np.array(simbody['layers'])
    #self.layers[self.layers == simbody['layers'].FillValue] = np.NaN
    #self.vars=dict({'latfalt':latflat,'lonfalt':lonflat,'inan':inan})

    self.vars={'time':time,'latflat':latflat,'lonflat':lonflat,'inan':inan}
    for var in vars:
      tempvar=np.array(simbody[var])
      #tempvar[tempvar == simbody[var].FillValue]= np.NaN # Remove fill values
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
    
 
 
class SimBody2:
  '''Body Simulated in NetHFC4 format.
    It allow to read simulated data at t,lat,lon,depth'''
    
  def __init__(self, name, bodyfile, vars):       
    simbody = netCDF4.Dataset(bodyfile)    # Let's open the file or not
    #   Not all variables have the same dimensions, see file info for details
    # Read variables
    #   Not all variables have the same dimensions, see file info for details
    lat = np.array(simbody['lat'])
    lon = np.array(simbody['lon'])
    bottom = np.array(simbody['Bottom'])
    sigma = np.array(simbody['sigma'])
    wsel= np.array(simbody['WSEL'])
    layers= np.array(simbody['layers'])
    time= np.array(simbody['time'])
    time=(time-time[0])*24*3600      #REINICIO EL TIEMPO A 0 y en segundos
    inan=lat == simbody['lat'].FillValue
    lat[inan] = np.nan
    lon[inan] = np.nan
    bottom[inan]=np.nan
    layers[inan]= np.nan
    sigma[sigma>1]=np.nan
    sigma[sigma<0]=np.nan
    wsel[wsel== simbody['WSEL'].FillValue]=np.nan
    depth=np.zeros(len(sigma[1]))
    self.vars={'time':time,'lat':lat,'lon':lon,'bottom':bottom,'sigma':sigma,'wsel':wsel,'layers':layers,'depth':depth}
    for var in vars:
      tempvar=np.array(simbody[var])
      tempvar[tempvar == simbody[var].FillValue]= np.nan # Remove fill values
      tempvar[tempvar == 0] =np.nan                      # Remove zeroes
      self.vars[var]= tempvar
    simbody.close()

  def readvar(self,myvar,mytime,mylat,mylon,mydepth):
    #  To read a value of myvar
    #myvar="WQ_O" Cabecera de variable en fichero.nc
    #mytime= time of simulation (seconds)
    #mylat= latitude (deg)
    #mylon= longitude (deg)
    #mydepth= depth(-meters)
    t=round(np.nanargmin(np.absolute(self.vars['time']-mytime)))
    rj=len(self.vars['bottom'][1])
    ind =round(np.nanargmin(np.sqrt((self.vars['lat']-mylat)*(self.vars['lat']-mylat)+(self.vars['lon']-mylon)*(self.vars['lon']-mylon))))
    i=round(ind/rj) 
    j=ind-i*rj
    nl=len(self.vars['depth'])
    for l in range(nl):
      self.vars['sigma'][i,l,j]=l/55.0     #SIGMA ESTA MAL, LA RECONSTRUIMOS en [0,1].
      self.vars['depth'][l]=-self.vars['sigma'][i,l,j]*(self.vars['wsel'][t,i,j] - self.vars['bottom'][i,j])
    myl =round(np.argmin(np.absolute(self.vars['depth']-mydepth),0),0)
    value=self.vars[myvar][t,i,j,myl]
    return value

class SimBody3:
  '''Body Simulated in NetHFC4 format.
  It allow to read simulated data at t,lat,lon,depth'''
    
  def __init__(self, name, bodyfile, vars):       
    self.name=name
    simbody = netCDF4.Dataset(bodyfile)    
    lat = np.array(simbody['lat'])
    lon = np.array(simbody['lon'])
    bottom = np.array(simbody['Bottom'])
    sigma = np.array(simbody['sigma'])
    wsel= np.array(simbody['WSEL'])
    layers= np.array(simbody['layers'])
    time= np.array(simbody['time'])

    #Conseguir DateTime inicial y final
    refstr=simbody['time'].units
    refdate=dt.datetime.fromisoformat(refstr[-10:])
    dtini=refdate+dt.timedelta(seconds=time[0]*24*3600)
    dtend=refdate+dt.timedelta(seconds=time[-1]*24*3600)
    print('BodySim IniDateTime:',dtini)
    print('BodySim EndDateTime:',dtend)
    #Inicialializamos el tiempo desde 0 en segundos
    time=(time-time[0])*24*3600             

    #Eliminamos FillValue y Ceros
    inan=lat == simbody['lat'].FillValue
    lat[inan] = np.nan
    lon[inan] = np.nan
    bottom[inan]=np.nan
    layers[inan]= np.nan
    depth=np.zeros(len(sigma[1]))
    wsel[wsel== simbody['WSEL'].FillValue]=np.nan
    sigma[sigma>1]=np.nan
    sigma[sigma<0]=np.nan
    #SIGMA ESTA MAL, LA RECONSTRUIMOS entre [0,1].
    for inds,s in np.ndenumerate(sigma):
      sigma[inds]=inds[1]/55.0     
    depth=np.zeros(len(sigma[1]))
    self.vars={'time':time,'dtini':dtini,'dtend':dtend,'lat':lat,'lon':lon,'bottom':bottom,'sigma':sigma,'wsel':wsel,'layers':layers,'depth':depth}
    for var in vars:
      tempvar=np.array(simbody[var])
      tempvar[tempvar == simbody[var].FillValue]= np.nan # Remove fill values
      tempvar[tempvar == 0] =np.nan                      # Remove zeroes
      self.vars[var]= tempvar
    simbody.close()

  def readvars(self,myvars,mytime,mylat,mylon,mydepth):
    #  To read values of myvars
    #myvars=('WQ_O','WQ_N') Tupla de variables del fichero.nc
    #mytime= time of simulation (seconds from 0)
    #mylat= latitude (deg)
    #mylon= longitude (deg)
    #mydepth= depth(-meters)
    t=round(np.nanargmin(np.absolute(self.vars['time']-mytime)))   #Nearest time index
    rj=len(self.vars['bottom'][1])
    ind =round(np.nanargmin(np.sqrt((self.vars['lat']-mylat)*(self.vars['lat']-mylat)+(self.vars['lon']-mylon)*(self.vars['lon']-mylon))))   #Nearest sqrt lat-lon indices
    i=round(ind/rj) 
    j=ind-i*rj
    nl=len(self.vars['depth'])
    for l in range(nl):
      #self.vars['sigma'][i,l,j]=l/55.0     #SIGMA ESTA MAL, LA RECONSTRUIMOS en [0,1].
      self.vars['depth'][l]=-self.vars['sigma'][i,l,j]*(self.vars['wsel'][t,i,j] - self.vars['bottom'][i,j])
    myl =round(np.argmin(np.absolute(self.vars['depth']-mydepth),0),0)  #Nearest Depth Layer index
    value={}
    for var in myvars:
      value[var]=self.vars[var][t,i,j,myl]
    return value

  def readvar(self,myvars,mytime,mylat,mylon,mydepth):
    #  To read a value of myvar
    #myvars='WQ_O'variable del fichero.nc
    #mytime= time of simulation (seconds from 0)
    #mylat= latitude (deg)
    #mylon= longitude (deg)
    #mydepth= depth(-meters)
    t=round(np.nanargmin(np.absolute(self.vars['time']-mytime)))   #Nearest time index
    rj=len(self.vars['bottom'][1])
    ind =round(np.nanargmin(np.sqrt((self.vars['lat']-mylat)*(self.vars['lat']-mylat)+(self.vars['lon']-mylon)*(self.vars['lon']-mylon))))   #Nearest sqrt lat-lon indices
    i=round(ind/rj) 
    j=ind-i*rj
    nl=len(self.vars['depth'])
    for l in range(nl):
      #self.vars['sigma'][i,l,j]=l/55.0     #SIGMA ESTA MAL, LA RECONSTRUIMOS en [0,1].
      self.vars['depth'][l]=-self.vars['sigma'][i,l,j]*(self.vars['wsel'][t,i,j] - self.vars['bottom'][i,j])
    myl =round(np.argmin(np.absolute(self.vars['depth']-mydepth),0),0)  #Nearest Depth Layer index
    value=self.vars[myvars][t,i,j,myl]
    return value



if __name__ == "__main__":
  
  print('Cargando BodySim')
  bodyfile='./body/Washington-1d-2008-09-12_compr.nc'
  #bodyfile= 'D:/Unidades compartidas/ia-ges-bloom-cm/IoT/Washington-1d-2008-09-12_compr.nc'
  vars=('WQ_O','WQ_N','WQ_ALG')
  simbody=SimBody3('SimWater',bodyfile,vars)
  print('Solicitando Datos')
  values=simbody.readvars(vars,0,47.64,-122.28,-10)
  print(values)
  print('Fin')


'''
if __name__ == "__main__":
  print('Cargando BodySim')
  bodyfile='./body/Washington-1d-2008-09-12_compr.nc'
  #bodyfile= 'D:/Unidades compartidas/ia-ges-bloom-cm/IoT/Washington-1d-2008-09-12_compr.nc'
  vars=('WQ_O','WQ_N')
  simbody=SimBody2('SimWater',bodyfile,vars)
  print('Solicitando Datos')
  O2=simbody.readvar("WQ_O",50,47.64,-122.28,-10)
  print("WQ_O: ",O2)
  N=simbody.readvar("WQ_N",50,47.64,-122.28,-10)
  print("WQ_N: ",N)
  print('Fin')
'''