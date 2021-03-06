#!/usr/bin/env python
import curses, time

import global_mod as g
import footer

def draw_window(state, window, rpc_queue=None):
    window.clear()
    window.refresh()

    win_header = curses.newwin(4, g.x, 0, 0)

    if 'chaintips' in state:
        win_header.addstr(0, 1, "chain tips: " + str(len(state['chaintips'])), curses.A_BOLD)
        g.addstr_rjust(win_header, 0, "(UP/DOWN: scroll, F: refresh)", curses.A_BOLD)
        win_header.addstr(1, 1, "key: Active/Invalid/HeadersOnly/ValidFork/ValidHeaders", curses.A_BOLD)
        win_header.addstr(3, 1, "height, length, status, 0-prefix hash", curses.A_BOLD + curses.color_pair(5))
        draw_tips(state)

    else:
        if rpc_queue.qsize() > 0:
            g.addstr_cjust(win_header, 0, "...waiting for chain tip information being processed...", curses.A_BOLD + curses.color_pair(3))
        else:
            win_header.addstr(0, 1, "no chain tip information loaded.", curses.A_BOLD + curses.color_pair(3))
            win_header.addstr(1, 1, "press 'F' to refresh", curses.A_BOLD)
            if g.coin_unit == 'BTC':
                win_header.addstr(2, 1, "(note that bitcoind 0.9.3 and older do not support this feature)", curses.A_BOLD)

    win_header.refresh()
    footer.draw_window(state, rpc_queue)

def draw_tips(state):
    window_height = state['y'] - 5
    win_tips = curses.newwin(window_height, state['x'] if state['x'] > 73 else 73, 4, 0)
    
    offset = state['chaintips_offset']

    for index in xrange(offset, offset + window_height):
        if index < len(state['chaintips']):
            tip = state['chaintips'][index]

            condition = (index == offset + window_height - 1) and (index + 1 < len(state['chaintips']))
            condition = condition or ( (index == offset) and (index > 0) )

            if condition:
                # scrolling up or down is possible
                win_tips.addstr(index-offset, 3, "...")

            else:
                style = 0
                if 'status' in tip:
                    if tip['status'] == 'invalid': string = 'I'
                    elif tip['status'] == 'headers-only': string = 'HO'
                    elif tip['status'] == 'valid-headers': string = 'VH'
                    elif tip['status'] == 'valid-fork': string = 'VF'
                    elif tip['status'] == 'active': string = 'A'
                    else: string = '?'
                    if string == 'A': style = curses.A_BOLD + curses.color_pair(1)
                    win_tips.addstr(index-offset, 15, string, style)
                    
                if 'height' in tip:
                    win_tips.addstr(index-offset, 1, str(tip['height']), style)
                if 'branchlen' in tip:
                    win_tips.addstr(index-offset, 9, str(tip['branchlen']), style)
                if 'hash' in tip:
                    i = 0
                    while i < len(tip['hash']): # off by one but doesn't really matter
                        if tip['hash'][i] == '0': i += 1
                        else: break
                    if i > 5:
                        win_tips.addstr(index-offset, 18, str(i) + ' ...' + tip['hash'][i:], style)
                    else:
                        win_tips.addstr(index-offset, 18, tip['hash'], style)

    win_tips.refresh()
