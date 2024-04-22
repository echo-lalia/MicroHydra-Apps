import esp32
import time

# IR TX class for ESP32
# micropython v1.17 - v1.18(latest as of 2022/5)

class UpyIrTx():

    def __init__(self, ch, pin, freq=38000, duty=99, idle_level=0):
        self._raise = False
        if freq <= 0 or duty <= 0 or duty >= 100 or ch < 0 or ch > 7:
            raise(IndexError())
        if idle_level:
            self._rmt = esp32.RMT(ch, pin=pin, clock_div=80, tx_carrier=(freq, (100-duty), 0), idle_level=True)
            self._posi = 0
        else:
            self._rmt = esp32.RMT(ch, pin=pin, clock_div=80, tx_carrier=(freq, duty, 1), idle_level=False)
            self._posi = 1

    def send_raw(self, signal_tuple):
        # Blocking until transmission
        # Value[us] must be less than 32,768(15bit)
        if signal_tuple:
            self._rmt.write_pulses(signal_tuple, self._posi)
            self._rmt.wait_done(timeout=2000)
        return(True)
    
    def send(self, signal_tuple):
        # Blocking until transmission
        # Value[us] is free
        if not signal_tuple:
            return(True)
        overindex = []
        offsets = []
        cumsum = 0
        len_signal = len(signal_tuple)
        if len_signal % 2 == 0:
            return(False)
        for i in range(len_signal):
            if signal_tuple[i] >= 32768:
                if i % 2 == 0:
                    return(False)
                else:
                    overindex.append(i)
                    offsets.append(cumsum)
                    cumsum = 0
            else:
                cumsum += signal_tuple[i]
        if len(overindex) == 0:
            self._rmt.write_pulses(signal_tuple, self._posi)
            self._rmt.wait_done(timeout=2000)
        else:
            last_index = 0
            for i in range(len(overindex)):
                self._rmt.write_pulses(signal_tuple[last_index: overindex[i]], self._posi)
                time.sleep_us(signal_tuple[overindex[i]]+offsets[i])
                last_index = overindex[i] + 1
            self._rmt.write_pulses(signal_tuple[last_index: len_signal], self._posi)
            self._rmt.wait_done(timeout=2000)
        return(True)

    def send_cls(self, ir_rx):
        # Blocking until transmission
        if ir_rx.get_record_size() != 0:
            return(self.send(ir_rx.get_calibrate_list()))
        else:
            return(False)
