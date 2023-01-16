# DEVS-BLOOM: public release

DEVS-BLOOM is a novel framework to enable real-time monitoring and hazard prediction of CBs. The purpose of our approach, based on the principles of Model Based Systems Engineering (MBSE), is to ensure high-performance hazard detection via the implementation of model-driven technologies and an infrastructure based on Internet of Things (IoT) for dynamic environments. As a result, we address three main topics in the sustainable management of water resources under the umbrella of model-driven technologies: (i) the automatic and intelligent management of harmful CBs in water environments, (ii) the improvement of the use of water resources as well as the ecosystems in which CBs appear, and (iii) the capability of finding correlations among environmental parameters and CBs in water bodies with drinking and recreational uses.

To test this software, clone this repository, open a bash terminal inside, and run:

```bash
# Clone the repository
git clone git@github.com:iscar-ucm/devs-bloom-public.git
cd devs-bloom-public

# Python dependencies
pip3 install xdevs
pip3 install netCDF4
pip3 install scipy
pip3 install bokeh
pip3 install pyproj
pip3 install matplotlib
pip3 install plotly

# System (GNU/Linux) dependencies
sudo apt install ffmpeg

# Dowload the Lake Washington water body into dataedge/Washington-1m-2008-09_UGRID.nc:
# URL: https://drive.google.com/file/d/1quY0chlibsaeFFJnZT8YDFVMuMBcX1CJ/view?usp=share_link
## Alternatively run the following command:
wget --load-cookies /tmp/cookies.txt "https://docs.google.com/uc?export=download&confirm=$(wget --quiet --save-cookies tmp/cookies.txt --keep-session-cookies --no-check-certificate 'https://docs.google.com/uc?export=download&id=1quY0chlibsaeFFJnZT8YDFVMuMBcX1CJ' -O- | sed -rn 's/.*confirm=([0-9A-Za-z_]+).*/\1\n/p')&id=1quY0chlibsaeFFJnZT8YDFVMuMBcX1CJ" -O dataedge/Washington-1m-2008-09_UGRID.nc && rm -rf /tmp/cookies.txt

# Run
python3 main_beatriz_tfm.py

# Open reports
firefox output/ModelBeatrizTFM/fog_report.html
firefox output/ModelBeatrizTFM/cloud_report.html
```
