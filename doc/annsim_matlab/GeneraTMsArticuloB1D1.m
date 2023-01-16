%Genera Datos Posición
clear all
file1='B1DetBloom20210801.xlsx'
file2='B1LatLon20210801.xlsx'
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
PosY=100*sin(2*pi*(DateTime.Minute)/60);
PosZ=-10+10*sin(2*pi*(DateTime.Minute)/10);

Pos=[PosX,PosY,PosZ];
Lat=PosX;
Lon=PosY;
Depth=PosZ;
PosBloom=[100,0];        %Posición del Bloom
DepthBloom=-15
SizeBloom=20
for i=1:size(Pos,1)
    LayBloom(i)=norm(Depth(i)-DepthBloom);       %Capa de Bloom
    DisBloom(i)=norm([Lat(i),Lon(i)]-PosBloom);      %Distancia al Bloom
    if (DisBloom(i)<SizeBloom)&(LayBloom(i)<1)
        DetB(i)=min(SizeBloom/DisBloom(i),1);        %Detector de Bloom continuo 
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


%OutLayers
DetBloom.DetB(1:10:end)=NaN;
DetBloom.DetBb(1:10:end)=NaN;
LatLon.Lat(1:10:end)=NaN;
LatLon.Lon(1:10:end)=NaN;

%figure,plot(DetBloom.DateTime,DetBloom.DetB)
%subplot(3,1,3),plot(Posicion.PosX,DisBloom);title('Detección Bloom X-Detector')
writetable(DetBloom,file1)
writetable(LatLon,file2)


figure(1)
subplot(3,1,1),plot(Posicion.PosX,Posicion.PosY);title('Plan Path');xlabel('X(m)');ylabel('Y(m))');
subplot(3,1,2),plot(Posicion.PosX,Posicion.PosZ);title('Cross Path');xlabel('X(m)');ylabel('Z(m))');
subplot(3,1,3),plot(Posicion.PosX,DetBloom.DetB,Posicion.PosX,DetBloom.DetBb);
title('Cross Detection');xlabel('X(m)');ylabel('BloomDet(Bool)');


figure(2);
b=boolean(DetBb);
plot3(PosX(b),PosY(b),PosZ(b),'-o')
axis([min(PosX) max(PosX) min(PosY) max(PosY) min(PosZ) max(PosZ)])
grid on
xlabel('X(m)')
ylabel('Y(m)')
zlabel('Z(m)')


figure(3)
F=scatteredInterpolant(PosX,PosY,DetB);
x=[min(PosX):max(PosX)];y=[min(PosY):max(PosY)];z=[-30:0];
[X,Y]=meshgrid(x,y);
contour(X,Y,100*F(X,Y));title('Bloom Detection Plan ')
colorbar
axis equal
xlabel('X(m)')
ylabel('Y(m)')
zlabel('DetBloom')


 