#!/usr/bin/env python
import curses

import global_mod as g
import footer

def draw_window(state, window, rpc_queue=None):
    window.clear()
    window.refresh()
    win_header = curses.newwin(2, g.x, 0, 0)

    unit = g.coin_unit
    if 'testnet' in state:
        if state['testnet']:
            unit = g.coin_unit_test

    if 'wallet' in state:
        if 'balance' in state:
            balance_string = "balance: " + "%0.8f" % state['balance'] + " " + unit
            if 'unconfirmedbalance' in state:
                if state['unconfirmedbalance'] != 0:
                    balance_string += " (+" + "%0.8f" % state['unconfirmedbalance'] + " unconf)"
            window.addstr(0, 1, balance_string, curses.A_BOLD)
            

        if state['wallet']['mode'] == 'tx':
            g.addstr_rjust(window, 0, "(W: refresh, A: list addresses)", curses.A_BOLD, 1)
            draw_transactions(state)
        else:
            g.addstr_rjust(window, 0, "(A: refresh, W: list transactions)", curses.A_BOLD, 1)
            draw_addresses(state)

    else:
        if rpc_queue.qsize() > 0:
            g.addstr_cjust(win_header, 0, "...waiting for wallet information being processed...", curses.A_BOLD + curses.color_pair(3))
            # win_header.addstr(0, 1, "...waiting for wallet information being processed...", curses.A_BOLD + curses.color_pair(3))
        else:
            win_header.addstr(0, 1, "no wallet information loaded. -disablewallet, perhaps?", curses.A_BOLD + curses.color_pair(3))
            win_header.addstr(1, 1, "press 'W' to refresh", curses.A_BOLD)

    win_header.refresh()
    footer.draw_window(state, rpc_queue)

def draw_transactions(state):
    window_height = g.y - 3
    win_transactions = curses.newwin(window_height, g.x, 2, 0)

    
    win_transactions.addstr(0, 1, str(len(state['wallet']['view_string'])/4) + " transactions:", curses.A_BOLD + curses.color_pair(5))
    g.addstr_rjust(win_transactions, 0, "(UP/DOWN: scroll, ENTER: view)", curses.A_BOLD + curses.color_pair(5), 1)
    
    offset = state['wallet']['offset']

    for index in xrange(offset, offset+window_height-1):
        if index < len(state['wallet']['view_string']):
                condition = (index == offset+window_height-2) and (index+1 < len(state['wallet']['view_string']))
                condition = condition or ( (index == offset) and (index > 0) )

                if condition:
                    win_transactions.addstr(index+1-offset, 1, "...")
                else:
                    win_transactions.addstr(index+1-offset, 1, state['wallet']['view_string'][index], curses.color_pair(state['wallet']['view_colorpair'][index]))

                if index == (state['wallet']['cursor']*4 + 1):
                    win_transactions.addstr(index+1-offset, 1, ">", curses.A_REVERSE + curses.A_BOLD)

    win_transactions.refresh()

def draw_addresses(state):
    window_height = g.y - 3
    win_addresses = curses.newwin(window_height, g.x, 2, 0)
    offset = state['wallet']['offset']

    if 'addresses_view_string' in state['wallet']:

        win_addresses.addstr(0, 1, str(len(state['wallet']['addresses_view_string'])/4) + " addresses:", curses.A_BOLD + curses.color_pair(5))
        g.addstr_rjust(win_addresses, 0, "(UP/DOWN: scroll)", curses.A_BOLD + curses.color_pair(5), 1)
        
        for index in xrange(offset, offset+window_height-1):
            if index < len(state['wallet']['addresses_view_string']):
                    condition = (index == offset+window_height-2) and (index+1 < len(state['wallet']['addresses_view_string']))
                    condition = condition or ( (index == offset) and (index > 0) )

                    if condition:
                        win_addresses.addstr(index+1-offset, 1, "...")
                    else:
                        try:
                            win_addresses.addstr(index+1-offset, 1, state['wallet']['addresses_view_string'][index], curses.color_pair(state['wallet']['addresses_view_colorpair'][index]))
                            # win_addresses.addstr(index+1-offset, 1, state['wallet']['addresses_view_string'][index], curses.color_pair(1))
                        except:
                            print(str(len(state['wallet']['addresses_view_colorpair'])) + "|" + str(state['wallet']['addresses_view_colorpair'][index]) + "|" + str(index))

    else:
        g.addstr_cjust(win_addresses, 0, "...waiting for address information being processed...", curses.A_BOLD + curses.color_pair(3))
        # win_addresses.addstr(1, 1, "...waiting for address information being processed...", curses.A_BOLD + curses.color_pair(3))

    win_addresses.refresh()
