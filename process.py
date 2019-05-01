#!/usr/bin/env python
import textwrap, time
from multiprocessing import Queue
from Queue import Empty
from unidecode import unidecode

import global_mod as g
import tx
import block
import mempool
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
    elif state['mode'] == 'mempool':
        mempool.draw_window(state, window, rpc_queue)
    elif state['mode'] == 'peers':
        peers.draw_window(state, window, rpc_queue)
    elif state['mode'] == 'wallet':
        wallet.draw_window(state, window, rpc_queue)
    elif state['mode'] == 'home':
        monitor.draw_window(state, window, rpc_queue)
    elif state['mode'] == 'console':
        console.draw_window(state, window, rpc_queue)
    elif state['mode'] == 'net':
        net.draw_window(state, window, rpc_queue)
    elif state['mode'] == 'forks':
        forks.draw_window(state, window, rpc_queue)

def getnetworkinfo(s, state, window, rpc_queue):
    state['version'] = str(s['getnetworkinfo']['version'] / 1000000)
    state['version'] += '.' + str((s['getnetworkinfo']['version'] % 1000000) / 10000)
    state['version'] += '.' + str((s['getnetworkinfo']['version'] % 10000) / 100)
    state['version'] += '.' + str((s['getnetworkinfo']['version'] % 100))

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

def getrawmempool(s, state, window, rpc_queue = None):
    state['mempool'] = {}
    state['mempool']['transactions'] = s['getrawmempool']
    state['mempool']['num_transactions'] = str(len(s['getrawmempool']))

    if state['mode'] == "mempool":
        state['mempool']['offset'] = 0
        state['mempool']['cursor'] = 0
        mempool.draw_window(state, window, rpc_queue)

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

    if s['getmininginfo']['chain'] != 'main':
        state['testnet'] = 1
        g.testnet = True
    else:
        state['testnet'] = 0
        g.testnet = False


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
    if 'walletversion' in s['getwalletinfo']:
        g.wallet_support = True
    else:
        g.wallet_support = False
        if 'wallet' in g.modes:
            g.modes.remove('wallet')

    if state['mode'] == "wallet":
        wallet.draw_window(state, window, rpc_queue)

def sendtoaddress(s, state, window, rpc_queue):
    if state['mode'] == "wallet":
        if state['wallet']['mode'] == 'sendtoaddress':
            state['newtransaction']['result'] = str(s['sendtoaddress'])
            wallet.draw_transaction_update(state, window)
            state['newtransaction'] = {}
            state['wallet']['mode'] = 'tx'
            rpc_queue.put('walletlock')
            rpc_queue.put('listsinceblock')
            rpc_queue.put('getwalletinfo')

def walletpassphrase(s, state, window, rpc_queue):
    if 'newtransaction' in state:
        if 'address' in state['newtransaction']:
            s = {'sendtoaddress': {'address': state['newtransaction']['address'], 'amount': state['newtransaction']['amount'], 'comment': state['newtransaction']['comment'], 'comment_to': state['newtransaction']['comment_to']}}
            rpc_queue.put(s)

def settxfee(s, state, window, rpc_queue):
    state['wallet']['mode'] = 'tx'
    rpc_queue.put('getwalletinfo')
    wallet.draw_window(state, window, rpc_queue)

def getnewaddress(s, state, window, rpc_queue):
    if state['mode'] == "wallet":
        if 'wallet' in state:
            state['wallet']['newaddress'] = str(s['getnewaddress'])
            wallet.draw_new_address_update(state, window)
            state['wallet']['mode'] = 'addresses'
            rpc_queue.put('listreceivedbyaddress')
            wallet.draw_window(state, window, rpc_queue)

def importaddress(s, state, window, rpc_queue):
    if state['mode'] == "wallet":
        if 'wallet' in state:
            state['wallet']['mode'] = 'addresses'
            rpc_queue.put('listreceivedbyaddress')
            wallet.draw_window(state, window, rpc_queue)

def backupwallet(s, state, window, rpc_queue):
    if state['mode'] == "wallet":
        if state['wallet']['mode'] == 'backupwallet':
            state['wallet']['mode'] = 'tx'
            rpc_queue.put('getwalletinfo')
            rpc_queue.put('listsinceblock')

def wallet_toggle_tx(s, state, window, rpc_queue):
    if state['mode'] == "wallet":
        if state['wallet']['mode'] == 'tx':
            state['wallet']['verbose'] = 1 - state['wallet']['verbose']
            listsinceblock(s, state, window, rpc_queue, False)


def listsinceblock(s, state, window, rpc_queue, reload = True):
    if reload:
        state['wallet'] = s['listsinceblock']
    state['wallet']['cursor'] = 0
    state['wallet']['offset'] = 0
    if not 'verbose' in state['wallet']:
        state['wallet']['verbose'] = 0

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

    indent = "          "
    comment_split = " To: "
    comment_maxlen = (g.x - len(indent) - len(comment_split)) // 2
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
            output_string += " " + "% 17.8f" % entry['cumulative_balance'] + " " + unit
            state['wallet']['view_string'].append(output_string)
            if delta < 0:
                state['wallet']['view_colorpair'].append(3)
            else:
                state['wallet']['view_colorpair'].append(1)

            is_watchonly = True if 'involvesWatchonly' in entry else False
            color = 2 if is_watchonly else 0
            output_string = entry['txid'].rjust(74)
            state['wallet']['view_string'].append(output_string)
            state['wallet']['view_colorpair'].append(color)

            if 'address' in entry: # TODO: more sanity checking here
                output_string = indent + entry['category'].ljust(15) + entry['address'].ljust(34)
            else:
                output_string = indent + "unknown transaction type"
            if is_watchonly:
                output_string += "(watchonly)".rjust(15)
            state['wallet']['view_string'].append(output_string)
            state['wallet']['view_colorpair'].append(color)

            if state['wallet']['verbose'] > 0:
                if 'comment' in entry and 'to' in entry:
                    output_string = indent + unidecode(entry['comment'][:comment_maxlen].ljust(comment_maxlen)) + comment_split + unidecode(entry['to'][:comment_maxlen])
                    state['wallet']['view_string'].append(output_string)
                    state['wallet']['view_colorpair'].append(color)
                else:
                    state['wallet']['view_string'].append("")
                    state['wallet']['view_colorpair'].append(color)

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
            if 'involvesWatchonly' in entry:
                color = 2
                output_string = entry['address'] + " (watchonly)" + str("% 17.8f " % amount + unit).rjust(27)
            else:
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

def put_txid(s, state, window, rpc_queue):
    if not 'txid_history' in state:
        state['txid_history'] = []
    if len(state['txid_history']) >= 100:
        # only keep track of the last 100 txids
        del state['txid_history'][0]
    state['txid_history'].append(s['put_txid'])

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
            state['tx']['vout_string'].extend(textwrap.wrap(buffer_string,g.x - 5)) # change this to scale with window ?

    if 'total_inputs' in s:
        state['tx']['total_inputs'] = s['total_inputs']

    if 'confirmations' in s:
        state['tx']['confirmations'] = s['confirmations']

    if 'time' in s:
        state['tx']['time'] = s['time']

    if 'blockhash' in s:
        state['tx']['blockhash'] = s['blockhash']

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
        except Empty:
            return False

        if 'resize' in s: resize(s, state, window, rpc_queue)
        elif 'getnetworkinfo' in s: getnetworkinfo(s, state, window, rpc_queue)
        elif 'getconnectioncount' in s: getconnectioncount(s, state, window)
        elif 'getbalance' in s: getbalance(s, state, window)
        elif 'getunconfirmedbalance' in s: getunconfirmedbalance(s, state, window)
        elif 'getblock' in s: getblock(s, state, window, rpc_queue)
        elif 'getrawmempool' in s: getrawmempool(s, state, window, rpc_queue)
        elif 'coinbase' in s: coinbase(s, state, window)
        elif 'getnetworkhashps' in s: getnetworkhashps(s, state, window, rpc_queue)
        elif 'getnettotals' in s: getnettotals(s, state, window, rpc_queue)
        elif 'getmininginfo' in s: getmininginfo(s, state, window)
        elif 'getpeerinfo' in s: getpeerinfo(s, state, window, rpc_queue)
        elif 'getwalletinfo' in s: getwalletinfo(s, state, window, rpc_queue)
        elif 'settxfee' in s: settxfee(s, state, window, rpc_queue)
        elif 'backupwallet' in s: backupwallet(s, state, window, rpc_queue)
        elif 'getnewaddress' in s: getnewaddress(s, state, window, rpc_queue)
        elif 'importaddress' in s: importaddress(s, state, window, rpc_queue)
        elif 'getchaintips' in s: getchaintips(s, state, window, rpc_queue)
        elif 'listsinceblock' in s: listsinceblock(s, state, window, rpc_queue)
        elif 'wallet_toggle_tx' in s: wallet_toggle_tx(s, state, window, rpc_queue)
        elif 'listreceivedbyaddress' in s: listreceivedbyaddress(s, state, window, rpc_queue)
        elif 'lastblocktime' in s: lastblocktime(s, state, window)
        elif 'txid' in s: txid(s, state, window, rpc_queue)
        elif 'put_txid' in s: put_txid(s, state, window, rpc_queue)
        elif 'sendtoaddress' in s: sendtoaddress(s, state, window, rpc_queue)
        elif 'walletpassphrase' in s: walletpassphrase(s, state, window, rpc_queue)
        elif 'consolecommand' in s: consolecommand(s, state, window, rpc_queue)
        elif 'estimatefee' in s: estimatefee(s, state, window)

        elif 'stop' in s:
            return s['stop']
