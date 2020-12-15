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


from enum import Enum
from pint import UnitRegistry, DimensionalityError
from typing import Dict, List
ureg = UnitRegistry()


_field_list = []


class Field(object):
    def __init__(self, name, unit, length, description='', names=[]):
        self._name = name
        self._unit = unit
        self._length = length
        self._description = description
        self._names = self._make_names(names)
        _field_list.append(self)

    @property
    def name(self):
        return self._name

    def _make_names(self, names):
        _out_names = []
        for i in range(0, self._length):
            if i < len(names):
                _out_names.append(self._name + '_' + names[i])
            else:
                _out_names.append(self._name + '_' + str(i))
        return _out_names

    @property
    def names(self):
        return self._names

    def length(self):
        return self._length

    @property
    def description(self):
        return self._description

    @property
    def unit(self):
        return self._unit


class Fields(object):
    """This class defines the fields. Do not instantiate.
    """
    TIME = Field('time', ureg.second, 2, names=['flight', 'actual'])
    TXCONTROLS = Field('tx_controls', ureg.second, 8,
                       description='PWM Values coming from the TX')
    SERVOS = Field('servos', ureg.second, 8,
                   description='PWN Values going to the Servos')
    FLIGHTMODE = Field('mode', 1, 3, description='The active flight mode ID')
    POSITION = Field('position', ureg.meter, 3,
                     description='position of plane in cartesian coordinates (n, e, d)', names=['x', 'y', 'z'])
    GLOBALPOSITION = Field('global_position', ureg.degree,
                           2, names=['latitude', 'longitude'])
    GPSSATCOUNT = Field('gps_sat_count', 1, 1,
                        description='number of satellites')
    SENSORALTITUDE = Field('altitude', ureg.meters, 2, names=['gps', 'baro'])
    ATTITUDE = Field('attitude', ureg.radian, 3,
                     description='euler angles, order = yaw, pitch, roll', names=['roll', 'pitch', 'yaw'])
    AXISRATE = Field('axis_rate', ureg.radian / ureg.second, 3,
                     description='rotational velocities', names=['roll', 'pitch', 'yaw'])
    BATTERY = Field('battery', ureg.volt, 2, description='battery voltages')
    CURRENT = Field('current', ureg.amp, 4, description='motor currents')
    AIRSPEED = Field('airspeed', ureg.meter / ureg.second,
                     2, description='sensor airspeed')
    ACCELERATION = Field('acceleration', ureg.meter / ureg.second / ureg.second,
                         3, description='accelerations (earth frame)', names=['x', 'y', 'z'])
    VELOCITY = Field('velocity', ureg.meter / ureg.second, 3,
                     description='velocity data (earth frame)', names=['x', 'y', 'z'])
    WIND = Field('wind', ureg.meter / ureg.second, 2,
                 description='wind in earth frame', names=['x', 'y'])

    @staticmethod
    def all():
        return _field_list

    @staticmethod
    def all_names():
        _all_names = []
        for field in _field_list:
            _all_names += field.names
        return _all_names

    @staticmethod
    def some_names(fields):
        if isinstance(fields, list):
            _some_names = []
            for field in fields:
                _some_names += field.names
            return _some_names
        else:
            return fields.names

    def to_dict(self):
        outdict = {}
        for field in _field_list:
            outdict[field.name] = field.names
        return outdict


# TODO This needs an alternate source field if required info is not there
class MappedField(object):
    def __init__(self, field, position, name, unit):
        super().__init__()
        self._field = field
        self._position = position
        self._name = name
        self._unit = unit
        self._base_factor = None

    @property
    def field(self):
        return self._field

    @property
    def position(self):
        return self._position

    @property
    def unit(self):
        return self._unit

    @property
    def name(self):
        return self._name

    @property
    def base_factor(self):
        if not self._base_factor:
            try:
                self._base_factor = float(self.unit) / float(self.field.unit)
            except DimensionalityError:
                quantity = 1 * self.unit
                self._base_factor = quantity.to(self.field.unit).magnitude
        return self._base_factor


class FieldIOInfo(object):
    def __init__(self, field_maps: Dict[str, MappedField]):
        self._field_maps = field_maps

        self._io_names = []
        self._base_names = []
        self._factors_to_base = []
        self._factors_to_field = []

        for key, value in self._field_maps.items():
            self._io_names.append(key)
            self._base_names.append(value.field.names[value.position])
            self._factors_to_base.append(value.base_factor)
            self._factors_to_field.append(1 / value.base_factor)

    @property
    def io_names(self):
        return self._io_names

    @property
    def base_names(self):
        return self._base_names

    @property
    def factors_to_base(self) -> List[float]:
        return self._factors_to_base

    @property
    def factors_to_field(self) -> List[float]:
        return self._factors_to_field

    def subset(self, less_base_names):
        return FieldIOInfo({x: self._field_maps[x] for x in less_base_names if x in self._field_maps})


if __name__ == "__main__":
    print(Fields.all_names())
