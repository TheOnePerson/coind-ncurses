#!/usr/bin/env python
import curses

import global_mod as g

def draw_window(state, rpc_queue = None, only_work_indicator = False):
    win_footer = curses.newwin(1, g.x, g.y - 1, 0)

    color = curses.color_pair(1)
    if 'testnet' in state:
        if state['testnet']:
            color = curses.color_pair(2)

    if not only_work_indicator:
        x = 1
        for mode_string in g.modes:
            modifier = curses.A_BOLD
            if state['mode'] == mode_string:
                modifier += curses.A_REVERSE
            win_footer.addstr(0, x, mode_string[0].upper(), modifier + curses.color_pair(5)) 
            win_footer.addstr(0, x+1, mode_string[1:], modifier)
            x += len(mode_string) + 2

    if rpc_queue is not None:
        if rpc_queue.qsize() > 0:
            working_indicator = 'wrk... (' + str(rpc_queue.qsize()) + ')'
            g.addstr_rjust(win_footer, 0, working_indicator, curses.A_BOLD + curses.color_pair(3), 1)

    win_footer.refresh()
