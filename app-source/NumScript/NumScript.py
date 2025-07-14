"""
Numputer Script Editor for MicroHydra (Cardputer)
"""

import time
from lib import display, userinput
from lib.hydra import config
from font import vga1_8x16 as midfont

# ------------------------ Constants & Globals ------------------------
_MH_DISPLAY_HEIGHT = const(135)
_MH_DISPLAY_WIDTH = const(240)

DISPLAY = display.Display()
CONFIG = config.Config()
INPUT = userinput.UserInput()

script_lines = [""]
cursor_line = 0
result = ""
variables = {}

valid_chars = "1234567890+-*/=()<>'\"^~,.qwertyuiopasdfghjklzxcvbnm[]\\`;,:"
cardputer_keys = [
    "0", "1", "2", "3", "4", "5", "6", "7", "8", "9",
    "a", "b", "c", "d", "e", "f", "g", "h", "i", "j",
    "k", "l", "m", "n", "o", "p", "q", "r", "s", "t",
    "u", "v", "w", "x", "y", "z",
    "[", "]", "\\", "`", ";", "'", "\"", ".", "/", ",", ":",
    "ENT", "BSPC", "DEL", "ESC", "TAB", "SPC", "UP", "DOWN", "LEFT", "RIGHT"
]

terminal_log = []

# ----------------------------- Menu Constants -----------------------------
MENU_SCREEN_MAIN = 0
MENU_SCREEN_VARS = 1
MENU_SCREEN_INFO = 2
MENU_SCREEN_SAFEFILE = 3
MENU_SCREEN_TERMINAL = 4

LINES_PER_PAGE = 5
menu_screen = None
menu_selection = 0
scroll_offset = 0

# ------------------------- Helper Functions --------------------------
def pressed_key(key, pressed_keys):
    return key in pressed_keys

def process_key_macros(expr, pressed_keys):
    # Replace key(x) with "1" if pressed, else "0"
    while "key(" in expr:
        start = expr.find("key(")
        end = expr.find(")", start)
        if end == -1:
            break  # unmatched parentheses
        inside = expr[start + 4:end].strip()
        # Accept single character without quotes
        if len(inside) == 1 and inside in cardputer_keys:
            is_pressed = "1" if pressed_key(inside, pressed_keys) else "0"
            expr = expr[:start] + is_pressed + expr[end + 1:]
        else:
            # Invalid usage if not a single character in cardputer_keys
            return "invalid key() usage"
    return expr

def replace_variables(expr):
    # Replace variables only as whole words to avoid partial replacements
    # For simplicity, a basic replace - can be improved with regex if needed
    for var in variables:
        val = variables[var]
        expr = expr.replace(var, str(val))
    return expr

def log(value):
    terminal_log.append(str(value))

def evaluate_expression(expr, pressed_keys):
    expr = expr.strip()
    expr = process_key_macros(expr, pressed_keys)
    if "invalid" in expr:
        return expr

    try:
        if "=" in expr and "==" not in expr:
            var, val_expr = expr.split("=", 1)
            var = var.strip()
            val_expr = replace_variables(val_expr.strip())
            val = eval(val_expr)
            variables[var] = val
            return var + "=" + str(val)
        else:
            expr_eval = replace_variables(expr)
            # Allow log() in eval context
            local_vars = variables.copy()
            local_vars["log"] = log
            val = eval(expr_eval, {}, local_vars)
            return str(val)
    except Exception as e:
        return "Error: " + str(e)

def run_full_script(pressed_keys):
    global terminal_log
    terminal_log = []
    line = 0
    while line < len(script_lines):
        if script_lines[line].strip():
            res = evaluate_expression(script_lines[line], pressed_keys)
            # If the expression uses log(), output is in terminal_log already
            # Otherwise, add the result if it's not an assignment
            if res is not None and not res.startswith("Error") and not ("=" in script_lines[line] and "==" not in script_lines[line]):
                #terminal_log.append(str(res))
                pass
                    #print(res)
                    #terminal_log.append(str(res))
        line = line + 1

def draw_script_screen():
    DISPLAY.fill(CONFIG.palette[2])
    DISPLAY.text("Script Mode", 10, 5, CONFIG.palette[8], midfont)
    for i in range(min(len(script_lines), LINES_PER_PAGE)):
        idx = i + scroll_offset
        if idx >= len(script_lines):
            break
        prefix = "=> " if idx == cursor_line else "   "
        DISPLAY.text(prefix + script_lines[idx], 10, 25 + i * 20, CONFIG.palette[8], midfont)
    DISPLAY.show()

def show_variables():
    DISPLAY.fill(CONFIG.palette[2])
    DISPLAY.text("Variables:", 10, 10, CONFIG.palette[8], midfont)
    var_names = list(variables.keys())
    for i in range(LINES_PER_PAGE):
        idx = i + scroll_offset
        if idx < len(var_names):
            var = var_names[idx]
            DISPLAY.text(f"{var} = {variables[var]}", 10, 30 + i * 20, CONFIG.palette[8], midfont)
    DISPLAY.text("ESC: Back", 10, 120, CONFIG.palette[8], midfont)
    DISPLAY.show()

def show_info():
    DISPLAY.fill(CONFIG.palette[2])
    info_lines = [
        "Numputer Script Editor",
        "ENTER: New Line",
        "SHIFT+ENTER: Run Line",
        "log('msg') to log",
        "DEL clears terminal",
        "UP(;)/DOWN(.) scroll",
        "Use key(x) to check key press",
        "Use == for comparison",
    ]
    for i in range(LINES_PER_PAGE):
        idx = i + scroll_offset
        if idx < len(info_lines):
            DISPLAY.text(info_lines[idx], 10, 10 + i * 20, CONFIG.palette[8], midfont)
    DISPLAY.text("ESC: Back", 10, 120, CONFIG.palette[8], midfont)
    DISPLAY.show()

def show_terminal():
    DISPLAY.fill(CONFIG.palette[2])
    DISPLAY.text("Terminal Output", 10, 5, CONFIG.palette[8], midfont)
    for i in range(LINES_PER_PAGE):
        idx = i + scroll_offset
        if idx < len(terminal_log):
            DISPLAY.text(terminal_log[idx], 10, 25 + i * 20, CONFIG.palette[8], midfont)
    DISPLAY.text("DEL: Clear | ESC", 10, 120, CONFIG.palette[8], midfont)
    DISPLAY.show()

def show_menu():
    options = ["Run Full Script", "View Variables", "View Terminal", "Info", "Back"]
    DISPLAY.fill(CONFIG.palette[2])
    DISPLAY.text("Menu:", 10, 10, CONFIG.palette[8], midfont)
    for i, opt in enumerate(options):
        prefix = "-> " if i == menu_selection else "   "
        DISPLAY.text(prefix + opt, 10, 30 + i * 20, CONFIG.palette[8], midfont)
    DISPLAY.show()
    return options

# ----------------------------- Main Loop -----------------------------
def main_loop():
    global cursor_line, scroll_offset, menu_screen, menu_selection, script_lines, result

    while True:
        keys = INPUT.get_new_keys()
        pressed_keys = INPUT.get_pressed_keys()

        if menu_screen is None:
            if keys:
                key = str(keys[0])
                if key == "TAB":
                    menu_screen = MENU_SCREEN_MAIN
                    scroll_offset = 0
                    menu_selection = 0
                elif key == "ENT":
                    if "SHIFT" in pressed_keys:
                        # Evaluate current line
                        line = script_lines[cursor_line]
                        res = evaluate_expression(line, pressed_keys)
                        terminal_log.append(res)
                        # Also update result so user sees it on screen
                        result = res
                    else:
                        # New line below
                        script_lines.insert(cursor_line + 1, "")
                        cursor_line += 1
                        if cursor_line >= scroll_offset + LINES_PER_PAGE:
                            scroll_offset += 1
                elif key == "BSPC":
                    line = script_lines[cursor_line]
                    if line:
                        script_lines[cursor_line] = line[:-1]
                    else:
                        if len(script_lines) > 1:
                            script_lines.pop(cursor_line)
                            cursor_line = max(cursor_line - 1, 0)
                elif key == "UP" or key == ";":
                    cursor_line = max(0, cursor_line - 1)
                    if cursor_line < scroll_offset:
                        scroll_offset = max(0, scroll_offset - 1)
                elif key == "DOWN" or key == ".":
                    cursor_line = min(len(script_lines) - 1, cursor_line + 1)
                    if cursor_line >= scroll_offset + LINES_PER_PAGE:
                        scroll_offset += 1
                elif key in valid_chars or key == "SPC":
                    script_lines[cursor_line] += " " if key == "SPC" else key
            draw_script_screen()

        elif menu_screen == MENU_SCREEN_MAIN:
            options = show_menu()
            if keys:
                key = str(keys[0])
                if key == "UP" or key == ";":
                    menu_selection = (menu_selection - 1) % len(options)
                elif key == "DOWN" or key == ".":
                    menu_selection = (menu_selection + 1) % len(options)
                elif key == "ENT":
                    sel = options[menu_selection]
                    if sel == "Run Full Script":
                        run_full_script(pressed_keys)
                        menu_screen = MENU_SCREEN_TERMINAL
                        scroll_offset = 0
                    elif sel == "View Variables":
                        menu_screen = MENU_SCREEN_VARS
                        scroll_offset = 0
                    elif sel == "View Terminal":
                        menu_screen = MENU_SCREEN_TERMINAL
                        scroll_offset = 0
                    elif sel == "Info":
                        menu_screen = MENU_SCREEN_INFO
                        scroll_offset = 0
                    elif sel == "Back":
                        menu_screen = None
                elif key == "ESC" or key == "`":
                    menu_screen = None

        elif menu_screen == MENU_SCREEN_VARS:
            show_variables()
            if keys:
                key = str(keys[0])
                if key == "UP" or key == ";":
                    scroll_offset = max(scroll_offset - 1, 0)
                elif key == "DOWN" or key == ".":
                    max_scroll = max(len(variables) - LINES_PER_PAGE, 0)
                    scroll_offset = min(scroll_offset + 1, max_scroll)
                elif key == "ESC" or key == "`":
                    menu_screen = MENU_SCREEN_MAIN

        elif menu_screen == MENU_SCREEN_INFO:
            show_info()
            if keys:
                key = str(keys[0])
                if key == "UP" or key == ";":
                    scroll_offset = max(scroll_offset - 1, 0)
                elif key == "DOWN" or key == ".":
                    scroll_offset = min(scroll_offset + 1, 3)
                elif key == "ESC" or key == "`":
                    menu_screen = MENU_SCREEN_MAIN

        elif menu_screen == MENU_SCREEN_TERMINAL:
            show_terminal()
            if keys:
                key = str(keys[0])
                if key == "DEL":
                    terminal_log.clear()
                elif key == "UP" or key == ";":
                    scroll_offset = max(scroll_offset - 1, 0)
                elif key == "DOWN" or key == ".":
                    max_scroll = max(len(terminal_log) - LINES_PER_PAGE, 0)
                    scroll_offset = min(scroll_offset + 1, max_scroll)
                elif key == "ESC" or key == "`":
                    menu_screen = MENU_SCREEN_MAIN

        time.sleep_ms(10)

main_loop()


