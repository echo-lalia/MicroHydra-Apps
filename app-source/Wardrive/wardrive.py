# wardrive.py — MicroHydra wardriving app for Cardputer ADV + LoRa/GPS cap + Glass2
#
# Hardware requirements:
#   - M5Stack Cardputer ADV (ESP32-S3)
#   - LoRa-1262 + GPS cap (ATGM336H on UART2, GPIO15=RX, GPIO13=TX, 115200 baud)
#   - M5Stack Glass2 Unit (SSD1309, I2C 0x3C, Grove GPIO1=SCL, GPIO2=SDA)
#   - microSD card (SPI, pre-mounted by MicroHydra)
#
# Install: copy to /apps/wardrive.py on the device
# Dependencies: ssd1306 (built into MicroHydra firmware), network, machine, uos, utime
#
# Controls:
#   A key      - Start / stop scanning
#   B key      - Save WiGLE CSV to SD card
#   Up/Down    - Scroll AP list
#   Enter      - AP detail view
#   Backquote  - Exit to launcher

import network
import utime
import uos
import struct
from machine import Pin, I2C, UART

# ── MicroHydra imports (fall back gracefully if run standalone) ──────────────
try:
    from lib.display import Display
    from lib.hydra.config import Config
    from lib.userinput import UserInput
    _mh_display = True
except ImportError:
    _mh_display = False

try:
    import ssd1306
    _has_ssd1306 = True
except ImportError:
    _has_ssd1306 = False

# ── Constants ──────────────────────────────────────────────────────────────────

GPS_UART    = 2
GPS_RX      = 15
GPS_TX      = 13
GPS_BAUD    = 115200

GROVE_SCL   = 1
GROVE_SDA   = 2
OLED_ADDR   = 0x3C
OLED_W      = 128
OLED_H      = 64

CHANNELS_UK = list(range(1, 14))   # 1-13
DWELL_MS    = 200                  # ms per channel (configurable)

WIGLE_HEADER = (
    "WigleWifi-1.4,appRelease=1.0,model=Cardputer,release=1.0,"
    "device=M5CardputerADV,display=,board=ESP32-S3,brand=M5Stack\n"
    "MAC,SSID,AuthMode,FirstSeen,Channel,RSSI,"
    "CurrentLatitude,CurrentLongitude,AltitudeMeters,AccuracyMeters,Type\n"
)

AUTHMODE_NAMES = {
    0: "OPEN",
    1: "WEP",
    2: "WPA",
    3: "WPA2",
    4: "WPA/WPA2",
    5: "WPA2-ENT",
    6: "WPA3",
    7: "WPA2/WPA3",
    8: "WAPI",
}


# ── NMEA parser ────────────────────────────────────────────────────────────────

class GPSState:
    def __init__(self):
        self.lat      = 0.0
        self.lon      = 0.0
        self.alt      = 0.0
        self.fix      = 0       # 0=no fix, 1=GPS, 2=DGPS
        self.sats     = 0
        self.time_str = ""      # "HH:MM:SS" UTC from GPS
        self.valid    = False

    def _dms_to_decimal(self, raw, hemi):
        # NMEA: ddmm.mmmm or dddmm.mmmm
        dot = raw.index(".")
        deg = int(raw[:dot - 2])
        mins = float(raw[dot - 2:])
        dec = deg + mins / 60.0
        if hemi in ("S", "W"):
            dec = -dec
        return dec

    def feed(self, line):
        try:
            line = line.strip()
            if not line.startswith("$"):
                return
            # strip checksum
            if "*" in line:
                line = line[:line.index("*")]
            parts = line.split(",")
            tag = parts[0][1:]  # e.g. "GPRMC" or "GPGGA"

            if tag in ("GPRMC", "GNRMC"):
                # $GPRMC,time,status,lat,N,lon,E,...
                if len(parts) < 7 or parts[2] != "A":
                    return
                t = parts[1]
                if len(t) >= 6:
                    self.time_str = f"{t[0:2]}:{t[2:4]}:{t[4:6]}"
                self.lat   = self._dms_to_decimal(parts[3], parts[4])
                self.lon   = self._dms_to_decimal(parts[5], parts[6])
                self.valid = True

            elif tag in ("GPGGA", "GNGGA"):
                # $GPGGA,time,lat,N,lon,E,fix,sats,hdop,alt,...
                if len(parts) < 10:
                    return
                self.fix  = int(parts[6]) if parts[6] else 0
                self.sats = int(parts[7]) if parts[7] else 0
                if parts[9]:
                    self.alt = float(parts[9])
        except Exception:
            pass  # ignore malformed sentences


# ── WiFi scan ─────────────────────────────────────────────────────────────────

def authmode_str(mode):
    return AUTHMODE_NAMES.get(mode, f"?{mode}")


def bssid_str(bssid_bytes):
    return ":".join(f"{b:02X}" for b in bssid_bytes)


class APRecord:
    __slots__ = ("ssid", "bssid", "channel", "rssi", "authmode",
                 "lat", "lon", "alt", "first_seen", "last_seen")

    def __init__(self, ssid, bssid, channel, rssi, authmode,
                 lat=0.0, lon=0.0, alt=0.0, timestamp=""):
        self.ssid       = ssid
        self.bssid      = bssid
        self.channel    = channel
        self.rssi       = rssi
        self.authmode   = authmode
        self.lat        = lat
        self.lon        = lon
        self.alt        = alt
        self.first_seen = timestamp
        self.last_seen  = timestamp

    def to_wigle_row(self):
        auth = f"[{authmode_str(self.authmode)}]"
        return (
            f"{self.bssid},{self.ssid},{auth},{self.first_seen},"
            f"{self.channel},{self.rssi},"
            f"{self.lat:.6f},{self.lon:.6f},{self.alt:.1f},5.0,WIFI\n"
        )


# ── Glass2 display ─────────────────────────────────────────────────────────────

class Glass2:
    def __init__(self):
        self._ready = False
        if not _has_ssd1306:
            return
        try:
            i2c = I2C(0, scl=Pin(GROVE_SCL), sda=Pin(GROVE_SDA), freq=400000)
            devices = i2c.scan()
            if OLED_ADDR in devices or 0x3D in devices:
                addr = OLED_ADDR if OLED_ADDR in devices else 0x3D
                self._oled = ssd1306.SSD1306_I2C(OLED_W, OLED_H, i2c, addr=addr)
                self._ready = True
        except Exception:
            pass

    def update(self, total_aps, new_aps, channel, gps):
        if not self._ready:
            return
        o = self._oled
        o.fill(0)
        o.text(f"APs: {total_aps:4d}", 0, 0)
        o.text(f"NEW: {new_aps:4d}", 0, 10)
        o.text(f"CH:  {channel:4d}", 0, 20)
        if gps.valid:
            lat_str = f"{abs(gps.lat):.4f}{'N' if gps.lat >= 0 else 'S'}"
            lon_str = f"{abs(gps.lon):.4f}{'E' if gps.lon >= 0 else 'W'}"
            o.text(f"GPS:{lat_str:>9s}", 0, 34)
            o.text(f"    {lon_str:>9s}", 0, 44)
            fix_label = ["NO FIX", "GPS   ", "DGPS  "].get(gps.fix, "?  ") if isinstance(["NO FIX", "GPS   ", "DGPS  "], list) else "?  "
            fix_labels = ["NO FIX", "GPS   ", "DGPS  "]
            fl = fix_labels[gps.fix] if gps.fix < len(fix_labels) else "?     "
            o.text(f"FIX:{fl} {gps.sats}s", 0, 54)
        else:
            o.text("GPS: NO FIX", 0, 34)
        o.show()

    def splash(self, line1, line2=""):
        if not self._ready:
            return
        self._oled.fill(0)
        self._oled.text(line1, 0, 24)
        if line2:
            self._oled.text(line2, 0, 36)
        self._oled.show()

    def clear(self):
        if not self._ready:
            return
        self._oled.fill(0)
        self._oled.show()


# ── SD card helpers ───────────────────────────────────────────────────────────

def sd_available():
    try:
        uos.stat("/sd")
        return True
    except OSError:
        return False


def save_wigle(ap_map, filename=None):
    if not sd_available():
        return False, "No SD card"
    if not ap_map:
        return False, "No APs to save"
    ts = utime.localtime()
    if filename is None:
        filename = f"/sd/wardrive_{ts[0]:04d}{ts[1]:02d}{ts[2]:02d}_{ts[3]:02d}{ts[4]:02d}.csv"
    try:
        with open(filename, "w") as f:
            f.write(WIGLE_HEADER)
            for rec in ap_map.values():
                f.write(rec.to_wigle_row())
        return True, filename
    except Exception as e:
        return False, str(e)


# ── Main app ──────────────────────────────────────────────────────────────────

def run():
    # ── hardware init ──
    gps_uart = UART(GPS_UART, baudrate=GPS_BAUD, rx=GPS_RX, tx=GPS_TX)
    # Request 10Hz update rate from AT6668 chip (CASIC proprietary command).
    # Default is 1Hz — 10Hz gives tighter GPS tags on each AP record.
    # $PCAS02,100*1E = 100ms interval (10Hz). Checksum is pre-calculated.
    utime.sleep_ms(500)  # let module settle before sending config
    gps_uart.write(b"$PCAS02,100*1E\r\n")
    gps = GPSState()
    glass2 = Glass2()
    glass2.splash("WARDRIVE", "Initialising...")

    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)

    ap_map = {}         # bssid_str -> APRecord
    channel_idx = 0
    current_ch  = CHANNELS_UK[0]
    scanning    = False
    scroll_pos  = 0
    status_msg  = "Press A to scan"
    last_hop    = utime.ticks_ms()
    last_glass2 = utime.ticks_ms()
    new_this_hop = 0

    # ── display setup ──
    if _mh_display:
        cfg = Config()
        disp = Display(cfg)
        keys_input = UserInput()
    else:
        disp = None
        keys_input = None

    def draw_main():
        if disp is None:
            return
        disp.fill(0)
        # header
        rec_str = "[*REC]" if scanning else "[    ]"
        disp.text(f"WARDRIVE {rec_str} {current_ch:2d}", 0, 0, 0xFFFF)
        disp.hline(0, 10, 240, 0x4228)
        # AP list (5 visible rows)
        items = list(ap_map.values())
        items.sort(key=lambda r: r.rssi, reverse=True)
        for i in range(5):
            idx = scroll_pos + i
            if idx >= len(items):
                break
            rec = items[idx]
            ssid_t = rec.ssid[:14] if rec.ssid else "<hidden>      "
            auth_t = authmode_str(rec.authmode)[:4]
            line = f"{'>' if i == 0 else ' '}{ssid_t:<14s} {rec.rssi:4d} {auth_t} {rec.channel:2d}"
            disp.text(line, 0, 14 + i * 10, 0xFFFF)
        # footer
        disp.hline(0, 64, 240, 0x4228)
        disp.text(f"[A]Scan [B]Save  {len(ap_map):3d}APs", 0, 68, 0x07E0)
        disp.text(status_msg[:30], 0, 78, 0xAD55)
        disp.show()

    nmea_buf = b""

    while True:
        # ── GPS feed ──
        if gps_uart.any():
            chunk = gps_uart.read(256)
            if chunk:
                nmea_buf += chunk
                while b"\n" in nmea_buf:
                    line, nmea_buf = nmea_buf.split(b"\n", 1)
                    gps.feed(line.decode("ascii", "ignore"))

        # ── channel hop + scan ──
        now = utime.ticks_ms()
        if scanning and utime.ticks_diff(now, last_hop) >= DWELL_MS:
            channel_idx = (channel_idx + 1) % len(CHANNELS_UK)
            current_ch  = CHANNELS_UK[channel_idx]
            new_this_hop = 0
            last_hop = now

            try:
                nets = wlan.scan()
                ts = gps.time_str if gps.valid and gps.time_str else f"up{utime.ticks_ms()//1000}"
                for ssid_b, bssid_b, ch, rssi, authmode, hidden in nets:
                    ssid = ssid_b.decode("utf-8", "ignore").strip("\x00")
                    mac  = bssid_str(bssid_b)
                    if mac not in ap_map:
                        ap_map[mac] = APRecord(
                            ssid, mac, ch, rssi, authmode,
                            lat=gps.lat, lon=gps.lon, alt=gps.alt,
                            timestamp=ts,
                        )
                        new_this_hop += 1
                    else:
                        ap_map[mac].rssi      = rssi
                        ap_map[mac].last_seen = ts
            except Exception:
                pass

        # ── Glass2 update (every ~1s) ──
        if utime.ticks_diff(now, last_glass2) >= 1000:
            glass2.update(len(ap_map), new_this_hop, current_ch, gps)
            last_glass2 = now

        # ── main screen ──
        draw_main()

        # ── key handling ──
        keys = keys_input.get_new_keys() if keys_input else []

        for k in keys:
            if k == "A":
                scanning = not scanning
                status_msg = "Scanning..." if scanning else "Paused"
                new_this_hop = 0
            elif k == "B":
                ok, msg = save_wigle(ap_map)
                status_msg = f"Saved {len(ap_map)} APs" if ok else f"Err: {msg}"
                glass2.splash("SAVED" if ok else "ERROR", msg[-13:] if not ok else f"{len(ap_map)}APs")
            elif k == "UP":
                scroll_pos = max(0, scroll_pos - 1)
            elif k == "DOWN":
                scroll_pos = min(max(0, len(ap_map) - 5), scroll_pos + 1)
            elif k in ("ESC", "`", "BSPC"):
                glass2.clear()
                wlan.active(False)
                return  # back to MicroHydra launcher

        utime.sleep_ms(50)


# MicroHydra entry point
run()
