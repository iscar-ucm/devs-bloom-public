import datetime as dt
import netCDF4
import numpy as np
from scipy.interpolate import griddata
from scipy.spatial import KDTree
#from math import floor

#from site import addsitedir   #Para añadir la ruta del proyecto
#addsitedir("C:/Users/segu2/OneDrive - Universidad Complutense de Madrid (UCM)/devs-bloom") 

class SimBody5:
    '''Body Simulated in NetHFC4 with new UGRID format.
    It allow to read simulated data at t,lat,lon,depth (t are seconds from init of BodySim)
    It returns the value and the index used to find the value on the file'''

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


class SimBody6:
    '''Body Simulated in NetHFC4 with new UGRID format.
    It reads an interpolated data at t,lat,lon,depth (t are seconds from init of BodySim)
    It use the 4 nearest (lat,lon) values to interpolate the returned value'''

    def __init__(self, name, bodyfile,log=False):       
        #Load the file and prepair the time vector [0..end] seconds 
        self.name=name
        self.simbody   = netCDF4.Dataset(bodyfile)    
        self.latc      = np.array(self.simbody['latc'])         # float32 latc(CELL)
        self.lonc      = np.array(self.simbody['lonc'])         # float32 lonc(CELL)
        self.lat       = np.array(self.simbody['lat'])          # float32 lat(CELL)
        self.lon       = np.array(self.simbody['lon'])          # float32 lon(CELL)
        self.nv        = np.array(self.simbody['nv'])           # float32 nv(CELL)
        self.time      = np.array(self.simbody['time'])         # float64 time(TIME), Dias desde 20050101
        #self.time      = np.moveaxis(self.time, 0 ,-1)
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
                dd,ij=self.lonlattree.query([mylon,mylat],4)
                if dd[0]<0.003:                                 #Spatial resolution < 0.003deg
                    #i,j=np.unravel_index(ii,(len(self.bottom),len(self.bottom[0])))
                    if np.isnan(mydepth):
                        value=np.average(self.simbody[myvar][t,ij].data,weights=1/dd)    
                        #value=float(self.simbody[myvar][t,ij].data)    
                        return value,t,ij,np.nan
                    else:
                        depthrange=self.wsel[t,ij[0]] - self.belv[ij[0]][0]
                        #depthrange=self.wsel[t,ij] - self.belv[ij][0]
                        if mydepth<=depthrange:                     #Depth over Bottom? 
                            depth=np.nan*np.array(self.sigma[ij[0]])
                            for ly in range(self.blayer[ij[0]]-1,self.blayer[ij[0]]+self.layers[ij[0]]-1):
                                #depth[ly]=self.sigma[ij,ly]*depthrange
                                depth[ly]= depthrange-self.sigma[ij[0],ly]*depthrange
                            l =round(np.nanargmin(np.absolute(depth-mydepth),0),0)  #Nearest Depth Layer index
                            if myvar=='ALG':
                                value=np.average(self.simbody[myvar][t,1,l,ij].data,weights=1/dd)     #Read the second algae
                                #value=float(self.simbody[myvar][t,1,l,ij].data)     #Read the second algae
                            else:
                                value=np.average(self.simbody[myvar][t,l,ij].data,weights=1/dd)       #Read the value              
                                #value=float(self.simbody[myvar][t,l,ij].data)       #Read the value              
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
    bodyfile='./util/Washington-1m-2008-09_UGRID.nc' 
    simbody5=SimBody5('NewSimBody',bodyfile)
    simbody6=SimBody6('NewSimBody',bodyfile)
    print('Data Req.')
    myt  = dt.datetime(2008,8,24,12,0,0)-simbody5.dtini
    myts = myt.total_seconds()
    var='DOX'
    value=simbody5.readvar(var,myts,47.64,-122.250,2.0)
    print(var,value)
    var='DOX'
    value=simbody6.readvar(var,myts,47.64,-122.250,2.0)
    print(var,value)
    var='NOX'
    value=simbody5.readvar(var,myts,47.64,-122.250,2.0)
    print(var,value)
    var='NOX'
    value=simbody6.readvar(var,myts,47.64,-122.250,2.0)
    print(var,value)
    var='ALG'
    value=simbody5.readvar(var,myts,47.64,-122.250,2.0)
    print(var,value)
    var='ALG'
    value=simbody6.readvar(var,myts,47.64,-122.250,2.0)
    print(var,value)
    var='U'
    value=simbody5.readvar(var,myts,47.64,-122.250,2.0)
    print(var,value)
    var='U'
    value=simbody6.readvar(var,myts,47.64,-122.250,2.0)
    print(var,value)
    var='sun'
    value=simbody5.readvar(var,myts)
    print(var,value)
    var='sun'
    value=simbody6.readvar(var,myts)
    print(var,value)
    var='wind_x'
    value=simbody5.readvar(var,myts,47.64,-122.250)
    print(var,value)
    var='wind_x'
    value=simbody6.readvar(var,myts,47.64,-122.250)
    print(var,value)
    print('End')




