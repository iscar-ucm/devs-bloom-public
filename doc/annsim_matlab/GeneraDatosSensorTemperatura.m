% Generar datos sintéticos de un sensor de temperatura.
clear all
file='Temperatura1.xlsx'
tini=datetime(2021,8,1,0,0,0)
tfin=datetime(2021,8,3,0,0,0)
DateTime=[tini:minutes(5):tfin]'
%tini=datetime(2021,8,1,0,0,0)
%tfin=datetime(2021,8,10,24,0,0)
%DateTime=[tini:hours(1):tfin]';
%tstamp = datetime(2021,8,1,0:23,0,0)';
medT=20;
ranT=10;
maxT=16;
enfT=-0.0001; %Enfriamiento por cada muestra
Temperature=medT+ranT*cos(2*pi*(DateTime.Hour+DateTime.Minute/60-maxT)/24);
%Temperature=Temperature+enfT*[1:length(Temperature)]';
Temperature=Temperature+rand(size(Temperature))-0.5;
Sensor=table(DateTime,Temperature);
plot(Sensor.DateTime,Sensor.Temperature)
writetable(Sensor,file1)