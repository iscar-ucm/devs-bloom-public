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

Pos=[PosX,PosY,PosZ];
PosBloom=[200,0,-5];        %Posición del Bloom
for i=1:size(Pos,1)
    DisBloom(i)=norm(Pos(i,:)-PosBloom);%Distancia al Bloom
    if DisBloom(i)<30
        DetB(i)=min(20/DisBloom(i),1);        %Detector de Bloom 
        DetBb(i)=1;
    else
        DetB(i)=0;
        DetBb(i)=0;
    end
end
Posicion=table(DateTime,PosX,PosY,PosZ)
DetB=DetB';
DetBb=DetBb';
DetBloom=table(DateTime,DetB,DetBb)
subplot(3,1,1),plot(Posicion.PosX,Posicion.PosY);title('Planta X-Y')
subplot(3,1,2),plot(Posicion.PosX,Posicion.PosZ);title('Alzado X-Z')
subplot(3,1,3),plot(Posicion.PosX,DetBloom.DetB,Posicion.PosX,DetBloom.DetBb);title('Detección Bloom X-Detector')
%figure,plot(DetBloom.DateTime,DetBloom.DetB)
%subplot(3,1,3),plot(Posicion.PosX,DisBloom);title('Detección Bloom X-Detector')
writetable(DetBloom,'DetBloom2d.xlsx')