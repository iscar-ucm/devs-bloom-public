%Genera Datos Posición
clear all
%tini=datetime(2021,8,1,0,0,0)
%tfin=datetime(2021,8,10,24,0,0)
tini=datetime(2021,8,1,0,0,0)
tfin=datetime(2021,8,2,0,0,0)
%DateTime=[tini:hours(1):tfin]'
DateTime=[tini:minutes(1):tfin]'
%Paso de Horas
%PosX=10*sin(2*pi*(DateTime.Hour)/6)+10*DateTime.Day;
%PosY=10*cos(2*pi*(DateTime.Hour)/6);
%PosZ=-10+10*sin(2*pi*(DateTime.Hour)/6);
%Paso de Minutos
PosX=0.2*(DateTime.Minute+DateTime.Hour*60+(DateTime.Day-DateTime(1).Day)*24*60);
PosY=50*sin(2*pi*(DateTime.Minute)/60);
PosZ=-10+10*sin(2*pi*(DateTime.Minute)/10);

Pos=[PosX,PosY,PosZ];
Lat=PosX;
Lon=PosY;
Depth=PosZ;
PosBloom=[200,0,-5];        %Posición del Bloom
for i=1:size(Pos,1)
    DisBloom(i)=norm(Pos(i,:)-PosBloom);      %Distancia al Bloom
    if DisBloom(i)<30
        DetB(i)=min(20/DisBloom(i),1);        %Detector de Bloom continuo 
        DetBb(i)=1;                           %Detector de Bloom booleano
    else
        DetB(i)=0;
        DetBb(i)=0;
    end
end
DetB=DetB';
DetBb=DetBb';
DetBloom=table(DateTime,Depth,DetB,DetBb)
Posicion=table(DateTime,PosX,PosY,PosZ)
LatLon=table(DateTime,Lat,Lon)

%figure,plot(DetBloom.DateTime,DetBloom.DetB)
%subplot(3,1,3),plot(Posicion.PosX,DisBloom);title('Detección Bloom X-Detector')
writetable(DetBloom,'DetBloom2d.xlsx')
writetable(LatLon,'LatLon2d.xlsx')


figure(1)
subplot(3,1,1),plot(Posicion.PosX,Posicion.PosY);title('Planta X-Y (LatLon')
subplot(3,1,2),plot(Posicion.PosX,Posicion.PosZ);title('Alzado X-Z')
subplot(3,1,3),plot(Posicion.PosX,DetBloom.DetB,Posicion.PosX,DetBloom.DetBb);
title('Detección Bloom X-Detector')

figure(2);
b=boolean(DetBb);
plot3(PosX(b),PosY(b),PosZ(b),'-o')
axis([min(PosX) max(PosX) min(PosY) max(PosY) min(PosZ) max(PosZ)])
grid on
xlabel('X')
ylabel('Y')
zlabel('Z')


figure(3)
F=scatteredInterpolant(PosX,PosY,DetB);
x=[min(PosX):max(PosX)];y=[-40:40];z=[-30:0];
[X,Y]=meshgrid(x,y);
mesh(X,Y,F(X,Y));title('Planta XY')
xlabel('X')
ylabel('Y')
zlabel('DetBloom')


 