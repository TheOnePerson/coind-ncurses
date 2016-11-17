#!/usr/bin/env python
import curses
import global_mod as g

def get_splash_array():
    if g.coinmode == 'BTC':
        global splash_array
        splash_array = [
            "  BB            BB                                   BB",
            "  BB       BB   BB    BBBB   BBBBB   BB  BB BB       BB",
            "  BBBBBB       BBBB  BB     BB   BB      BBB BB   BBBBB",
            "  BB   BB  BB   BB   BB     BB   BB  BB  BB  BB  BB  BB",
            "  BBB  BB  BB   BB   BB     BB   BB  BB  BB  BB  BB  BB",
            "  BB BBB   BB    BB   BBBB   BBBBB   BB  BB  BB   BBBBB",
        ]
    elif g.coinmode == 'LTC':
        splash_array = [
            "  BB       BB                                            BB",
            "  BB  BB   BB    BBBB    BBBB   BBBBB   BB  BB BBB       BB",
            "  BB      BBBB  BB  BB  BB     BB   BB      BBB  BB   BBBBB",
            "  BB  BB   BB   BBBBB   BB     BB   BB  BB  BB   BB  BB  BB",
            "  BB  BB   BB   BB      BB     BB   BB  BB  BB   BB  BB  BB",
            "  BB  BB    BB   BBBB    BBBB   BBBBB   BB  BB   BB   BBBBB",
        ]
    else:
        splash_array = [
            "                                               BB",
            "               BBBB   BBBBB   BB  BB BBB       BB",
            "              BB     BB   BB      BBB  BB   BBBBB",
            "              BB     BB   BB  BB  BB   BB  BB  BB",
            "              BB     BB   BB  BB  BB   BB  BB  BB",
            "  BB  BB  BB   BBBB   BBBBB   BB  BB   BB   BBBBB",
        ]

def draw_window(state, window, rpc_queue):
    window.clear()
    window.refresh()
    win_splash = curses.newwin(12, 76, 0, 0)

    color = curses.color_pair(0)
    if 'testnet' in state:
        if state['testnet']: color = curses.color_pair(2)
        else: color = curses.color_pair(1)

    get_splash_array()
    y = 0
    while y < len(splash_array):
        x = 0
        while x < len(splash_array[y]):
            if splash_array[y][x] != " ":
                win_splash.addstr(y+1, x, " ", color + curses.A_REVERSE)
            x += 1
        y += 1

    output_string =  "                                    n     c     u     r     s     e     s "

    win_splash.addstr(8, 0, output_string, color + curses.A_BOLD)

    version = "[ " + g.version + " ]"
    output_string = version.rjust(74)

    win_splash.addstr(10, 0, output_string, curses.color_pair(3) + curses.A_BOLD)
    win_splash.refresh()
    
    '''
    screen = curses.initscr()
    y, x = screen.getmaxyx()
    win_footer = curses.newwin(1, 76, y-1, 0)
    if rpc_queue is not None:
        if rpc_queue.qsize() > 0:
            working_indicator = 'working... (' + str(rpc_queue.qsize()) + ' commands in rpc queue)'
            win_footer.addstr(0, 76 - 1 - len(working_indicator), working_indicator, curses.A_BOLD + curses.color_pair(3))

    win_footer.refresh()
    '''
