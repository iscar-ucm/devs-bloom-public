%Genera Datos Posición
clear all
%tini=datetime(2021,8,1,0,0,0)
%tfin=datetime(2021,8,10,24,0,0)
tini=datetime(2021,8,1,0,0,0)
tfin=datetime(2021,8,3,0,0,0)
%DateTime=[tini:hours(1):tfin]'
DateTime=[tini:minutes(5):tfin]'
%Paso de Horas
%PosX=10*sin(2*pi*(DateTime.Hour)/6)+10*DateTime.Day;
%PosY=10*cos(2*pi*(DateTime.Hour)/6);
%PosZ=-10+10*sin(2*pi*(DateTime.Hour)/6);
%Paso de Minutos
PosX=-10*cos(2*pi*(DateTime.Minute)/60)+0.1*DateTime.Hour*60+0.1*DateTime.Day*24*60;
PosY=20*sin(2*pi*(DateTime.Minute)/60);
PosZ=-10+10*sin(2*pi*(DateTime.Minute)/60);

Posicion=table(DateTime,PosX,PosY,PosZ)
plot3(Posicion.PosX,Posicion.PosY,Posicion.PosZ);
axis equal
writetable(Posicion,'PosBarco2d.xlsx')