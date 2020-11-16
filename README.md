This repo is designed for the storage of and access to flight log data.

to read an ardupilot log the optional dependency pymavlink must be installed from pip.

# install:

conda install -c thomasdavid flightdata

# develop:

conda config --append channels thomasdavid
conda create --name flightdata --file requirements.txt
conda activate flightdata

# Use:

from flightdata import Flight, Fields

log_file = 'logfile.bin' # path to the log file
flight = Flight.from_log(log_file) # read the log
