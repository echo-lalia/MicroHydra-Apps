from lib import st7789fbuf, mhconfig, keyboard
import machine, time
import sys
machine.freq(240_000_000)
"""
MicroHydra BASIC Interpreter
Version: 1.0

Implementation of BASIC & REPL (Read-Eval-Print Loop).
Documentation:

**PRINT**: `PRINT <expr>;<expr>...` - Prints specified expressions. e.g., `PRINT "A=";a`

**LET**: `LET variable = <expr>` - Assigns value to variable. e.g., `LET A$="Hello"`

**Assignment**: `variable = <expr>` - Assigns value to variable. e.g., `A = 5`

**LIST**: `LIST [start],[end]` - Lists lines of code. e.g., `LIST`, `LIST 10,100`

**RUN**: `RUN [lineNumber]` - Executes program from line number. e.g., `RUN`, `RUN 20`

**GOTO**: `GOTO lineNumber` - Jumps to specified line number. e.g., `GOTO 30`

**REM**: `REM <comment>` - Adds a comment. e.g., `REM This is a comment`

**STOP**: `STOP` - Stops program execution. e.g., `STOP`

**CONT**: `CONT` - Continues execution after stop. e.g., `CONT`

**INPUT**: `INPUT variable` - Prompts user for input. e.g., `INPUT A$`, `INPUT A`

**IF**: `IF <expr> THEN cmd` - Executes command if expression is true. e.g., `IF A > 10 THEN PRINT "A is greater than 10"`

**FOR**: `FOR variable = start TO end STEP step` - Starts a for-loop. e.g., `FOR I = 1 TO 10 STEP 2`

**NEXT**: `NEXT variable` - Ends a for-loop. e.g., `NEXT I`

**WHILE**: `WHILE expr` - Begins a while-loop. e.g., `WHILE A < 10`

**WEND**: `WEND` - Ends a while-loop. e.g., `WEND`

**GOSUB**: `GOSUB lineNumber` - Calls a subroutine. e.g., `GOSUB 100`

**RETURN**: `RETURN` - Returns from subroutine. e.g., `RETURN`

**DIM**: `DIM variable(n1,n2...)` - Declares an array. e.g., `DIM A(10, 20)`

**LOAD**: `LOAD file_name` - Loads code from file. e.g., `LOAD "myprogram.bas"`

**SAVE**: `SAVE file_name` - Saves code to file. e.g., `SAVE "myprogram.bas"`

### Operators Supported
- **Single-character operators**: `+`, `-`, `*`, `/`, `%`, `=`, `<`, `>`, `&`, `|`
- **Two-character operators**: `==`, `<=`, `>=`

### Example Program
```basic
10 LET A = 5
20 PRINT "A = "; A
30 FOR I = 1 TO 10
40 PRINT I
50 NEXT I
60 IF A > 4 THEN PRINT "A is greater than 4"
70 STOP
```

TODO:
Better BASIC implementation.
"""

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ CONSTANTS: ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
_DISPLAY_HEIGHT = const(135)
_DISPLAY_WIDTH = const(240)
_DISPLAY_WIDTH_HALF = const(_DISPLAY_WIDTH // 2)

_CHAR_WIDTH = const(8)
_CHAR_WIDTH_HALF = const(_CHAR_WIDTH // 2)

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ GLOBAL OBJECTS: ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# init object for accessing display
tft = st7789fbuf.ST7789(
    machine.SPI(
        1, baudrate=40000000, sck=machine.Pin(36), mosi=machine.Pin(35), miso=None),
    _DISPLAY_HEIGHT,
    _DISPLAY_WIDTH,
    reset=machine.Pin(33, machine.Pin.OUT),
    cs=machine.Pin(37, machine.Pin.OUT),
    dc=machine.Pin(34, machine.Pin.OUT),
    backlight=machine.Pin(38, machine.Pin.OUT),
    rotation=1,
    color_order=st7789fbuf.BGR
)

# object for accessing microhydra config (Delete if unneeded)
config = mhconfig.Config()

# object for reading keypresses
kb = keyboard.KeyBoard()

# screen buffer
scr_buf = [""] * 13

#--------------------------------------------------------------------------------------------------
#-------------------------------------- FUNCTION DEFINITIONS: -------------------------------------
#--------------------------------------------------------------------------------------------------

def scr_feed(str):
    for i in range(1, 12):
        scr_buf[i - 1] = scr_buf[i]
    scr_buf[11] = str

def scr_show():
    # clear framebuffer 
    tft.fill(config['bg_color'])
    
    # write current text to framebuffer
    for i in range(12):
        tft.text(
            text=scr_buf[i],
            # center text on x axis:
            x=0, 
            y=10 * i,
            color=config['ui_color']
        )
    # write framebuffer to display
    tft.show()

# Used for Peeking Stdout

class OutputBuffer:
    def __init__(self):
        self.content = []

    def write(self, string):
        self.content.append(string)

    def getvalue(self):
        return ''.join(self.content)
    
    def clear(self):
        self.content = []

# Custom print function that writes to the buffer
def custom_print(*args, **kwargs):
    scr_feed(' '.join(map(str, args)) + kwargs.get('end', ''))
    scr_show()

# Replace the built-in print function with the custom one
print = custom_print

class BASICInterpreter:
    def __init__(self):
        self.lines = {}
        self.variables = {}
        self.pc = 0  # program counter
        self.running = False
        self.call_stack = []
        self.stop_flag = False

    def is_operator(self, char):
        return char in "+-*/%=<>|&"

    def tokenize(self, line):
        tokens = []
        current_token = ""
        in_string = False

        i = 0
        while i < len(line):
            char = line[i]
            
            if in_string:
                if char == '"':
                    in_string = False
                    current_token += char
                    tokens.append(current_token)
                    current_token = ""
                else:
                    current_token += char
            elif char == '"':
                in_string = True
                if current_token:
                    tokens.append(current_token)
                    current_token = ""
                current_token += char
            elif char.isspace():
                if current_token:
                    tokens.append(current_token)
                    current_token = ""
            elif self.is_operator(char):
                if current_token:
                    tokens.append(current_token)
                    current_token = ""

                tokens.append(char)
            else:
                current_token += char
            
            i += 1

        if current_token:
            tokens.append(current_token)

        return tokens

    def eval_expr(self, expr):
        try:
            if '"' in expr:
                return eval(expr)
            
            for var in self.variables:
                expr = expr.replace(var, str(self.variables[var]))
            
            for xx in {"==","!=","<=",">="}:
                expr = expr.replace(xx[0] + ' ' + xx[1],xx)
                
            return eval(expr)
        except Exception as e:
            print("Error in expression:")
            print(expr)
            print(e)
            return None

    def execute_line(self, line):
        tokens = self.tokenize(line)
        if not tokens:
            return

        cmd = tokens[0].upper()
        args = tokens[1:]

        if cmd == "PRINT":
            self.cmd_print(args)
        elif cmd == "LET":
            self.cmd_let(args)
        elif cmd == "FOR":
            self.cmd_for(args)
        elif cmd == "NEXT":
            self.cmd_next(args)
        elif cmd == "LIST":
            self.cmd_list(args)
        elif cmd == "RUN":
            self.cmd_run(args)
        elif cmd == "GOTO":
            self.cmd_goto(args)
        elif cmd == "REM":
            pass  # Ignore comments
        elif cmd == "STOP":
            self.cmd_stop()
        elif cmd == "CONT":
            self.cmd_cont()
        elif cmd == "INPUT":
            self.cmd_input(args)
        elif cmd == "IF":
            self.cmd_if(args)
        elif cmd == "WHILE":
            self.cmd_while(args)
        elif cmd == "WEND":
            self.cmd_wend(args)
        elif cmd == "GOSUB":
            self.cmd_gosub(args)
        elif cmd == "RETURN":
            self.cmd_return()
        elif cmd == "DIM":
            self.cmd_dim(args)
        elif cmd == "LOAD":
            self.cmd_load(args)
        elif cmd == "SAVE":
            self.cmd_save(args)
        elif '=' in tokens:
            self.cmd_assignment(tokens)
        else:
            try:
                output = self.eval_expr(line)
                if output is not None:
                    print(output)
            except Exception as e:
                print("Unknown command or error:", e)

    def cmd_print(self, args):
        to_print = " ".join(args).split(';')
        print_str = ""
        for item in to_print:
            if item.strip():
                print_str += f"{self.eval_expr(item)}"
        
        print(print_str)

    def cmd_let(self, args):
        var_name = args[0]
        expr = " ".join(args[2:])
        self.variables[var_name] = self.eval_expr(expr)

    def cmd_assignment(self, tokens):
        var_name = tokens[0]
        expr = " ".join(tokens[2:])
        self.variables[var_name] = self.eval_expr(expr)

    def cmd_list(self, args):
        if len(args) == 0:
            start = min(self.lines.keys(), default=0)
            end = max(self.lines.keys(), default=0)
            for i in range(start, end + 1):
                if i in self.lines:
                    print(f"{i} {self.lines[i]}")
        else:
            line_number = int(args[0])
            if line_number in self.lines:
                print(f"{line_number} {self.lines[line_number]}")
            else:
                print(f"Line {line_number} not found.")

    def cmd_run(self, args):
        self.pc = min(self.lines.keys(), default=0)
        self.pc_limit = max(self.lines.keys(), default=0)
        self.running = True
        self.stop_flag = False
        while self.running and not self.stop_flag and self.pc <= self.pc_limit:
            if "GO" in kb.get_new_keys():
                print("[BREAK] GO PRESSED.")
                break
            
            if self.pc in self.lines:
                self.execute_line(self.lines[self.pc])
            self.pc += 1

        self.running = False

    def cmd_goto(self, args):
        self.pc = int(args[0]) - 1

    def cmd_stop(self):
        self.stop_flag = True

    def cmd_cont(self):
        self.running = True
        self.stop_flag = False
        while self.running and not self.stop_flag:
            if self.pc not in self.lines:
                break
            self.execute_line(self.lines[self.pc])
            self.pc += 1

    def cmd_input(self, args):
        var_name = args[0]
        value = 0
        print(f"{var_name}? _")
        
        current_text = []
        while True:
            keys = kb.get_new_keys()
            # if there are keys, convert them to a string, and store for display
            if keys:
                if 'SPC' in keys:
                    current_text.append(' ')
                elif 'BSPC' in keys:
                    current_text = current_text[:-1]
                else:
                    current_text += [i for i in keys if i != 'ENT']
                
                scr_buf[11] = f"{var_name}? " + ''.join(current_text) + "_"
                scr_show()
                
                if 'ENT' in keys or 'GO' in keys:
                    scr_buf[11] = scr_buf[11][:-1]
                    try:
                        line = ''.join(current_text)
                        value = line
                        break
                    except Exception as e:
                        scr_feed(f"{e}")
                    
                    scr_show()
                
        if var_name.endswith("$"):
            self.variables[var_name] = value
        else:
            self.variables[var_name] = eval(value)

    def cmd_if(self, args):
        condition = " ".join(args[:args.index("THEN")])
        if self.eval_expr(condition):
            cmd = " ".join(args[args.index("THEN") + 1:])
            self.execute_line(cmd)

    def cmd_for(self, args):
        var_name = args[0]
        start = self.eval_expr(args[2])
        end = self.eval_expr(args[4])
        step = self.eval_expr(args[6]) if len(args) > 6 else 1
        self.variables[var_name] = start
        self.call_stack.append((self.pc, var_name, end, step))

    def cmd_next(self, args):
        if not self.call_stack:
            return
        loop_info = self.call_stack[-1]
        self.variables[loop_info[1]] += loop_info[3]
        if self.variables[loop_info[1]] <= loop_info[2]:
            self.pc = loop_info[0]
        else:
            self.call_stack.pop()

    def cmd_while(self, args):
        condition = " ".join(args)
        self.call_stack.append((self.pc, condition))

    def cmd_wend(self, args):
        if not self.call_stack:
            return
        loop_info = self.call_stack[-1]
        if self.eval_expr(loop_info[1]):
            self.pc = loop_info[0]
        else:
            self.call_stack.pop()

    def cmd_gosub(self, args):
        self.call_stack.append(self.pc)
        self.pc = int(args[0]) - 1

    def cmd_return(self):
        if self.call_stack:
            self.pc = self.call_stack.pop()

    def cmd_dim(self, args):
        var_name = args[0]
        dimensions = [int(dim) for dim in args[1][1:-1].split(',')]
        self.variables[var_name] = [[0] * dimensions[1] for _ in range(dimensions[0])]

    def cmd_load(self, args):
        file_name = args[0].strip('"')
        try:
            with open(file_name, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        line_number, code = line.split(" ", 1)
                        self.add_line(int(line_number), code)
            print(f"Loaded {file_name}")
        except Exception as e:
            print(f"Error loading {file_name}: {e}")

    def cmd_save(self, args):
        file_name = args[0].strip('"')
        try:
            with open(file_name, 'w') as f:
                for line_number in sorted(self.lines.keys()):
                    f.write(f"{line_number} {self.lines[line_number]}\n")
            print(f"Saved to {file_name}")
        except Exception as e:
            print(f"Error saving to {file_name}: {e}")

    def add_line(self, line_number, line):
        self.lines[line_number] = line

    def remove_line(self, line_number):
        if line_number in self.lines:
            del self.lines[line_number]

#--------------------------------------------------------------------------------------------------
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ Main Loop: ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def main_loop():
    """
    The main loop of the program. Runs forever (until program is closed).
    """
    
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ INITIALIZATION: ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    
    # If you need to do any initial work before starting the loop, this is a decent place to do that.
    
    # create BASIC interpreter
    interpreter = BASICInterpreter()
    
    # create variable to remember text between loops
    current_text = []
    scr_feed("MicroHydra BASIC 1.0.")
    scr_feed("Press GO Button to Break.")
    scr_feed("] _")
    scr_show()
    
    
    while True: # Fill this loop with your program logic! (delete old code you dont need)
        
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ INPUT: ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        
        # put user input logic here
        
        # get list of newly pressed keys
        keys = kb.get_new_keys()
        
        # if there are keys, convert them to a string, and store for display
        if keys:
            if 'GO' in keys:
                machine.reset()
            if 'SPC' in keys:
                current_text.append(' ')
            elif 'BSPC' in keys:
                current_text = current_text[:-1]
            else:
                current_text += [i.upper() if i in "abcdefghijklmnopqrstuvwxyz" else i.lower() for i in keys if i != 'ENT']
            
            scr_buf[11] = "] " + ''.join(current_text) + "_"
            scr_show()
            
            if 'ENT' in keys:
                scr_buf[11] = scr_buf[11][:-1]
                try:
                    line = ''.join(current_text)
                    if not line.strip():
                        continue
                    if line.isdigit():
                        interpreter.remove_line(int(line))
                    elif line.split()[0].isdigit():
                        line_number = int(line.split()[0])
                        interpreter.add_line(line_number, " ".join(line.split()[1:]))
                    else:
                        interpreter.execute_line(line)
                        
                except Exception as e:
                    scr_feed(f"{e}")
                
                scr_feed("] _") 
                scr_show()
                current_text = []
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ HOUSEKEEPING: ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        
        # anything that needs to be done to prepare for next loop
        
        # do nothing for 10 milliseconds
        time.sleep_ms(10)


# start the main loop
try:
    main_loop()
except Exception as e:
    with open('/log.txt', 'w') as f:
        f.write('[MHBASIC]')
        sys.print_exception(e, f)
    
    tft.text(text=f"{e}", x=0, y=0, color=config['ui_color'])
    tft.show()

