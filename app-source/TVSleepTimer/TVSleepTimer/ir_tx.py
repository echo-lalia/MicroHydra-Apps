# Minimal raw-IR transmitter for the Cardputer's built-in IR LED.
# Adapted from UpyIrTx (https://github.com/meloncookie/RemotePy),
# as used by the MicroHydra "IR" app (https://github.com/ndrnmnk/mh_infrared).
#
# Sends a list of raw pulse durations (in microseconds, alternating
# mark/space) using the ESP32's RMT peripheral with a 38kHz IR carrier.

import esp32
from time import sleep_ms


class IRTransmitter:
    # duty=33 is the confirmed-working carrier duty for this device's
    # onboard IR LED with an LG TV (NEC address=0x04, command=0x08) --
    # found via the candidate-tester build of this app.
    def __init__(self, pin, channel=0, freq=38000, duty=33):
        self._pin = pin
        self._channel = channel
        self._freq = freq
        self.configure(duty=duty, invert=False)

    def send_raw(self, pulses, repeats=3, repeat_gap_ms=40):
        """Send a raw signal: a list/tuple of alternating mark/space
        durations in microseconds, e.g. [9000, 4500, 560, 560, ...].

        Sends the signal multiple times (with a short gap in between)
        by default, since a single IR frame is often missed by the
        receiver.
        """
        if not pulses:
            return False
        for i in range(repeats):
            self._rmt.write_pulses(pulses, self._posi)
            self._rmt.wait_done(timeout=2000)
            if i < repeats - 1:
                sleep_ms(repeat_gap_ms)
        return True

    def send_nec(self, address, command, repeats=3):
        """Encode and send a standard 32-bit NEC-protocol signal from an
        8-bit address and 8-bit command (the format most IR databases,
        including Flipper's, use for NEC-based remotes -- e.g. most LG
        TVs use address=0x04, command=0x08 for power).
        """
        return self.send_raw(encode_nec(address, command), repeats=repeats)

    def configure(self, duty=99, invert=False):
        """Reconfigure the carrier duty cycle / signal polarity used for
        subsequent sends. `invert=True` mirrors the alternate branch
        found in the original UpyIrTx library (idle-high output), in
        case a receiver expects the opposite polarity.
        """
        # release the previous RMT channel before claiming it again --
        # esp32.RMT raises if you try to re-init an already-active channel.
        old_rmt = getattr(self, "_rmt", None)
        if old_rmt is not None:
            try:
                old_rmt.deinit()
            except Exception:
                pass

        if invert:
            self._rmt = esp32.RMT(
                self._channel,
                pin=self._pin,
                clock_div=80,
                tx_carrier=(self._freq, (100 - duty), 0),
                idle_level=True,
            )
            self._posi = 0
        else:
            self._rmt = esp32.RMT(
                self._channel,
                pin=self._pin,
                clock_div=80,
                tx_carrier=(self._freq, duty, 1),
                idle_level=False,
            )
            self._posi = 1


def encode_nec(address, command):
    """Build the raw mark/space pulse list (in microseconds) for a
    standard NEC-protocol IR frame: a 9000/4500us leader, then the
    address byte, its inverse, the command byte, and its inverse -- each
    bit sent LSB-first as a 560us mark, followed by either a 560us (0)
    or 1690us (1) space -- and a final 560us mark to terminate the frame.
    """

    def encode_byte(byte):
        pulses = []
        for i in range(8):
            bit = (byte >> i) & 1
            pulses.append(560)
            pulses.append(1690 if bit else 560)
        return pulses

    addr_inv = (~address) & 0xFF
    cmd_inv = (~command) & 0xFF

    pulses = [9000, 4500]
    for byte in (address, addr_inv, command, cmd_inv):
        pulses.extend(encode_byte(byte))
    pulses.append(560)
    return pulses


def encode_nec_literal(byte0, byte1, byte2, byte3):
    """Build a raw NEC-shaped frame from 4 literal bytes, with no
    auto-computed complement bytes. Some LG sets/remotes (seen in the
    wild as protocol 'NECext') transmit an independent second
    address/command byte instead of the usual bitwise-inverse -- this
    covers that variant.
    """

    def encode_byte(byte):
        pulses = []
        for i in range(8):
            bit = (byte >> i) & 1
            pulses.append(560)
            pulses.append(1690 if bit else 560)
        return pulses

    pulses = [9000, 4500]
    for byte in (byte0, byte1, byte2, byte3):
        pulses.extend(encode_byte(byte))
    pulses.append(560)
    return pulses
