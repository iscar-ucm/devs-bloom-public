#This file Generates a File to ask sensors telemetries
from datetime import datetime, timedelta
from numpy import linspace

filename='.\dataedge\Sensor2008_WQ_ALG.xlsx'
Var='WQ_N'
Var='WQ_O'
Var='WQ_ALG'

inicio = datetime(2008,9,12,0,29,0)
fin   = datetime(2008,9,13,0,29,0)
#inicio = datetime(2008,9,12,0,30,30)
#fin   = datetime(2008,9,13,0,29,30)

delta= 60 #seconds
diferencia = fin - inicio
ts=diferencia.total_seconds()
r=range(0,round(ts)+1,delta)
DateTime = [inicio + timedelta(seconds=s) for s in r] 
n=len(DateTime)
#print(DateTime)

ILat=47.5
ELat=47.73
lat=linspace(ILat,ELat,n)
Lat=lat.tolist()
#print(Lat)

ILon=-122.3
ELon=-122.231
lon=linspace(ILon,ELon,n)
Lon=lon.tolist()
#print(Lon)

IDep=0
EDep=-15
dep=linspace(IDep,EDep,n)
Depth=dep.tolist()
#print(Depth)

Sensor = [Var for x in r] 

import pandas as pd
tabla=pd.DataFrame({'DateTime':DateTime,'Lat':Lat,'Lon':Lon,'Depth':Depth,'Sensor':Sensor},index=None)
print(tabla)
tabla.to_excel(filename,index=False)  #Escritura de resultados a excel


#Representación
PB=pd.read_excel(filename)  #Lectura de resultados excel
import matplotlib.pyplot as plt
t=PB['DateTime']
x3=PB['Lon']
y3=PB['Lat']
z3=PB['Depth']

fig1 = plt.figure()
#ax1 = fig.gca(projection='3d')
#plt.rcParams["figure.figsize"] = (10,10)

ax1=plt.subplot(221)
ax1.plot(x3,z3,color='b',marker='o')
ax1.set_title('PerfilXZ (Lat-Depth)')
ax1.set_xlabel('Lon(º)')
ax1.set_ylabel('Depth(m))')
ax2=plt.subplot(222)
ax2.plot(y3,z3,color='b',marker='o')
ax2.set_title('AlzadoYZ (Lat-Depth)')
ax2.set_xlabel('Lat(º)')
ax2.set_ylabel('Depth(m)')
ax3=plt.subplot(223)
ax3.plot(x3,y3,color='b',marker='o')
ax3.set_title('PlantaXY (Lat-Lon)')
ax3.set_xlabel('Lon(º)')
ax3.set_ylabel('Lat(º)')
ax3=plt.subplot(224)
ax3.plot(t,z3,color='b',marker='o')
ax3.set_title('Time-Depth')
ax3.set_xlabel('Time')
ax3.set_ylabel('Depth(m)')

plt.show()