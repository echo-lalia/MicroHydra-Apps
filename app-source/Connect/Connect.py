import uasyncio as asyncio
import ujson as json
import network
import os
import gc
from lib.hydra.config import Config  # Import the Config class
from lib.battlevel import Battery  # Import the Battery class
from lib import display
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ _CONSTANTS: ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
_MH_DISPLAY_HEIGHT = const(135)
_MH_DISPLAY_WIDTH = const(240)
_DISPLAY_WIDTH_HALF = const(_MH_DISPLAY_WIDTH // 2)

_CHAR_WIDTH = const(8)
_CHAR_WIDTH_HALF = const(_CHAR_WIDTH // 2)


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ GLOBAL_OBJECTS: ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# init object for accessing display
DISPLAY = display.Display(use_tiny_buf=True)

# Create a global config instance
config = Config()

# Create a global battery instance
battery = Battery()

# Function to connect to WiFi using settings from config.json
def connect_wifi():
    ssid = config['wifi_ssid']
    password = config['wifi_pass']

    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(ssid, password)

    print(f"Connecting to {ssid}...")
    while not wlan.isconnected():
        pass

    print('Connected to WiFi')
    print('Network config:', wlan.ifconfig())
    
    DISPLAY.fill(config.palette[2])
    # write current text to framebuffer
    txt = wlan.ifconfig()[0]
    DISPLAY.text(
        text=txt,
        # center text on x axis:
        x=_DISPLAY_WIDTH_HALF - (len(txt) * _CHAR_WIDTH_HALF), 
        y=50,
        color=config.palette[8]
        )
    
    # write framebuffer to display
    DISPLAY.show()

    # Update system info with current WiFi info
    sys_info['wifi_ssid'] = ssid
    sys_info['wifi_ip'] = wlan.ifconfig()[0]

# Function to update system info with real data
def update_sys_info():
    # Get filesystem stats
    statvfs = os.statvfs('/')
    total_space = (statvfs[0] * statvfs[2]) // 1024  # Total space in KB
    free_space = (statvfs[0] * statvfs[3]) // 1024   # Free space in KB

    # Get memory info
    free_memory = gc.mem_free() // 1024  # Free memory in KB
    total_memory = (gc.mem_free()+gc.mem_alloc()) // 1024  # Total memory in KB

    # Get build information
    build_info = os.uname()

    # Get battery info
    battery_level = battery.read_level()
    battery_pct = battery.read_pct()

    # Update sys_info dictionary with real values
    sys_info.update({
        'free_memory': f"{free_memory} KB",
        'total_memory': f"{total_memory} KB",
        'free_space': f"{free_space} KB",
        'total_space': f"{total_space} KB",
        'wifi_ssid': config['wifi_ssid'],
        'wifi_ip': '',  # Will be updated after WiFi connection
        'battery_status': 'Charging' if battery_level > 0 else 'Not Charging',
        'battery_level': f"{battery_pct}%",
        'version': 'V2.1',  # Example version, adjust as needed
        'build': f"{build_info.sysname} {build_info.release} {build_info.version}",
    })

# Initialize system info dictionary
sys_info = {
    'free_memory': '',
    'total_memory': '',
    'free_space': '',
    'total_space': '',
    'wifi_ssid': '',
    'wifi_ip': '',
    'battery_status': 'Unknown',  # Placeholder
    'battery_level': 'Unknown',   # Placeholder
    'version': 'V2.1',
    'build': '',
}

# HTTP server to handle requests
async def serve_client(reader, writer):
    try:
        request_line = await reader.readline()
        print("Request:", request_line)

        # Read headers
        while await reader.readline() != b"\r\n":
            pass

        # Parse HTTP request
        request_line = request_line.decode('utf-8')
        method, path, _ = request_line.split()
        
        if path == '/sysinfo' and method == 'GET':
            response = json.dumps(sys_info)
            await send_response(writer, response)

        elif path == '/settings' and method == 'GET':
            response = json.dumps(config.config)  # Return current settings
            await send_response(writer, response)

        elif path == '/settings_modify' and method == 'POST':
            # Read the request body
            print("Enter Modify")
            # Read the request body in chunks
            body = b""
            while True:
                chunk = await reader.read(1)  # Read in 512-byte chunks
                body += chunk
                if chunk == b"}":
                    break
            print(f'body is {body}')
            new_settings = json.loads(body.decode('utf-8'))
            print(new_settings)
            # Update settings
            for key in new_settings:
                if key in config.config:
                    config[key] = new_settings[key]  # Update config using the class method

            config.save()  # Save updated config
            response = json.dumps({"status": "success", "message": "Settings updated successfully."})
            await send_response(writer, response)

        else:
            # 404 Not Found
            response = json.dumps({"status": "error", "message": "Not Found"})
            await send_response(writer, response, status_code="404 Not Found")
    
    except Exception as e:
        print(f"Error handling request: {e}")
    
    finally:
        await writer.aclose()

async def send_response(writer, response, status_code="200 OK"):
    writer.write(f"HTTP/1.0 {status_code}\r\n".encode('utf-8'))
    writer.write("Content-Type: application/json\r\n".encode('utf-8'))
    writer.write("Connection: close\r\n\r\n".encode('utf-8'))
    writer.write(response.encode('utf-8'))
    await writer.drain()

async def main():
    # Update system information with real data
    update_sys_info()

    # Connect to WiFi
    connect_wifi()

    # Start the server
    print('Starting server...')
    server = await asyncio.start_server(serve_client, "0.0.0.0", 5000)
    while True:
        await asyncio.sleep(3600)  # Run indefinitely

try:
    asyncio.run(main())
except Exception as e:
    print("An error occurred:", e)

