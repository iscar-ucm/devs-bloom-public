% Caraga datos de Simulación
%Salida=readtable('SensorTemperatura1.xlsx')
Salida=readtable('Salida3.xlsx')
figure(1);stairs(Salida.DateTime,Salida.Value)
figure(2);plot3(Salida.PosX,Salida.PosY,Salida.PosZ)
tini=datetime(Salida.DateTime(1))
tfin=datetime(Salida.DateTime(end))
step=Salida.DateTime(2)-Salida.DateTime(1)
