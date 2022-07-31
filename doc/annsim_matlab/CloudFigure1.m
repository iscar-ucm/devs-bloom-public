close all
subplot(1,2,2)
file3='Atazar1.png'
img=imread(file3);
imshow(img)
hold on;

file1='B2S2DetBloom20210801.xlsx'
file2='B2S2LatLon20210801.xlsx'
DetBloom=readtable(file1);
LatLon=readtable(file2);
DB=boolean(DetBloom.DetBb)
X=LatLon.Lat(DB)
Y=LatLon.Lon(DB)
%Xom=100;
%Yom=400;
Xom=100;
Yom=200;
Xm=X+Xom;
Ym=Y+Yom;
plot(Xm,Ym,'wy');hold on
RX=min(x+Xom);
RY=min(y+Yom);
RW=max(x+Xom)-min(x+Xom);
RH=max(y+Yom)-min(y+Yom);
rectangle('Position',[RX RY RW RH],'EdgeColor','r')
title('Body2 Evolution');%, USV1 & USV2, 3 days evolution')
%xlabel('X(Lon)')
%ylabel('Y(Lat)')