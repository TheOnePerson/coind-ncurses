#!/usr/bin/env python
import Queue, textwrap, time
from unidecode import unidecode

import global_mod as g
import tx
import block
import monitor
import peers
import wallet
import splash
import console
import net
import forks

def resize(s, state, window, rpc_queue):
    if state['mode'] == 'tx':
        tx.draw_window(state, window, rpc_queue)
    elif state['mode'] == 'block':
        block.draw_window(state, window, rpc_queue)
    elif state['mode'] == 'peers':
        peers.draw_window(state, window, rpc_queue)
    elif state['mode'] == 'wallet':
        wallet.draw_window(state, window, rpc_queue)
    elif state['mode'] == 'monitor':
        monitor.draw_window(state, window, rpc_queue)
    elif state['mode'] == 'console':
        console.draw_window(state, window, rpc_queue)
    elif state['mode'] == 'net':
        net.draw_window(state, window, rpc_queue)
    elif state['mode'] == 'forks':
        forks.draw_window(state, window, rpc_queue)

def getinfo(s, state, window, rpc_queue):
    state['version'] = str(s['getinfo']['version'] / 1000000)
    state['version'] += '.' + str((s['getinfo']['version'] % 1000000) / 10000)
    state['version'] += '.' + str((s['getinfo']['version'] % 10000) / 100)
    state['version'] += '.' + str((s['getinfo']['version'] % 100))
    if s['getinfo']['testnet'] == True:
        state['testnet'] = 1
    else:
        state['testnet'] = 0

    if state['mode'] == "splash":
        splash.draw_window(state, window, rpc_queue)

def getconnectioncount(s, state, window):
    state['peers'] = s['getconnectioncount']

def getbalance(s, state, window):
    state['balance'] = s['getbalance']

def getunconfirmedbalance(s, state, window):
    state['unconfirmedbalance'] = s['getunconfirmedbalance']

def getblock(s, state, window, rpc_queue=None):
    height = s['getblock']['height']

    state['blocks'][str(height)] = s['getblock']

    if state['mode'] == "monitor":
        #monitor.draw_window(state, window, rpc_queue)
        pass
    if state['mode'] == "block":
        if 'queried' in s['getblock']:
            state['blocks'][str(height)].pop('queried')
            state['blocks']['browse_height'] = height
            state['blocks']['offset'] = 0
            state['blocks']['cursor'] = 0
            block.draw_window(state, window, rpc_queue)

def coinbase(s, state, window):
    height = str(s['height'])
    if height in state['blocks']:
        state['blocks'][height]['coinbase_amount'] = s['coinbase']

def getnetworkhashps(s, state, window, rpc_queue):
    blocks = s['getnetworkhashps']['blocks']
    state['networkhashps'][blocks] = s['getnetworkhashps']['value']

    if state['mode'] == "splash" and blocks == 2016: # initialization complete
        state['mode'] = "monitor"
        #monitor.draw_window(state, window, rpc_queue)
        pass

def getnettotals(s, state, window, rpc_queue):
    state['totalbytesrecv'] = s['getnettotals']['totalbytesrecv']
    state['totalbytessent'] = s['getnettotals']['totalbytessent']

    state['history']['getnettotals'].append(s['getnettotals'])

    # ensure getnettotals history does not fill RAM eventually, 300 items is enough
    if len(state['history']['getnettotals']) > 500:
        state['history']['getnettotals'] = state['history']['getnettotals'][-300:]

    if state['mode'] == 'net':
        net.draw_window(state, window, rpc_queue)

def getmininginfo(s, state, window):
    state['mininginfo'] = s['getmininginfo']

    if 'browse_height' not in state['blocks']:
        state['blocks']['browse_height'] = s['getmininginfo']['blocks']

    state['networkhashps']['diff'] = (int(s['getmininginfo']['difficulty'])*2**32)/600

def getpeerinfo(s, state, window, rpc_queue):
    state['peerinfo'] = s['getpeerinfo']
    state['peerinfo_offset'] = 0
    if state['mode'] == "peers":
        peers.draw_window(state, window, rpc_queue)

def getchaintips(s, state, window, rpc_queue):
    state['chaintips'] = s['getchaintips']
    state['chaintips_offset'] = 0
    if state['mode'] == 'forks':
        forks.draw_window(state, window, rpc_queue)

def getwalletinfo(s, state, window, rpc_queue):
    state['walletinfo'] = s['getwalletinfo']
    if state['mode'] == "wallet":
        wallet.draw_window(state, window, rpc_queue)

def settxfee(s, state, window, rpc_queue):
    window.addstr(0,10,"DEBUG! settxfee process")   #DEBUG!
    state['wallet']['mode'] = 'tx'
    rpc_queue.put('getwalletinfo')
    wallet.draw_window(state, window, rpc_queue)

def getnewaddress(s, state, window, rpc_queue):
    if state['mode'] == "wallet":
        if 'wallet' in state:
            state['wallet']['newaddress'] = str(s['getnewaddress'])
            state['wallet']['mode'] = 'newaddress'
        wallet.draw_window(state, window, rpc_queue)

def listsinceblock(s, state, window, rpc_queue):
    state['wallet'] = s['listsinceblock']
    state['wallet']['cursor'] = 0
    state['wallet']['offset'] = 0

    state['wallet']['view_string'] = []
    state['wallet']['view_colorpair'] = []
    state['wallet']['spendings'] = {}
    state['wallet']['mode'] = 'tx'

    state['wallet']['transactions'].sort(key=lambda entry: entry['category'], reverse=True)

    # add cumulative balance field to transactions once ordered by time
    state['wallet']['transactions'].sort(key=lambda entry: entry['time'])
    state['wallet']['transactions'].sort(key=lambda entry: entry['confirmations'], reverse=True)
    cumulative_balance = 0
    nonce = 0 # ensures a definitive ordering of transactions for cumulative balance
    for entry in state['wallet']['transactions']:
        entry['nonce'] = nonce
        nonce += 1
        if 'amount' in entry:
            if 'fee' in entry:
                cumulative_balance += entry['fee']
            cumulative_balance += entry['amount']
            entry['cumulative_balance'] = cumulative_balance

    state['wallet']['transactions'].sort(key=lambda entry: entry['nonce'], reverse=True)

    unit = g.coin_unit
    if 'testnet' in state:
        if state['testnet']:
            unit = g.coin_unit_test

    for entry in state['wallet']['transactions']:
        if 'txid' in entry:
            entry_time = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(entry['time']))
            output_string = entry_time + " %8d" % entry['confirmations'] + " conf"
            delta = entry['amount']
            # keep track of spendings for later use in addresses view
            if delta < 0 and 'address' in entry:
                if str(entry['address']) in state['wallet']['spendings']:
                    state['wallet']['spendings'][str(entry['address'])] += delta      # TODO: check if fee has to be substracted here also!
                else:
                    state['wallet']['spendings'].update({str(entry['address']): delta})
                
            if 'fee' in entry:
                delta += entry['fee'] # this fails if not all inputs owned by wallet; could be 'too negative'
            output_string += "% 17.8f " % delta + unit
            output_string += " " + "% 17.8f" % entry['cumulative_balance'] + unit
            state['wallet']['view_string'].append(output_string)
            if delta < 0:
                state['wallet']['view_colorpair'].append(3)
            else:
                state['wallet']['view_colorpair'].append(1)

            output_string = entry['txid'].rjust(74)
            state['wallet']['view_string'].append(output_string)
            state['wallet']['view_colorpair'].append(0)

            if 'address' in entry: # TODO: more sanity checking here
                output_string = "          " + entry['category'].ljust(15) + entry['address']
            else:
                output_string = "          unknown transaction type"
            state['wallet']['view_string'].append(output_string)
            state['wallet']['view_colorpair'].append(0)

            state['wallet']['view_string'].append("")
            state['wallet']['view_colorpair'].append(0)

    if state['mode'] == "wallet":
        wallet.draw_window(state, window, rpc_queue)

def listreceivedbyaddress(s, state, window, rpc_queue):
    state['wallet']['addresses'] = s['listreceivedbyaddress']
    state['wallet']['cursor'] = 0
    state['wallet']['offset'] = 0

    state['wallet']['addresses_view_string'] = []
    state['wallet']['addresses_view_colorpair'] = []
    state['wallet']['mode'] = 'addresses'

    state['wallet']['addresses'].sort(key=lambda entry: 999999 if entry['confirmations'] == 0 else entry['confirmations'], reverse=False)

    unit = g.coin_unit
    if 'testnet' in state:
        if state['testnet']:
            unit = g.coin_unit_test

    for entry in state['wallet']['addresses']:
        if 'address' in entry:
            amount_in = entry['amount']
            # find spendings for address
            if 'spendings' in state['wallet']:
                if str(entry['address']) in state['wallet']['spendings']:
                    amount_out = -state['wallet']['spendings'][str(entry['address'])]
                    amount = entry['amount'] + state['wallet']['spendings'][str(entry['address'])]
                else:
                    amount_out = 0.0
                    amount = entry['amount']
            else:
                amount_out = 0.0
                amount = entry['amount']
            
            if amount > 0:
                color = 1
            elif amount < 0:
                color = 3
            else:
                color = 0
            output_string = entry['address'] + str("% 17.8f " % amount + unit).rjust(39)
            state['wallet']['addresses_view_string'].append(output_string)
            state['wallet']['addresses_view_colorpair'].append(color)
            
            output_string = " " + str(str(entry['confirmations']) + " conf").ljust(15)
            output_string += str(str(len(entry['txids'])) + ' tx').rjust(10)
            output_string += str("(in:" + "% 1.8f" % amount_in + ", out:" + "% 1.8f" % amount_out + ")").rjust(44)
            state['wallet']['addresses_view_string'].append(output_string)
            state['wallet']['addresses_view_colorpair'].append(0)

            output_string = " " + unidecode(entry['account'].ljust(36))
            state['wallet']['addresses_view_string'].append(output_string)
            state['wallet']['addresses_view_colorpair'].append(0)

            state['wallet']['addresses_view_string'].append("")
            state['wallet']['addresses_view_colorpair'].append(0)

    if state['mode'] == "wallet":
        wallet.draw_window(state, window, rpc_queue)

def lastblocktime(s, state, window):
    state['lastblocktime'] = s['lastblocktime']

def txid(s, state, window, rpc_queue):
    if s['size'] < 0:
        if 'tx' in state:
            state.pop('tx')
        if state['mode'] == 'tx':
            tx.draw_window(state, window, rpc_queue)
        return False

    state['tx'] = {
        'txid': s['txid'],
        'vin': [],
        'vout_string': [],
        'cursor': 0,
        'offset': 0,
        'out_offset': 0,
        'loaded': 1,
        'mode': 'inputs',
        'size': s['size'],
    }

    for vin in s['vin']:
        if 'coinbase' in vin:
            state['tx']['vin'].append({'coinbase': vin['coinbase']})
        elif 'txid' in vin:
            if 'prev_tx' in vin:
                state['tx']['vin'].append({'txid': vin['txid'], 'vout': vin['vout'], 'prev_tx': vin['prev_tx']})
            else:
                state['tx']['vin'].append({'txid': vin['txid'], 'vout': vin['vout']})

    state['tx']['total_outputs'] = 0
    for vout in s['vout']:
        if 'value' in vout:
            buffer_string = "% 3d" % vout['n'] + "."
            if vout['scriptPubKey']['type'] == "pubkeyhash":
                buffer_string += "% 14.8f" % vout['value'] + ": " + vout['scriptPubKey']['addresses'][0]
            else:
                buffer_string += "% 14.8f" % vout['value'] + ": " + vout['scriptPubKey']['asm']

            if 'confirmations' in s:
                if 'spent' in vout:
                    if vout['spent'] == 'confirmed':
                        buffer_string += " [SPENT]"
                    elif vout['spent'] == 'unconfirmed':
                        buffer_string += " [UNCONFIRMED SPEND]"
                    else:
                        buffer_string += " [UNSPENT]"

            state['tx']['total_outputs'] += vout['value']
            state['tx']['vout_string'].extend(textwrap.wrap(buffer_string,70)) # change this to scale with window ?

    if 'total_inputs' in s:
        state['tx']['total_inputs'] = s['total_inputs']

    if 'confirmations' in s:
        state['tx']['confirmations'] = s['confirmations']

    if state['mode'] == 'tx':
        tx.draw_window(state, window, rpc_queue)

def consolecommand(s, state, window, rpc_queue):
    state['console']['cbuffer'].append(s['consolecommand'])
    state['console']['rbuffer'].append(s['consoleresponse'])
    state['console']['offset'] = 0
    if state['mode'] == "console":
        console.draw_window(state, window, rpc_queue)

def estimatefee(s, state, window):
    state['estimatefee'] = s['estimatefee']

def queue(state, window, interface_queue, rpc_queue=None):
    while True:
        try:
            s = interface_queue.get(False)
        except Queue.Empty:
            return False

        if 'resize' in s: resize(s, state, window, rpc_queue)
        elif 'getinfo' in s: getinfo(s, state, window, rpc_queue)
        elif 'getconnectioncount' in s: getconnectioncount(s, state, window)
        elif 'getbalance' in s: getbalance(s, state, window)
        elif 'getunconfirmedbalance' in s: getunconfirmedbalance(s, state, window)
        elif 'getblock' in s: getblock(s, state, window, rpc_queue)
        elif 'coinbase' in s: coinbase(s, state, window)
        elif 'getnetworkhashps' in s: getnetworkhashps(s, state, window, rpc_queue)
        elif 'getnettotals' in s: getnettotals(s, state, window, rpc_queue)
        elif 'getmininginfo' in s: getmininginfo(s, state, window)
        elif 'getpeerinfo' in s: getpeerinfo(s, state, window, rpc_queue)
        elif 'getwalletinfo' in s: getwalletinfo(s, state, window, rpc_queue)
        elif 'settxfee' in s: settxfee(s, state, window, rpc_queue)
        elif 'getnewaddress' in s: getnewaddress(s, state, window, rpc_queue)
        elif 'getchaintips' in s: getchaintips(s, state, window, rpc_queue)
        elif 'listsinceblock' in s: listsinceblock(s, state, window, rpc_queue)
        elif 'listreceivedbyaddress' in s: listreceivedbyaddress(s, state, window, rpc_queue)
        elif 'lastblocktime' in s: lastblocktime(s, state, window)
        elif 'txid' in s: txid(s, state, window, rpc_queue)
        elif 'consolecommand' in s: consolecommand(s, state, window, rpc_queue)
        elif 'estimatefee' in s: estimatefee(s, state, window)

        elif 'stop' in s:
            return s['stop']
