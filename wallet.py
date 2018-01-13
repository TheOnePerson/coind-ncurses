#!/usr/bin/env python
# -*- coding: latin-1 -*-
import curses, time


import global_mod as g
import getstr
import footer

def draw_window(state, window, rpc_queue=None, do_clear = True):

	if do_clear:
		window.clear()
		window.refresh()

	win_header = curses.newwin(3, g.x, 0, 0)

	unit = g.coin_unit
	if 'testnet' in state:
		if state['testnet']:
			unit = g.coin_unit_test

	if 'wallet' in state or 'walletinfo' in state:
		if 'balance' in state:
			balance_string = "Balance: " + "%0.8f" % state['balance'] + " " + unit
			if 'unconfirmedbalance' in state:
				if state['unconfirmedbalance'] != 0:
					balance_string += " (+" + "%0.8f" % state['unconfirmedbalance'] + " unconf)"
			if 'unconfirmed_balance' in state:
				if state['unconfirmed_balance'] != 0:
					balance_string += " (+" + "%0.8f" % state['unconfirmed_balance'] + " unconf)"
			window.addstr(0, 1, balance_string, curses.A_BOLD)
		
		if 'walletinfo' in state:
			if 'paytxfee' in state['walletinfo']:
				fee_string = "Fee: " + "%0.8f" % state['walletinfo']['paytxfee'] + " " + unit + " per kB"
				window.addstr(1, 1, fee_string, curses.A_BOLD)
			fee_string = "Wallet status: "
			if 'unlocked_until' in state['walletinfo']:
				if state['walletinfo']['unlocked_until'] == 0:
					fee_string += 'locked'
					window.addstr(2, 1, fee_string, curses.A_BOLD)
				else:
					fee_string += 'unlocked until ' + time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(state['walletinfo']['unlocked_until']))
					window.addstr(2, 1, fee_string, curses.A_BOLD + curses.A_REVERSE)
			else:
				fee_string += 'not encrypted!'
				window.addstr(2, 1, fee_string, curses.A_BOLD + curses.A_REVERSE)

		if state['wallet']['mode'] == 'tx':
			g.addstr_rjust(window, 0, "(W: refresh, A: list addresses)", curses.A_BOLD, 1)
			g.addstr_rjust(window, 1, "(X: set tx fee, R: new address)", curses.A_BOLD, 1)
			g.addstr_rjust(window, 2, "(S: send " + unit + ", E: export wallet.dat)", curses.A_BOLD, 1)
			draw_transactions(state)
		elif state['wallet']['mode'] == 'settxfee':
			draw_fee_input_window(state, window, rpc_queue)
		elif state['wallet']['mode'] == 'newaddress':
			draw_new_address_window(state, window, rpc_queue)
		elif state['wallet']['mode'] == 'sendtoaddress':
			draw_send_coins_window(state, window, rpc_queue)
		elif state['wallet']['mode'] == 'backupwallet':
			draw_backup_wallet_window(state, window, rpc_queue)
		else:
			g.addstr_rjust(window, 0, "(A: refresh, W: list tx)", curses.A_BOLD, 1)
			g.addstr_rjust(window, 1, "(X: set tx fee, R: new address)", curses.A_BOLD, 1)
			g.addstr_rjust(window, 2, "(S: send " + unit + ", E: export wallet.dat)", curses.A_BOLD, 1)
			draw_addresses(state)

	else:
		if rpc_queue.qsize() > 0:
			g.addstr_cjust(win_header, 0, "...waiting for wallet information being processed...", curses.A_BOLD + curses.color_pair(3))
		else:
			win_header.addstr(0, 1, "no wallet information loaded.", curses.A_BOLD + curses.color_pair(3))
			win_header.addstr(1, 1, "press 'W' to refresh", curses.A_BOLD)

	win_header.refresh()
	footer.draw_window(state, rpc_queue)

def draw_transactions(state):
	g.viewport_heigth = g.y - 5
	win_transactions = curses.newwin(g.viewport_heigth, g.x, 4, 0)

	win_transactions.addstr(0, 1, "{:,d}".format(len(state['wallet']['view_string'])/(5 if state['wallet']['verbose'] > 0 else 4)) + " transactions:", curses.A_BOLD + curses.color_pair(5))
	caption = "(UP/DOWN: scroll, ENTER: view, V: less verbose)" if state['wallet']['verbose'] > 0 else "(UP/DOWN: scroll, ENTER: view, V: verbose)"
	g.addstr_rjust(win_transactions, 0, caption, curses.A_BOLD + curses.color_pair(5), 1)
	
	offset = state['wallet']['offset']

	for index in xrange(offset, offset + g.viewport_heigth - 1):
		if index < len(state['wallet']['view_string']):
				condition = (index == offset + g.viewport_heigth - 2) and (index+1 < len(state['wallet']['view_string']))
				condition = condition or ( (index == offset) and (index > 0) )

				if condition:
					win_transactions.addstr(index+1-offset, 1, "...")
				else:
					win_transactions.addstr(index+1-offset, 1, state['wallet']['view_string'][index], curses.color_pair(state['wallet']['view_colorpair'][index]))

				if index == (state['wallet']['cursor']* (5 if state['wallet']['verbose'] > 0 else 4) + 1):
					win_transactions.addstr(index+1-offset, 1, ">", curses.A_REVERSE + curses.A_BOLD)

	win_transactions.refresh()

def draw_addresses(state):
	g.viewport_heigth = g.y - 5
	win_addresses = curses.newwin(g.viewport_heigth, g.x, 4, 0)
	offset = state['wallet']['offset']

	if 'addresses_view_string' in state['wallet']:

		win_addresses.addstr(0, 1, str(len(state['wallet']['addresses_view_string'])/4) + " addresses:", curses.A_BOLD + curses.color_pair(5))
		g.addstr_rjust(win_addresses, 0, "(UP/DOWN: scroll)", curses.A_BOLD + curses.color_pair(5), 1)
		
		for index in xrange(offset, offset + g.viewport_heigth - 1):
			if index < len(state['wallet']['addresses_view_string']):
					condition = (index == offset + g.viewport_heigth - 2) and (index+1 < len(state['wallet']['addresses_view_string']))
					condition = condition or ( (index == offset) and (index > 0) )

					if condition:
						win_addresses.addstr(index+1-offset, 1, "...")
					else:
						win_addresses.addstr(index+1-offset, 1, state['wallet']['addresses_view_string'][index], curses.color_pair(state['wallet']['addresses_view_colorpair'][index]))

	else:
		g.addstr_cjust(win_addresses, 0, "...waiting for address information being processed...", curses.A_BOLD + curses.color_pair(3))
		# win_addresses.addstr(1, 1, "...waiting for address information being processed...", curses.A_BOLD + curses.color_pair(3))

	win_addresses.refresh()

def draw_fee_input_window(state, window, rpc_queue):
	color = curses.color_pair(1)
	unit = g.coin_unit
	if g.testnet:
		color = curses.color_pair(2)
		unit = g.coin_unit_test

	UI = getstr.UserInput(window, "fee input mode")
	if 'walletinfo' in state:
		if 'paytxfee' in state['walletinfo']:
			fee_string = "Current transaction fee: " + "%0.8f" % state['walletinfo']['paytxfee'] + " " + unit + " per kB"
			UI.addline(fee_string)

	if 'estimatefee' in state and len(state['estimatefee']):
		string = "Estimatefee: "
		for item in state['estimatefee']:
			if item['value'] >= 0:
				string += "{:0.8f}".format(item['value']) + " " + unit + " per kB (" + str(item['blocks']) + (" blocks) " if int(item['blocks']) > 1 else " block) ")
		UI.addline(string, curses.A_NORMAL)

	UI.addline("Please enter new transaction fee in " + unit + " per kB:", curses.A_BOLD)
	
	try:
		new_fee = float(UI.getstr(64))
	except ValueError:
		new_fee = -1
	
	if new_fee >= 0:
		s = {'settxfee': "{:0.8f}".format(new_fee)}
		UI.addmessageline("Setting transaction fee value to " + "{:0.8f}".format(new_fee) + " " + unit + " per kB...", color + curses.A_BOLD)
		rpc_queue.put(s)
	else:
		UI.addmessageline("No valid fee amount entered. Aborting.", color + curses.A_BOLD)
		UI.clear()
		state['wallet']['mode'] = 'addresses'
		rpc_queue.put('listsinceblock')

def draw_new_address_window(state, window, rpc_queue):
	color = curses.color_pair(1)
	if g.testnet:
		color = curses.color_pair(2)

	UI = getstr.UserInput(window, "new receiving address mode")

	abort = False
	error_string = ""
	UI.addline("Please enter an address label (optional):", curses.A_BOLD)
	try:
		new_account = str(UI.getstr(128)).strip()
	except:
		abort = True
	
	if not abort:
		UI.addline("Do you want to add a [r]eceiving or a [w]atch-only address? [r/w]", curses.A_BOLD)
		try:
			new_type = str(UI.getstr(1))
		except:
			error_string = "Invalid address type entered. "
			abort = True

		if new_type == 'r':
			state['wallet']['y'] = UI._y + 2
			state['wallet']['newlabel'] = new_account
			rpc_queue.put({'getnewaddress': new_account})
			UI.addmessageline("Creating new receiving address" + (" for account " + "'{}'".format(new_account) if len(new_account) else "") + "...", 
								color + curses.A_BOLD)
		elif new_type == 'w':
			UI.addline("Please enter watch-only address:", curses.A_BOLD)
			new_address = ""
			try:
				new_address = UI.getstr(35).strip()
			except:
				abort = True
			if not check_address(new_address):
				error_string = "Invalid address entered. "
				abort = True
			if not abort:
				UI.addline("Do you want to rescan the entire blockchain for matching transactions? [y/N]", curses.A_BOLD)
				try:
					new_rescan = str(UI.getstr(1))
				except:
					abort = True
				if new_rescan in ['y', 'Y']:
					new_rescan = True
				elif new_rescan in ['n', 'N']:
					new_rescan = False
				else:
					abort = True

				if not abort:
					state['wallet']['newlabel'] = new_account
					state['wallet']['newaddress'] = new_address
					s = {'importaddress': {'account': new_account, 'address': new_address, 'rescan': bool(new_rescan)}}
					rpc_queue.put(s)
					UI.addmessageline("Importing watch-only address" + (" for account " + "'{}'".format(new_account) if len(new_account) else "") + "...", 
										color + curses.A_BOLD)
		else:
			abort = True

	if abort:
		UI.addmessageline(error_string + "Aborting.", color + curses.A_BOLD)
		state['wallet']['mode'] = 'addresses'
		rpc_queue.put('listreceivedbyaddress')
		UI.clear()
		footer.draw_window(state, rpc_queue, True)

def draw_new_address_update(state, window):
	color = curses.color_pair(1)
	if g.testnet:
		color = curses.color_pair(2)

	if 'newaddress' in state['wallet'] and 'y' in state['wallet']:
		y = int(state['wallet']['y'])
		this_y, this_x = window.getmaxyx()
		if y >= this_y:
			y -= 1
		window.addstr(y, 1, "Address successfully added: " + state['wallet']['newaddress'], color + curses.A_BOLD)
		window.refresh()
		time.sleep(4)

def draw_backup_wallet_window(state, window, rpc_queue):
	color = curses.color_pair(1)
	if g.testnet:
		color = curses.color_pair(2)

	UI = getstr.UserInput(window, "backup wallet.dat mode")

	UI.addline("Please enter destination file or directory name:", curses.A_BOLD)
	try:
		backup = str(UI.getstr(254)).strip()
	except ValueError:
		backup = ""
	
	state['wallet']['y'] = UI._y + 1
	if backup != "":
		rpc_queue.put({'backupwallet': backup })
		UI.addmessageline("Backing up wallet.dat...", color + curses.A_BOLD)
	else:
		UI.addmessageline("Invalid file or directory name. Aborting.", color + curses.A_BOLD)
		state['wallet']['mode'] = 'tx'
		rpc_queue.put('getwalletinfo')
		rpc_queue.put('listsinceblock')
		UI.clear()

def draw_send_coins_window(state, window, rpc_queue):
	color = curses.color_pair(1)
	unit = g.coin_unit
	if g.testnet:
		color = curses.color_pair(2)
		unit = g.coin_unit_test

	UI = getstr.UserInput(window, "send " + unit + " mode")

	if 'balance' in state and g.y >= 14:
		display_string = "Current balance: " + "%0.8f" % state['balance'] + " " + unit
		if 'unconfirmedbalance' in state:
			if state['unconfirmedbalance'] != 0:
				display_string += " (+" + "%0.8f" % state['unconfirmedbalance'] + " unconf)"
		if 'unconfirmed_balance' in state:
			if state['unconfirmed_balance'] != 0:
				display_string += " (+" + "%0.8f" % state['unconfirmed_balance'] + " unconf)"
		UI.addline(display_string)

	if 'walletinfo' in state:
		if 'paytxfee' in state['walletinfo'] and g.y >= 15:
			display_string = "Current transaction fee: " + "%0.8f" % state['walletinfo']['paytxfee'] + " " + unit + " per kB"
			UI.addline(display_string, curses.A_NORMAL)

	if 'estimatefee' in state and g.y >= 17:
		display_string = "Estimatefee: "
		for item in state['estimatefee']:
			if item['value'] > 0:
				display_string += "{:0.8f}".format(item['value']) + " " + unit + " per kB (" + str(item['blocks']) + (" blocks) " if int(item['blocks']) > 1 else " block) ")
		UI.addline(display_string, curses.A_NORMAL)

	err_msg = ""
	abort = False

	UI.addline("Please enter amount of " + unit + " so send:", curses.A_BOLD)
	try:
		amount = float(UI.getstr(32))
	except ValueError:
		amount = -1
	
	if amount > 0:

		state['newtransaction']['amount'] = "%0.8f" % amount

		UI.addline("Please enter receiving address:", curses.A_BOLD)
		try:
			address = UI.getstr(35).strip()
		except:
			abort = True

		if check_address(address) and not abort:

			state['newtransaction']['address'] = address
			
			UI.addline("Please enter a comment on the transaction (optional):", curses.A_BOLD)
			try:
				comment = UI.getstr(128).strip()
			except:
				abort = True

			if not abort:

				state['newtransaction']['comment'] = comment
				
				UI.addline("Please enter a comment on the recipient (optional):", curses.A_BOLD)
				try:
					comment_to = UI.getstr(128).strip()
				except:
					abort = True

				if not abort:

					state['newtransaction']['comment_to'] = comment_to
				
					if g.y >= 19:
						UI.addline()
					if g.y >= 16:
						UI.addline("You will send " + "{:0.8f}".format(amount) + " " + unit + " (+ fee) to the address '" + address + "'")
					if g.y >= 18:
						UI.addline()

					encrypted = False
					if 'walletinfo' in state:
						if 'unlocked_until' in state['walletinfo']:
							encrypted = True

					if encrypted:
						UI.addline("Please confirm this transaction by providing your wallet's passphrase:", curses.A_BOLD)
						try:
							password = getstr.getstr(128, UI._y, 1, "*")
							pass
						except:
							abort = True
					else:
						abort = not UI.continue_yesno(False)
						UI._y -= 1

					if not abort:

						if encrypted:
							if g.y >= 18:
								UI.addline()
							s = {'walletpassphrase': password}
							rpc_queue.put(s)
							UI.addmessageline("Unlocking wallet and sending transaction...", color + curses.A_BOLD)
						else:
							if g.y >= 17:
								UI.addline()
							s = {'sendtoaddress': {'address': address, 'amount': str(amount), 'comment': comment, 'comment_to': comment_to}}
							rpc_queue.put(s)
							UI.addmessageline("Sending transaction...", color + curses.A_BOLD)
						state['wallet']['y'] = UI._y

		else:
			err_msg = "Invalid receiving address."
			abort = True

	else:
		err_msg = "Invalid amount."
		abort = True

	if abort:
		UI.addmessageline(err_msg + " Aborting.", color + curses.A_BOLD)
		UI.clear()
		state['wallet']['mode'] = 'addresses'
		rpc_queue.put('listsinceblock')

def draw_transaction_update(state, window):
	color = curses.color_pair(1)
	if g.testnet:
		color = curses.color_pair(2)

	if 'newtransaction' in state:
		if 'y' in state['wallet']:
			y = int(state['wallet']['y'])
			this_y, this_x = window.getmaxyx()
			if y >= this_y:
				y -= 1
			if 'result' in state['newtransaction']:
				if len(state['newtransaction']['result']) < 26:
					window.addstr(y, 1, "Sending error - transaction failed.".ljust(g.x - 2, " "), color + curses.A_BOLD)
				else:
					window.addstr(y, 1, ("Transaction successful. Tx id: " + state['newtransaction']['result']).ljust(g.x - 2, " "), color + curses.A_BOLD)
				window.refresh()
				time.sleep(4)

def check_address(address):
	if g.coinmode == 'LTC':
		# Addresses for litecoin:
		return bool(len(address) >= 26 and len(address) <= 35 and ((not g.testnet and (address.startswith('L') or address.startswith('3') or address.startswith('M'))) or (g.testnet and (address.startswith('m') or address.startswith('n') or address.startswith('2')))))
	elif g.coinmode == 'BCH':
		# Addresses for bitcoin cash:
		return bool(len(address) >= 26 and len(address) <= 35 and ((not g.testnet and (address.startswith('1') or address.startswith('3'))) or (g.testnet and (address.startswith('m') or address.startswith('n') or address.startswith('2')))))
	else:
		# Addresses for bitcoin:
		return bool(len(address) >= 26 and len(address) <= 35 and ((not g.testnet and (address.startswith('1') or address.startswith('3'))) or (g.testnet and (address.startswith('m') or address.startswith('n') or address.startswith('2')))))
