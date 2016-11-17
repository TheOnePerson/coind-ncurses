#!/usr/bin/env python
import curses, sys, time

import global_mod as g

import monitor
import process
import hotkey
import splash

def check_window_size(interface_queue, state, window, min_y, min_x, max_y, max_x):
    # TODO: use SIGWINCH interrupt
    if (state['y'], state['x']) != window.getmaxyx():
        new_y, new_x = window.getmaxyx()

        if (new_y < min_y) or (new_x < min_x):
            interface_queue.put({ 'stop': "Window is too small - must be at least " + str(min_x) + "x" + str(min_y)})

        if new_y > max_y: new_y = max_y
        if new_x > max_x: new_x = max_x

        if (state['y'], state['x']) != (new_y, new_x): # initialized
            interface_queue.put({'resize': 1})

        state['x'] = new_x
        state['y'] = new_y
        g.x = new_x
        g.y = new_y

def init_curses():
    window = curses.initscr()
    curses.noecho() # prevents user input from being echoed
    curses.cbreak() # is this actually necessary or useful?
    curses.curs_set(0) # make cursor invisible

    curses.start_color()
    curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_CYAN, curses.COLOR_BLACK)
    curses.init_pair(3, curses.COLOR_RED, curses.COLOR_BLACK)
    curses.init_pair(4, curses.COLOR_MAGENTA, curses.COLOR_BLACK)
    curses.init_pair(5, curses.COLOR_YELLOW, curses.COLOR_BLACK)

    window.timeout(50)
    window.keypad(1) # interpret arrow keys, etc

    return window

def init_state():
    state = {
        'mode': "splash",
        'blocks': { 'cursor': 0, 'offset': 0 },
        'networkhashps': {},
        'console': { 'cbuffer': [], 'rbuffer': [], 'offset': 0 },
        'x': -1,
        'y': -1,
        'history': { 'getnettotals': [] }
    }

    return state

def loop(state, window, interface_queue, rpc_queue):
    iterations = 0
    tick = 25
    while 1:
        check_window_size(interface_queue, state, window, 12, 79, 80, 120) # min_y, min_x, max_x, max_y
        error_message = process.queue(state, window, interface_queue, rpc_queue)
        if error_message:
            return error_message # ends if stop command sent by rpc

        if not iterations % tick:
            iterations = 0
            if state['mode'] == "monitor":
                monitor.draw_window(state, window, rpc_queue, False)

        if hotkey.check(state, window, rpc_queue): # poll for user input
            break # returns 1 when quit key is pressed

        iterations += 1

    return False

def main(interface_queue, rpc_queue):
    window = init_curses()
    error_message = False
    try:
        state = init_state()
        splash.draw_window(state, window, rpc_queue)
        error_message = loop(state, window, interface_queue, rpc_queue)
    finally: # restore sane terminal state, end RPC thread
        curses.nocbreak()
        curses.endwin()
        rpc_queue.put({ 'stop': True })
    
        if error_message:
            sys.stderr.write(g.rpc_deamon + "-ncurses encountered an error\n")
            sys.stderr.write("Message: " + error_message + "\n")
