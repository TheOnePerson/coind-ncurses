#!/usr/bin/env python

version = "v0.0.24"
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
