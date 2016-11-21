#!/usr/bin/env python
# -*- coding: latin-1 -*-
import curses, time


import global_mod as g
from getstr import UserInput
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
            if 'unlocked_until' in state['walletinfo']:
                fee_string = "Wallet status: "
                if state['walletinfo']['unlocked_until'] == 0:
                    fee_string += 'locked'
                    window.addstr(2, 1, fee_string, curses.A_BOLD)
                else:
                    fee_string += 'unlocked until ' + time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(state['walletinfo']['unlocked_until']))
                    window.addstr(2, 1, fee_string, curses.A_BOLD + curses.A_REVERSE)

        if state['wallet']['mode'] == 'tx':
            g.addstr_rjust(window, 0, "(W: refresh, A: list addresses)", curses.A_BOLD, 1)
            g.addstr_rjust(window, 1, "(X: set tx fee, R: new receiving address)", curses.A_BOLD, 1)
            g.addstr_rjust(window, 2, "(S: send " + g.coin_unit + ")", curses.A_BOLD, 1)
            draw_transactions(state)
        elif state['wallet']['mode'] == 'settxfee':
            draw_fee_input_window(state, window, rpc_queue)
        elif state['wallet']['mode'] == 'newaddress':
            draw_new_address_window(state, window, rpc_queue)
        elif state['wallet']['mode'] == 'sendtoaddress':
            draw_send_coins_window(state, window, rpc_queue)
        else:
            g.addstr_rjust(window, 0, "(A: refresh, W: list tx)", curses.A_BOLD, 1)
            g.addstr_rjust(window, 1, "(X: set tx fee, R: new receiving address)", curses.A_BOLD, 1)
            g.addstr_rjust(window, 2, "(S: send " + g.coin_unit + ")", curses.A_BOLD, 1)
            draw_addresses(state)

    else:
        if rpc_queue.qsize() > 0:
            g.addstr_cjust(win_header, 0, "...waiting for wallet information being processed...", curses.A_BOLD + curses.color_pair(3))
        else:
            win_header.addstr(0, 1, "no wallet information loaded. -disablewallet, perhaps?", curses.A_BOLD + curses.color_pair(3))
            win_header.addstr(1, 1, "press 'W' to refresh", curses.A_BOLD)

    win_header.refresh()
    footer.draw_window(state, rpc_queue)

def draw_transactions(state):
    g.viewport_heigth = g.y - 5
    win_transactions = curses.newwin(g.viewport_heigth, g.x, 4, 0)

    win_transactions.addstr(0, 1, str(len(state['wallet']['view_string'])/4) + " transactions:", curses.A_BOLD + curses.color_pair(5))
    g.addstr_rjust(win_transactions, 0, "(UP/DOWN: scroll, ENTER: view)", curses.A_BOLD + curses.color_pair(5), 1)
    
    offset = state['wallet']['offset']

    for index in xrange(offset, offset + g.viewport_heigth - 1):
        if index < len(state['wallet']['view_string']):
                condition = (index == offset + g.viewport_heigth - 2) and (index+1 < len(state['wallet']['view_string']))
                condition = condition or ( (index == offset) and (index > 0) )

                if condition:
                    win_transactions.addstr(index+1-offset, 1, "...")
                else:
                    win_transactions.addstr(index+1-offset, 1, state['wallet']['view_string'][index], curses.color_pair(state['wallet']['view_colorpair'][index]))

                if index == (state['wallet']['cursor']*4 + 1):
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
    if g.testnet:
        color = curses.color_pair(2)

    UI = UserInput(window, "fee input mode")
    if 'walletinfo' in state:
        if 'paytxfee' in state['walletinfo']:
            fee_string = "Current transaction fee: " + "%0.8f" % state['walletinfo']['paytxfee'] + " " + g.coin_unit + " per kB"
            UI.addline(fee_string)

    if 'estimatefee' in state:
        string = "Estimatefee: "
        for item in state['estimatefee']:
            if item['value'] > 0:
                string += "{:0.8f}".format(item['value']) + " " + g.coin_unit + " per kB (" + str(item['blocks']) + (" blocks) " if int(item['blocks']) > 1 else " block) ")
        UI.addline(string, curses.A_NORMAL)

    UI.addline("Please enter new transaction fee in " + g.coin_unit + " per kB:", curses.A_BOLD)
    
    try:
        new_fee = float(UI.getstr(64))
    except ValueError:
        new_fee = -1
    
    if new_fee >= 0:
        s = {'settxfee': "{:0.8f}".format(new_fee)}
        UI.addmessageline("Setting transaction fee value to " + "{:0.8f}".format(new_fee) + " " + g.coin_unit + " per kB...", color + curses.A_BOLD)
        rpc_queue.put(s)
    else:
        UI.addmessageline("No valid fee amount entered", color + curses.A_BOLD)
        UI.clear()
        state['wallet']['mode'] = 'addresses'
        rpc_queue.put('listsinceblock')

def draw_new_address_window(state, window, rpc_queue):
    color = curses.color_pair(1)
    if g.testnet:
        color = curses.color_pair(2)

    UI = UserInput(window, "new receiving address mode")

    if 'newaddress' in state['wallet']:
        if 'newlabel' in state['wallet']:
            UI.addline("New receiving address created!", curses.A_BOLD)
            UI.addline("Label: " + state['wallet']['newlabel'], curses.A_NORMAL)
        UI.addline("Address: " + state['wallet']['newaddress'], curses.A_BOLD)
        UI.addline()
        UI.continue_enter()
        state['wallet']['mode'] = 'addresses'
        rpc_queue.put('getwalletinfo')
        rpc_queue.put('listsinceblock')
        UI.clear()

    else:

        UI.addline("Please enter address label:", curses.A_BOLD)
        try:
            new_account = str(UI.getstr(64)).strip()
        except ValueError:
            new_account = ""
    
        if new_account != "":
            s = {'getnewaddress': new_account }
            state['wallet']['newlabel'] = new_account
            rpc_queue.put(s)
            UI.addmessageline("Creating new receiving address for account " + "'{}'".format(new_account) + "...", color + curses.A_BOLD)
        else:
            UI.addmessageline("Aborting", color + curses.A_BOLD)
            state['wallet']['mode'] = 'addresses'
            rpc_queue.put('getwalletinfo')
            rpc_queue.put('listsinceblock')
            UI.clear()

def draw_send_coins_window(state, window, rpc_queue):
    color = curses.color_pair(1)
    if g.testnet:
        color = curses.color_pair(2)

    UI = UserInput(window, "send " + g.coin_unit + " mode")

    if 'balance' in state:
        display_string = "Current balance: " + "%0.8f" % state['balance'] + " " + g.coin_unit
        if 'unconfirmedbalance' in state:
            if state['unconfirmedbalance'] != 0:
                display_string += " (+" + "%0.8f" % state['unconfirmedbalance'] + " unconf)"
        if 'unconfirmed_balance' in state:
            if state['unconfirmed_balance'] != 0:
                display_string += " (+" + "%0.8f" % state['unconfirmed_balance'] + " unconf)"
        UI.addline(display_string)

    if 'walletinfo' in state:
        if 'paytxfee' in state['walletinfo']:
            display_string = "Current transaction fee: " + "%0.8f" % state['walletinfo']['paytxfee'] + " " + g.coin_unit + " per kB"
            UI.addline(display_string, curses.A_NORMAL)

    if 'estimatefee' in state:
        display_string = "Estimatefee: "
        for item in state['estimatefee']:
            if item['value'] > 0:
                display_string += "{:0.8f}".format(item['value']) + " " + g.coin_unit + " per kB (" + str(item['blocks']) + (" blocks) " if int(item['blocks']) > 1 else " block) ")
        UI.addline(display_string, curses.A_NORMAL)

    err_msg = ""
    abort = False

    UI.addline("Please enter amount of " + g.coin_unit + " so send:", curses.A_BOLD)
    try:
        amount = float(UI.getstr(32))
    except ValueError:
        amount = -1
    
    if amount > 0:

        UI.addline("Please enter receiving address:", curses.A_BOLD)
        try:
            address = UI.getstr(35).strip()
        except:
            abort = True

        if len(address) >= 26 and len(address) <= 35 and (address.startswith('1') or address.startswith('3')) and not abort:

            UI.addline("Please enter a comment (optional):", curses.A_BOLD)
            try:
                comment = UI.getstr(64).strip()
            except:
                abort = True

            if not abort:

                UI.addline()
                UI.addline("You will send " + "{:0.8f}".format(amount) + " " + g.coin_unit + " to the address '" + address + "'.")
                UI.addline()
                # TODO: check if wallet is locked! And add blank lines only if there is space for it!
                UI.addline("Please confirm this transaction by providing your wallet's passphrase:", curses.A_BOLD)
                try:
                    password = UI.getstr(128)
                except:
                    abort = True

                #s = {'settxfee': "{:0.8f}".format(new_fee)}
                #UI.addmessageline("Setting transaction fee value to " + "{:0.8f}".format(new_fee) + " " + g.coin_unit + " per kB...", color + curses.A_BOLD)
                #rpc_queue.put(s)

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
