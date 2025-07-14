"""
NumScript app for MicroHydra on Cardputer
"""

import time
import json
from lib import display, userinput
from lib.hydra import config
from font import vga1_8x16 as midfont

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

info_lines = [
    "NumScript:",
    "A quick code builder",
    "(scroll down to see more)",
    "",
    "Documentation:",
    "Defining a variable:",
    "<var name>=<value>",
    "eg dog=2",
    "",
    "Operating on variables:",
    "<var name>=<value><operator><value>",
    "for example:",
    "a=3-b",
    "aura=n*-1-200",
    "alphabet=(a+b)**c",
    "",
    "Comparing variables",
    "<value><operator><value>",
    "operators can be either:",
    "<(less?), >(more?), or == (equals?)",
    "for example:",
    "y=a>b",
    "better=dog<cat",
    "c=(qwerty*2)==4",
    "",
    "Logging:",
    "log(value)",
    "for example:",
    "log('hello world')",
    "n=29",
    "log(n)",
    "#known issue#:",
    "using log('value') where",
    "value is the name of a",
    "variable will not work."
]

terminal_log = []

MENU_SCREEN_MAIN = 0
MENU_SCREEN_VARS = 1
MENU_SCREEN_INFO = 2
MENU_SCREEN_SAEFILE = 3
MENU_SCREEN_TERMINAL = 4

LINES_PER_PAGE = 5
menu_screen = None
menu_selection = 0
scroll_offset = 0


def pressed_key(key, pressed_keys):
    return key in pressed_keys


def process_key_macros(expr, pressed_keys):
    while "key(" in expr:
        start = expr.find("key(")
        end = expr.find(")", start)
        if end == -1:
            break
        inside = expr[start + 4:end].strip()
        if len(inside) == 1 and inside in cardputer_keys:
            is_pressed = "1" if pressed_key(inside, pressed_keys) else "0"
            expr = expr[:start] + is_pressed + expr[end + 1:]
        else:
            return "invalid key() usage"
    return expr


def replace_variables(expr):
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
            local_vars = variables.copy()
            local_vars["log"] = log
            val = eval(expr_eval, {}, local_vars)
            return str(val)
    except Exception as e:
        return "Error: " + str(e)


def run_full_script(pressed_keys):
    global terminal_log
    line = 0
    while line < len(script_lines):
        if script_lines[line].strip():
            show_terminal()
            res = evaluate_expression(script_lines[line], pressed_keys)
            print(res)
            if "Error" in res:
                log(res)
        line += 1


def draw_script_screen():
    DISPLAY.fill(CONFIG.palette[2])
    DISPLAY.text("Script Editor: (TAB for menu)", 10, 5, CONFIG.palette[8], midfont)
    for i in range(min(len(script_lines), LINES_PER_PAGE)):
        idx = i + scroll_offset
        if idx >= len(script_lines):
            break
        prefix = "=> " if idx == cursor_line else "   "
        DISPLAY.text(prefix + script_lines[idx], 10, 25 + i * 20, CONFIG.palette[8], midfont)
    DISPLAY.show()


def clamp(val, minimum, maximum):
    if val > maximum:
        return maximum
    if val < minimum:
        return minimum
    return val


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
    global info_lines
    DISPLAY.fill(CONFIG.palette[2])
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
    options = ["Run Full Script", "View Variables", "View Terminal", "Info", "Save/Load"]
    DISPLAY.fill(CONFIG.palette[2])
    DISPLAY.text("Menu:", 10, 10, CONFIG.palette[8], midfont)
    for i, opt in enumerate(options):
        prefix = "-> " if i == menu_selection else "   "
        DISPLAY.text(prefix + opt, 10, 30 + i * 20, CONFIG.palette[8], midfont)
    DISPLAY.show()
    return options


def show_save(sel):
    sel = int(sel)
    options = ["Save", "Load"]
    DISPLAY.fill(CONFIG.palette[2])
    DISPLAY.text("Save/Load:(ESC to return)", 10, 10, CONFIG.palette[8], midfont)
    for i in range(len(options)):
        prefix = "-> " if options[sel] == options[i] else "   "
        DISPLAY.text(prefix + options[i], 10, 30 + i * 20, CONFIG.palette[8], midfont)
    DISPLAY.show()
    return options


def main_loop():
    global cursor_line, scroll_offset, menu_screen, menu_selection, script_lines, result, info_lines

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
                    cursor_line = 0
                elif key == "ENT":
                    if "SHIFT" in pressed_keys:
                        line = script_lines[cursor_line]
                        res = evaluate_expression(line, pressed_keys)
                        terminal_log.append(res)
                        result = res
                    else:
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
                elif key == "UP":
                    cursor_line = max(0, cursor_line - 1)
                    if cursor_line < scroll_offset:
                        scroll_offset = max(0, scroll_offset - 1)
                elif key == "DOWN":
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
                if key in ("UP", ";"):
                    menu_selection = (menu_selection - 1) % len(options)
                elif key in ("DOWN", "."):
                    menu_selection = (menu_selection + 1) % len(options)
                elif key == "ENT":
                    sel = options[menu_selection]
                    if sel == "Run Full Script":
                        menu_screen = MENU_SCREEN_TERMINAL
                        run_full_script(pressed_keys)
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
                    elif sel == "Save/Load":
                        menu_screen = "Savescreen"
                elif key in ("ESC", "`"):
                    cursor_line = 0
                    scroll_offset = 0
                    menu_screen = None

        elif menu_screen == MENU_SCREEN_VARS:
            show_variables()
            if keys:
                key = str(keys[0])
                if key in ("UP", ";"):
                    scroll_offset = max(scroll_offset - 1, 0)
                elif key in ("DOWN", "."):
                    max_scroll = max(len(variables) - LINES_PER_PAGE, 0)
                    scroll_offset = min(scroll_offset + 1, max_scroll)
                elif key in ("ESC", "`"):
                    menu_screen = MENU_SCREEN_MAIN

        elif menu_screen == MENU_SCREEN_INFO:
            show_info()
            if keys:
                key = str(keys[0])
                if key in ("UP", ";"):
                    scroll_offset = max(scroll_offset - 1, 0)
                elif key in ("DOWN", "."):
                    scroll_offset = min(scroll_offset + 1, len(info_lines))
                elif key in ("ESC", "`"):
                    menu_screen = MENU_SCREEN_MAIN

        elif menu_screen == MENU_SCREEN_TERMINAL:
            show_terminal()
            if keys:
                key = str(keys[0])
                if key == "DEL":
                    terminal_log.clear()
                elif key in ("UP", ";"):
                    scroll_offset = max(scroll_offset - 1, 0)
                elif key in ("DOWN", "."):
                    max_scroll = max(len(terminal_log) - LINES_PER_PAGE, 0)
                    scroll_offset = min(scroll_offset + 1, max_scroll)
                elif key in ("ESC", "`"):
                    menu_screen = MENU_SCREEN_MAIN

        elif menu_screen == "Savescreen":
            save_options = show_save(scroll_offset)
            filename_prompt = ""
            input_filename = ""
            typing_filename = False

            if keys:
                key = str(keys[0])
                if key in ("UP", ";"):
                    scroll_offset = clamp(scroll_offset - 1, 0, 1)
                elif key in ("DOWN", "."):
                    scroll_offset = clamp(scroll_offset + 1, 0, 1)
                elif key in ("ESC", "`"):
                    menu_screen = MENU_SCREEN_MAIN
                elif key == "ENT":
                    typing_filename = True

            while typing_filename:
                DISPLAY.fill(CONFIG.palette[2])
                DISPLAY.text("Enter filename:", 10, 10, CONFIG.palette[8], midfont)
                DISPLAY.text(input_filename + "_", 10, 40, CONFIG.palette[8], midfont)
                DISPLAY.text("ENT: Confirm | ESC: Cancel", 10, 100, CONFIG.palette[8], midfont)
                DISPLAY.show()

                keys = INPUT.get_new_keys()
                if keys:
                    key = str(keys[0])

                    if key == "ENT":
                        filename = input_filename.strip()
                        if not filename:
                            menu_screen = MENU_SCREEN_TERMINAL
                            terminal_log.append("Filename empty.")
                            break
                        try:
                            if scroll_offset == 0:
                                with open(filename, "w") as f:
                                    f.write(json.dumps(script_lines))
                                scroll_offset = len(terminal_log)
                                menu_screen = MENU_SCREEN_TERMINAL
                                terminal_log.append(f"Saved to: {filename}")
                            else:
                                with open(filename, "r") as f:
                                    content = f.read()
                                    script_lines = json.loads(content)
                                scroll_offset = len(terminal_log)
                                menu_screen = MENU_SCREEN_TERMINAL
                                terminal_log.append(f"Loaded from: {filename}")
                        except Exception as e:
                            scroll_offset = len(terminal_log)
                            menu_screen = MENU_SCREEN_TERMINAL
                            terminal_log.append("File error: " + str(e))
                        break

                    elif key in ("ESC", "`"):
                        break
                    elif key == "BSPC":
                        input_filename = input_filename[:-1]
                    elif key == "SPC":
                        input_filename += " "
                    elif key in valid_chars:
                        input_filename += key

                time.sleep_ms(10)

        time.sleep_ms(10)


main_loop()
