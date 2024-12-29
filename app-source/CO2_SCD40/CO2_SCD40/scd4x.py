# original version
# SPDX-FileCopyrightText: 2017 Scott Shawcroft, written for Adafruit Industries
# SPDX-FileCopyrightText: Copyright (c) 2021 ladyada for Adafruit Industries
#
# SPDX-License-Identifier: MIT
#
# this version: also Copyright (c) 2022-2024 peter-l5
# build version: v103

"""
`micropython_scd4x`
================================================================================

Driver for Sensirion SCD4X CO2 sensor


* Author(s): ladyada, peter-l5

Implementation Notes
--------------------

**Hardware:**

* `Adafruit SCD4X breakout board <https://www.adafruit.com/product/5187>`_

** Documentation **
* The library is dervived from the adafruit CircuitPython version.
* The adafruit version and documentation can be found at
* https://github.com/adafruit/Adafruit_CircuitPython_SCD4X.git
"""

import time
from machine import I2C
from micropython import const
import struct

__version__ = "v103"
__repo__ = "https://github.com/peter-l5/MicroPython_SCD4X"

SCD4X_DEFAULT_ADDR = 0x62
_SCD4X_REINIT = const(0x3646)
_SCD4X_FACTORYRESET = const(0x3632)
_SCD4X_FORCEDRECAL = const(0x362F)
_SCD4X_SELFTEST = const(0x3639)
_SCD4X_DATAREADY = const(0xE4B8)
_SCD4X_STOPPERIODICMEASUREMENT = const(0x3F86)
_SCD4X_STARTPERIODICMEASUREMENT = const(0x21B1)
_SCD4X_STARTLOWPOWERPERIODICMEASUREMENT = const(0x21AC)
_SCD4X_READMEASUREMENT = const(0xEC05)
_SCD4X_SERIALNUMBER = const(0x3682)
_SCD4X_GETTEMPOFFSET = const(0x2318)
_SCD4X_SETTEMPOFFSET = const(0x241D)
_SCD4X_GETALTITUDE = const(0x2322)
_SCD4X_SETALTITUDE = const(0x2427)
_SCD4X_SETPRESSURE = const(0xE000)
_SCD4X_PERSISTSETTINGS = const(0x3615)
_SCD4X_GETASCE = const(0x2313)
_SCD4X_SETASCE = const(0x2416)


class SCD4X:
    """
    MicroPython helper class for using the SCD4X CO2 sensor

    :param ~machine.I2C i2c_bus: The I2C bus the SCD4X is connected to.
    :param int address: The I2C device address for the sensor. Default is :const:`0x62`

    **Quickstart: Importing and using the SCD4X**

        Here is an example of using the :class:`SCD4X` class.
        First you will need to import the libraries to use the sensor

        .. code-block:: python

            import scd4x

        Once this is done you can define your `board.I2C` object and define your sensor object

        .. code-block:: python

            i2c = machine.I2C(0, sda=Pin(2), scl=Pin(3), freq=100000)   # RaspberryPi pico example
            scd = scd4x.SCD4X(i2c)
            scd.start_periodic_measurement()  # start_low_periodic_measurement() is a lower power alternative

        Now you have access to the CO2, temperature and humidity using
        the :attr:`CO2`, :attr:`temperature` and :attr:`relative_humidity` attributes

        .. code-block:: python

            if scd.data_ready:
                temperature = scd.temperature
                relative_humidity = scd.relative_humidity
                co2_ppm_level = scd.CO2

    """

    def __init__(self, i2c_bus: I2C, address: int = SCD4X_DEFAULT_ADDR) -> None:
        print("__init__ :", dir())
        print("address : %x" % address)
        print("i2c_bus : ", i2c_bus)
        self.address = address
        print(i2c_bus)
        self.i2c_device = i2c_bus
        self._buffer = bytearray(18)
        self._cmd = bytearray(2)
        self._crc_buffer = bytearray(2)

        # cached readings
        self._temperature = None
        self._relative_humidity = None
        self._co2 = None

        self.stop_periodic_measurement()

    @property
    def CO2(self) -> int:  # pylint:disable=invalid-name
        """Returns the CO2 concentration in PPM (parts per million)

        .. note::
            Between measurements, the most recent reading will be cached and returned.

        """
        if self.data_ready:
            self._read_data()
        return self._co2

    @property
    def temperature(self) -> float:
        """Returns the current temperature in degrees Celsius

        .. note::
            Between measurements, the most recent reading will be cached and returned.

        """
        if self.data_ready:
            self._read_data()
        return self._temperature

    @property
    def relative_humidity(self) -> float:
        """Returns the current relative humidity in %rH.

        .. note::
            Between measurements, the most recent reading will be cached and returned.

        """
        if self.data_ready:
            self._read_data()
        return self._relative_humidity

    def reinit(self) -> None:
        """Reinitializes the sensor by reloading user settings from EEPROM."""
        self.stop_periodic_measurement()
        self._send_command(_SCD4X_REINIT, cmd_delay=0.02)

    def factory_reset(self) -> None:
        """Resets all configuration settings stored in the EEPROM and erases the
        FRC and ASC algorithm history."""
        self.stop_periodic_measurement()
        self._send_command(_SCD4X_FACTORYRESET, cmd_delay=1.2)

    def force_calibration(self, target_co2: int) -> None:
        """Forces the sensor to recalibrate with a given current CO2"""
        self.stop_periodic_measurement()
        self._set_command_value(_SCD4X_FORCEDRECAL, target_co2)
        time.sleep(0.5)
        self._read_reply(self._buffer, 3)
        correction = struct.unpack_from(">h", self._buffer[0:2])[0]
        if correction == 0xFFFF:
            raise RuntimeError(
                "Forced recalibration failed.\
            Make sure sensor is active for 3 minutes first"
            )

    @property
    def self_calibration_enabled(self) -> bool:
        """Enables or disables automatic self calibration (ASC). To work correctly, the sensor must
        be on and active for 7 days after enabling ASC, and exposed to fresh air for at least 1 hour
        per day. Consult the manufacturer's documentation for more information.

        .. note::
            This value will NOT be saved and will be reset on boot unless
            saved with persist_settings().

        """
        self._send_command(_SCD4X_GETASCE, cmd_delay=0.001)
        self._read_reply(self._buffer, 3)
        return self._buffer[1] == 1

    @self_calibration_enabled.setter
    def self_calibration_enabled(self, enabled: bool) -> None:
        self._set_command_value(_SCD4X_SETASCE, enabled)

    def self_test(self) -> None:
        """Performs a self test, takes up to 10 seconds"""
        self.stop_periodic_measurement()
        self._send_command(_SCD4X_SELFTEST, cmd_delay=10)
        self._read_reply(self._buffer, 3)
        if (self._buffer[0] != 0) or (self._buffer[1] != 0):
            raise RuntimeError("Self test failed")

    def _read_data(self) -> None:
        """Reads the temp/hum/co2 from the sensor and caches it"""
        self._send_command(_SCD4X_READMEASUREMENT, cmd_delay=0.001)
        self._read_reply(self._buffer, 9)
        self._co2 = (self._buffer[0] << 8) | self._buffer[1]
        temp = (self._buffer[3] << 8) | self._buffer[4]
        self._temperature = -45 + 175 * (temp / 2**16)
        humi = (self._buffer[6] << 8) | self._buffer[7]
        self._relative_humidity = 100 * (humi / 2**16)

    @property
    def data_ready(self) -> bool:
        """Check the sensor to see if new data is available"""
        self._send_command(_SCD4X_DATAREADY, cmd_delay=0.001)
        self._read_reply(self._buffer, 3)
        return not ((self._buffer[0] & 0x07 == 0) and (self._buffer[1] == 0))

    @property
    def serial_number(self) -> Tuple[int, int, int, int, int, int]:
        """Request a 6-tuple containing the unique serial number for this sensor"""
        self._send_command(_SCD4X_SERIALNUMBER, cmd_delay=0.001)
        self._read_reply(self._buffer, 9)
        return (
            self._buffer[0],
            self._buffer[1],
            self._buffer[3],
            self._buffer[4],
            self._buffer[6],
            self._buffer[7],
        )

    def stop_periodic_measurement(self) -> None:
        """Stop measurement mode"""
        self._send_command(_SCD4X_STOPPERIODICMEASUREMENT, cmd_delay=0.5)

    def start_periodic_measurement(self) -> None:
        """Put sensor into working mode, about 5s per measurement

        .. note::
            Only the following commands will work once in working mode:

            * :attr:`CO2 <scd4x.SCD4X.CO2>`
            * :attr:`temperature <scd4x.SCD4X.temperature>`
            * :attr:`relative_humidity <scd4x.SCD4X.relative_humidity>`
            * :meth:`data_ready() <scd4x.SCD4x.data_ready>`
            * :meth:`reinit() <scd4x.SCD4X.reinit>`
            * :meth:`factory_reset() <scd4x.SCD4X.factory_reset>`
            * :meth:`force_calibration() <scd4x.SCD4X.force_calibration>`
            * :meth:`self_test() <scd4x.SCD4X.self_test>`
            * :meth:`set_ambient_pressure() <scd4x.SCD4X.set_ambient_pressure>`

        """
        self._send_command(_SCD4X_STARTPERIODICMEASUREMENT)

    def start_low_periodic_measurement(self) -> None:
        """Put sensor into low power working mode, about 30s per measurement. See
        :meth:`start_periodic_measurement() <scd4x.SCD4X.start_perodic_measurement>`
        for more details.
        """
        self._send_command(_SCD4X_STARTLOWPOWERPERIODICMEASUREMENT)

    def persist_settings(self) -> None:
        """Save temperature offset, altitude offset, and selfcal enable settings to EEPROM"""
        self._send_command(_SCD4X_PERSISTSETTINGS, cmd_delay=0.8)

    def set_ambient_pressure(self, ambient_pressure: int) -> None:
        """Set the ambient pressure in hPa at any time to adjust CO2 calculations"""
        if ambient_pressure < 0 or ambient_pressure > 65535:
            raise AttributeError("`ambient_pressure` must be from 0~65535 hPascals")
        self._set_command_value(_SCD4X_SETPRESSURE, ambient_pressure)

    @property
    def temperature_offset(self) -> float:
        """Specifies the offset to be added to the reported measurements to account for a bias in
        the measured signal. Value is in degrees Celsius with a resolution of 0.01 degrees and a
        maximum value of 374 C

        .. note::
            This value will NOT be saved and will be reset on boot unless saved with
            persist_settings().

        """
        self._send_command(_SCD4X_GETTEMPOFFSET, cmd_delay=0.001)
        self._read_reply(self._buffer, 3)
        temp = (self._buffer[0] << 8) | self._buffer[1]
        return 175.0 * temp / 2**16

    @temperature_offset.setter
    def temperature_offset(self, offset: Union[int, float]) -> None:
        if offset > 374:
            raise AttributeError(
                "Offset value must be less than or equal to 374 degrees Celsius"
            )
        temp = int(offset * 2**16 / 175)
        self._set_command_value(_SCD4X_SETTEMPOFFSET, temp)

    @property
    def altitude(self) -> int:
        """Specifies the altitude at the measurement location in metres above sea level. Setting
        this value adjusts the CO2 measurement calculations to account for the air pressure's effect
        on readings.

        .. note::
            This value will NOT be saved and will be reset on boot unless saved with
            persist_settings().
        """
        self._send_command(_SCD4X_GETALTITUDE, cmd_delay=0.001)
        self._read_reply(self._buffer, 3)
        return (self._buffer[0] << 8) | self._buffer[1]

    @altitude.setter
    def altitude(self, height: int) -> None:
        if height > 65535:
            raise AttributeError("Height must be less than or equal to 65535 metres")
        self._set_command_value(_SCD4X_SETALTITUDE, height)

    def _check_buffer_crc(self, buf: bytearray) -> bool:
        for i in range(0, len(buf), 3):
            self._crc_buffer[0] = buf[i]
            self._crc_buffer[1] = buf[i + 1]
            if self._crc8(self._crc_buffer) != buf[i + 2]:
                raise RuntimeError("CRC check failed while reading data")
        return True

    def _send_command(self, cmd: int, cmd_delay: float = 0) -> None:
        self._cmd[0] = (cmd >> 8) & 0xFF
        self._cmd[1] = cmd & 0xFF

        try:
            self.i2c_device.writeto(self.address, self._cmd)
        except OSError as err:
            raise RuntimeError(
                "Could not communicate via I2C, some commands/settings "
                "unavailable while in working mode"
            ) from err
        time.sleep(cmd_delay)

    def _set_command_value(self, cmd, value, cmd_delay=0):
        self._buffer[0] = (cmd >> 8) & 0xFF
        self._buffer[1] = cmd & 0xFF
        self._crc_buffer[0] = self._buffer[2] = (value >> 8) & 0xFF
        self._crc_buffer[1] = self._buffer[3] = value & 0xFF
        self._buffer[4] = self._crc8(self._crc_buffer)
        self.i2c_device.writeto(self.address, self._buffer[:5])
        time.sleep(cmd_delay)

    def _read_reply(self, buff, num):
        self.i2c_device.readfrom_into(self.address, buff)
        self._check_buffer_crc(self._buffer[0:num])

    @staticmethod
    def _crc8(buffer: bytearray) -> int:
        crc = 0xFF
        for byte in buffer:
            crc ^= byte
            for _ in range(8):
                if crc & 0x80:
                    crc = (crc << 1) ^ 0x31
                else:
                    crc = crc << 1
        return crc & 0xFF  # return the bottom 8 bits
