#!/usr/bin/env python

from curses import A_NORMAL

version = "v0.0.28"
modes = ['monitor', 'wallet', 'peers', 'block', 'tx', 'console', 'net', 'forks', 'quit']

# the following line just declares the default coinmode. Will be overwritten by main.py if user has provided another value as argument
coinmode = None

# now init with nothing...
coin_unit = None
coin_unit_test = None
coin_name = None
coin_smallname = None
rpc_deamon = None
rpc_port = None
rpc_port_test = None
node_port = None
node_port_test = None
reward_base = None		# initial reward for mining a block
halving_blockamount = None	# number ob blocks after which the reward is being halved
blocks_per_day = None
testnet = None
x = None
y = None
viewport_heigth = None
wallet_support = True		# default, get's adjusted in process.py

def get_default_coinmode():
	return 'BTC'

def init_coinmode():
	global coinmode
	global coin_unit
	global coin_unit_test
	global coin_name
	global coin_smallname
	global rpc_deamon
	global rpc_port
	global rpc_port_test
	global node_port
	global node_port_test
	global reward_base
	global halving_blockamount
	global blocks_per_day
	if coinmode == 'LTC':
		# Config for litecoin:
		coin_unit = 'LTC'
		coin_unit_test = 'TNC'
		coin_name = 'Litecoin'
		coin_smallname = 'litecoin'
		rpc_deamon = coin_smallname + 'd'
		rpc_port = '9332'
		rpc_port_test = '19332'
		node_port = '9333'
		node_port_test = '19333'
		reward_base = 50		# initial reward for mining a block
		halving_blockamount = 840000	# number ob blocks after which the reward is being halved
		blocks_per_day = 576
	elif coinmode == 'BCH':
		# Config for bitcoin cash:
		coin_unit = 'BCH'
		coin_unit_test = 'TCH'
		coin_name = 'Bitcoin Cash'
		coin_smallname = 'bitcoincash'
		rpc_deamon = 'bitcoind'
		rpc_port = '8332'
		rpc_port_test = '18332'
		node_port = '8333'
		node_port_test = '18333'
		reward_base = 50		# initial reward for mining a block
		halving_blockamount = 210000	# number ob blocks after which the reward is being halved
		blocks_per_day = 144
	elif coinmode == 'BSV':
		# Config for bitcoin cash SV:
		coin_unit = 'BSV'
		coin_unit_test = 'TSV'
		coin_name = 'Bitcoin Cash SV'
		coin_smallname = 'bitcoincashsv'
		rpc_deamon = 'bitcoind'
		rpc_port = '8332'
		rpc_port_test = '18332'
		node_port = '8333'
		node_port_test = '18333'
		reward_base = 50		# initial reward for mining a block
		halving_blockamount = 210000	# number ob blocks after which the reward is being halved
		blocks_per_day = 144
	elif coinmode == 'BTG':
		# Config for bitcoin gold:
		coin_unit = 'BTG'
		coin_unit_test = 'TTG'
		coin_name = 'Bitcoin Gold'
		coin_smallname = 'bitcoingold'
		rpc_deamon = 'bgoldd'
		rpc_port = '8332'
		rpc_port_test = '18332'
		node_port = '8333'
		node_port_test = '18333'
		reward_base = 50		# initial reward for mining a block
		halving_blockamount = 210000	# number ob blocks after which the reward is being halved
		blocks_per_day = 144
	else:
		# Config for bitcoin:
		coin_unit = 'BTC'
		coin_unit_test = 'TNC'
		coin_name = 'Bitcoin'
		coin_smallname = 'bitcoin'
		rpc_deamon = coin_smallname + 'd'
		rpc_port = '8332'
		rpc_port_test = '18332'
		node_port = '8333'
		node_port_test = '18333'
		reward_base = 50		# initial reward for mining a block
		halving_blockamount = 210000	# number ob blocks after which the reward is being halved
		blocks_per_day = 144

def addstr_rjust(window, y, string, attribs=A_NORMAL, padding=0, num_cols=1, col=0):
	""" prints out a right-aligned string on the given curses window.
	Max x position is taken from module's global variable.
	padding = number of spaces as a right margin. Default 0.
	num_cols = window can be split into virtual columns. Default 1.
	col = virtual column where the string is printed. Default 0 (=first column).
	"""
	global x
	(max_y, max_x) = window.getmaxyx()
	if max_x > x: max_x = x
	if num_cols > 1:
		max_x = int(max_x / num_cols) * (col + 1)
	if len(string) <= max_x:
		if padding + len(string) <= max_x:
			try:
				window.addstr(y, max_x - len(string) - padding, string, attribs)
			except:
				#print("Error! y=" + str(y) + ", max_x=" + str(max_x) + ", len(string)=" + str(len(string)) + ", padding=" + str(padding))
				pass
		else:
			window.addstr(y, max_x - len(string), string, attribs)

def addstr_ljust(window, y, string, attribs=A_NORMAL, padding=0, num_cols=1, col=0):
	""" prints out a left-aligned string on the given curses window.
	padding = number of spaces as a left margin. Default 0.
	num_cols = window can be split into virtual columns. Default 1.
	col = virtual column where the string is printed. Default 0 (=first column).
	"""
	global x
	if num_cols > 1:
		(max_y, max_x) = window.getmaxyx()
		if max_x > x: max_x = x
		print_x = int(max_x / num_cols) * col
	else:
		print_x = 0
	window.addstr(y, print_x + padding, string, attribs)

def addstr_cjust(window, y, string, attribs=A_NORMAL, padding=0, num_cols=1, col=0):
	""" prints out a centered string on the given curses window.
	Max x position is taken from module's global variable.
	padding = number of spaces as an additional right margin. Default 0.
	num_cols = window can be split into virtual columns. Default 1.
	col = virtual column where the string is printed. Default 0 (=first column).
	"""
	global x
	(max_y, max_x) = window.getmaxyx()
	if max_x > x: max_x = x
	min_x = 0
	if num_cols > 1:
		max_x = int(max_x / num_cols) * (col + 1)
		min_x = int(max_x / num_cols) * col
	l = len(string)
	print_x = int((max_x - padding - min_x - l) / 2) + min_x
	if print_x < 0: print_x = 0
	if l <= max_x + print_x:
		window.addstr(y, print_x, string, attribs)


