%  close all
subplot(1,2,1)
   file3='Valmayor3.png'
   img=imread(file3);
   imshow(img)
   hold on;

file1='B1S1DetBloom20210803.xlsx'
file2='B1S1LatLon20210803.xlsx'
DetBloom=readtable(file1);
LatLon=readtable(file2);
DB=boolean(DetBloom.DetBb)
X=LatLon.Lat(DB)
Y=LatLon.Lon(DB)
Xom=200;
Yom=300;
%Xom=100;
%Yom=200;
Xm=X+Xom;
Ym=Y+Yom;
plot(Xm,Ym,'sc');hold on
RX=min(x+Xom);
RY=min(y+Yom);
RW=max(x+Xom)-min(x+Xom);
RH=max(y+Yom)-min(y+Yom);
rectangle('Position',[RX RY RW RH],'EdgeColor','r')
title('Body2 Evolution');%title('Body1, USV1, 3 days evolution')
%xlabel('X(Lon)')
%ylabel('Y(Lat)')