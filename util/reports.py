import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import logging
from xdevs import get_logger

logger = get_logger(__name__, logging.DEBUG)


class FogReportService:
    """Class to generate fog reports."""

    def __init__(self, base_folder: str = 'output'):
        self.base_folder = base_folder
        self.html_title = "Fog Report"

    def run(self):
        logger.debug("FogReportService::run()")
        self.prepare_data()
        with open(self.base_folder + '/fog_report.html', 'w') as f:
            f.write(self.prepare_html_code())

    def prepare_data(self):
        self.prepare_figure3()

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

    def prepare_html_code(self):
        html = f'''
            <html>
                <head>
                    <title>{self.html_title}</title>
                </head>
                <body>
                    <h1>Sensors</h1>
                    <p>Currently, all the data used in this simulation are synthetic. Consequently, 
                    all the sensors work on virtual mode, as DTs. When a sensor must take a measurement, 
                    it searches the database (the EEMS file or the irradiance database), modifies the 
                    signal according to its technical characteristics, and generates a message with
                    the signal value. The fog layer receives these signals to perform different calculations 
                    like the model inference and periodically uploads them to the cloud layer. This Figure shows 
                    the signal values recorded by all the sensors of this use case after several days of 
                    simulation.</p>
                    <img src="figure3.png" width="90%" alt="Sensors' data" class="center">
                </body>
            </html>'''
        return html
