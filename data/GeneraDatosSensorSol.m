% Generar datos sintéticos de posición del Barco
clear all
tini=datetime(2021,8,1,0,0,0)
tfin=datetime(2021,8,3,0,0,0)
DateTime=[tini:minutes(5):tfin]'
%tini=datetime(2021,8,1,0,0,0)
%tfin=datetime(2021,8,10,24,0,0)
%DateTime=[tini:hours(1):tfin]'
%tstamp = datetime(2021,8,1,0:23,0,0)';
HoraMax=14;
Sun=0.4+cos(2*pi*(DateTime.Hour+DateTime.Minute/60+HoraMax)/24);
Sun=max(0,Sun);
Value=Sun/max(Sun);
Sensor=table(DateTime,Sun);
plot(Sensor.DateTime,Sensor.Sun)
writetable(Sensor,'SensorSol1.xlsx')