%% Crea Video
%% Carga Nuevos Datos UGRID
close all
clear
clc
dibuja=false;
generavideo=false;
saveframes=false;
savedata=false;
file='video10';

% % Open video file
if generavideo==true
     vid = VideoWriter(file,'MPEG-4');
     vid.Quality = 100;
     open(vid);
end

%%
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
time = ncread(filename,'time');   %En días
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
days=day(dt);
sun=max(cos((hours+12)/24*2*pi)-cos(days-5)/5,0); %Genero el Sol

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
x=x0;  %Modelo Bloom
xs=[0.5,x0(2),x0(3)];   %Modelo Barco

if dibuja

f=figure(1);
%f.Position(3:4) = [1000 500];
f.WindowState='maximized';
myxlim=[-122.25,-122.2];
myylim=[47.5,47.55];


subplot(2,3,1);
colormap('default')

xlim([0,24])
ylim([0,1])

subplot(2,3,4)
xlim(myxlim)
ylim(myylim)
title('Water Speed (m/s)')
xlabel('Longitude'); 
ylabel('Latitude'); 

subplot(2,3,2)
colormap('default')
c2=colorbar;
c2.Label.String = 'Disolved Oxigen (mg/L)';
caxis([0 25]);
xlabel('Longitude'); 
ylabel('Latitude'); 
xlim(myxlim)
ylim(myylim)

subplot(2,3,5)
colormap('default')
c3=colorbar;
c3.Label.String = 'Nitrate (mg/L)';
caxis([0 0.2]);
%c3.Label.String = 'Dissolved organic nitrogen (mg/L)';
%caxis([0 5]);
xlabel('Longitude'); 
ylabel('Latitude'); 
xlim(myxlim)
ylim(myylim)

subplot(1,3,3);
colormap('default')
c1=colorbar;
caxis([0 10]);
xlabel('Longitude'); 
ylabel('Latitude'); 
c1.Label.String = 'Algae2 (mg/L)';
%plot(x(2),x(3),'or');
%plot(xs(2),xs(3),'sk');
%legend('Algae Model','Bloom Model','USV Position')
xlim(myxlim)
ylim(myylim)
hold on;
end

vtemp=nan;
vhour=0;
vpwr=xs(1);

vx=x';
vxs=xs';
vbloom=false;
vN=nan;
vO=nan;
vA=nan;
vt=nan;
vs=nan;
vu=nan;
vv=nan;

for lyr = 55 %1:55
 for tau = 1:length(time)
    ['DateTime = ', datestr(dt(tau))]
    if (hours(tau)==0) 
         x=x0;
         bloom=false;
         vtemp=temp(ip,lyr,tau);
         vhour=hours(tau);
         vpwr=xs(1);
    end
    me=mean(temp(:,lyr,tau),'omitnan');
    ma=max(temp(:,lyr,tau))-me;
    mi=me-min(temp(:,lyr,tau));
    if dibuja
    subplot(2,3,1)
     yyaxis left
     plot(hours,sun,hours(tau),sun(tau),'o');hold on
     ylabel('Sun Radiation (Norm.)')
     ylim([0,1])
     plot(vhour,vpwr,'-k',hours(tau),vpwr(end),'pk');hold off
     title('Ship Power [0,1]')
     yyaxis right
     %plot(vhour,vtemp);hold on;
     plot(vhour,vtemp,'-',hours(tau),vtemp(end),'s');
     %errorbar(hours(tau),vtemp(end),ma,'s'); 
     ylabel('Water Temperature (ºC)')
     xlabel('Hour')
     ylim([19,21])
    subplot(2,3,4)
     quiver(lonc,latc,u(:,lyr,tau)/10,v(:,lyr,tau)/10,0);
     xlim(myxlim)
     ylim(myylim)
     title(['Mean Water Speed (m/s):',num2str(mean(sqrt(u(:,lyr,tau).^2+v(:,lyr,tau).^2),'omitnan'))])    
     %ylabel('Water Flow')
     xlabel('Longitude'); 
     ylabel('Latitude'); 
    subplot(2,3,2)
     patch(lonF,latF,dox(:,lyr,tau),'EdgeColor','none'); % Two types of algae
     title(['DateTime = ', datestr(dt(tau))])
    subplot(2,3,5)
     patch(lonF,latF,nox(:,lyr,tau),'EdgeColor','none'); % Two types of algae
     %patch(lonF,latF,don(:,lyr,tau),'EdgeColor','none'); % Two types of algae
    subplot(1,3,3)
     cla
     colormap('default')
     c1=colorbar;
     caxis([0 10]);
     xlabel('Longitude'); 
     ylabel('Latitude'); 
     c1.Label.String = 'Algae2 (mg/L)';
     xlim(myxlim)
     ylim(myylim)
     patch(lonF,latF,ALG(:,lyr,2,tau),'EdgeColor','none'); % Two types of algae
     hold on;
     %bt=text(x(2),x(3),num2str(x(1),2));
     [lat,lon] = scircle1(x(3),x(2),0.001*sqrt(x(1)));
     plot(lon,lat,'r','LineWidth',2)
     plot(xs(2),xs(3),'pk','MarkerSize',10)
     %legend('Algae Model','Bloom Model','USV Position')
     hold off;
     title('Sim. Bloom, Inf. Bloom & Ship Pos.')
      %Initialize Bloom and vectors at 0:00
    end
     
    %Input of Bloom Model 
     %[ip,dist] = dsearchn(map,[x(2),x(3)]); %Measure at model
     [ip,dist] = dsearchn(map,[xs(2),xs(3)]);  %Measure at ship
         
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
     x=bloomdyn(x,ux,bloom,x0);
    %Error of Ship
     eu=(x(2)-xs(2));
     ev=(x(3)-xs(3));
    %Inputs os ship
     uxs(1)=-0.003;     %Consumo Electrónica (Puede ser cargador)
     uxs(2)=1*eu;       %Control Action
     uxs(3)=1*ev;
     pxs(1)=0.04*sun(tau);   %Sun Raditation
     pxs(2)=u(ip,lyr,tau);   %Water drag Perturbation
     pxs(3)=v(ip,lyr,tau);
    %Ship Dynamic
     xs=shipdyn(xs,uxs,pxs);
     if xs(1)>1, xs(1)=1;end %Limit maximum power
     
    %Prepara vector para pintar
     vhour=[vhour,hours(tau)];
     vtemp=[vtemp,temp(ip,lyr,tau)];
     vpwr=[vpwr,xs(1)];
     vx=[vx,x'];
     vxs=[vxs,xs'];
     vbloom=[vbloom,bloom];
     vN=[vN,nox(ip,lyr,tau)];
     vO=[vO,dox(ip,lyr,tau)];
     vA=[vA,ALG(ip,lyr,2,tau)];
     vu=[vu,u(ip,lyr,tau)];
     vv=[vv,v(ip,lyr,tau)];
     vt=[vt,temp(ip,lyr,tau)];
     vs=[vs,sun(tau)];
    if dibuja, 
        drawnow; 
    end
    if saveframes
        savefig(['.\fg\F',num2str(tau,4)]);
    end
    % % Record video
    if generavideo==true
     frame = getframe(gcf);
     writeVideo(vid,frame);
    end

 end
end

% % Close video file
if generavideo==true
    close(vid);
end
  
if savedata==true
    save file
end

%% PLOTS
in=50;
en=480;
figure(2);
subplot(5,1,1);
plot(dt(in:en),sun(in:en),'LineWidth',2);
ylabel('Sun Ratiation [0,1]')
title('Things Measurements');
subplot(5,1,2);
plot(dt(in:en),vt(in:en),'LineWidth',2);
ylabel('Water Temperature (ºC)')
subplot(5,1,3);
plot(dt(in:en),vN(in:en),'LineWidth',2);
ylabel('Nitrate (mg/L)');
subplot(5,1,4);
plot(dt(in:en),vO(in:en),'LineWidth',2);
ylabel('Disolved Oxigen (mg/L)');
subplot(5,1,5)
plot(dt(in:en),sqrt(vu(in:en).^2+vv(in:en).^2),'LineWidth',2);
ylabel('Water Speed (m/s)')


in=50;
en=480;
figure(3);
subplot(4,1,1);
plot(dt(in:en),vbloom(in:en),'LineWidth',2);
ylabel('Detection (bool)');ylim([-0.1,1.1])
title('Infered Bloom');
subplot(4,1,2);
plot(dt(in:en),vx(1,in:en)',dt(in:en),vA(in:en),'LineWidth',2);
%plot(dt(in:en),vx(1,in:en)','LineWidth',2);
ylabel('Density (mg/L)');
subplot(4,1,3)
plot(dt(in:en),vx(2,in:en)','LineWidth',2);
ylabel('Longitude(º)')
subplot(4,1,4)
plot(dt(in:en),vx(3,in:en)','LineWidth',2);
ylabel('Latitude(º)')

in=50;
en=480;
figure(4);
subplot(4,1,1);
plot(dt(in:en),vxs(1,in:en)',dt(in:en),sun(in:en),'LineWidth',2);
ylabel('Electric Power [0,1]')
legend('Batery','Sun');
title('USV');
subplot(4,1,2)
vvx=diff(vxs')';
vv=sqrt(vvx(2,:).^2+vvx(3,:).^2)*2*pi*6700/360*2; % Km/h
plot(dt(in:en),vv(in:en),'LineWidth',2);
ylabel('Speed (km/h)');
subplot(4,1,3)
plot(dt(in:en),vxs(2,in:en)','LineWidth',2);
ylabel('Longitude(º)')
subplot(4,1,4)
plot(dt(in:en),vxs(3,in:en)','LineWidth',2);
ylabel('Latitude(º)')


%% FUNCTIONS

function x=bloomdyn(x,u,bloom,x0)
%This function implements a simplyfied dynamic if the bloom
%ode45(t,x,parametros)
%x(1)=size,x(2)=lon,x(3)=lat, x(4)=time of last update
%u(1)=Nfood,u(2)=eastwaterspeed,u(3)=nordwaterspeed
 kdecline=1/6;
 kgrow=1;
 k2d=1/60;
 if bloom
     x(1)=x(1)+kgrow*u(1)-kdecline*x(1);
     x(2)=x(2)+k2d*u(2);
     x(3)=x(3)+k2d*u(3);
 else   %No desplazo el modelo de Bloom
     x(1)=x(1)+kgrow*u(1)-kdecline*x(1);
     x(2)=x0(2);
     x(3)=x0(3);
 end
 if x(1)>10,x(1)=10;end
end

function x=shipdyn(x,u,p)
%This function implements a simplyfied dynamic of a ship
%x(1)=power,x(2)=lon,x(3)=lat
%u(1)=charger,u(2)=eastspeed,u(3)=nordspeed, u(4)=time of actuator activation 
%p(1)=solarpower,p(2)=eastwaterspeed,p(3)=nordwaterspeed
maxspeed=0.002;
if x(1)>0
     if u(2)>maxspeed, u(2)=maxspeed;end
     if u(3)>maxspeed, u(3)=maxspeed;end
     if u(2)<-maxspeed, u(2)=-maxspeed;end
     if u(3)<-maxspeed, u(3)=-maxspeed;end
     xdel(1)=u(1)+p(1)-30*sqrt(u(2)^2+u(3)^2); %Electrónica+Solar-Propulsion
     k2d=1/100;
     xdel(2)=u(2)+k2d*p(2);
     xdel(3)=u(3)+k2d*p(3);
 else
     x(1)=0;
     xdel(1)=p(1); %Solar
     xdel(2)=0;
     xdel(3)=0;
end
    x=x+xdel;
    if x(1)>1, x(1)=1;end
end

function bloom=bloomlog(dox,bloom)
%Is It a Bloom? At actual position.
%Rich in oxigen=>It is a bloom
%Poor in oxigen=>It is not a bloom
%Other case bypass bloom
 %if x(1)<0.1, bloom=false;end
 if dox>20, bloom=true;end
 if dox<15, bloom=false;end
end
 
