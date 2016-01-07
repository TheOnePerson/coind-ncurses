#!/usr/bin/env python

version = "v0.0.24"
modes = ['monitor', 'wallet', 'peers', 'block', 'tx', 'console', 'net', 'forks', 'quit']

# the following globals are coin specific!

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

'''
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
'''