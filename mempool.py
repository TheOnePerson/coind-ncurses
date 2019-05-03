#!/usr/bin/env python
import curses, time, calendar

import global_mod as g
from getstr import UserInput
import footer

def draw_window(state, window, rpc_queue=None):
    window.clear()
    window.refresh()
    win_header = curses.newwin(1, g.x, 0, 0)

    if 'mempool' in state:
        if 'num_transactions' in state['mempool']:
            height = str(state['mempool']['num_transactions'])
            if height > 0:
                win_header.addstr(0, 1, "Transactions in mempool: " + "{:,d}".format(int(height)), curses.A_BOLD)
                draw_transactions(state)
            else:
                win_header.addstr(0, 1, "No transactions in mempool - yet...", curses.A_BOLD)

        else:
            if rpc_queue.qsize() > 0:
                g.addstr_cjust(win_header, 0, "...waiting for mempool information being processed...", curses.A_BOLD + curses.color_pair(3))
            else:
                win_header.addstr(0, 1, "no mempool information loaded.", curses.A_BOLD + curses.color_pair(3))
    else:
        win_header.addstr(0, 1, "no mempool information loaded.", curses.A_BOLD + curses.color_pair(3))
        win_header.addstr(0, 32, "press 'M' to load mempool data.", curses.A_BOLD)

    win_header.refresh()
    footer.draw_window(state, rpc_queue)

def draw_transactions(state):
    g.viewport_height = state['y'] - 2
    win_transactions = curses.newwin(g.viewport_height, g.x, 1, 0)

    txdata = state['mempool']['transactions']

    g.addstr_rjust(win_transactions, 0, "(UP/DOWN: scroll, ENTER: view, M: refresh)", curses.A_BOLD + curses.color_pair(5), 1)
    # reset cursor if it's been resized off the bottom
    if state['mempool']['cursor'] > state['mempool']['offset'] + (g.viewport_height - 2):
        state['mempool']['offset'] = state['mempool']['cursor'] - (g.viewport_height - 2)

    offset = state['mempool']['offset']

    for index in xrange(offset, offset+g.viewport_height-1):
        if index < len(txdata):
            if index == int(state['mempool']['cursor']):
                win_transactions.addstr(index+1-offset, 1, ">", curses.A_REVERSE + curses.A_BOLD)

            condition = (index == offset+g.viewport_height-2) and (index+1 < len(txdata))
            condition = condition or ( (index == offset) and (index > 0) )

            if condition:
                win_transactions.addstr(index+1-offset, 3, "...")
            else:
                win_transactions.addstr(index+1-offset, 3, "{: 6,d}".format(int(index) + 1) + ": " + txdata[index])

    win_transactions.refresh()
