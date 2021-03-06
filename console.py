#!/usr/bin/env python
import curses, pprint

import global_mod as g
import getstr
import footer

def draw_window(state, window, rpc_queue):
    window.clear()
    window.refresh()
    win_header = curses.newwin(1, g.x, 0, 0)

    g.addstr_rjust(win_header, 0, "(G: enter command, E: erase output)", curses.A_BOLD + curses.color_pair(5), 1)
    win_header.refresh()

    if len(state['console']['rbuffer']):
        draw_buffer(state)

    footer.draw_window(state, rpc_queue)

def draw_buffer(state):
    window_height = g.y - 3
    win_buffer = curses.newwin(window_height, g.x, 1, 0)

    #TODO: reimplement and print JSON dicts in a more readable format
    lines = []
    for index in xrange(0,len(state['console']['rbuffer'])):
        command = state['console']['cbuffer'][index]
        lines.append(">> " + command)

        # rbuffer should always exist if cbuffer does
        item = state['console']['rbuffer'][index]
        # str.replace accounts for 'help' sending literal \n
        lines.extend( pprint.pformat(item,width=(state['x']-2)).replace('\\n','\n').splitlines() )

    numlines = len(lines)

    offset = state['console']['offset']
    if offset + 1 >= numlines and numlines > 0:
        offset = numlines - 2
        state['console']['offset'] = offset

    for index in xrange(offset, offset + window_height):
        if index < numlines:
            if index == offset+window_height-1:
                win_buffer.addstr(window_height-(index-offset)-1, 1, "...")
            if index == offset and index:
                win_buffer.addstr(window_height-(index-offset)-1, 1, "...")
            else:
                line = lines[(numlines-1)-index]

                fmt = False
                if len(line) > 1:
                    if line[1] == ">":
                        if state['testnet']:
                            fmt = curses.color_pair(2) + curses.A_BOLD
                        else:
                            fmt = curses.color_pair(1) + curses.A_BOLD

                if len(line) > state['x'] - 1:
                    win_buffer.addstr(window_height-(index-offset)-1, 1, line[:(state['x']-5)] + '...', fmt)
                else:
                    win_buffer.addstr(window_height-(index-offset)-1, 1, line, fmt)
        elif index == offset and index: 
            win_buffer.addstr(window_height-(index-offset)-1, 1, "...")
 
    win_buffer.refresh()

def draw_input_box(state, rpc_queue):
    entered_command = getstr.getstr(state['x'], state['y']-2, 1, '', state['console']['cbuffer'][0::1]).strip() # w, y, x

    if entered_command == "":
        pass
    else:
        s = {'consolecommand': entered_command}
        rpc_queue.put(s)
        footer.draw_window(state, rpc_queue)
        
