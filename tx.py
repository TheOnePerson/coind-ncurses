#!/usr/bin/env python
import curses, binascii, time

import global_mod as g
from getstr import UserInput
import footer

def draw_window(state, window, rpc_queue):
    # TODO: add transaction locktime, add sequence to inputs
    window.clear()
    window.refresh()
    win_header = curses.newwin(3, g.x, 0, 0)

    unit = g.coin_unit
    if g.testnet:
        unit = g.coin_unit_test
    if 'tx' in state:
        win_header.addstr(0, 1, "txid: " + state['tx']['txid'], curses.A_BOLD)
        win_header.addstr(1, 1, str(state['tx']['size']) + " bytes (" + "{:.2f}".format(float(state['tx']['size'])/1024.0) + " KB)       ", curses.A_BOLD)

        if 'total_outputs' in state['tx']:
            output_string = "%.8f" % state['tx']['total_outputs'] + " " + unit
            if 'total_inputs' in state['tx']:
                if state['tx']['total_inputs'] == 'coinbase':
                    fee = float(0)
                    output_string += " (coinbase)"
                else: # Verbose mode only
                    try:
                        if float(state['tx']['total_inputs']) == 0:
                            fee = float(0)
                        else:			    
                            fee = float(state['tx']['total_inputs']) - float(state['tx']['total_outputs'])
                    except:
                        fee = float(state['tx']['total_inputs']) - float(state['tx']['total_outputs'])
                    output_string += " + " + "%.8f" % fee + " " + unit + " fee"
            else:
                output_string += " + unknown fee"
            win_header.addstr(1, 26, output_string.rjust(45), curses.A_BOLD)

        if 'time' in state['tx']:
            output_string = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(state['tx']['time']))
        else:
            output_string = ""
        if 'confirmations' in state['tx']:
            output_string += ("" if not len(output_string) else " / ") + "{:,d}".format(int(state['tx']['confirmations'])) + " conf"
        else:
            output_string += ("" if not len(output_string) else " / ") + "unconfirmed"
        win_header.addstr(2, 1, output_string[:g.x - 2], curses.A_BOLD)

        history_height = 0 if not 'txid_history' in state else len(state['txid_history']) - 1
        if history_height <= 0:
            history_msg = ""
        else: 
            if g.x > 79:
                history_msg = ", J: browse back"
            else: history_msg = ", J: go back"
        g.addstr_rjust(win_header, 2, "(V: verbose, G: enter txid" + history_msg + ")", curses.A_BOLD, 1)

        draw_inputs(state)
        draw_outputs(state)

    else:
        if rpc_queue.qsize() > 0:
            g.addstr_cjust(win_header, 0, "...waiting for transaction information being processed...", curses.A_BOLD + curses.color_pair(3))
        else:
            win_header.addstr(0, 1, "no transaction loaded or no transaction information found", curses.A_BOLD + curses.color_pair(3))
            win_header.addstr(1, 1, "if you have entered one, consider running " + g.rpc_deamon + " with -txindex", curses.A_BOLD)
            win_header.addstr(2, 1, "press 'G' to enter a txid", curses.A_BOLD)

    win_header.refresh()
    footer.draw_window(state, rpc_queue)

def draw_inputs(state):
    window_height = (state['y'] - 4) / 2
    window_width = state['x']
    win_inputs = curses.newwin(window_height, window_width, 3, 0)
    if state['tx']['mode'] == 'inputs':
        win_inputs.addstr(0, 1, "inputs:", curses.A_BOLD + curses.color_pair(3))
        g.addstr_rjust(win_inputs, 0, "(UP/DOWN: select, ENTER: view)", curses.A_BOLD + curses.color_pair(3), 1)
    else:
        win_inputs.addstr(0, 1, "inputs:", curses.A_BOLD + curses.color_pair(5))
        g.addstr_rjust(win_inputs, 0, "(TAB: switch to)", curses.A_BOLD + curses.color_pair(5), 1)

    # reset cursor if it's been resized off the bottom
    if state['tx']['cursor'] > state['tx']['offset'] + (window_height-2):
        state['tx']['offset'] = state['tx']['cursor'] - (window_height-2)

    offset = state['tx']['offset']

    for index in xrange(offset, offset+window_height-1):
        if index < len(state['tx']['vin']):
            if 'txid' in state['tx']['vin'][index]:

                buffer_string = state['tx']['vin'][index]['txid'] + ":" + "%03d" % state['tx']['vin'][index]['vout']
                if 'prev_tx' in state['tx']['vin'][index]:
                    vout = state['tx']['vin'][index]['prev_tx']

                    if 'value' in vout:
                        if vout['scriptPubKey']['type'] == "pubkeyhash":
                            buffer_string = "% 14.8f" % vout['value'] + ": " + vout['scriptPubKey']['addresses'][0].ljust(34)
                        else:
                            if len(vout['scriptPubKey']['asm']) > window_width-37:
                                buffer_string = "% 14.8f" % vout['value'] + ": ..." + vout['scriptPubKey']['asm'][-(window_width-40):]
                            else:
                                buffer_string = "% 14.8f" % vout['value'] + ": " + vout['scriptPubKey']['asm']

                        length = len(buffer_string)
                        if length + 72 < window_width:
                            buffer_string += " " + state['tx']['vin'][index]['txid'] + ":" + "%03d" % state['tx']['vin'][index]['vout']
                        else:
                            buffer_string += " " + state['tx']['vin'][index]['txid'][:(window_width-length-14)] + "[...]:" + "%03d" % state['tx']['vin'][index]['vout']

                if index == (state['tx']['cursor']):
                    win_inputs.addstr(index+1-offset, 1, ">", curses.A_REVERSE + curses.A_BOLD)

                condition = (index == offset+window_height-2) and (index+1 < len(state['tx']['vin']))
                condition = condition or ( (index == offset) and (index > 0) )
                if condition:
                    win_inputs.addstr(index+1-offset, 3, "...")
                else:
                    win_inputs.addstr(index+1-offset, 3, buffer_string)

            elif 'coinbase' in state['tx']['vin'][index]:
                coinbase = "[coinbase] " + state['tx']['vin'][index]['coinbase']
                coinbase_string = " [strings] " +  binascii.unhexlify(state['tx']['vin'][index]['coinbase'])

                # strip non-ASCII characters
                coinbase_string = ''.join([x for x in coinbase_string if 31 < ord(x) < 127])

                if len(coinbase) > window_width-1:
                    win_inputs.addstr(index+1-offset, 1, coinbase[:window_width-5] + " ...")
                else:
                    win_inputs.addstr(index+1-offset, 1, coinbase[:window_width-1])

                if len(coinbase_string) > window_width-1:
                    win_inputs.addstr(index+2-offset, 1, coinbase_string[:window_width-5] + " ...")
                else:
                    win_inputs.addstr(index+2-offset, 1, coinbase_string[:window_width-1])

    win_inputs.refresh()

def draw_outputs(state):
    window_height = (g.y - 4) / 2
    win_outputs = curses.newwin(window_height, g.x, 3 + window_height, 0)
    if state['tx']['mode'] == 'outputs':
        win_outputs.addstr(0, 1, "outputs:", curses.A_BOLD + curses.color_pair(3))
        g.addstr_rjust(win_outputs, 0, "(UP/DOWN: scroll)", curses.A_BOLD + curses.color_pair(3), 1)
    else:
        win_outputs.addstr(0, 1, "outputs:", curses.A_BOLD + curses.color_pair(5))
        g.addstr_rjust(win_outputs, 0, "(TAB: switch to)", curses.A_BOLD + curses.color_pair(5), 1)

    offset = state['tx']['out_offset']

    for index in xrange(offset, offset+window_height-1):
        if index < len(state['tx']['vout_string']):
            condition = (index == offset+window_height-2) and (index+1 < len(state['tx']['vout_string']))
            condition = condition or ( (index == offset) and (index > 0) )
            if condition:
                win_outputs.addstr(index+1-offset, 1, "... ")
            else:
                string = state['tx']['vout_string'][index]
                if '[UNSPENT]' in string:
                    color = curses.color_pair(1)
                elif '[SPENT]' in string or '[UNCONFIRMED SPEND]' in string:
                    color = curses.color_pair(3)
                else:
                    color = 0
                win_outputs.addstr(index+1-offset, 1, string, color)
    win_outputs.refresh()

def draw_input_window(state, window, rpc_queue):
    color = curses.color_pair(1)
    if g.testnet:
        color = curses.color_pair(2)

    UI = UserInput(window, "transaction input mode")
    UI.addline("please enter txid:", curses.A_BOLD)
    entered_txid = UI.getstr(64)
    
    if len(entered_txid) == 64: # TODO: better checking for valid txid here
        s = {'txid': entered_txid}
        rpc_queue.put(s)
        UI.addmessageline("waiting for transaction (will stall here if not found)", color + curses.A_BOLD, 0)
        state['mode'] = 'tx'

    else:
        UI.addmessageline("This is no valid txid. Aborting.", color + curses.A_BOLD)
        UI.clear()
        state['mode'] = "monitor"
