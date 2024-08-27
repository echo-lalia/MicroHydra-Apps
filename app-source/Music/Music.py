from lib.display import Display
from lib.hydra.config import Config
from lib.userinput import UserInput
from lib.hydra.beeper import Beeper
from lib.hydra.popup import UIOverlay
from font import vga2_16x32 as font
from font import vga1_8x16 as small_font  # Import a smaller font
import os, machine, time, math, framebuf, random, urequests
from machine import SDCard, Pin
from micropython import const
machine.freq(240000000)

"""
Music App
Version: 1

Description:
Gets wav files from a directory on the sd card called 'music'. It then lists this files to be selected and played.

Arrow keys to navigate/change songs, enter to play/pause.

Add this code to the launcher.py for the icon:
_MUSIC_ICON = const("a20,2,20,20,18,24,16,24,12,24,12,20,12,16,16,16,18,16,18,4,10,6,10,24,8,28,6,28,2,28,2,24,2,20,6,20,8,20,8,4,8,2,10,1,22,0,24,0,24,2ut,a14,16,14,20,16,22,18,20,18,16ut")
"""

# Constants
_DISPLAY_HEIGHT = const(135)
_DISPLAY_WIDTH = const(240)
_CHAR_HEIGHT = const(32)
_ITEMS_PER_SCREEN = const(_DISPLAY_HEIGHT // _CHAR_HEIGHT)
_CHARS_PER_SCREEN = const(_DISPLAY_WIDTH // 16)
_SCROLL_TIME = const(5000)  # ms per one text scroll
_SCROLLBAR_WIDTH = const(3)
_SCROLLBAR_START_X = const(_DISPLAY_WIDTH - _SCROLLBAR_WIDTH)

# New constants for the smaller font
_SMALL_CHAR_HEIGHT = const(16)
_SMALL_CHAR_WIDTH = const(8)
_SMALL_CHARS_PER_SCREEN = const(_DISPLAY_WIDTH // _SMALL_CHAR_WIDTH)

# Define pin constants
_SCK_PIN = const(41)
_WS_PIN = const(43)
_SD_PIN = const(42)

# Initialize hardware                                                                                                                                                                                                                                                                                                                                      
tft = Display()

config = Config()
kb = UserInput()
overlay = UIOverlay()
beep = Beeper()

sd = None
i2s = None

def mount_sd():
    global sd
    try:
        if sd is None:
            sd = SDCard(slot=2, sck=Pin(40), miso=Pin(39), mosi=Pin(14), cs=Pin(12))
        os.mount(sd, '/sd')
        print("SD card mounted successfully")
    except OSError as e:
        print("Could not mount SDCard:", str(e))
        overlay.error("SD Card Mount Error")

def read_wav_header(file):
    file.seek(0)
    riff = file.read(12)
    fmt = file.read(24)
    data_hdr = file.read(8)
    
    sample_rate = int.from_bytes(fmt[12:16], 'little')
    return sample_rate * 2

def setup_i2s(sample_rate):
    global i2s
    i2s = machine.I2S(0,
                      sck=machine.Pin(_SCK_PIN),
                      ws=machine.Pin(_WS_PIN),
                      sd=machine.Pin(_SD_PIN),
                      mode=machine.I2S.TX,
                      bits=16,
                      format=machine.I2S.MONO,
                      rate=sample_rate,
                      ibuf=1024)
        
def display_play_screen(selected_file):
    # Clear the screen
    tft.fill(config["bg_color"])
    
    # Display song info
    parts = selected_file.rsplit('.', 1)[0].split(' - ')
    
    if len(parts) == 3:
        artist, album, song = parts
        info = [
            f"Artist: {artist}",
            f"Album: {album}",
            f"Song: {song}"
        ]
    else:
        info = [f"Playing: {selected_file}"]
    
    # Calculate starting y position to center the text vertically
    total_height = len(info) * _SMALL_CHAR_HEIGHT
    start_y = (_DISPLAY_HEIGHT - total_height) // 2
    
    for idx, text in enumerate(info):
        y = start_y + idx * _SMALL_CHAR_HEIGHT
        x = 10  # Left align with a small margin
        
        # Truncate text if it's too long
        if len(text) > _SMALL_CHARS_PER_SCREEN:
            text = text[:_SMALL_CHARS_PER_SCREEN - 3] + "..."
        
        tft.text( text, x, y, config.palette[4], font=small_font)
    
    tft.show()

def format_time(seconds):
    minutes, secs = divmod(int(seconds), 60)
    return f"{minutes:02d}:{secs:02d}"

class EasyWavMenu:
    def __init__(self, tft, config):
        self.tft = tft
        self.config = config
        self.main_items = ['Library', 'Shuffle', 'Settings']
        self.library_items = ['Artists', 'Albums', 'Songs']
        self.cursor_index = 0
        self.view_index = 0
        self.current_view = 'main'
        self.items = self.main_items
        self.artists = []
        self.albums = []
        self.songs = []
        self.songs_by_artist = {}
        self.songs_by_album = {}
        self.current_artist = None
        self.current_album = None
        self.populate_music_lists()
    
    def populate_music_lists(self):
        music_dir = '/sd/music'  # Adjust this path as needed
        self.artists = []
        self.albums = []
        self.songs = []
        self.songs_by_artist = {}
        self.songs_by_album = {}

        try:
            for filename in os.listdir(music_dir):
                if filename.endswith('.wav'):
                    parts = filename[:-4].split(' - ')
                    if len(parts) == 3:
                        artist, album, song = parts
                        
                        if artist not in self.artists:
                            self.artists.append(artist)
                            self.songs_by_artist[artist] = []
                        
                        if album not in self.albums:
                            self.albums.append(album)
                            self.songs_by_album[album] = []
                        
                        if song not in self.songs:
                            self.songs.append(song)
                        
                        self.songs_by_artist[artist].append(song)
                        self.songs_by_album[album].append(song)

            # Sort the lists
            self.artists.sort()
            self.albums.sort()
            self.songs.sort()
            for artist in self.songs_by_artist:
                self.songs_by_artist[artist].sort()
            for album in self.songs_by_album:
                self.songs_by_album[album].sort()

        except OSError as e:
            print(f"Error accessing music directory: {e}")

    def draw(self):
        self.tft.fill(self.config["bg_color"])
        if self.current_view == 'main':
            self._draw_items(self.main_items)
        elif self.current_view == 'library_submenu':
            self._draw_items(self.library_items)
        elif self.current_view == 'artists':
            self._draw_items(self.artists)
        elif self.current_view == 'albums':
            self._draw_items(self.albums)
        elif self.current_view == 'songs':
            self._draw_items(self.songs)
        elif self.current_view == 'artist_songs':
            self._draw_items(self.songs_by_artist[self.current_artist])
        elif self.current_view == 'album_songs':
            self._draw_items(self.songs_by_album[self.current_album])
        self.tft.show()

    def _draw_items(self, items):
        current_time = time.ticks_ms()
        for idx, item in enumerate(items[self.view_index:self.view_index + _ITEMS_PER_SCREEN]):
            is_selected = idx + self.view_index == self.cursor_index
            color = self.config.palette[5] if is_selected else self.config.palette[4]
            
            # Apply ping-pong scrolling only to the selected item if it's long
            if is_selected and len(item) > _CHARS_PER_SCREEN - 2:
                scroll_distance = (len(item) - _CHARS_PER_SCREEN + 1) * 8  # Adjust for 8x8 font
                x = int(self.ping_pong_ease(current_time, _SCROLL_TIME) * scroll_distance)
                x = -x  # Reverse direction
            else:
                x = 0

            self.tft.text( item, x, idx * _CHAR_HEIGHT, color, font=font)

    def get_full_filename(self, song):
            for artist in self.songs_by_artist:
                if song in self.songs_by_artist[artist]:
                    for album in self.songs_by_album:
                        if song in self.songs_by_album[album]:
                            return f"{artist} - {album} - {song}.wav"
            return None

    def select(self):
        if self.current_view == 'main':
            selected_item = self.main_items[self.cursor_index]
            if selected_item == 'Library':
                self.current_view = 'library_submenu'
                self.cursor_index = 0
                self.view_index = 0
                self.items = self.library_items
            elif selected_item == 'Shuffle':
                return self.shuffle_play()
            elif selected_item == 'Settings':
                return self.show_coming_soon_message()
        elif self.current_view == 'library_submenu':
            selected_item = self.library_items[self.cursor_index]
            if selected_item == 'Artists':
                self.current_view = 'artists'
                self.cursor_index = 0
                self.view_index = 0
                self.items = self.artists
            elif selected_item == 'Songs':
                self.current_view = 'songs'
                self.cursor_index = 0
                self.view_index = 0
                self.items = self.songs
            elif selected_item == 'Albums':
                self.current_view = 'albums'
                self.cursor_index = 0
                self.view_index = 0
                self.items = self.albums
            else:
                return self.show_coming_soon_message(f"{selected_item} view")
        elif self.current_view == 'artists':
            self.current_artist = self.artists[self.cursor_index]
            self.current_view = 'artist_songs'
            self.cursor_index = 0
            self.view_index = 0
            self.items = self.songs_by_artist[self.current_artist]
        elif self.current_view == 'albums':
            self.current_album = self.albums[self.cursor_index]
            self.current_view = 'album_songs'
            self.cursor_index = 0
            self.view_index = 0
            self.items = self.songs_by_album[self.current_album]
        elif self.current_view in ['songs', 'artist_songs', 'album_songs']:
            selected_song = self.items[self.cursor_index]
            full_filename = self.get_full_filename(selected_song)
            if full_filename:
                return "play", full_filename
        return "refresh"

    def shuffle_play(self):
        if self.songs:
            random_song = random.choice(self.songs)
            full_filename = self.get_full_filename(random_song)
            if full_filename:
                return "play_shuffle", full_filename
        print("No songs available for shuffle play")
        return None

    def show_coming_soon_message(self, feature="Settings"):
        overlay.draw_textbox(f"{feature}", _DISPLAY_WIDTH//2, _DISPLAY_HEIGHT//2 - 10)
        overlay.draw_textbox("in progress", _DISPLAY_WIDTH//2, _DISPLAY_HEIGHT//2 + 10)
        self.tft.show()
        time.sleep(2)
        return "refresh"

    def up(self):
        if self.cursor_index > 0:
            self.cursor_index -= 1
            if self.cursor_index < self.view_index:
                self.view_index = self.cursor_index
        elif self.cursor_index == 0 and self.view_index > 0:
            self.view_index -= 1
            self.cursor_index = self.view_index

    def down(self):
        if self.cursor_index < len(self.items) - 1:
            self.cursor_index += 1
            if self.cursor_index >= self.view_index + _ITEMS_PER_SCREEN:
                self.view_index = self.cursor_index - _ITEMS_PER_SCREEN + 1

    def back(self):
        if self.current_view == 'library_submenu':
            self.current_view = 'main'
            self.items = self.main_items
        elif self.current_view in ['artists', 'albums', 'songs']:
            self.current_view = 'library_submenu'
            self.items = self.library_items
        elif self.current_view == 'artist_songs':
            self.current_view = 'artists'
            self.items = self.artists
            self.current_artist = None
        elif self.current_view == 'album_songs':
            self.current_view = 'albums'
            self.items = self.albums
            self.current_album = None
        else:
            return False
        self.cursor_index = 0
        self.view_index = 0
        return True

    def handle_input(self, key):
        if key == ";":
            self.up()
            return "up"
        elif key == ".":
            self.down()
            return "down"
        elif key in ("ENT", "SPC"):
            return self.select()
        elif key in ("`", "DEL", "ESC", "BKSP"):
            if self.back():
                return "back"
            else:
                return "exit"
        return None
    
    def ping_pong_ease(self, value, maximum):
        odd_pong = ((value // maximum) % 2 == 1)
        fac = self.ease_in_out_sine((value % maximum) / maximum)
        return 1 - fac if odd_pong else fac

    def ease_in_out_sine(self, x):
        return -(math.cos(math.pi * x) - 1) / 2

def play_sound(notes, time_ms=30):
    if config['ui_sound']:
        beep.play(notes, time_ms, config['volume'])

def main_loop():
    mount_sd()
    view = EasyWavMenu(tft, config)
    
    while True:
        view.draw()
        
        new_keys = kb.get_new_keys()
        for key in new_keys:
            action = view.handle_input(key)
            
            if action == "up":
                play_sound(("G3","B3"), 30)
            elif action == "down":
                play_sound(("D3","B3"), 30)
            elif action == "select":
                play_sound(("G3","B3","D3"), 30)
                
            if isinstance(action, tuple) and action[0] in ["play", "play_shuffle"]:
                selected_file = action[1]
                
                try:
                    with open(f"/sd/music/{selected_file}", 'rb') as file:
                        display_play_screen(selected_file)
                        sample_rate = read_wav_header(file)
                        setup_i2s(sample_rate)
                        
                        while True:
                            data = file.read(1024)
                            if not data:
                                break
                            i2s.write(data)
                            
                            # Continuously check for new key presses during playback
                            new_keys = kb.get_new_keys()
                            for key in new_keys:
                                if key in ("`", "DEL", "ESC", "BKSP"):  # Exit playback
                                    break
                            else:
                                # Continue playing if no exit key is pressed
                                continue
                            
                            # If exit key is pressed, break the loop
                            break
                        
                        i2s.deinit()
                except Exception as e:
                    print(f"Error playing file: {str(e)}")
                    overlay.error(f"Playback Error: {str(e)[:20]}")
                    
            elif action == "back":
                play_sound(("D3","B3","G3"), 30)
            elif action == "exit":
                return  # Exit the app
        
        time.sleep_ms(10)


try:
    main_loop()
except Exception as e:
    print("Error:", str(e))
    overlay.error(str(e))
finally:
    if sd:
        os.umount('/sd')
        print("SD card unmounted")
