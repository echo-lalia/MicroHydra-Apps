from machine import Pin, disable_irq, enable_irq
from micropython import const
import time

# IR RX class for ESP32 & RaspberryPi pico

class UpyIrRx():
    # Default record stop condition
    WAIT_MS_DEFAULT  = const(5000)   # [ms]
    BLANK_MS_DEFAULT = const(200)    # [ms]
    MAX_DEFAULT      = const(1023)
    # Binary bytes per sample
    UNIT_BYTES = const(3)

    # Record mode
    MODE_STAND_BY  = const(0)    # stop recording
    MODE_DONE_OK   = const(1)
    MODE_DONE_NG   = const(2)
    MODE_READY     = const(3)    # run recording
    MODE_RECORDING = const(4)

    # Error code
    ERROR_NONE        = const(0)
    ERROR_NO_DATA     = const(1)
    ERROR_OVERFLOW    = const(2)
    ERROR_START_POINT = const(3)
    ERROR_END_POINT   = const(4)
    ERROR_TIMEOUT     = const(5)

    def __init__(self, pin, max_size=0, idle_level=1):
        self._pin = pin
        if max_size <= 0:
            self._max_size = UpyIrRx.MAX_DEFAULT
        else:
            if max_size % 2 == 0:
                self._max_size = max_size + 1
            else:
                self._max_size = max_size
        if idle_level:
            self._idle_level = 1
        else:
            self._idle_level = 0
        self._buffer = bytearray(self._max_size * UpyIrRx.UNIT_BYTES)
        self._record_size = 0
        self._mode = UpyIrRx.MODE_STAND_BY
        self._error = UpyIrRx.ERROR_NONE
        self._now = 0
        self._last = 0
        self._stop_size = 0
        dmy = self._pin.irq(trigger=Pin.IRQ_RISING | Pin.IRQ_FALLING, handler=self._callback)

    def get_mode(self):
        return(self._mode)

    def get_error_code(self):
        return(self._error)

    def get_record_buffer(self):
        if self._mode == UpyIrRx.MODE_DONE_OK:
            return(self._buffer)
        else:
            return(b'')

    def get_record_size(self):
        if self._mode == UpyIrRx.MODE_DONE_OK:
            return(self._record_size)
        else:
            return(0)

    def get_encode_bytes(self):
        return(UpyIrRx.UNIT_BYTES)

    def get_record_list(self):
        if self._mode == UpyIrRx.MODE_DONE_OK:
            return([int.from_bytes(self._buffer[i*UpyIrRx.UNIT_BYTES: (i+1)*UpyIrRx.UNIT_BYTES], 'little') for i in range(self._record_size)])
        else:
            return([])

    def get_calibrate_list(self):
        top32 = [9999]*32
        for i in range(self._record_size if self._record_size < 32 else 32):
            top32[i] = int.from_bytes(self._buffer[i*UpyIrRx.UNIT_BYTES: (i+1)*UpyIrRx.UNIT_BYTES], 'little')
        min_interval = min(top32)
        for i in range(31):
            if top32[i] < min_interval*1.4 and top32[i+1] < min_interval*1.4:
                basic_time = (top32[i]+top32[i+1]) // 2
                break
        else:
            return([])
        return([round(int.from_bytes(self._buffer[i*UpyIrRx.UNIT_BYTES: (i+1)*UpyIrRx.UNIT_BYTES], 'little')/basic_time)*basic_time for i in range(self._record_size)])

    def record(self, wait_ms=0, blank_ms=0, stop_size=0):
        if wait_ms <= 0:
            _wait_ms = UpyIrRx.WAIT_MS_DEFAULT
        else:
            _wait_ms = wait_ms
        if blank_ms <= 0:
            _blank_us = UpyIrRx.BLANK_MS_DEFAULT*1000
        else:
            _blank_us = blank_ms*1000
        if stop_size <= 0:
            self._stop_size = self._max_size
        else:
            if stop_size % 2 == 0:
                self._stop_size = stop_size + 1
            else:
                self._stop_size = stop_size
            if self._stop_size > self._max_size:
                self._stop_size = self._max_size
        self._record_size = 0
        self._error = UpyIrRx.ERROR_NONE
        if self._pin.value() != self._idle_level:
            self._mode = UpyIrRx.MODE_DONE_NG
            self._error = UpyIrRx.ERROR_START_POINT
            self._record_size = 0
            return(self._error)
        # begin recording
        self._mode = UpyIrRx.MODE_READY
        _start_us = time.ticks_us()
        time.sleep_ms(_wait_ms)
        # judgement
        if self._mode == UpyIrRx.MODE_DONE_NG:
            return(self._error)
        elif self._mode == UpyIrRx.MODE_DONE_OK:
            return(self._error)
        # begin critical
        irq_state = disable_irq()
        if self._mode == UpyIrRx.MODE_READY:
            self._mode = UpyIrRx.MODE_DONE_NG
            self._error = UpyIrRx.ERROR_NO_DATA
            self._record_size = 0
        elif time.ticks_diff(self._last, _start_us) + _blank_us > _wait_ms*1000:
            # < self._mode == UpyIrRx.MODE_RECORDING >
            self._mode = UpyIrRx.MODE_DONE_NG
            self._error = UpyIrRx.ERROR_TIMEOUT
            self._record_size = 0
        else:
            for i in range(self._record_size):
                if int.from_bytes(self._buffer[i*UpyIrRx.UNIT_BYTES: (i+1)*UpyIrRx.UNIT_BYTES], 'little') >= _blank_us:
                    self._record_size = i
                    break
            if self._record_size % 2 == 0:
                self._mode = UpyIrRx.MODE_DONE_NG
                self._error = UpyIrRx.ERROR_END_POINT
                self._record_size = 0
            else:
                self._mode = UpyIrRx.MODE_DONE_OK
                self._error = UpyIrRx.ERROR_NONE
        enable_irq(irq_state)
        # end critial
        return(self._error)

    def _callback(self, p):
        if self._mode == UpyIrRx.MODE_READY:
            self._last = time.ticks_us()
            self._mode = UpyIrRx.MODE_RECORDING
        elif self._mode == UpyIrRx.MODE_RECORDING:
            self._now = time.ticks_us()
            if self._record_size >= self._max_size:
                self._mode = UpyIrRx.MODE_DONE_NG
                self._error = UpyIrRx.ERROR_OVERFLOW
                self._record_size = 0
                return
            self._buffer[self._record_size*UpyIrRx.UNIT_BYTES: (self._record_size+1)*UpyIrRx.UNIT_BYTES] = time.ticks_diff(self._now, self._last).to_bytes(UpyIrRx.UNIT_BYTES, 'little')
            self._last = self._now
            self._record_size += 1
            if self._record_size >= self._stop_size:
                self._mode = UpyIrRx.MODE_DONE_OK
                self._error = UpyIrRx.ERROR_NONE
