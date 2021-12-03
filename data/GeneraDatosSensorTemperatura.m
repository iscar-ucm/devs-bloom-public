% Generar datos sintéticos de un sensor de temperatura.
clear all
tini=datetime(2021,8,1,0,0,0)
tfin=datetime(2021,8,10,24,0,0)
DateTime=[tini:hours(1):tfin]';
%tstamp = datetime(2021,8,1,0:23,0,0)';
medT=20;
ranT=10;
maxT=16;
enfT=-0.01; %Enfriamiento por cada muestra
temperature=medT+ranT*cos(2*pi*(DateTime.Hour-maxT)/24);
temperature=temperature+enfT*[1:length(temperature)]';
Value=temperature+rand(size(temperature));
Sensor=table(DateTime,Value);
plot(Sensor.DateTime,Sensor.Value)
writetable(Sensor,'SensorTemperatura1.xlsx')