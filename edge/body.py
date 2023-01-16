import datetime as dt
import netCDF4
import numpy as np
from scipy.interpolate import griddata
from scipy.spatial import KDTree
#from math import floor

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
  It allow to read simulated data at t,lat,lon,depth.
  Sigma is emulated in the initialization, due tu NetHFC4 file errors'''
    
  def __init__(self, name, bodyfile, vars):       
    self.name=name
    simbody = netCDF4.Dataset(bodyfile)    
    self.lat = np.array(simbody['lat'])
    self.lon = np.array(simbody['lon'])
    llc=np.c_[self.lon.ravel(), self.lat.ravel()]
    self.lonlattree = KDTree(llc)
    self.bottom = np.array(simbody['Bottom'])
    self.sigma = np.array(simbody['sigma'])
    self.wsel= np.array(simbody['WSEL'])
    self.layers= np.array(simbody['layers'])
    self.time= np.array(simbody['time'])
    #Repair sigma
    l=len(self.sigma[1])
    for i in range(l):
      self.sigma[:,i,:]=(i-l)/l 
    self.depth=np.zeros(l)
    #Get Ini-End DateTime
    refstr=simbody['time'].units
    refdate=dt.datetime.fromisoformat(refstr[-10:])
    self.dtini=refdate+dt.timedelta(seconds=self.time[0]*24*3600)
    self.dtend=refdate+dt.timedelta(seconds=self.time[-1]*24*3600)
    print('BodySim IniDateTime:',self.dtini)
    print('BodySim EndDateTime:',self.dtend)
    print('BodySim Loading...')
    self.time=(self.time-self.time[0])*24*3600             
    self.vars={}
    for var in vars:
      tempvar=np.array(simbody[var])
      fillvalue=simbody[var].FillValue
      tempvar[np.logical_or(tempvar == fillvalue,tempvar == 0.0)]=np.nan 
      if var=='WQ_ALG': 
        self.vars[var]=myvar=tempvar[:,:,:,:,0]
      else:
        self.vars[var]=tempvar
    
    simbody.close()

  def readvar(self,myvars,mytime,mylat,mylon,mydepth):
    #  To read a value of myvar
    #myvars='WQ_O'variable del fichero.nc
    #mytime= time of simulation (seconds from 0)
    #mylat= latitude (deg)
    #mylon= longitude (deg)
    #mydepth= depth(-meters)
    mytime=mytime-self.dtini
    mytime=mytime.total_seconds()
    t=round(np.argmin(np.absolute(self.time-mytime)))   #Nearest time index
    if np.absolute(self.time[t]-mytime)>31:             #Time resolution <30s
      return np.nan,np.nan,np.nan,np.nan,np.nan
    dd,ii=self.lonlattree.query([mylon,mylat])
    i,j=np.unravel_index(ii,(len(self.bottom),len(self.bottom[0])))
    if dd<0.003:                                        #Spatial relosution < 0.003deg
      #myl=round(mydepth)        #Como sigma está mal utilizo la capa como profundidad
      #if myl>=0 & myl<=54: 
      if mydepth<=self.wsel[t,i,j] - self.bottom[i,j]: #Limit the bottom
        for ly in range(len(self.depth)):
          self.depth[ly]=-self.sigma[i,ly,j]*(self.wsel[t,i,j] - self.bottom[i,j])
        l =round(np.argmin(np.absolute(self.depth-mydepth),0),0)  #Nearest Depth Layer index
        value=self.vars[myvars][t,i,j,l]
        if type(value)==np.ndarray: 
          value=value[0]
      else: 
        l=np.nan
        value=np.nan
    else:
      value=np.nan
      i=np.nan
      j=np.nan
      l=np.nan
    return value,t,i,j,l


class SimBody4:
  '''Body Simulated in NetHFC4 format.
  It allow to read simulated data at t,lat,lon,depth.
  Sigma is emulated in the initialization, due tu NetHFC4 file errors'''
    
  def __init__(self, name, bodyfile, vars):       
    self.name=name
    #print('BodySim Loading...')
    self.simbody = netCDF4.Dataset(bodyfile)    
    self.lat = np.array(self.simbody['lat'])
    self.lon = np.array(self.simbody['lon'])
    llc=np.c_[self.lon.ravel(), self.lat.ravel()]
    self.lonlattree = KDTree(llc)
    self.bottom = np.array(self.simbody['Bottom'])
    self.sigma = np.array(self.simbody['sigma'])
    #Repair sigma
    l=len(self.sigma[1])
    for i in range(l):
      self.sigma[:,i,:]=(i-l)/l 
    self.depth=np.zeros(l)
    self.wsel= np.array(self.simbody['WSEL'])
    self.layers= np.array(self.simbody['layers'])
    self.time= np.array(self.simbody['time'])
    #Get Ini-End DateTime
    refstr=self.simbody['time'].units
    refdate=dt.datetime.fromisoformat(refstr[-10:])
    self.dtini=refdate+dt.timedelta(seconds=self.time[0]*24*3600)
    self.dtend=refdate+dt.timedelta(seconds=self.time[-1]*24*3600)
    print('BodySim IniDateTime:',self.dtini)
    print('BodySim EndDateTime:',self.dtend)
    self.time=(self.time-self.time[0])*24*3600      #Time in seconds from 0.       
    
  def __exit__(self):       
    self.simbody.close()

  def readvar(self,myvar,mytime,mylat,mylon,mydepth):
    #  To read a value of myvar
    #myvar='WQ_O'variable del fichero.nc
    #mytime= DateTime 
    #mylat= latitude (deg)
    #mylon= longitude (deg)
    #mydepth= depth(+meters)
    value=np.nan
    t=np.nan
    i=np.nan
    j=np.nan
    l=np.nan
    mytime=mytime-self.dtini
    mytime=mytime.total_seconds()
    t=round(np.argmin(np.absolute(self.time-mytime)))   #Nearest time index
    if np.absolute(self.time[t]-mytime)<=60:            #Time resolution <=60s
      dd,ii=self.lonlattree.query([mylon,mylat])
      if dd<0.003:                                      #Spatial relosution < 0.003deg
        i,j=np.unravel_index(ii,(len(self.bottom),len(self.bottom[0])))
        depthrange=self.wsel[t,i,j] - self.bottom[i,j]
        if mydepth<=depthrange:            
          for ly in range(len(self.depth)):
            self.depth[ly]=-self.sigma[i,ly,j]*depthrange
          l =round(np.argmin(np.absolute(self.depth-mydepth),0),0)  #Nearest Depth Layer index
          value=float(self.simbody[myvar][t,i,j,l].data)
          if value==self.simbody[myvar].FillValue: value=np.nan
          if value==0.0: value=np.nan
        else: 
          l=np.nan
      else:
        i=np.nan
        j=np.nan
    else: 
      t=np.nan
    return value,t,i,j,l


class SimBody5:
    '''Body Simulated in NetHFC4 with new UGRID format.
    It allow to read simulated data at t,lat,lon,depth.
    t are seconds from init of BodySim'''

    def __init__(self, name, bodyfile,log=False):       
        #Load the file and prpair the time vector [0..end] seconds 
        self.name=name
        self.simbody   = netCDF4.Dataset(bodyfile)    
        self.latc      = np.array(self.simbody['latc'])         # float32 latc(CELL)
        self.lonc      = np.array(self.simbody['lonc'])         # float32 lonc(CELL)
        self.lat       = np.array(self.simbody['lat'])          # float32 lat(CELL)
        self.lon       = np.array(self.simbody['lon'])          # float32 lon(CELL)
        self.nv        = np.array(self.simbody['nv'])           # float32 nv(CELL)
        self.time      = np.array(self.simbody['time'])         # float64 time(TIME), Dias desde 20050101
        self.time      = np.moveaxis(self.time, 0 ,-1)
        self.belv      = np.array(self.simbody['BELV'])         # float32 BELV(TIME, CELL), 
        self.wsel      = np.array(self.simbody['WSEL'])         # float32 WSEL(TIME, CELL), 
        self.layers    = np.array(self.simbody['layers'])       # int8 layers(CELL)
        self.temp      = np.array(self.simbody['temperature'])
        self.rssbc     = np.array(self.simbody['RSSBC'])
        self.cuv       = np.array(self.simbody['CUV'])
        self.blayer    = np.array(self.simbody['bottom_layer']) # int8 bottom_layer(CELL)
        self.sigma     = np.array(self.simbody['sigma'])        # float32 sigma(CELL, KC)
        self.sun       = np.array(self.simbody['sun'])
        self.u         = np.array(self.simbody['U'])            # Velocidad del agua este(m/s)
        self.v         = np.array(self.simbody['V'])            # Velocidad del agua norte(m/s) 
        self.w         = np.array(self.simbody['W'])            # Velocidad del agua arriba(m/s)        
        #Prepare KDtree
        llc = np.c_[self.lonc.ravel(), self.latc.ravel()] 
        self.lonlattree = KDTree(llc)
        #Copute Ini/End DateTime
        refstr=self.simbody['time'].units
        refdate=dt.datetime.fromisoformat(refstr[-19:])
        self.dtini=refdate+dt.timedelta(seconds=self.time[0]*24*3600)
        self.dtend=refdate+dt.timedelta(seconds=self.time[-1]*24*3600)
        self.T=(self.time[1]-self.time[0])*24*3600      #Period
        self.time=(self.time-self.time[0])*24*3600      #Time in seconds from [0..end]. 
        if log==True:
            print('BodySim IniDateTime:',self.dtini)
            print('BodySim EndDateTime:',self.dtend)
            print('BodySim DeltaTime(min)',self.T/60)
      
    def __exit__(self):       
        self.simbody.close()

    def readvar(self,myvar,mytime,mylat=np.nan,mylon=np.nan,mydepth=np.nan):
        #To read a value of myvar
        # myvar='DOX'variable del fichero.nc
        # mytime= seconds from 0    (Now it is not DateTime to allow Jonsify) 
        # mylat= latitude (deg)
        # mylon= longitude (deg)
        # mydepth= depth(+meters)
        #The next variables are readed by readvar function
        # float32 sun(TIME), Synthetic Sun (generado por mí)
        # float32 temperature(TIME, KC, CELL)   Water temperature (ºC)
        # float32 ALG(TIME, NALG, KC, CELL), 2 Algae (Tan solo leemos las 2ª Alga)
        # float32 wind_x(TIME, CELL), Velocidad viento este (m/s)
        # float32 wind_y(TIME, CELL), Velocidad viento norte (m/s)
        # float32 NOX Nitratos (mg/L)
        # float32 DOX Oxigeno disuelto (mg/L)
        # float32 U(TIME, KC, CELL), Velocidad del agua este(m/s)
        # float32 V(TIME, KC, CELL), Velocidad del agua norte(m/s)
        # float32 W(TIME, KC, CELL), Velocidad del agua arriba(m/s)
        # float32 ALG(TIME, NALG, KC, CELL), 2 Algas
        # float32 wind_x(TIME, CELL), Velocidad viento este (m/s)
        # float32 wind_y(TIME, CELL), Velocidad viento norte (m/s)
        # float32 NOX(TIME, KC, CELL), Nitratos orgánicos (mg/L)
        # float32 DOX(TIME, KC, CELL), Oxigeno disuelto (mg/L)
        # float32 DON(TIME, KC, CELL), Nitrógeno orgánico Disuelto
        # float32 NHX(TIME, KC, CELL), Nitrógeno amoniaco
        # float32 SUU(TIME, KC, CELL), Sodio...
        # float32 SAA(TIME, KC, CELL), Sodio...
        # float32 COD(TIME, KC, CELL), Carbono organico

        value=np.nan
        t=np.nan
        ij=np.nan
        l=np.nan
        mytime=mytime
        t=round(np.argmin(np.absolute(self.time-mytime)))       #Nearest time index
        if np.absolute(self.time[t]-mytime)<=self.T*1.1:        #Time resolution 30m*60s*1.1
            if np.isnan(mylat):
                value=float(self.simbody[myvar][t].data) 
                return value,t,np.nan,np.nan                    #Return Value and time index
            else:
                dd,ij=self.lonlattree.query([mylon,mylat])
                if dd<0.003:                                    #Spatial resolution < 0.003deg
                    #i,j=np.unravel_index(ii,(len(self.bottom),len(self.bottom[0])))
                    if np.isnan(mydepth):
                        value=float(self.simbody[myvar][t,ij].data)    
                        return value,t,ij,np.nan
                    else:
                        depthrange=self.wsel[t,ij] - self.belv[ij][0]
                        if mydepth<=depthrange:                     #Depth over Bottom? 
                            depth=np.nan*np.array(self.sigma[ij])
                            for ly in range(self.blayer[ij]-1,self.blayer[ij]+self.layers[ij]-1):
                                #depth[ly]=self.sigma[ij,ly]*depthrange
                                depth[ly]= depthrange-self.sigma[ij,ly]*depthrange
                            l =round(np.nanargmin(np.absolute(depth-mydepth),0),0)  #Nearest Depth Layer index
                            if myvar=='ALG':
                                value=float(self.simbody[myvar][t,1,l,ij].data)     #Read the second algae
                            else:
                                value=float(self.simbody[myvar][t,l,ij].data)       #Read the value              
                            if value==self.simbody[myvar]._FillValue: value=np.nan
                            #if value==0.0: value=np.nan
                            return value,t,ij,l             #Value of var, time index, lonlat index,layer index
                        else: 
                            return np.nan,t,ij,np.nan
                else:
                    return np.nan,t,np.nan,np.nan
        else: 
            return np.nan,np.nan,np.nan,np.nan


if __name__ == "__main__":
    print('BodySim Loading')
    bodyfile='.\dataedge\Washington-1m-2008-09_UGRID.nc' 
    simbody=SimBody5('NewSimBody',bodyfile)
    print('Data Req.')
    myt  = dt.datetime(2008,8,24,12,0,0)-simbody.dtini
    myts = myt.total_seconds()
    var='DOX'
    value=simbody.readvar(var,myts,47.64,-122.250,2.0)
    print(var,value)
    var='NOX'
    value=simbody.readvar(var,myts,47.64,-122.250,2.0)
    print(var,value)
    var='ALG'
    value=simbody.readvar(var,myts,47.64,-122.250,2.0)
    print(var,value)
    var='U'
    value=simbody.readvar(var,myts,47.64,-122.250,2.0)
    print(var,value)
    var='sun'
    value=simbody.readvar(var,myts)
    print(var,value)
    var='wind_x'
    value=simbody.readvar(var,myts,47.64,-122.250)
    print(var,value)
    print('End')





'''
if __name__ == "__main__":
  
  print('BodySim Loading')
  bodyfile='./body/Washington-1d-2008-09-12_compr.nc'
  #bodyfile= 'D:/Unidades compartidas/ia-ges-bloom-cm/IoT/Washington-1d-2008-09-12_compr.nc'
  vars=('WQ_O','WQ_N','WQ_ALG')

  #simbody=SimBody3('SimWater',bodyfile,vars)
  simbody=SimBody4('SimWater',bodyfile,vars)
  print('Data Req.')
  myt  = dt.datetime(2008,9,12,5,28,49)
  var='WQ_O'
  value=simbody.readvar(var,myt,47.64,-122.250,2)
  print(value)
  var='WQ_N'
  value=simbody.readvar(var,myt,47.64,-122.250,2)
  print(value)
  var='WQ_ALG'
  value=simbody.readvar(var,myt,47.64,-122.250,2)
  print(value)
  print('End')

'''


'''
if __name__ == "__main__":
  
  print('BodySim Loading')
  bodyfile='./body/Washington-1d-2008-09-12_compr.nc'
  #bodyfile= 'D:/Unidades compartidas/ia-ges-bloom-cm/IoT/Washington-1d-2008-09-12_compr.nc'
  vars=('WQ_O','WQ_N','WQ_ALG')

  #simbody=SimBody3('SimWater',bodyfile,vars)
  simbody=SimBody4('SimWater',bodyfile,vars)
  print('Data Req.')
  myt  = dt.datetime(2008,9,12,5,28,49)
  var='WQ_O'
  value=simbody.readvar(var,myt,47.64,-122.250,2)
  print(value)
  var='WQ_N'
  value=simbody.readvar(var,myt,47.64,-122.250,2)
  print(value)
  var='WQ_ALG'
  value=simbody.readvar(var,myt,47.64,-122.250,2)
  print(value)
  print('End')
'''

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