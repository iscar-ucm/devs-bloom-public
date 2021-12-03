% Generar datos sintéticos de posición del Barco
clear all
tini=datetime(2021,8,1,0,0,0)
tfin=datetime(2021,8,10,24,0,0)
DateTime=[tini:hours(1):tfin]'
%tstamp = datetime(2021,8,1,0:23,0,0)';
HoraMax=14;
sol=0.4+cos(2*pi*(DateTime.Hour+HoraMax)/24);
sol=max(0,sol);
Value=sol/max(sol);
Sensor=table(DateTime,Value);
plot(Sensor.DateTime,Sensor.Value)
writetable(Sensor,'SensorSol1.xlsx')