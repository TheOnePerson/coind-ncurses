#/usr/bin/env python
import curses

import global_mod as g
import tx
import block
import mempool
import monitor
import peers
import wallet
import console
import net
import forks
import footer

def change_mode(state, window, mode, rpc_queue=None):
    try:
        g.modes.index(mode)
    except ValueError:
        return False

    state['mode'] = mode

    if mode == 'home':
        monitor.draw_window(state, window, rpc_queue)
    elif mode == 'tx':
        tx.draw_window(state, window, rpc_queue)
    elif mode == 'peers':
        peers.draw_window(state, window, rpc_queue)
    elif mode == 'wallet':
        wallet.draw_window(state, window, rpc_queue)
    elif mode == 'mempool':
        mempool.draw_window(state, window, rpc_queue)
    elif mode == 'block':
        block.draw_window(state, window, rpc_queue)
    elif mode == 'console':
        console.draw_window(state, window, rpc_queue)
    elif mode == 'net':
        net.draw_window(state, window, rpc_queue)
    elif mode == 'forks':
        forks.draw_window(state, window, rpc_queue)
    
def key_left(state, window, rpc_queue):
    try:
        index = g.modes.index(state['mode']) - 1
        if index < 0:
            index = len(g.modes) - 2
        change_mode(state, window, g.modes[index], rpc_queue)
    except:
        pass

def key_right(state, window, rpc_queue):
    try:
        index = g.modes.index(state['mode']) + 1
        if index > len(g.modes) - 2: # last index item is 'quit'
            index = 0
        change_mode(state, window, g.modes[index], rpc_queue)
    except:
        pass

def key_w(state, window, rpc_queue):
    if g.wallet_support:
        rpc_queue.put('listsinceblock')
        rpc_queue.put('getwalletinfo')
        change_mode(state, window, 'wallet', rpc_queue)

def key_a(state, window, rpc_queue):
    if state['mode'] == 'wallet':
        if 'wallet' in state:
            state['wallet']['mode'] = 'addresses'
            rpc_queue.put('getwalletinfo')
            rpc_queue.put('listreceivedbyaddress')
            wallet.draw_window(state, window, rpc_queue)

def key_e(state, window, rpc_queue):
    if state['mode'] == 'wallet':
        if 'wallet' in state:
            state['wallet']['mode'] = 'backupwallet'
            wallet.draw_window(state, window, rpc_queue)

    elif state['mode'] == 'console':
        state['console']['cbuffer'] = []
        state['console']['rbuffer'] = []
        state['console']['offset'] = 0
        console.draw_window(state, window, rpc_queue)

def key_o(state, window, rpc_queue):
    if state['mode'] == 'wallet':
        if 'wallet' in state:
            if state['wallet']['mode'] == 'tx':
                state['wallet']['mode'] = 'exporttx'
                wallet.draw_window(state, window, rpc_queue)

def key_p(state, window, rpc_queue):
    rpc_queue.put('getpeerinfo')
    change_mode(state, window, 'peers', rpc_queue)

def key_m(state, window, rpc_queue):
    rpc_queue.put('getrawmempool')
    change_mode(state, window, 'mempool', rpc_queue)

def key_f(state, window, rpc_queue):
    rpc_queue.put('getchaintips')
    change_mode(state, window, 'forks', rpc_queue)

def key_g(state, window, rpc_queue):
    if state['mode'] == 'tx':
        state['mode'] = "transaction-input"
        tx.draw_input_window(state, window, rpc_queue)
    elif state['mode'] == "block":
        state['mode'] = "block-input"
        block.draw_input_window(state, window, rpc_queue)
    elif state['mode'] == "console":
        console.draw_input_box(state, rpc_queue)

def key_r(state, window, rpc_queue):
    if state['mode'] == 'wallet':
        if 'wallet' in state:
            state['wallet']['mode'] = 'newaddress'
            wallet.draw_window(state, window, rpc_queue)

def key_x(state, window, rpc_queue):
    if state['mode'] == 'wallet':
        if 'wallet' in state:
            state['wallet']['mode'] = 'settxfee'
            wallet.draw_window(state, window, rpc_queue)

def key_s(state, window, rpc_queue):
    if state['mode'] == 'wallet':
        if 'wallet' in state:
            state['wallet']['mode'] = 'sendtoaddress'
            state['newtransaction'] = {}
            wallet.draw_window(state, window, rpc_queue)

def go_to_latest_block(state, window, rpc_queue):
    if state['mode'] == "block":
        if 'mininginfo' in state:
            if state['mininginfo']['blocks'] not in state['blocks']:
                s = {'getblockhash': state['mininginfo']['blocks']}
                rpc_queue.put(s)
                footer.draw_window(state, rpc_queue)
            else:
                state['blocks']['browse_height'] = state['mininginfo']['blocks']
                block.draw_window(state, window, rpc_queue)

def scroll_down(state, window, rpc_queue):
    if state['mode'] == 'tx':
        if 'tx' in state:
            window_height = (state['y'] - 4) / 2
            if state['tx']['cursor'] < (len(state['tx']['vin']) - 1) and state['tx']['mode'] == 'inputs':
                state['tx']['cursor'] += 1

                if (state['tx']['cursor'] - state['tx']['offset']) > window_height-2:
                    state['tx']['offset'] += 1
                tx.draw_inputs(state)

            elif state['tx']['out_offset'] < (len(state['tx']['vout_string']) - (window_height-1)) and state['tx']['mode'] == 'outputs':
                state['tx']['out_offset'] += 1
                tx.draw_outputs(state)

    elif state['mode'] == "mempool":
        if 'mempool' in state:
            if 'transactions' in state['mempool']:
                txdata = state['mempool']['transactions']
                if state['mempool']['cursor'] < (len(txdata) - 1):
                    state['mempool']['cursor'] += 1
                    window_height = g.viewport_height
                    if (state['mempool']['cursor'] - state['mempool']['offset']) > window_height - 2:
                        state['mempool']['offset'] += 1
                    mempool.draw_transactions(state)

    elif state['mode'] == "block":
        if 'blocks' in state:
            height = str(state['blocks']['browse_height'])
            if height in state['blocks']:
                blockdata = state['blocks'][height]
                if state['blocks']['cursor'] < (len(blockdata['tx']) - 1):
                    state['blocks']['cursor'] += 1
                    window_height = g.viewport_height
                    if (state['blocks']['cursor'] - state['blocks']['offset']) > window_height - 2:
                        state['blocks']['offset'] += 1
                    block.draw_transactions(state)

    elif state['mode'] == "peers":
        if 'peerinfo' in state and 'peerinfo_offset' in state:
            window_height = state['y'] - 4
            if state['peerinfo_offset'] < (len(state['peerinfo']) - window_height):
                state['peerinfo_offset'] += 1
                peers.draw_peers(state)

    elif state['mode'] == "forks":
        if 'chaintips' in state and 'chaintips_offset' in state:
            window_height = state['y'] - 5
            if state['chaintips_offset'] < (len(state['chaintips']) - window_height):
                state['chaintips_offset'] += 1
                forks.draw_tips(state)

    elif state['mode'] == "wallet":
        if 'wallet' in state:
            window_height = g.viewport_heigth
            if state['wallet']['mode'] == 'tx':
                if 'transactions' in state['wallet']:
                    if state['wallet']['cursor'] < (len(state['wallet']['transactions']) - 1):
                        state['wallet']['cursor'] += 1
                        lines = 5 if state['wallet']['verbose'] > 0 else 4
                        if (state['wallet']['cursor'] * lines) - state['wallet']['offset'] >= window_height - 1:
                            state['wallet']['offset'] += lines  #(state['wallet']['cursor'] * lines) - 1
                        # make sure that the last tx is fully visible
                        if state['wallet']['cursor'] == len(state['wallet']['transactions']) - 1:
                            if state['wallet']['offset'] + window_height - 1 <= len(state['wallet']['transactions']) * lines:
                                state['wallet']['offset'] += (len(state['wallet']['transactions']) * lines) - (state['wallet']['offset'] + window_height - 1)

                        wallet.draw_transactions(state)
            elif state['wallet']['mode'] == 'addresses':
                if 'addresses' in state['wallet']:
                    if len(state['wallet']['addresses']) * 4 - state['wallet']['offset'] > window_height - 1:
                        state['wallet']['offset'] += 1
                        wallet.draw_addresses(state)

    elif state['mode'] == "console":
        if state['console']['offset'] > 0:
            state['console']['offset'] -= 1
            console.draw_buffer(state)

def scroll_up(state, window, rpc_queue):
    if state['mode'] == 'tx':
        if 'tx' in state:
            if state['tx']['cursor'] > 0 and state['tx']['mode'] == 'inputs':
                if (state['tx']['cursor'] - state['tx']['offset']) == 0:
                    state['tx']['offset'] -= 1
                state['tx']['cursor'] -= 1
                tx.draw_inputs(state)

            if state['tx']['out_offset'] > 0 and state['tx']['mode'] == 'outputs':
                state['tx']['out_offset'] -= 1
                tx.draw_outputs(state)

    elif state['mode'] == "mempool":
        if 'mempool' in state:
            if state['mempool']['cursor'] > 0:
                if (state['mempool']['cursor'] - state['mempool']['offset']) == 0:
                    state['mempool']['offset'] -= 1
                state['mempool']['cursor'] -= 1
                mempool.draw_transactions(state)

    elif state['mode'] == "block":
        if 'blocks' in state:
            if state['blocks']['cursor'] > 0:
                if (state['blocks']['cursor'] - state['blocks']['offset']) == 0:
                    state['blocks']['offset'] -= 1
                state['blocks']['cursor'] -= 1
                block.draw_transactions(state)

    elif state['mode'] == "peers":
        if 'peerinfo' in state and 'peerinfo_offset' in state:
            if state['peerinfo_offset'] > 0:
                state['peerinfo_offset'] -= 1
                peers.draw_peers(state)

    elif state['mode'] == "forks":
        if 'chaintips' in state and 'chaintips_offset' in state:
            if state['chaintips_offset'] > 0:
                state['chaintips_offset'] -= 1
                forks.draw_tips(state)

    elif state['mode'] == "wallet":
        if 'wallet' in state:
            if state['wallet']['mode'] == 'tx':
                if state['wallet']['cursor'] > 0:
                    state['wallet']['cursor'] -= 1
                    lines = 5 if state['wallet']['verbose'] > 0 else 4
                    if ((state['wallet']['cursor'] * lines - 1) < state['wallet']['offset']):
                        state['wallet']['offset'] = state['wallet']['cursor'] * lines - 1
                    wallet.draw_transactions(state)
            elif state['wallet']['mode'] == 'addresses':
                if state['wallet']['offset'] > 0:
                    state['wallet']['offset'] -= 1
                    wallet.draw_addresses(state)

    elif state['mode'] == "console":
        state['console']['offset'] += 1
        console.draw_buffer(state)

def scroll_up_page(state, window, rpc_queue):
    if state['mode'] == "console":
        window_height = state['y'] - 3 - 2
        state['console']['offset'] += window_height
        console.draw_buffer(state)

    elif state['mode'] == "block":
        if 'blocks' in state:
            window_height = state['y'] - 7
            if state['blocks']['cursor'] >= window_height - 2:
                if state['blocks']['offset'] >= window_height - 2:
                    state['blocks']['offset'] -= window_height - 2
                else:
                    state['blocks']['offset'] = 0
                state['blocks']['cursor'] -= window_height - 2
            else:
                state['blocks']['cursor'] = 0
                state['blocks']['offset'] = 0
            block.draw_transactions(state)

    elif state['mode'] == "mempool":
        if 'mempool' in state:
            window_height = state['y'] - 2
            if state['mempool']['cursor'] >= window_height - 2:
                if state['mempool']['offset'] >= window_height - 2:
                    state['mempool']['offset'] -= window_height - 2
                else:
                    state['mempool']['offset'] = 0
                state['mempool']['cursor'] -= window_height - 2
            else:
                state['mempool']['cursor'] = 0
                state['mempool']['offset'] = 0
            mempool.draw_transactions(state)

def scroll_down_page(state, window, rpc_queue):
    if state['mode'] == "console":
        window_height = state['y'] - 3 - 2
        if state['console']['offset'] > window_height:
            state['console']['offset'] -= window_height
        else:
            state['console']['offset'] = 0
        console.draw_buffer(state)

    elif state['mode'] == "block":
        if 'blocks' in state:
            height = str(state['blocks']['browse_height'])
            if height in state['blocks']:
                blockdata = state['blocks'][height]
                window_height = g.viewport_height
                if state['blocks']['cursor'] < (len(blockdata['tx']) - window_height - 3):
                    state['blocks']['cursor'] += window_height - 3
                else:
                    state['blocks']['cursor'] = len(blockdata['tx']) - 1
                if (state['blocks']['offset'] < (len(blockdata['tx']) - window_height - 3)):
                    state['blocks']['offset'] += window_height - 3
                block.draw_transactions(state)

    elif state['mode'] == "mempool":
        if 'mempool' in state:
            if 'transactions' in state['mempool']:
                txdata = state['mempool']['transactions']
                window_height = g.viewport_height
                if state['mempool']['cursor'] < (len(txdata) - window_height - 3):
                    state['mempool']['cursor'] += window_height - 3
                else:
                    state['mempool']['cursor'] = len(txdata) - 1
                if (state['mempool']['offset'] < (len(txdata) - window_height - 3)):
                    state['mempool']['offset'] += window_height - 3
                mempool.draw_transactions(state)

def toggle_submode(state, window, rpc_queue):
    if state['mode'] == 'tx':
        if 'tx' in state:
            if 'mode' in state['tx']:
                if state['tx']['mode'] == 'inputs':
                    state['tx']['mode'] = 'outputs'
                else:
                    state['tx']['mode'] = 'inputs'
                tx.draw_window(state, window, rpc_queue)

def load_transaction(state, window, rpc_queue):
    # TODO: some sort of indicator that a transaction is loading
    if state['mode'] == 'tx':
        if 'tx' in state:
            if 'txid' in state['tx']['vin'][ state['tx']['cursor'] ]:
                if state['tx']['loaded']:
                    state['tx']['loaded'] = 0
                    s = {'txid': state['tx']['vin'][ state['tx']['cursor'] ]['txid']}
                    rpc_queue.put(s)
                    footer.draw_window(state, rpc_queue)

    elif state['mode'] == "mempool":
        if 'mempool' in state:
            if 'transactions' in state['mempool']:
                s = {'txid': state['mempool']['transactions'][ int(state['mempool']['cursor']) ]}
                rpc_queue.put(s)
                state['mode'] = 'tx'
                change_mode(state, window, state['mode'], rpc_queue)

    elif state['mode'] == "block":
        if 'blocks' in state:
            if state['blocks']['browse_height'] > 0: # block 0 is not indexed
                height = str(state['blocks']['browse_height'])
                if height in state['blocks']:
                    blockdata = state['blocks'][height]
                    s = {'txid': blockdata['tx'][ state['blocks']['cursor'] ]}
                    rpc_queue.put(s)
                    state['mode'] = 'tx'
                    change_mode(state, window, state['mode'], rpc_queue)

    elif state['mode'] == "wallet":
        if 'wallet' in state:
            if 'transactions' in state['wallet']:
                s = {'txid': state['wallet']['transactions'][ state['wallet']['cursor'] ]['txid']}
                rpc_queue.put(s)
                state['mode'] = 'tx'
                change_mode(state, window, state['mode'], rpc_queue)

def toggle_verbose_mode(state, window, rpc_queue):
    if state['mode'] == 'tx':
        if 'tx' in state:
            if 'txid' in state['tx']:
                if state['tx']['loaded']:
                    state['tx']['loaded'] = 0

                    if 'total_inputs' not in state['tx']:
                        s = {'txid': state['tx']['txid'], 'verbose': 1, 'notrack':1}
                    else:
                        s = {'txid': state['tx']['txid'], 'notrack':1}

                    rpc_queue.put(s)
                    footer.draw_window(state, rpc_queue)

    elif state['mode'] == "wallet":
        if 'wallet' in state:
            if 'transactions' in state['wallet']:
                rpc_queue.put('wallet_toggle_tx')
                footer.draw_window(state, rpc_queue)

def block_seek_back_one(state, window, rpc_queue):
    if state['mode'] == "block":
        if 'blocks' in state:
            if (state['blocks']['browse_height']) > 0:
                if state['blocks']['loaded'] == 1:
                    state['blocks']['loaded'] = 0
                    state['blocks']['browse_height'] -= 1
                    state['blocks']['cursor'] = 0
                    state['blocks']['offset'] = 0
                    if str(state['blocks']['browse_height']) in state['blocks']:
                        block.draw_window(state, window, rpc_queue)
                    else:
                        s = {'getblockhash': state['blocks']['browse_height']}
                        rpc_queue.put(s)
                        footer.draw_window(state, rpc_queue)

    elif state['mode'] == "tx":
        if 'txid_history' in state:
            if len(state['txid_history']) > 1:
                s = {'txid': state['txid_history'][len(state['txid_history']) - 2]}
                del state['txid_history'][len(state['txid_history']) - 1]
                del state['txid_history'][len(state['txid_history']) - 1]
                rpc_queue.put(s)
                footer.draw_window(state, rpc_queue)
                state['mode'] = 'tx'

def block_seek_forward_one(state, window, rpc_queue):
    if state['mode'] == "block":
        if 'blocks' in state:
            if state['blocks']['browse_height'] < state['mininginfo']['blocks']:
                if state['blocks']['loaded'] == 1:
                    state['blocks']['loaded'] = 0
                    state['blocks']['browse_height'] += 1
                    state['blocks']['cursor'] = 0
                    state['blocks']['offset'] = 0
                    if str(state['blocks']['browse_height']) in state['blocks']:
                        block.draw_window(state, window, rpc_queue)
                    else:
                        s = {'getblockhash': state['blocks']['browse_height']}
                        rpc_queue.put(s)
                        footer.draw_window(state, rpc_queue)

def block_seek_back_thousand(state, window, rpc_queue):
    if state['mode'] == "block":
        if 'blocks' in state:
            if (state['blocks']['browse_height']) > 999:
                if state['blocks']['loaded'] == 1:
                    state['blocks']['loaded'] = 0
                    state['blocks']['browse_height'] -= 1000
                    state['blocks']['cursor'] = 0
                    state['blocks']['offset'] = 0
                    if str(state['blocks']['browse_height']) in state['blocks']:
                        block.draw_window(state, window, rpc_queue)
                    else:
                        s = {'getblockhash': state['blocks']['browse_height']}
                        rpc_queue.put(s)
                        footer.draw_window(state, rpc_queue)

def block_seek_forward_thousand(state, window, rpc_queue):
    if state['mode'] == "block":
        if 'blocks' in state:
            if (state['blocks']['browse_height']) < state['mininginfo']['blocks'] - 999:
                if state['blocks']['loaded'] == 1:
                    state['blocks']['loaded'] = 0
                    state['blocks']['browse_height'] += 1000
                    state['blocks']['cursor'] = 0
                    state['blocks']['offset'] = 0
                    if str(state['blocks']['browse_height']) in state['blocks']:
                        block.draw_window(state, window, rpc_queue)
                    else:
                        s = {'getblockhash': state['blocks']['browse_height']}
                        rpc_queue.put(s)
                        footer.draw_window(state, rpc_queue)

keymap = {
    curses.KEY_LEFT: key_left,
    curses.KEY_RIGHT: key_right,
    curses.KEY_DOWN: scroll_down,
    curses.KEY_UP: scroll_up,
    curses.KEY_PPAGE: scroll_up_page,
    curses.KEY_NPAGE: scroll_down_page,
    curses.KEY_HOME: block_seek_back_thousand,
    curses.KEY_END: block_seek_forward_thousand,

    curses.KEY_ENTER: load_transaction,
    ord('\n'): load_transaction,

    ord('w'): key_w,
    ord('W'): key_w,

    ord('a'): key_a,
    ord('A'): key_a,

    ord('e'): key_e,
    ord('E'): key_e,

    ord('x'): key_x,
    ord('X'): key_x,

    ord('o'): key_o,
    ord('O'): key_o,

    ord('m'): key_m,
    ord('M'): key_m,

    ord('p'): key_p,
    ord('P'): key_p,

    ord('r'): key_r,
    ord('R'): key_r,

    ord('s'): key_s,
    ord('S'): key_s,

    ord('g'): key_g,
    ord('G'): key_g,

    ord('f'): key_f,
    ord('F'): key_f,

    ord('l'): go_to_latest_block,
    ord('L'): go_to_latest_block,

    ord('\t'): toggle_submode,
    9: toggle_submode,

    ord("v"): toggle_verbose_mode,
    ord("V"): toggle_verbose_mode,

    ord('j'): block_seek_back_one,
    ord('J'): block_seek_back_one,

    ord('k'): block_seek_forward_one,
    ord('K'): block_seek_forward_one
}

modemap = {
    ord('h'): 'home',
    ord('H'): 'home',

    ord('b'): 'block',
    ord('B'): 'block',

    ord('t'): 'tx',
    ord('T'): 'tx',

    ord('c'): 'console',
    ord('C'): 'console',

    ord('n'): 'net',
    ord('N'): 'net'
}

def check(state, window, rpc_queue):
    key = window.getch()

    if key < 0 or state['mode'] == 'splash':
        pass

    elif key in keymap:
        keymap[key](state, window, rpc_queue)

    elif key in modemap:
        change_mode(state, window, modemap[key], rpc_queue)

    elif key == ord('q') or key == ord('Q'): # quit
        return True

    return False
