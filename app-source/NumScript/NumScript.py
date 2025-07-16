import json
import time
import random
from lib import display, userinput
from lib.hydra import config
from font import vga1_8x16 as midfont
MHDH = const(135)
MHDW= const(240)
MLE = const(50)
MSL = const(100)
DISPLAY = display.Display()
CONFIG = config.Config()
INPUT = userinput.UserInput()
scr = [""]
cl = 0
result = ""
variables = {}
ths = 0
cel = -1
pdw = 64
pdh = 32
plot_buffer = {}
spd = True
valid_chars = "1234567890+-*/=()<>'\"^~,.qwertyuiopasdfghjklzxcvbnmQWERTYUIOPASDFGHJKLZXCVBNM[]\\`;,:"
cardputer_keys = [
    "0", "1", "2", "3", "4", "5", "6", "7", "8", "9",
    "a", "b", "c", "d", "e", "f", "g", "h", "i", "j",
    "k", "l", "m", "n", "o", "p", "q", "r", "s", "t",
    "u", "v", "w", "x", "y", "z",
    "[", "]", "\\", "`", ";", "'", "\"", ".", "/", ",", ":",
    "ENT", "BSPC", "DEL", "ESC", "TAB", "SPC", "UP", "DOWN", "LEFT", "RIGHT"
]
info_lines = ["not enough mem"]
terminal_log = []
msma = 0
msva = 1
msin = 2
mssa = 3
mste = 4
msse = 5
mssf = 6
lpp = 5
mscrn = None
msel = 0
scrl = 0
def show_settings():
    global pdw, pdh, spd    
    DISPLAY.fill(CONFIG.palette[2])
    DISPLAY.text("Settings:", 10, 10, CONFIG.palette[8], midfont)
    settings_options = [
        f"Plot Width: {pdw}",
        f"Plot Height: {pdh}",
        f"Show Plot: {'Yes' if spd else 'No'}",
        "Reset Plot Size"
    ]
    for i, opt in enumerate(settings_options):
        prefix = "-> " if i == scrl else "   "
        DISPLAY.text(prefix + opt, 10, 30 + i * 20, CONFIG.palette[8], midfont)
    DISPLAY.text("ENT: Edit | ESC: Back", 10, 120, CONFIG.palette[8], midfont)
    DISPLAY.show()
    return settings_options
def script_plot(x, y, greyscale=0.5):
    if isinstance(x, (int, float)) and isinstance(y, (int, float)):
        x, y = int(x), int(y)
        if 0 <= x < pdw and 0 <= y < pdh:
            greyscale = max(0, min(1, float(greyscale)))
            plot_buffer[(x, y)] = greyscale
    return 0
def clear_plot():
    global plot_buffer
    plot_buffer.clear()
    return 0
def draw_plot_display():
    if not spd:
        return
    plot_x = MHDW- pdw - 10
    plot_y = 25
    DISPLAY.rect(plot_x - 1, plot_y - 1, pdw + 2, pdh + 2, CONFIG.palette[8])
    DISPLAY.fill_rect(plot_x, plot_y, pdw, pdh, CONFIG.palette[2])
    for (px, py), greyscale in plot_buffer.items():
        if 0 <= px < pdw and 0 <= py < pdh:
            color_index = int(greyscale * 7) + 1
            color_index = min(color_index, len(CONFIG.palette) - 1)
            DISPLAY.pixel(plot_x + px, plot_y + py, CONFIG.palette[color_index])
class JumpException(Exception):
    def __init__(self, line_number):
        self.line_number = line_number
        super().__init__(f"Jump to line {line_number}")
def script_jump(line_num):
    if isinstance(line_num, (int, float)):
        target_line = int(line_num) - 1
        if 0 <= target_line < len(scr):
            raise JumpException(target_line)
    return 0
def ifjump(condition, line_num):
    if condition:
        script_jump(line_num)
    return condition
def script_rand(decimal_places):
    if not isinstance(decimal_places, (int, float)):
        return 0.0
    decimal_places = int(decimal_places)
    if decimal_places < 0:
        decimal_places = 0
    elif decimal_places > 10:
        decimal_places = 10
    random_value = random.random()
    return round(random_value, decimal_places)
def script_list(*args):
    return list(args)
def script_append(lst, item):
    if isinstance(lst, list):
        lst.append(item)
        return lst
    return lst
def script_get(lst, index):
    if isinstance(lst, list) and isinstance(index, (int, float)):
        idx = int(index)
        if 0 <= idx < len(lst):
            return lst[idx]
    return None
def script_set(lst, index, value):
    if isinstance(lst, list) and isinstance(index, (int, float)):
        idx = int(index)
        if 0 <= idx < len(lst):
            lst[idx] = value
            return lst
    return lst
def script_remove(lst, index):
    if isinstance(lst, list) and isinstance(index, (int, float)):
        idx = int(index)
        if 0 <= idx < len(lst):
            lst.pop(idx)
            return lst
    return lst
def script_size(lst):
    if isinstance(lst, list):
        return len(lst)
    return 0
def script_contains(lst, item):
    if isinstance(lst, list):
        return 1 if item in lst else 0
    return 0
def script_sort(lst):
    if isinstance(lst, list):
        try:
            lst.sort()
            return lst
        except TypeError:
            return lst
    return lst
def script_reverse(lst):
    if isinstance(lst, list):
        lst.reverse()
        return lst
    return lst
def script_join(lst, separator=""):
    if isinstance(lst, list):
        return str(separator).join(str(item) for item in lst)
    return ""
def script_split(text, separator=" "):
    if isinstance(text, str):
        return text.split(str(separator))
    return []
safe_functions = {
    'abs': abs,
    'round': round,
    'min': min,
    'max': max,
    'sqrt': lambda x: x ** 0.5,
    'pow': pow,
    'log': lambda x: None,
    'key': lambda x: None,
    'jump': script_jump,
    'ifjump': ifjump,
    'range': range,
    'len': len,
    'int': int,
    'float': float,
    'str': str,
    'bool': bool,
    'rand': script_rand,
    'list': script_list,
    'append': script_append,
    'get': script_get,
    'set': script_set,
    'remove': script_remove,
    'size': script_size,
    'contains': script_contains,
    'sort': script_sort,
    'reverse': script_reverse,
    'join': script_join,
    'split': script_split
}
safe_functions['plot'] = script_plot
safe_functions['clearplot'] = clear_plot
def manage_log_memory():
    global terminal_log
    if len(terminal_log) > MLE:
        terminal_log = terminal_log[-MLE:]
def manage_script_memory():
    global scr
    if len(scr) > MSL:
        scr = scr[-MSL:]
def pressed_key(key, pressed_keys):
    return key in pressed_keys
def safe_key_check(key_name):
    if not isinstance(key_name, str) or len(key_name) != 1:
        return False
    if key_name not in cardputer_keys:
        return False
    pressed_keys = INPUT.get_pressed_keys()
    return pressed_key(key_name, pressed_keys)
def process_key_macros(expr):
    result = expr
    while "key(" in result:
        start = result.find("key(")
        if start == -1:
            break
        
        paren_count = 0
        end = start + 4
        while end < len(result):
            if result[end] == '(':
                paren_count += 1
            elif result[end] == ')':
                if paren_count == 0:
                    break
                paren_count -= 1
            end += 1
        if end >= len(result):
            break
        inside = result[start + 4:end].strip()
        if len(inside) >= 3 and inside[0] in ("'", '"') and inside[-1] in ("'", '"'):
            key_char = inside[1:-1]
            if len(key_char) == 1 and key_char in cardputer_keys:
                pressed_keys = INPUT.get_pressed_keys()
                replacement = "1" if pressed_key(key_char, pressed_keys) else "0"
                result = result[:start] + replacement + result[end + 1:]
            else:
                result = result[:start] + "0" + result[end + 1:]
        else:
            result = result[:start] + "0" + result[end + 1:]
    return result
def tokenize_expression(expr):
    result = str(expr)
    def is_alnum(c):
        return ('0' <= c <= '9') or ('a' <= c <= 'z') or ('A' <= c <= 'Z')
    for var in variables:
        i = 0
        while i < len(result):
            pos = result.find(var, i)
            if pos == -1:
                break
            start_ok = pos == 0 or (not is_alnum(result[pos-1]) and result[pos-1] != '_')
            end_ok = pos + len(var) == len(result) or (not is_alnum(result[pos + len(var)]) and result[pos + len(var)] != '_')
            if start_ok and end_ok:
                replacement = str(variables[var])
                result = result[:pos] + replacement + result[pos + len(var):]
                i = pos + len(replacement)
            else:
                i = pos + 1
    return result
def log(value):
    print(value)
    terminal_log.append(str(value))
    manage_log_memory()
    if mscrn == mste:
        global scrl
        scrl = max(0, len(terminal_log) - lpp)
def safe_eval(expr, local_vars=None):
    if local_vars is None:
        local_vars = {}
    safe_context = safe_functions.copy()
    safe_context.update(local_vars)
    def script_log(value):
        log(value)
        return str(value)
    safe_context['log'] = script_log
    safe_context['key'] = safe_key_check
    safe_builtins = {
        '__builtins__': {},
        'True': True,
        'False': False,
        'None': None
    }
    try:
        return eval(expr, safe_builtins, safe_context)
    except Exception as e:
        raise 
def is_valid_variable_name(name):
    if not name:
        return False
    def is_alpha(c):
        return ('a' <= c <= 'z') or ('A' <= c <= 'Z')
    def is_digit(c):
        return '0' <= c <= '9'
    def is_alnum(c):
        return is_alpha(c) or is_digit(c)
    if not (is_alpha(name[0]) or name[0] == '_'):
        return False
    for char in name:
        if not (is_alnum(char) or char == '_'):
            return False
    return True
def parse_assignment(expr):
    comparison_ops = ['==', '!=', '<=', '>=']
    for op in comparison_ops:
        if op in expr:
            return None, expr
    if '=' in expr:
        parts = expr.split('=', 1)
        if len(parts) == 2:
            var_name = parts[0].strip()
            value_expr = parts[1].strip()
            if is_valid_variable_name(var_name):
                return var_name, value_expr
    return None, expr
def evaluate_expression(expr):
    expr = expr.strip()
    if not expr or expr.startswith('#'):
        return ""
    if '#' in expr:
        expr = expr.split('#')[0].strip()
        if not expr:
            return ""
    expr = process_key_macros(expr)
    try:
        var_name, value_expr = parse_assignment(expr)
        if var_name:
            value_expr = tokenize_expression(value_expr)
            val = safe_eval(value_expr, variables)
            variables[var_name] = val
            return f"{var_name} = {val}"
        else:
            expr_eval = tokenize_expression(expr)
            val = safe_eval(expr_eval, variables)
            return str(val) if val is not None else ""
    except JumpException:
        raise
    except ZeroDivisionError:
        return "Error: Division by zero"
    except NameError as e:
        return "Error: Undefined variable"
    except SyntaxError as e:
        return "Error: Syntax error"
    except Exception as e:
        return f"Error: {str(e)[:40]}"
def run_full_script():
    global terminal_log, scrl, cel
    line_num = 0
    while line_num < len(scr):
        line = scr[line_num].strip()
        if line:
            cel = line_num
            show_terminal()
            try:
                res = evaluate_expression(line)
                if res and "Error" in res:
                    log(f"Line {line_num + 1}: {res}")
                    log(f"Execution stopped at line {line_num + 1}")
                    break
            except JumpException as e:
                line_num = e.line_number
                continue
        line_num += 1
        time.sleep_ms(10)
    cel = -1
    if mscrn == mste:
        scrl = max(0, len(terminal_log) - lpp)
def draw_script_screen():
    DISPLAY.fill(CONFIG.palette[2])
    DISPLAY.text("Script Editor: (TAB for menu)", 10, 5, CONFIG.palette[8], midfont)
    for i in range(min(len(scr), lpp)):
        idx = i + scrl
        if idx >= len(scr):
            break
        line_num = f"{idx + 1:2d}"
        prefix = "=> " if idx == cl else "   "
        line_text = scr[idx][:30]
        DISPLAY.text(f"{line_num}|{prefix}{line_text}", 10, 25 + i * 20, CONFIG.palette[8], midfont)
    if cl < len(scr):
        line_len = len(scr[cl])
        DISPLAY.text(f"Line {cl + 1}, Len: {line_len}", 10, 115, CONFIG.palette[8], midfont)
    DISPLAY.show()
def clamp(val, minimum, maximum):
    return max(minimum, min(val, maximum))
def show_variables():
    DISPLAY.fill(CONFIG.palette[2])
    DISPLAY.text("Variables:", 10, 10, CONFIG.palette[8], midfont)
    var_names = list(variables.keys())
    for i in range(lpp):
        idx = i + scrl
        if idx < len(var_names):
            var = var_names[idx]
            val = variables[var]
            val_type = type(val).__name__
            display_val = str(val)[:20]  # Truncate long values
            DISPLAY.text(f"{var} = {display_val} ({val_type})", 10, 30 + i * 20, CONFIG.palette[8], midfont)
    DISPLAY.text(f"Total: {len(var_names)} | ESC: Back", 10, 120, CONFIG.palette[8], midfont)
    DISPLAY.show()
def show_info():
    """Enhanced info display"""
    DISPLAY.fill(CONFIG.palette[2])
    for i in range(lpp):
        idx = i + scrl
        if idx < len(info_lines):
            DISPLAY.text(info_lines[idx], 10, 10 + i * 20, CONFIG.palette[8], midfont)
    DISPLAY.text(f"Page {scrl//lpp + 1} | ESC: Back", 10, 120, CONFIG.palette[8], midfont)
    DISPLAY.show()

def show_terminal():
    global ths
    DISPLAY.fill(CONFIG.palette[2])
    terminal_width = (MHDW- pdw - 30) // 8 if spd else 35
    DISPLAY.text("Terminal Output", 10, 5, CONFIG.palette[8], midfont)
    if cel >= 0:
        line_text = f"Executing line {cel + 1}"
        DISPLAY.text(line_text, 10, 15, CONFIG.palette[6], midfont)
        display_start_y = 35
    else:
        display_start_y = 25
    available_lines = (120 - display_start_y) // 20
    for i in range(available_lines+1):
        idx = i + scrl
        if idx < len(terminal_log):
            log_line = terminal_log[idx]
            # Apply horizontal scrolling
            if len(log_line) > ths:
                displayed_line = log_line[ths:ths + terminal_width]
            else:
                displayed_line = ""
            DISPLAY.text(displayed_line, 10, display_start_y + i * 20, CONFIG.palette[8], midfont)
    scroll_info = f"Logs: {len(terminal_log)}"
    if ths > 0:
        scroll_info += f" | H-Scroll: {ths}"
    DISPLAY.text(scroll_info, 175, 120, CONFIG.palette[8], midfont)
    draw_plot_display()
    DISPLAY.show()
def show_menu():
    options = ["Run Script", "Variables", "Terminal", "Help", "Save/Load", "Settings", "Clear All"]
    DISPLAY.fill(CONFIG.palette[2])
    DISPLAY.text("Menu:", 10, 10, CONFIG.palette[8], midfont)
    for i, opt in enumerate(options):
        prefix = "-> " if i == msel else "   "
        DISPLAY.text(prefix + opt, 10, 28 + i * 15, CONFIG.palette[8], midfont)
    DISPLAY.show()
    return options
def show_save(sel):
    options = ["Save Script", "Load Script", "Export Variables", "Clear Variables"]
    DISPLAY.fill(CONFIG.palette[2])
    DISPLAY.text("File Operations:", 10, 10, CONFIG.palette[8], midfont)
    for i, opt in enumerate(options):
        prefix = "-> " if i == sel else "   "
        DISPLAY.text(prefix + opt, 10, 30 + i * 20, CONFIG.palette[8], midfont)
    DISPLAY.text("ESC: Back", 10, 120, CONFIG.palette[8], midfont)
    DISPLAY.show()
    return options
def handle_file_operation(operation, filename):
    global scr, variables
    try:
        if operation == 0:
            with open(filename, "w") as f:
                json.dump({"script": scr, "variables": variables}, f)
            return f"Saved script to: {filename}"
        elif operation == 1:
            with open(filename, "r") as f:
                data = json.load(f)
                scr = data.get("script", [""])
                variables = data.get("variables", {})
                manage_script_memory()
            return f"Loaded script from: {filename}"
        elif operation == 2:
            with open(filename, "w") as f:
                json.dump(variables, f)
            return f"Exported variables to: {filename}"
        elif operation == 3:
            variables.clear()
            return "Variables cleared"
    except OSError:
        return f"Error: File '{filename}' not found"
    except ValueError:
        return f"Error: Invalid file format"
    except Exception as e:
        return f"Error: {str(e)[:30]}"
def main_loop():
    global cl, scrl, mscrn, msel, scr, result

    while True:
        keys = INPUT.get_new_keys()
        pressed_keys = INPUT.get_pressed_keys()
        if mscrn is None:
            if keys:
                key = str(keys[0])
                if key == "TAB":
                    mscrn = msma
                    scrl = 0
                    msel = 0
                elif key == "ENT":
                    if "SHIFT" in pressed_keys:
                        line = scr[cl]
                        try:
                            res = evaluate_expression(line)
                            if res:
                                terminal_log.append(res)
                                result = res
                        except JumpException as e:
                            terminal_log.append(f"Jump to line {e.line_number + 1}")
                    else:
                        scr.insert(cl + 1, "")
                        cl += 1
                        if cl >= scrl + lpp:
                            scrl += 1
                        manage_script_memory()
                elif key == "BSPC":
                    line = scr[cl]
                    if line:
                        scr[cl] = line[:-1]
                    else:
                        if len(scr) > 1:
                            scr.pop(cl)
                            cl = max(cl - 1, 0)
                elif key == "DEL":
                    if len(scr) > 1:
                        scr.pop(cl)
                        cl = min(cl, len(scr) - 1)
                elif key == "UP":
                    cl = max(0, cl - 1)
                    if cl < scrl:
                        scrl = max(0, scrl - 1)
                elif key == "DOWN":
                    cl = min(len(scr) - 1, cl + 1)
                    if cl >= scrl + lpp:
                        scrl += 1
                elif key in valid_chars or key == "SPC":
                    char = " " if key == "SPC" else key
                    scr[cl] += char
            draw_script_screen()
        elif mscrn == msma:
            options = show_menu()
            if keys:
                key = str(keys[0])
                if key in ("UP", ";"):
                    msel = (msel - 1) % len(options)
                elif key in ("DOWN", "."):
                    msel = (msel + 1) % len(options)
                elif key == "ENT":
                    sel = options[msel]
                    if sel == "Run Script":
                        mscrn = mste
                        run_full_script()
                        scrl = max(0, len(terminal_log) - lpp)
                    elif sel == "Variables":
                        mscrn = msva
                        scrl = 0
                    elif sel == "Terminal":
                        mscrn = mste
                        scrl = max(0, len(terminal_log) - lpp)
                    elif sel == "Help":
                        mscrn = msin
                        scrl = 0
                    elif sel == "Save/Load":
                        mscrn = "Savescreen"
                        scrl = 0
                    elif sel == "Settings":
                        mscrn = msse
                        scrl = 0
                    elif sel == "Clear All":
                        scr = [""]
                        variables.clear()
                        terminal_log.clear()
                        plot_buffer.clear()
                        cl = 0
                        scrl = 0
                        mscrn = None
                elif key in ("ESC", "`"):
                    mscrn = None
                    scrl = 0
        elif mscrn == msva:
            show_variables()
            if keys:
                key = str(keys[0])
                if key in ("UP", ";"):
                    scrl = max(scrl - 1, 0)
                elif key in ("DOWN", "."):
                    max_scroll = max(len(variables) - lpp, 0)
                    scrl = min(scrl + 1, max_scroll)
                elif key in ("ESC", "`"):
                    mscrn = msma
        elif mscrn == msin:
            show_info()
            if keys:
                key = str(keys[0])
                if key in ("UP", ";"):
                    scrl = max(scrl - 1, 0)
                elif key in ("DOWN", "."):
                    max_scroll = max(len(info_lines) - lpp, 0)
                    scrl = min(scrl + 1, max_scroll)
                elif key in ("ESC", "`"):
                    mscrn = msma
        elif mscrn == mste:
            show_terminal()
            if keys:
                key = str(keys[0])
                if key == "DEL":
                    terminal_log.clear()
                    plot_buffer.clear()
                elif key in ("UP", ";"):
                    scrl = max(scrl - 1, 0)
                elif key in ("DOWN", "."):
                    max_scroll = max(len(terminal_log) - lpp, 0)
                    scrl = min(scrl + 1, max_scroll)
                elif key in ("LEFT", ","):
                    ths = max(ths - 1, 0)
                elif key in ("RIGHT", "/"):
                    ths += 1
                elif key in ("ESC", "`"):
                    mscrn = msma
                    ths = 0
        elif mscrn == mssf:
            save_options = show_save(scrl)
            if keys:
                key = str(keys[0])
                if key in ("UP", ";"):
                    scrl = (scrl - 1) % len(save_options)
                elif key in ("DOWN", "."):
                    scrl = (scrl + 1) % len(save_options)
                elif key in ("ESC", "`"):
                    mscrn = msma
                elif key == "ENT":
                    if scrl == 3:
                        result = handle_file_operation(3, "")
                        terminal_log.append(result)
                        mscrn = mste
                    else:
                        input_filename = ""
                        typing_filename = True
                        while typing_filename:
                            DISPLAY.fill(CONFIG.palette[2])
                            DISPLAY.text("Enter filename:", 10, 10, CONFIG.palette[8], midfont)
                            DISPLAY.text(input_filename + "_", 10, 40, CONFIG.palette[8], midfont)
                            DISPLAY.text("ENT: OK | ESC: Cancel", 10, 100, CONFIG.palette[8], midfont)
                            DISPLAY.show()
                            keys = INPUT.get_new_keys()
                            if keys:
                                key = str(keys[0])
                                if key == "ENT":
                                    filename = input_filename.strip()
                                    if filename:
                                        result = handle_file_operation(scrl, filename)
                                        terminal_log.append(result)
                                        mscrn = mste
                                        scrl = max(0, len(terminal_log) - lpp)
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
        elif mscrn == msse:
            settings_options = show_settings()
            if keys:
                key = str(keys[0])
                if key in ("UP", ";"):
                    scrl = (scrl - 1) % len(settings_options)
                elif key in ("DOWN", "."):
                    scrl = (scrl + 1) % len(settings_options)
                elif key == "ENT":
                    if scrl == 0:
                        input_value = ""
                        typing_value = True
                        while typing_value:
                            DISPLAY.fill(CONFIG.palette[2])
                            DISPLAY.text("Enter plot width (8-128):", 10, 10, CONFIG.palette[8], midfont)
                            DISPLAY.text(input_value + "_", 10, 40, CONFIG.palette[8], midfont)
                            DISPLAY.text("ENT: OK | ESC: Cancel", 10, 100, CONFIG.palette[8], midfont)
                            DISPLAY.show()
                            keys = INPUT.get_new_keys()
                            if keys:
                                key = str(keys[0])
                                if key == "ENT":
                                    try:
                                        new_width = int(input_value)
                                        if 8 <= new_width <= 128:
                                            global pdw
                                            pdw = new_width
                                            plot_buffer.clear()
                                    except ValueError:
                                        pass
                                    break
                                elif key in ("ESC", "`"):
                                    break
                                elif key == "BSPC":
                                    input_value = input_value[:-1]
                                elif key in "0123456789":
                                    input_value += key
                            time.sleep_ms(10)
                    elif scrl == 1:
                        input_value = ""
                        typing_value = True
                        while typing_value:
                            DISPLAY.fill(CONFIG.palette[2])
                            DISPLAY.text("Enter plot height (8-64):", 10, 10, CONFIG.palette[8], midfont)
                            DISPLAY.text(input_value + "_", 10, 40, CONFIG.palette[8], midfont)
                            DISPLAY.text("ENT: OK | ESC: Cancel", 10, 100, CONFIG.palette[8], midfont)
                            DISPLAY.show()
                            keys = INPUT.get_new_keys()
                            if keys:
                                key = str(keys[0])
                                if key == "ENT":
                                    try:
                                        new_height = int(input_value)
                                        if 8 <= new_height <= 64:
                                            global pdh
                                            pdh = new_height
                                            plot_buffer.clear()
                                    except ValueError:
                                        pass
                                    break
                                elif key in ("ESC", "`"):
                                    break
                                elif key == "BSPC":
                                    input_value = input_value[:-1]
                                elif key in "0123456789":
                                    input_value += key
                            time.sleep_ms(10)
                    elif scrl == 2:
                        global spd
                        spd = not spd
                    elif scrl == 3:
                        global pdw, pdh
                        pdw = 64
                        pdh = 32
                        plot_buffer.clear()
                elif key in ("ESC", "`"):
                    mscrn = msma
        time.sleep_ms(10)
main_loop()
