import unittest
from flightdata.fields import Fields
from flightdata.data import Flight


class TestFlightData(unittest.TestCase):
    def setUp(self):
        self.flight = Flight.from_log('test/ekfv3_test.BIN')

    def test_duration(self):
        self.assertAlmostEqual(self.flight.duration, 601, 0)

    def test_slice(self):
        short_flight = self.flight.subset(100, 200)
        self.assertAlmostEqual(short_flight.duration, 100, 0)

    def test_read_tuples(self):
        vals = self.flight.read_field_tuples(Fields.TIME)
        self.assertAlmostEqual(
            max(vals[0]), 601 + self.flight.zero_time, 0)
        self.assertEqual(len(vals), 2)
        vals1 = self.flight.read_field_tuples(Fields.GPSSATCOUNT)
        self.assertEqual(len(vals1), 1)

    def test_transform(self):
        funcdict = {i: lambda *x: x for i in range(0, 7)}

        flightcopy = self.flight.transform(funcdict)
        self.assertAlmostEqual(flightcopy.duration, 601, 0)


if __name__ == "__main__":

    unittest.main()