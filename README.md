This repo is designed for the storage of and access to flight log data.

to read an ardupilot log the optional dependency pymavlink must be installed from pip.


# install:
conda install flightdata -c thomasdavid

# develop:
conda config --append channels thomasdavid

conda create --name flightdata --file requirements.txt

conda activate flightdata


# Use:
from flightdata.data import Flight
from flightdata.fields import Fields
from flightdata.flightline import Box

#read a box, this defines the pilot position and a point on the way towards centre. A constructor is provided to read a file from Andrew Palmers F3A zone app

box = Box.from_f3a_zone_file('/home/tom/Desktop/logs/20200801/EmailedBox.f3a')

#path to the log file

log_file = 'flight_log.bin'

#read the log and rotate the data to the flightline. defaults to ardupilot format

flight=Flight.from_log(
    log_file,
    box
)