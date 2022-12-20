import math
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.animation import FuncAnimation
from functools import partial
from matplotlib.patches import Polygon
from matplotlib.patches import Circle
from matplotlib.collections import PatchCollection
import pandas as pd
import numpy as np
import logging
import netCDF4 as nc
from xdevs import get_logger

logger = get_logger(__name__, logging.DEBUG)


class FogReportService:
    """Class to generate fog reports."""

    def __init__(self, base_folder: str = 'output', emms_file: str = 'dataedge/Washington-1m-2008-09_UGRID.nc'):
        self.base_folder = base_folder
        self.emms_file = emms_file
        self.html_title = "Fog Report"

    def run(self):
        logger.debug("FogReportService::run()")
        self.prepare_data()
        with open(self.base_folder + '/fog_report.html', 'w') as f:
            f.write(self.prepare_html_code())

    def prepare_data(self):
        self.prepare_figure1()
        self.prepare_figure3()
        self.prepare_figure4()
        self.prepare_figure5()

    def update(self, ax, color_bars, usv_data, num_frames_usv, emms_data, num_frames_emms, step):
        logger.debug("Generating figure 1: current frame is: " +
                     str(step) + "/100")

        # Preparing the index:
        size_step_usv = num_frames_usv/100
        curr_indx_usv = int(step*size_step_usv)
        size_step_emms = num_frames_emms/100
        curr_indx_emms = int(step*size_step_emms)

#        mean_water_speed = np.mean(
#            np.sqrt((usv_data["water_x"][frame])**2 + (usv_data["water_y"][frame])**2))
#        mean_wind_speed = np.mean(
#            np.sqrt((usv_data["wind_x"][frame])**2 + (usv_data["wind_y"][frame])**2))

        plt.suptitle(usv_data["timestamp"][curr_indx_usv].strftime(
            "%d/%m/%Y, %H:%M"), x=0.2, y=1, fontsize='small')
#        ax[1].set_title(
#            f"Mean Water Speed (m/s): {mean_water_speed:.6f}", fontsize='small')
#        ax[2].set_title(
#            f"Mean Wind Speed (m/s): {mean_wind_speed:.6f}", fontsize='small')

        # ax[0].set_xlabel("Hour")
        # ax[1].set_xlabel("Longitude")
        # ax[2].set_xlabel("Longitude")

        # ax[1].set_ylabel("Latitude")
        # ax[2].set_ylabel("Latitude")

        #ax0.set_ylim([19, 21])

        #ax[1].set_xlim([-122.25, -122.2])
        #ax[1].set_ylim([47.5, 47.55])

        #ax[2].set_xlim([-122.25, -122.2])
        #ax[2].set_ylim([47.5, 47.55])

        # Legend
        #lines_labels = [ax.get_legend_handles_labels() for ax in fig.axes]
        #lines, labels = [sum(lol, []) for lol in zip(*lines_labels)]
        # fig.legend(lines, labels, loc="upper left",
        #           bbox_to_anchor=(0.05, 0.98), prop={'size': 6})

        # GRAPHIC 1
        # ----------------------
        # Water temperature
        ax[0][0].clear()
        ax[0][0].tick_params(axis='y', colors='red')
        ax[0][0].plot(usv_data["timestamp"][0:curr_indx_usv], usv_data["water_temp"]
                      [0:curr_indx_usv], color="red", label="Water Temperature (ºC)")
        ax[0][0].plot(usv_data["timestamp"][curr_indx_usv],
                      usv_data["water_temp"][curr_indx_usv], marker="o", color="red")
        # ----------------------

        # GRAPHIC 2
        # ----------------------
        # Water speed
        ax[0][1].clear()
        ax[0][1].set_xlim([-122.25, -122.2])
        ax[0][1].set_ylim([47.5, 47.55])
        ax[0][1].quiver(emms_data["zonal_lon"], emms_data["zonal_lat"], emms_data["water_x"]
                        [curr_indx_emms][54][:]/10, emms_data["water_y"][curr_indx_emms][54][:]/10, color='b')
        # ----------------------

        # GRAPHIC 3
        # ----------------------
        # Wind speed
        ax[0][2].clear()
        ax[0][2].set_xlim([-122.25, -122.2])
        ax[0][2].set_ylim([47.5, 47.55])
        ax[0][2].quiver(emms_data["zonal_lon"], emms_data["zonal_lat"], emms_data["wind_x"]
                        [curr_indx_emms][:]/10, emms_data["wind_y"][curr_indx_emms][:]/10, color='b')
        # ----------------------

        # GRAPHIC 4
        # ----------------------
        # Algae concentration
        ax[1][0].clear()
        ax[1][0].add_collection(color_bars["collection1"])
        ax[1][0].set_xlim([-122.25, -122.2])
        ax[1][0].set_ylim([47.5, 47.55])
        ax[1][0].set_title("Sim. Bloom, Inf. Bloom & Ship Pos.", fontsize = 'small')
        ax[1][0].set_xlabel("Longitude")
        ax[1][0].set_ylabel("Latitude")
        alg = np.array(
            list(map(color_bars["norm1"], emms_data["algae"][curr_indx_emms][1][54][:])))
        colors1 = color_bars["cmap1"](alg)
        color_bars["collection1"].set_color(colors1)
        # USV trajectory
        ax[1][0].plot(usv_data["usv_lon"][curr_indx_usv], usv_data["usv_lat"][curr_indx_usv], color = "black", marker = 'd', markersize = 5)
        # Infected bloom
        # TODO: This boolean has a initial blank space. Fix it at the inference service.
        if(usv_data["bloom_detection"][curr_indx_usv]==" True"):
            circle  = Circle((usv_data["bloom_lon"][curr_indx_usv], usv_data["bloom_lat"][curr_indx_usv]), radius = 0.05 * math.sqrt(usv_data["bloom_size"][curr_indx_usv]), fill = False, color = "red") 
            ax[1][0].add_patch(circle)
        ax[1][0].autoscale_view()

        # GRAPHIC 5
        # ----------------------
        # Disolved Oxygen
        ax[1][1].clear()
        ax[1][1].add_collection(color_bars["collection2"])
        ax[1][1].set_xlim([-122.25, -122.2])
        ax[1][1].set_ylim([47.5, 47.55])
        ax[1][1].set_title("Disolved Oxygen", fontsize = 'small')
        ax[1][1].set_xlabel("Longitude")
        ax[1][1].set_ylabel("Latitude")
        disox = np.array(
            list(map(color_bars["norm2"], emms_data["dox"][curr_indx_emms][54][:])))
        colors2 = color_bars["cmap2"](disox)
        color_bars["collection2"].set_color(colors2)
        ax[1][1].autoscale_view()

        # GRAPHIC 5
        # ----------------------
        # Disolved Oxygen
        ax[1][2].clear()
        ax[1][2].add_collection(color_bars["collection3"])
        ax[1][2].set_xlim([-122.25, -122.2])
        ax[1][2].set_ylim([47.5, 47.55])
        ax[1][2].set_title("Nitrate", fontsize = 'small')
        ax[1][2].set_xlabel("Longitude")
        ax[1][2].set_ylabel("Latitude")
        nit = np.array(
            list(map(color_bars["norm3"], emms_data["nox"][curr_indx_emms][54][:])))
        colors3 = color_bars["cmap3"](nit)
        color_bars["collection3"].set_color(colors3)
        line = ax[1][2].autoscale_view()

        return line

    def prepare_figure1(self):
        # Prepare the interval and important data
        # USV
        usv_data = pd.read_csv(
            self.base_folder + "/FogServer.InferenceService.csv")
        usv_data['timestamp'] = pd.to_datetime(usv_data['timestamp'])
        # EMMS
        emms_df = nc.Dataset(self.emms_file)
        emms_data = {}
        # Zonal longitude
        emms_data["zonal_lon"] = emms_df.variables["lonc"][:]
        # Zonal latitude
        emms_data["zonal_lat"] = emms_df.variables["latc"][:]
        # Wind speed x axis
        emms_data["wind_x"] = emms_df.variables["wind_x"][:]
        # Wind speed y axis
        emms_data["wind_y"] = emms_df.variables["wind_y"][:]
        # Water speed x axis
        emms_data["water_x"] = emms_df.variables["U"][:]
        # Water speed y axis
        emms_data["water_y"] = emms_df.variables["V"][:]
        # Algae concentration
        emms_data["algae"] = emms_df.variables["ALG"][:]  
        # Dissolved oxygen 
        emms_data["dox"] = emms_df.variables["DOX"][:]                   
        # Nitrate nitrogen 
        emms_data["nox"] = emms_df.variables["NOX"][:]                   

        # Prepare the figure
        fig, ax = plt.subplots(2, 3)
        fig.tight_layout(h_pad=0.5)

        # Prepare the color bars
        color_bars = {}
        # subplot 1
        color_bars["cmap1"] = plt.get_cmap('viridis')
        color_bars["norm1"] = plt.Normalize(0, 10)
        sm1 = plt.cm.ScalarMappable(cmap = color_bars["cmap1"])
        sm1.set_clim(vmin = 0, vmax = 10)
        cbar1 = plt.colorbar(sm1, ax = ax[1][0])
        cbar1.set_label('Algae (mg/L)')
        # subplot 2
        color_bars["cmap2"] = plt.get_cmap('viridis')
        color_bars["norm2"] = plt.Normalize(0, 25)
        sm2 = plt.cm.ScalarMappable(cmap = color_bars["cmap2"])
        sm2.set_clim(vmin = 0, vmax = 25)
        cbar2 = plt.colorbar(sm2, ax = ax[1][1])
        cbar2.set_label('Disolved Oxygen (mg/L)')
        # subplot 3
        color_bars["cmap3"] = plt.get_cmap('viridis')
        color_bars["norm3"] = plt.Normalize(0, 0.2)
        sm3 = plt.cm.ScalarMappable(cmap = color_bars["cmap3"])
        sm3.set_clim(vmin = 0, vmax = 0.2)
        cbar3 = plt.colorbar(sm3, ax = ax[1][2])
        cbar3.set_label('Nitrate (mg/L)')

        # Color map
        nodal_lon = emms_df.variables["lon"][:] 
        nodal_lat = emms_df.variables["lat"][:] 
        nodes = emms_df.variables["nv"][:]
        longitude = nodal_lon[nodes-1]
        latitude  = nodal_lat[nodes-1]
        patches = []
        for i in range(len(longitude)):
            verts   = np.column_stack((longitude[i], latitude[i])) 
            polygon = Polygon(verts, closed = True) 
            patches.append(polygon)
        color_bars["collection1"] = PatchCollection(patches)
        color_bars["collection2"] = PatchCollection(patches)
        color_bars["collection3"] = PatchCollection(patches)

        # fig.set_figheight(10)
        # ani = FuncAnimation(fig, partial(self.update, usv_data, ax),
        #                     repeat=False, frames=len(usv_data['timestamp']), interval=10, blit=True)
        ani = FuncAnimation(fig, partial(self.update, ax, color_bars, usv_data, len(usv_data['timestamp']), emms_data, len(emms_data["wind_x"])),
                            repeat=False, blit=True)
        # plt.subplots_adjust(wspace=0.7)
        # plt.show()
        # ani.save("figure1.gif", writer=ani.ImageMagickWriter(fps=30))
        ani.save(self.base_folder + "/figure1.mp4",
                 writer=animation.FFMpegWriter(fps=5))

    def prepare_figure3(self):
        fig, ax = plt.subplots(5, 1)
        fig.tight_layout(h_pad=0.5)
        fig.set_figheight(10)

        # Sun radiation
        df = pd.read_csv(self.base_folder + "/FogServer.SimSenS.csv")
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        # data_sun.info()
        ax[0].set_title('Normalized Sun Radiation')
        ax[0].plot(df["timestamp"], df["SUN"])
        ax[0].tick_params(labelrotation=20, labelsize=7)

        # Water temperature
        df = pd.read_csv(self.base_folder + "/FogServer.SimSenT.csv")
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        ax[1].set_title('Water Temperature (ºC)')
        ax[1].plot(df["timestamp"], df["WTE"])
        ax[1].tick_params(labelrotation=20, labelsize=7)

        # Nitrate
        df = pd.read_csv(self.base_folder + "/FogServer.SimSenN.csv")
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        ax[2].set_title('Nitrate (mg/L)')
        ax[2].plot(df["timestamp"], df["NOX"])
        ax[2].tick_params(labelrotation=20, labelsize=7)

        # Disolved oxygen
        df = pd.read_csv(self.base_folder + "/FogServer.SimSenO.csv")
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        ax[3].set_title('Disolved Oxygen (mg/L)')
        ax[3].plot(df["timestamp"], df["DOX"])
        ax[3].tick_params(labelrotation=20, labelsize=7)

        # Water speed
        df1 = pd.read_csv(self.base_folder + "/FogServer.SimSenU.csv")
        df1['timestamp'] = pd.to_datetime(df1['timestamp'])
        df2 = pd.read_csv(self.base_folder + "/FogServer.SimSenV.csv")
        df2['timestamp'] = pd.to_datetime(df2['timestamp'])
        ax[4].set_title('Water Speed (m/s)')
        ax[4].plot(df["timestamp"], np.sqrt(df1["WFU"]**2+df2["WFV"]**2))
        ax[4].tick_params(labelrotation=20, labelsize=7)

        fig.suptitle('Measurements', x=0.2, y=1)
        # plt.subplots_adjust(hspace = 2)
        # plt.show()
        plt.savefig(self.base_folder + "/figure3.png",
                    dpi=400, bbox_inches='tight')

    def prepare_figure4(self):
        fig, ax = plt.subplots(4, 1)
        fig.tight_layout(h_pad=0.5)
        fig.set_figheight(10)

        # Bloom detection
        df = pd.read_csv(self.base_folder + "/FogServer.InferenceService.csv")
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        ax[0].set_title('Detection (bool)')
        ax[0].set_ylim([-0.1, 1.1])
        ax[0].plot(df["timestamp"], df["bloom_detection"])
        ax[0].tick_params(labelrotation=20, labelsize=7)

        # Bloom density
        ax[1].set_title('Density (mg/L)')
        ax[1].plot(df["timestamp"], df["bloom_size"])
        ax[1].tick_params(labelrotation=20, labelsize=7)

        # Bloom longitude
        ax[2].set_title('Longitude (º)')
        ax[2].plot(df["timestamp"], df["bloom_lon"])
        ax[2].tick_params(labelrotation=20, labelsize=7)

        # Bloom latitude
        ax[3].set_title('Latitude (º)')
        ax[3].plot(df["timestamp"], df["bloom_lat"])
        ax[3].tick_params(labelrotation=20, labelsize=7)

        fig.suptitle('Inferred Bloom', x=0.2, y=1)
        plt.savefig(self.base_folder + "/figure4.png",
                    dpi=400, bbox_inches='tight')

    def prepare_figure5(self):
        fig, ax = plt.subplots(4, 1)
        fig.tight_layout(h_pad=0.5)
        fig.set_figheight(10)

        # USV Power
        df = pd.read_csv(self.base_folder + "/FogServer.InferenceService.csv")
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        ax[0].set_title('Normalized electric power')
        ax[0].plot(df["timestamp"], df["usv_power"], label='Battery')
        ax[0].plot(df["timestamp"], df["sun_radiation"], label='Sun')
        ax[0].legend(loc="upper right")
        ax[0].tick_params(labelrotation=20, labelsize=7)

        # USV Speed
        ax[1].set_title('Speed (Km/h)')
        ax[1].plot(df["timestamp"], df["usv_power"])
        ax[1].tick_params(labelrotation=20, labelsize=7)

        # USV longitude
        ax[2].set_title('Longitude (º)')
        ax[2].plot(df["timestamp"], df["usv_lon"])
        ax[2].tick_params(labelrotation=20, labelsize=7)

        # USV latitude
        ax[3].set_title('Latitude (º)')
        ax[3].plot(df["timestamp"], df["usv_lat"])
        ax[3].tick_params(labelrotation=20, labelsize=7)

        fig.suptitle('USV', x=0.2, y=1)
        plt.savefig(self.base_folder + "/figure5.png",
                    dpi=400, bbox_inches='tight')

    def prepare_html_code(self):
        html = f'''
            <html>
                <head>
                    <title>{self.html_title}</title>
                </head>
                <body>
                    <h1>Bloom tracking simulation</h1>
                    <p>The following video illustrates the simulation state while tracking of a CB. It contains 
                    sensor measurements and maps some signals that are part of the simulation, described below:
                    <ul>
                        <li>The upper left graph shows the water temperature</li>
                        <li>...</li>
                    </ul>
                    </p>
                    <p style="text-align:center;">
                        <video width="90%" controls>
                            <source src="figure1.mp4" type="video/mp4">
                            Your browser does not support the video tag.
                        </video>
                    </p>
                    <h1>Sensors</h1>
                    <p>Currently, all the data used in this simulation are synthetic. Consequently, 
                    all the sensors work on virtual mode, as DTs. When a sensor must take a measurement, 
                    it searches the database (the EEMS file or the irradiance database), modifies the 
                    signal according to its technical characteristics, and generates a message with
                    the signal value. The fog layer receives these signals to perform different calculations 
                    like the model inference and periodically uploads them to the cloud layer. This Figure shows 
                    the signal values recorded by all the sensors of this use case after several days of 
                    simulation.</p>
                    <p style="text-align:center;">
                        <img src="figure3.png" width="70%" alt="Sensors data">
                    </p>
                    <h1>Bloom inference model</h1>
                    <p>The following figure shows the evolution of the HAB inference model.
                    The first plot shows a boolean value indicating whether the bloom has been detected or not. 
                    The second plot shows the estimated bloom density. The third and fourth plots show the 
                    displacement estimation: longitude and latitude. This Figure shows how blooms are detected and 
                    monitored almost every day. Some of these blooms have significant densities and move around 
                    significantly, requiring dynamic monitoring.</p>
                    <p style="text-align:center;">
                        <img src="figure4.png" width="70%" alt="Bloom inference model">
                    </p>
                    <h1>USV model</h1>
                    <p>The following Figure depicts the status of the USV model. The first graph shows 
                    the status of the power unit. The second plot shows the velocity of the USV. The third 
                    and fourth graphs show the position, longitude, and latitude. On August 30, the Figure 
                    shows that the USV runs out of battery since it has been tracking blooms to distant points 
                    for four consecutive days.</p>
                    <p style="text-align:center;">
                        <img src="figure5.png" width="70%" alt="USV model">
                    </p>
                </body>
            </html>'''
        return html
