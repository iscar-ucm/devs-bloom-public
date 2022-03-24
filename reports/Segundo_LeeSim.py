import pandas as pd
import matplotlib.pyplot as plt
plt.close("all")
fig, axes=plt.subplots(nrows=4,ncols=1)

P3=pd.read_csv("./data/N1T2R1-1_IoT.csv")  #Lectura de resultados excel
P3.plot(ax=axes[0],x='time (s)',y=' x (m)',title='',marker='.',xlabel='t(s)',ylabel='x(m)')
P3.plot(ax=axes[1],x='time (s)',y=' y (m)',title='',marker='.',xlabel='t(s)',ylabel='y(m)')
P3.plot(ax=axes[2],x='time (s)',y=' z (m)',title='',marker='.',xlabel='t(s)',ylabel='z(m)')

P3.plot(ax=axes[3],x='time (s)',y=' rho',title='Bloom Detection',marker='.',xlabel='t(s)',ylabel='Rho')
#plt.show()


PB=P3[P3[' rho']>0.001]
x3=PB[' x (m)']
y3=PB[' y (m)']
z3=PB[' z (m)']

fig1 = plt.figure()
#ax1 = fig.gca(projection='3d')
plt.rcParams["figure.figsize"] = (10,10)

ax1=plt.subplot(221)
ax1.plot(x3,z3,color='b',marker='o')
ax1.set_title('PerfilXZ (Lat-Depth)')
ax1.set_xlabel('X Lat')
ax1.set_ylabel('Z Depth')
ax2=plt.subplot(222)
ax2.plot(y3,z3,color='b',marker='o')
ax2.set_title('AlzadoYZ (Lat-Depth)')
ax2.set_xlabel('Y Lon')
ax2.set_ylabel('Z Depth')
ax3=plt.subplot(223)
ax3.plot(x3,y3,color='b',marker='o')
ax3.set_title('PlantaXY (Lat-Lon)')
ax3.set_xlabel('X Lat')
ax3.set_ylabel('Y Lon')

#plt.rcParams["figure.figsize"] = (10,30)
ax4=plt.subplot(224,projection='3d')
ax4.scatter(x3, y3, z3, color='b')
ax4.bar3d(x3, y3, 0, 1, 1, z3, color='b')
#ax1.bar(x,y, zs=-50, zdir='z',data=z)
ax4.set_xlabel('X Lat')
ax4.set_ylabel('Y Lon')
ax4.set_zlabel('Z Depth')
plt.xlim([-100,300])
plt.ylim([-700,100])
ax4.view_init(elev=10., azim=-80)
plt.show()