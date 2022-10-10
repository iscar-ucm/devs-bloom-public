%% Crea Video
%% Carga Nuevos Datos UGRID
close all
clear
clc

filename = 'Washington-1m-2008-09_UGRID.nc';

ncdisp(filename)
ncinfo = ncinfo(filename);


ncinfo.Variables(14).Attributes(3).Name
ncinfo.Variables(14).Attributes(3).Value


% Indices
tau = 100; % Time index
lyr = 55;  % Layer (top is 55) 
IJ = 798;  % Cell number (near lake center)
IJ = 445;  % Cell number (near outlet center)

% Read data
lonc = ncread(filename,'lonc');
latc = ncread(filename,'latc');
lon = ncread(filename,'lon');
lat = ncread(filename,'lat');
nv = ncread(filename,'nv');
sigma = ncread(filename,'sigma');
BELV = ncread(filename,'BELV');
WSEL = ncread(filename,'WSEL');
temp = ncread(filename,'temperature');
RSSBC = ncread(filename,'RSSBC');
CUV = ncread(filename,'CUV');
bottom_layer = ncread(filename,'bottom_layer');
ALG = ncread(filename,'ALG');
time = ncread(filename,'time');
wind_x=ncread(filename,'wind_x');
wind_y=ncread(filename,'wind_y');
nox=ncread(filename,'NOX');
dox=ncread(filename,'DOX');
u=ncread(filename,'U');           %Velocidad del agua este(m/s)
v=ncread(filename,'V');           %Velocidad del agua norte(m/s)
w=ncread(filename,'W');           %Velocidad del agua arriba(m/s)


inidt=datetime(ncinfo.Variables(14).Attributes(3).Value(end-18:end))
deltat=days(1)
dt=inidt+time*deltat
hours=hour(dt);
sun=max(cos((hours+12)/24*2*pi),0); %Genero el Sol

lonF = lon(nv);
latF = lat(nv);
sigma(sigma == 0) = NaN;
sumRSSBC = sum(RSSBC);
sumRSSBC(sumRSSBC==0) = [];

% Get z and depth
z = BELV(:,1)' + sigma.*(WSEL(:,tau)' - BELV(:,1)');
depth = WSEL(:,tau)' - z;


%% Simula
close all;
clf;

tau=100;
lyr=55;
%Intial State of Bloom
seccion=1:200;
map = [lonc(seccion),latc(seccion)];
ip=10
%ip=2
x0=[0,lonc(ip),latc(ip)]
%x=[1,-122.215,45.501]
x=x0;
f=figure(2);
f.Position(3:4) = [1000 500];
myxlim=[-122.25,-122.2];
myylim=[47.5,47.55];


subplot(2,3,1);
colormap('default')

xlim([0,24])
ylim([0,1])

subplot(2,3,2)
 
xlim(myxlim)
ylim(myylim)
title('Water Speed (m/s)')

subplot(2,3,3)

xlim(myxlim)
ylim(myylim)
title('Wind (m/s)')

subplot(2,3,4);
colormap('default')
c1=colorbar;
caxis([0 10]);
xlabel('Longitude'); 
ylabel('Latitude'); 
c1.Label.String = 'Algae2 (mg/L)';
xlim(myxlim)
ylim(myylim)


subplot(2,3,5)
colormap('default')
c2=colorbar;
c2.Label.String = 'Disolved Oxigen (mg/L)';
caxis([0 25]);
xlabel('Longitude'); 
%ylabel('Latitude'); 
xlim(myxlim)
ylim(myylim)

subplot(2,3,6)
colormap('default')
c3=colorbar;
c3.Label.String = 'Nitrate (mg/L)';
caxis([0 0.2]);
%c3.Label.String = 'Dissolved organic nitrogen (mg/L)';
%caxis([0 5]);
xlabel('Longitude'); 
%ylabel('Latitude'); 
xlim(myxlim)
ylim(myylim)

vtemp=mean(temp(:,lyr,tau),'omitnan');
vhour=0;

% % Open video file
     vid = VideoWriter('video5','MPEG-4');
     vid.Quality = 100;
     open(vid);

for lyr = 55 %1:55
 for tau = 1:length(time)
 %for tau = 100:1:300 
    subplot(2,3,1)
     yyaxis left
     plot(hours,sun,hours(tau),sun(tau),'o');
     ylabel('Sun Radiation (Norm.)')
     ylim([0,1])
     yyaxis right
     me=mean(temp(:,lyr,tau),'omitnan');
     ma=max(temp(:,lyr,tau))-me;
     mi=me-min(temp(:,lyr,tau));
     %plot(vhour,vtemp);hold on;
     plot(vhour,vtemp,'-',vhour(end),vtemp(end),'s');
     %errorbar(hours(tau),vtemp(end),ma,'s'); 
     ylabel('Water Temperature (ºC)')
     xlabel('Hour')
     ylim([19,21])
    subplot(2,3,2)
     quiver(lonc,latc,u(:,lyr,tau)/10,v(:,lyr,tau)/10,0);
     xlim(myxlim)
     ylim(myylim)
     title(['Mean Water Speed (m/s):',num2str(mean(sqrt(u(:,lyr,tau).^2+v(:,lyr,tau).^2),'omitnan'))])    
     ylabel('Water Flow')
    subplot(2,3,3)
     quiver(lonc,latc,wind_x(:,tau)/1000,wind_y(:,tau)/1000,0);
     xlim(myxlim)
     ylim(myylim)
     title(['Mean Wind Speed (m/s):',num2str(mean(sqrt(wind_x(:,tau).^2+wind_y(:,tau).^2)))])
     ylabel('Wind Flow')
    subplot(2,3,4)
     cla
     patch(lonF,latF,ALG(:,lyr,2,tau),'EdgeColor','none'); % Two types of algae
     hold on;
     bt=text(x(2),x(3),num2str(x(1),2));
     [lat,lon] = scircle1(x(3),x(2),0.001*sqrt(x(1)));
     plot(lon,lat,'r')
     hold off;
    subplot(2,3,5)
     patch(lonF,latF,dox(:,lyr,tau),'EdgeColor','none'); % Two types of algae
     title(['DateTime = ', datestr(dt(tau))])
    subplot(2,3,6)
     patch(lonF,latF,nox(:,lyr,tau),'EdgeColor','none'); % Two types of algae
     %patch(lonF,latF,don(:,lyr,tau),'EdgeColor','none'); % Two types of algae
   
    %Initial Bloom
     if (hours(tau)==0) 
         x=x0;
         bloom=false;
         vtemp=[];
         vhour=[];
     end
    %Input of Bloom Model 
     [ip,dist] = dsearchn(map,[x(2),x(3)]);
         
     %ux(1)=nox(ip,lyr,tau)/0.3*dox(ip,lyr,tau)/50+nox(ip,lyr,tau)/0.3*sun(tau);
     %ux(1)=nox(ip,lyr,tau)/0.5*dox(ip,lyr,tau)/20*sun(tau);
     %ux(1)=nox(ip,lyr,tau)/10;
     
     %breath=don(ip,lyr,tau)*dox(ip,lyr,tau);%nox
     %photosynthesis=don(ip,lyr,tau)*sun(tau);%nox
     breath=nox(ip,lyr,tau)*dox(ip,lyr,tau);%nox
     photosynthesis=nox(ip,lyr,tau)*sun(tau);%nox
     kbreath=0.05;%3/50;
     kphoto=5;%3;
     ux(1)=kbreath*breath+kphoto*photosynthesis;
     ux(2)=u(ip,lyr,tau);
     ux(3)=v(ip,lyr,tau);
    %Logic of Bloom
     bloom=bloomlog(dox(ip,lyr,tau),bloom);   
    %Dynamic of Bloom
     if bloom  
         xdel=bloomdyn(x,ux);
     else      
         x=x0;xdel=[0,0,0];
     end
    %Restrictions
    
    %Update of Bloom
     x=x+xdel;
     
    %Prepara vector Temperaturas
     vhour=[vhour,hours(tau)];
     vtemp=[vtemp,temp(ip,lyr,tau)];
    drawnow
    
    % % Record video
     frame = getframe(gcf);
     writeVideo(vid,frame);
    ['DateTime = ', datestr(dt(tau))]
 end
end
 
% % Close video file
    close(vid);
    
function xdel=bloomdyn(x,u)
%This function implements a simplyfied dynamic if the bloom
%x(0)=size,x(1)=lat,x(2)=lon
%u(1)=Nfood,u(2)=eastwaterspeed,u(3)=nordwaterspeed
 kdecline=1/6;
 kgrow=1;
 xdel(1)=kgrow*u(1)-kdecline*x(1);
 k2d=1/60;
 xdel(2)=k2d*u(2);
 xdel(3)=k2d*u(3);
end

function bloom=bloomlog(dox,bloom)
%Is It a Bloom? At actual position.
%Rich in oxigen=>It is a bloom
%Poor in oxigen=>It is not a bloom
%Other case bypass bloom
 if (dox>20), bloom=true;
 elseif (dox<15), bloom=false;
 end
end