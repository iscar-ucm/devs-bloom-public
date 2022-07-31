%  close all
%   file3='Atazar1.png'
%   img=imread(file3);
%   imshow(img)
%   hold on;

file1='B2S2DetBloom20210802.xlsx'
file2='B2S2LatLon20210802.xlsx'
DetBloom=readtable(file1);
LatLon=readtable(file2);
x=LatLon.Lat;
y=LatLon.Lon;
DB=boolean(DetBloom.DetBb);
X=LatLon.Lat(DB);
Y=LatLon.Lon(DB);
%Xom=200;
%Yom=300;
Xom=100;
Yom=200;
%Yom=400;
Xm=X+Xom;
Ym=Y+Yom;
plot(Xm,Ym,'dg','LineWidth',10);hold on
RX=min(x+Xom);
RY=min(y+Yom);
RW=max(x+Xom)-min(x+Xom);
RH=max(y+Yom)-min(y+Yom);
rectangle('Position',[RX RY RW RH],'EdgeColor','r')
title('Body2, USV1 & USV2 fusion at 2nd day ')
xlabel('X(Lon)')
ylabel('Y(Lat)')