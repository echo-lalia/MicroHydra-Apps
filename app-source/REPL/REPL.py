try:
	import sys
	import io
	from lib import display
	from lib.hydra.config import Config
	from lib.userinput import UserInput
	from font import vga1_8x16 as font

	global sysprint
	sysprint = print

	global tft
	tft = display.Display(use_tiny_buf=True)

	global config
	config = Config()

	global kb
	kb = UserInput()

	global MAX_X
	MAX_X = tft.width - 16

	global MAX_Y
	MAX_Y = tft.height - (16 * 2)

	global SCREEN_POSITION
	SCREEN_POSITION = 0

	global printly_lines
	printly_lines = []

	def printly(text, no_increment=False):
		global MAX_X
		global MAX_Y
		global SCREEN_POSITION
		global tft
		global config
		global kb
		global printly_lines

		msg = str(text)

		if '\n' in msg:
			for line in msg.split("\n"):
				printly(line)
			return None

		# TODO: Line soft wrap.

		tft.fill(config.palette[2])

		if not no_increment:
			SCREEN_POSITION += 16

		while SCREEN_POSITION >= MAX_Y:
			if len(printly_lines) > 0:
				printly_lines.pop(0)
			SCREEN_POSITION -= 16
		if SCREEN_POSITION < 0:
			SCREEN_POSITION = 16

		if no_increment:
			if len(printly_lines) > 0:
				printly_lines.pop()
		printly_lines.append(msg)
		for idx, line in enumerate(printly_lines):
			offset = idx * 16
			tft.text(line, 16, offset, config.palette[8], font=font)
		
		tft.show()

	def printly_wrapper(*args, sep=' ', end='\n', file=None, flush=False):
		if file:
			return sysprint(*args, sep=sep, end=end, file=file, flush=flush)
		else:
			msg = sep.join([str(x) for x in args])
			return printly(msg, no_increment=(end != '\n'))

	def repl_help():
		helpdata = [
			'HELP: REPL',
			'GO button: Clear current input.',
			'ENTER button: Exec input.'
		]
		for line in helpdata:
			printly(line)
		printly('')
		return ''

	def reval(text):
		global print
		global sysprint

		if text == 'help':
			return repl_help()

		print = printly_wrapper # Swapout to print to REPL.

		try:
			try:
				r = eval(text)
			except SyntaxError:
				r = exec(text)
		except Exception as e:
			tmp = io.StringIO()
			tmp.write(str(e))
			tmp.write("\n\n")
			sys.print_exception(e, tmp)
			err = tmp.getvalue()
			r = ''
			for line in err.split("\n"):
				printly(line)
			printly('')

		# TODO: exec to get imports might need ast parsing. Shit.
		# As "last expression" needs a return or something.

		print = sysprint
		return r

	input_data = []
	while True:
		keys = kb.get_new_keys()
		keys = [x for x in keys if x not in ('ALT', 'CTL', 'FN', 'SHIFT', 'OPT')] # Strip invisible.
		
		if 'SPC' in keys:
			keys = list(map(lambda x: x if x != 'SPC' else ' ', keys)) # Expose spaces.

		while 'BSPC' in keys:
			if keys.index('BSPC') == 0:
				if len(input_data) > 0:
					input_data.pop(-1)
				keys.pop(0)
			else:
				keys.pop(keys.index('BSPC') - 1)
				keys.pop(keys.index('BSPC'))

		if 'UP' in keys or 'DOWN' in keys:
			pass # TODO: Input history...?
		if 'LEFT' in keys or 'RIGHT' in keys:
			pass # TODO: Line position editing...

		if 'ENT' in keys:
			before_ent = keys[:keys.index('ENT')]
			input_data.extend(before_ent)
			printly('> ' + ''.join(input_data), no_increment=True)

			r = reval(''.join(input_data)) # eval

			printly('$ ' + str(r))
			printly('')

			input_data = keys[keys.index('ENT') + 1:]
		elif 'G0' in keys or 'ESC' in keys:
			input_data = []
		else:
			input_data.extend(keys)
			printly('> ' + ''.join(input_data), no_increment=True)

		tft.show()

except Exception as e:
	with open('/REPL.crash.log', 'a+') as openFile:
		openFile.write(str(e))
		openFile.write("\n\n")
		sys.print_exception(e, openFile)
