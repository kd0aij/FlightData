"""
This program is free software: you can redistribute it and/or modify it under
the terms of the GNU General Public License as published by the Free Software
Foundation, either version 3 of the License, or (at your option) any later
version.
This program is distributed in the hope that it will be useful, but WITHOUT
ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
You should have received a copy of the GNU General Public License along with
this program. If not, see <http://www.gnu.org/licenses/>.
"""
import unittest
from typing import List, Dict
import numpy as np
import pandas as pd
from importlib.util import find_spec
from enum import Enum

from ardupilot_log_reader.reader import Ardupilot

from flightdata.fields import Fields
from flightdata.mapping import get_ardupilot_mapping


def _read_ardupilot(log_file: str) -> (Ardupilot, pd.DataFrame):
    """reads an ardupilot bin file to a Pandas Dataframe.
    fields are renamed and units converted to the tool fields defined in ./fields.py
    The input fields, read from the log are specified in ./mapping 

    Args:
        log_file (str): [description]

    Raises:
        IOError: [description]

    Returns:
        Ardupilot: the parser object containing the raw data as described in ./mapping
        DataFrame: a DataFrame containing the transformed data to the fields and units defined in ./fields.py
    """
    _field_request = ['ARSP', 'ATT', 'BARO', 'GPS', 'IMU',
                      'RCIN', 'RCOU', 'BAT', 'MODE', 'NKF1', 'STAT', 'XKF1']
    _parser = Ardupilot(log_file, types=_field_request, zero_time_base=True)
    fulldf = _parser.join_logs(_field_request)

    ardupilot_io_info = get_ardupilot_mapping(_parser.parms['AHRS_EKF_TYPE'])

    # expand the dataframe to include all the columns listed in the io_info instance
    input_data = fulldf.get(list(set(fulldf.columns.to_list())
                                 & set(ardupilot_io_info.io_names)))

    # Generate a reordered io instance to match the columns in the dataframe
    _fewer_io_info = ardupilot_io_info.subset(input_data.columns.to_list())

    _data = input_data * _fewer_io_info.factors_to_base  # do the unit conversion
    _data.columns = _fewer_io_info.base_names  # rename the columns

    # add the missing tool columns
    missing_cols = pd.DataFrame(
        columns=list(set(Fields.all_names()) -
                     set(_data.columns.to_list()))+[Fields.TIME.names[0]]
    )
    output_data = _data.merge(
        missing_cols, on=Fields.TIME.names[0], how='left')

    # set the first time in the index to 0
    output_data.index = _data[Fields.TIME.names[0]].copy()
    output_data.index.name = 'time_index'
    return _parser, output_data.loc[pd.isna(output_data['time_actual']) == False]


class Flight(object):
    def __init__(self, data, parameters: List = None, zero_time_offset: float = 0):
        self.data = data
        self.parameters = parameters
        self.zero_time = self.data.index[0] + zero_time_offset
        self.data.index = self.data.index - self.data.index[0]

    @staticmethod
    def from_log(log_path, box=None):
        _parser, data = _read_ardupilot(log_path)
        return Flight(data, _parser.parms)

    @property
    def duration(self):
        return self.data.tail(1).index.item()

    def read_row_by_id(self, names, index):
        return list(map(self.data.iloc[index].to_dict().get, names))

    def read_closest(self, names, time):
        """Get the row closest to the requested time.

        :param names: list of columns to return
        :param time: desired time in microseconds
        :return: dict[column names, values]
        """
        return self.read_row_by_id(names, self.data.index.get_loc(time, method='nearest'))

    @property
    def column_names(self):
        return self.data.columns.to_list()

    def read_fields(self, fields):
        return self.data[Fields.some_names(fields)]

    def origin(self) -> Dict[str, float]:
        """the latitude and longitude of the home position

        Returns:
            dict: dictionary containing home position lat and long
        """
        gpsdata = self.read_fields([Fields.GLOBALPOSITION, Fields.GPSSATCOUNT])
        gpsdata = gpsdata.loc[pd.isna(gpsdata.iloc[:, 0]) == False]
        firstgps = gpsdata.loc[gpsdata.iloc[:, 2] > 5].iloc[0]
        # more than 5 satellites
        return {
            'latitude': firstgps.latitude,
            'longitude': firstgps.longitude
        }

    def subset(self, start_time: float, end_time: float):
        """generate a subset between the specified times

        Args:
            start_time (float): the start of the subset, 0 for the start of the dataset
            end_time (float): end of the subset, -1 for the end of the flight

        Returns:
            Flight: a new instance of Flight contianing a refernce to the subset. parameters referenced, 
            index adjusted so 0 is the start of the subset.
        """

        if start_time == 0 and end_time == -1:
            new_data = self.data
        elif start_time == 0:
            end = self.data.index.get_loc(end_time, method='nearest')
            new_data = self.data.iloc[:end]
        elif end_time == -1:
            start = self.data.index.get_loc(start_time, method='nearest')
            new_data = self.data.iloc[start:]
        else:
            start = self.data.index.get_loc(start_time, method='nearest')
            end = self.data.index.get_loc(end_time, method='nearest')
            new_data = self.data.iloc[start:end]

        return Flight(
            data=new_data,
            parameters=self.parameters,
            zero_time_offset=self.zero_time
        )


class TestFlightData(unittest.TestCase):
    def setUp(self):
        self.flight = Flight.from_log('test/ekfv3_test.BIN')

    def test_duration(self):
        self.assertAlmostEqual(self.flight.duration, 278.923721)

    def test_read_closest(self):
        self.assertAlmostEqual(
            self.flight.read_closest(Fields.TIME.names, 220)[
                0] - self.flight.zero_time,
            220,
            0)

    def test_slice(self):
        short_flight = self.flight.subset(100, 200)
        self.assertAlmostEqual(short_flight.duration, 100, 0)


if __name__ == "__main__":

    unittest.main()
