#!/usr/bin/env python
import curses, time, calendar

import global_mod as g
from getstr import UserInput
import footer

def draw_window(state, window, rpc_queue=None):
    window.clear()
    window.refresh()
    win_header = curses.newwin(5, g.x, 0, 0)

    if 'browse_height' in state['blocks']:
        height = str(state['blocks']['browse_height'])
        if height in state['blocks']:
            blockdata = state['blocks'][height]

            win_header.addstr(0, 1, "Height: " + "{:,d}".format(int(height)), curses.A_BOLD)
            g.addstr_rjust(win_header, 0, "(J/K: browse, HOME/END: quicker, L: latest, G: seek)", curses.A_BOLD, 1)
            win_header.addstr(1, 1, "Hash: " + blockdata['hash'], curses.A_BOLD)
            win_header.addstr(2, 1, "Root: " + blockdata['merkleroot'], curses.A_BOLD)
            win_header.addstr(3, 1, str("{:,d}".format(int(blockdata['size']))) + " bytes (" + str(blockdata['size']/1024) + " KB)       ", curses.A_BOLD)
            g.addstr_cjust(win_header, 3, "Diff: " + "{:,d}".format(int(blockdata['difficulty'])), curses.A_BOLD, 0, 4, 2)
            g.addstr_rjust(win_header, 3, time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(blockdata['time'])), curses.A_BOLD, 1)
            version_bits = "{0:032b}".format(int(blockdata['version']))
            version_bits = version_bits[0:7] + " " + version_bits[8:15] + " " + version_bits[16:23] + " " + version_bits[24:]
            win_header.addstr(4, 1, "Version: " + str(blockdata['version']) + " (" + version_bits + ")", curses.A_BOLD)

            draw_transactions(state)
            state['blocks']['loaded'] = 1

        else:
            if rpc_queue.qsize() > 0:
                g.addstr_cjust(win_header, 0, "...waiting for block information being processed...", curses.A_BOLD + curses.color_pair(3))
            else:
                win_header.addstr(0, 1, "no block information loaded.", curses.A_BOLD + curses.color_pair(3))
                win_header.addstr(1, 1, "press 'G' to enter a block hash, height, or timestamp", curses.A_BOLD)

    else:
        if rpc_queue.qsize() > 0:
            g.addstr_cjust(win_header, 0, "...waiting for block information being processed...", curses.A_BOLD + curses.color_pair(3))
        else:
            win_header.addstr(0, 1, "no block information loaded.", curses.A_BOLD + curses.color_pair(3))
            win_header.addstr(1, 1, "press 'G' to enter a block hash, height, or timestamp", curses.A_BOLD)

    win_header.refresh()
    footer.draw_window(state, rpc_queue)

def draw_transactions(state):
    g.viewport_height = state['y'] - 6
    win_transactions = curses.newwin(g.viewport_height, g.x, 5, 0)

    height = str(state['blocks']['browse_height'])
    blockdata = state['blocks'][height]
    tx_count = len(blockdata['tx'])
    bytes_per_tx = blockdata['size'] / tx_count

    win_transactions.addstr(0, 1, "Transactions: " + "{: 4,d}".format(int(tx_count)) + " (" + str(bytes_per_tx) + " bytes/tx)", curses.A_BOLD + curses.color_pair(5))
    g.addstr_rjust(win_transactions, 0, "(UP/DOWN: scroll, ENTER: view)", curses.A_BOLD + curses.color_pair(5), 1)
    # reset cursor if it's been resized off the bottom
    if state['blocks']['cursor'] > state['blocks']['offset'] + (g.viewport_height - 2):
        state['blocks']['offset'] = state['blocks']['cursor'] - (g.viewport_height - 2)

    offset = state['blocks']['offset']

    for index in xrange(offset, offset+g.viewport_height-1):
        if index < len(blockdata['tx']):
            if index == state['blocks']['cursor']:
                win_transactions.addstr(index+1-offset, 1, ">", curses.A_REVERSE + curses.A_BOLD)

            condition = (index == offset+g.viewport_height-2) and (index+1 < len(blockdata['tx']))
            condition = condition or ( (index == offset) and (index > 0) )

            if condition:
                win_transactions.addstr(index+1-offset, 3, "...")
            else:
                win_transactions.addstr(index+1-offset, 3, "{: 5d}".format(int(index) + 1) + ": " + blockdata['tx'][index])

    win_transactions.refresh()

def draw_input_window(state, window, rpc_queue):
    color = curses.color_pair(1)
    if g.testnet:
        color = curses.color_pair(2)

    UI = UserInput(window, "block input mode")
    UI.addline("please enter block height or hash", curses.A_BOLD)
    UI.addline("or timestamp (accepted formats: YYYY-MM-DD hh:mm:ss, YYYY-MM-DD):", curses.A_BOLD)
    entered_block = UI.getstr(64)
    
    entered_block_timestamp = 0

    try:
        entered_block_time = time.strptime(entered_block, "%Y-%m-%d")
        entered_block_timestamp = calendar.timegm(entered_block_time)
    except: pass

    try: 
        entered_block_time = time.strptime(entered_block, "%Y-%m-%d %H:%M:%S")
        entered_block_timestamp = calendar.timegm(entered_block_time)
    except: pass

    if entered_block_timestamp:
        s = {'findblockbytimestamp': entered_block_timestamp} 
        rpc_queue.put(s)

        UI.addmessageline("waiting for block (will stall here if not found)", color + curses.A_BOLD, 0)
        state['mode'] = "block"

    elif len(entered_block) == 64:
        s = {'getblock': entered_block}
        rpc_queue.put(s)

        UI.addmessageline("waiting for block (will stall here if not found)", color + curses.A_BOLD, 0)
        state['mode'] = "block"

    elif (len(entered_block) < 9) and entered_block.isdigit() and (int(entered_block) <= state['mininginfo']['blocks']):
        if entered_block in state['blocks']:
            state['blocks']['browse_height'] = int(entered_block)
            state['mode'] = "block"
            draw_window(state, window)
        else:
            s = {'getblockhash': int(entered_block)}
            rpc_queue.put(s)

            UI.addmessageline("waiting for block (will stall here if not found)", color + curses.A_BOLD, 0)
            state['mode'] = "block"
            state['blocks']['browse_height'] = int(entered_block)

    else:
        UI.addmessageline("This is not a valid hash, height, or timestamp format", color + curses.A_BOLD)
        UI.clear()
        state['mode'] = "monitor"
