#!/usr/bin/env python
from anycoinrpc.authproxy import AuthServiceProxy
import global_mod as g
import curses, time, decimal
from multiprocessing import Queue
from Queue import Empty
import sys, os

def log(logfile, loglevel, string):
    if loglevel > 0: # hardcoded loglevel here
        return False
    from datetime import datetime
    #now = datetime.utcnow()
    now = datetime.now()
    string_time = now.strftime('%Y-%m-%d %H:%M:%S.')
    millisecond = now.microsecond / 1000
    string_time += "%03d" % millisecond

    with open(os.path.abspath(os.path.dirname(sys.argv[0])) + '/' + logfile, 'a') as f:
        f.write(string_time + ' LL' + str(loglevel) + ' ' + string + '\n')
    
def stop(interface_queue, error_message):
    interface_queue.put({'stop': error_message})

def init(interface_queue, cfg):
    try:
        rpcuser = cfg.get('rpcuser')
        rpcpassword = cfg.get('rpcpassword')
        rpcip = cfg.get('rpcip', '127.0.0.1')

        if cfg.get('testnet') == "1":
            g.testnet = 1
        else:
            g.testnet = 0
            
        if cfg.get('rpcport'):
            rpcport = cfg.get('rpcport')
        elif g.testnet:
            rpcport = str(g.rpc_port_test)
        else:
            rpcport = str(g.rpc_port)

        if cfg.get('rpcssl') == "1":
            protocol = "https"
        else:
            protocol = "http"

        rpcurl = protocol + "://" + rpcuser + ":" + rpcpassword + "@" + rpcip + ":" + rpcport
    except:
        stop(interface_queue, "invalid configuration file or missing values")
        return False

    try:
        rpchandle = AuthServiceProxy(rpcurl, None, 500)
        log('debug.log', 2, 'rpchandle: ' + str(rpchandle))
        return rpchandle
    except:
        return False

def rpcrequest(rpchandle, request, interface_queue, *args):
    #try:
        log('debug.log', 2, 'rpcrequest: ' + request + ', args: ' + str(args))

        request_time = time.time()
        try:
            response = getattr(rpchandle, request)(*args)
        except:
            interface_queue.put({ 'stop': g.rpc_deamon + " server not reachable"})
            return False
        request_time_delta = time.time() - request_time

        log('debug.log', 3, request + ' done in ' + "%.3f" % request_time_delta + 's')
        log('debug.log', 2, request + ' response: ' + str(response))
        if interface_queue:
            interface_queue.put({request: response})

        return response
    #except:
    #    log('debug.log', 2, request + ' failed')
    #    return False

def getblock(rpchandle, interface_queue, block_to_get, queried = False, new = False):
    try:
        if (len(str(block_to_get)) < 9) and str(block_to_get).isdigit(): 
            blockhash = rpcrequest(rpchandle, 'getblockhash', False, block_to_get)
        elif len(block_to_get) == 64:
            blockhash = block_to_get

        block = rpcrequest(rpchandle, 'getblock', False, blockhash)

        if queried:
            block['queried'] = 1

        if new:
            block['new'] = True

        interface_queue.put({'getblock': block})

        return block

    except:
        return 0

def sendtoaddress(rpchandle, interface_queue, s):
    try:
        txid = rpcrequest(rpchandle, 'sendtoaddress', False, s['address'], s['amount'], s['comment'], s['comment_to'])
        interface_queue.put({'sendtoaddress': txid})
        return txid

    except:
        return 0

def loop(interface_queue, rpc_queue, cfg):
    # TODO: add error checking for broken config, improve exceptions
    rpchandle = init(interface_queue, cfg)
    if not rpchandle: # TODO: this doesn't appear to trigger, investigate
        stop(interface_queue, "failed to connect to " + g.rpc_deamon + " (handle not obtained)")
        return True

    update_interval = 2 # seconds

    last_update = time.time() - update_interval
    
    info = rpcrequest(rpchandle, 'getnetworkinfo', interface_queue)
    if not info:
        stop(interface_queue, "failed to connect to " + g.rpc_deamon + " (getnetworkinfo failed)")
        return True

    log('debug.log', 1, 'CONNECTED')

    prev_blockcount = 0
    while True:
        try:
            s = rpc_queue.get(True, 0.1)
        except Empty:
            s = {}

        if len(s):
            log('debug.log', 1, 'interface request: ' + str(s))
            request_time = time.time()

        if 'stop' in s:
            log('debug.log', 1, 'halting RPC thread on request by user')
            break

        elif 'consolecommand' in s:
            arguments = s['consolecommand'].split()
            command = arguments[0]
            arguments = arguments[1:]

            # TODO: figure out how to encode properly for submission; this is hacky.
            index = 0
            while index < len(arguments):
                if arguments[index].isdigit():
                    arguments[index] = int(arguments[index])
                elif arguments[index] == "False":
                    arguments[index] = False
                elif arguments[index] == "false":
                    arguments[index] = False
                elif arguments[index] == "True":
                    arguments[index] = True
                elif arguments[index] == "true":
                    arguments[index] = True
                else:
                    try:
                        arguments[index] = decimal.Decimal(arguments[index])
                    except:
                        pass
                index += 1

            try:
                response = rpcrequest(rpchandle, command, False, *arguments)
                interface_queue.put({'consolecommand': s['consolecommand'], 'consoleresponse': response})
            except:
                interface_queue.put({'consolecommand': s['consolecommand'], 'consoleresponse': "ERROR"})

        elif 'getblockhash' in s:
            getblock(rpchandle, interface_queue, s['getblockhash'], True)

        elif 'getblock' in s:
            getblock(rpchandle, interface_queue, s['getblock'], True)

        elif 'settxfee' in s:
            response = rpcrequest(rpchandle, 'settxfee', interface_queue, s['settxfee'])

        elif 'backupwallet' in s:
            response = rpcrequest(rpchandle, 'backupwallet', interface_queue, s['backupwallet'])

        elif 'walletpassphrase' in s:
            response = rpcrequest(rpchandle, 'walletpassphrase', interface_queue, s['walletpassphrase'], 60)

        elif 'txid' in s:
            try:
                # put txid onto browse stack
                if not 'notrack' in s:
                    interface_queue.put({'put_txid': s['txid']})
                # get actual data
                tx = rpcrequest(rpchandle, 'getrawtransaction', False, s['txid'], 1)
                tx['size'] = len(tx['hex'])/2

                if 'coinbase' in tx['vin'][0]: # should always be at least 1 vin
                    tx['total_inputs'] = 'coinbase'

                if 'verbose' in s:
                    tx['total_inputs'] = 0
                    prev_tx = {}
                    for vin in tx['vin']:
                        if 'txid' in vin:
                            try:
                                txid = vin['txid']
                                if txid not in prev_tx:
                                    prev_tx[txid] = rpcrequest(rpchandle, 'getrawtransaction', False,
                                                               txid, 1)

                                vin['prev_tx'] = prev_tx[txid]['vout'][vin['vout']]
                                if 'value' in vin['prev_tx']:
                                    tx['total_inputs'] += vin['prev_tx']['value']
                            except:
                                pass
                        elif 'coinbase' in vin:
                            tx['total_inputs'] = 'coinbase'
                    for vout in tx['vout']:
                        try:
                            utxo = rpcrequest(rpchandle, 'gettxout', False,
                                                s['txid'], vout['n'], False)
                            if utxo == None:
                                vout['spent'] = 'confirmed'
                            else:
                                utxo = rpcrequest(rpchandle, 'gettxout', False,
                                                    s['txid'], vout['n'], True)
                                if utxo == None:
                                    vout['spent'] = 'unconfirmed'
                                else:
                                    vout['spent'] = False
                        except:
                            pass

            except: 
                tx = {'txid': s['txid'], 'size': -1}

            interface_queue.put(tx)

        elif 'getpeerinfo' in s:
            rpcrequest(rpchandle, 'getpeerinfo', interface_queue)

        elif 'getnewaddress' in s:
            rpcrequest(rpchandle, 'getnewaddress', interface_queue, s['getnewaddress'])
            
        elif 'importaddress' in s:
            rpcrequest(rpchandle, 'importaddress', interface_queue, s['importaddress']['address'], s['importaddress']['account'], bool(s['importaddress']['rescan']))
            
        elif 'getwalletinfo' in s:
            rpcrequest(rpchandle, 'getwalletinfo', interface_queue)

        elif 'listsinceblock' in s:
            rpcrequest(rpchandle, 'listsinceblock', interface_queue, "", 1, True)

        elif 'wallet_toggle_tx' in s:
            interface_queue.put(s)

        elif 'listreceivedbyaddress' in s:
            rpcrequest(rpchandle, 'listreceivedbyaddress', interface_queue, 0, True, True)

        elif 'getchaintips' in s:
            rpcrequest(rpchandle, 'getchaintips', interface_queue)

        elif 'findblockbytimestamp' in s:
            request = s['findblockbytimestamp']

            # initializing the while loop 
            block_to_try = 0
            delta = 10000 
            iterations = 0
 
            while abs(delta) > 3600 and iterations < 15: # one day
                block = getblock(rpchandle, interface_queue, block_to_try, True)
                if not block:
                    break

                delta = request - block['time']
                block_to_try += int(delta / 600) # guess 10 mins per block. seems to work on testnet anyway 

                if (block_to_try < 0):
                    block = getblock(rpchandle, interface_queue, 0, True)
                    break # assume genesis has earliest timestamp

                elif (block_to_try > blockcount):
                    block = getblock(rpchandle, interface_queue, blockcount, True)
                    break

                iterations += 1

        elif 'sendtoaddress' in s:
            sendtoaddress(rpchandle, interface_queue, s['sendtoaddress'])

        elif 'walletlock' in s:
            rpcrequest(rpchandle, 'walletlock', interface_queue)

        elif (time.time() - last_update) > update_interval:
            update_time = time.time()
            log('debug.log', 1, 'updating (' + "%.3f" % (time.time() - last_update) + 's since last)')

            rpcrequest(rpchandle, 'getnettotals', interface_queue)
            rpcrequest(rpchandle, 'getconnectioncount', interface_queue)
            mininginfo = rpcrequest(rpchandle, 'getmininginfo', interface_queue)
            rpcrequest(rpchandle, 'getbalance', interface_queue, "*", 1, True)
            rpcrequest(rpchandle, 'getunconfirmedbalance', interface_queue)

            blockcount = mininginfo['blocks']
            if blockcount:
                if (prev_blockcount != blockcount): # minimise RPC calls
                    if prev_blockcount == 0:
                        lastblocktime = {'lastblocktime': 0}
                    else:
                        lastblocktime = {'lastblocktime': time.time()}
                    interface_queue.put(lastblocktime)

                    log('debug.log', 1, '=== NEW BLOCK ' + str(blockcount) + ' ===')

                    block = getblock(rpchandle, interface_queue, blockcount, False, True)
                    if block:
                        prev_blockcount = blockcount

                        try:
                            decoded_tx = rpcrequest(rpchandle, 'getrawtransaction', False,
                                                    block['tx'][0], 1)

                            coinbase_amount = 0
                            for output in decoded_tx['vout']:
                                if 'value' in output:
                                    coinbase_amount += output['value']

                            interface_queue.put({"coinbase": coinbase_amount, "height": blockcount})
                            
                        except: pass 

                    try:
                        nethash144 = rpcrequest(rpchandle, 'getnetworkhashps', False, g.blocks_per_day)
                        nethash2016 = rpcrequest(rpchandle, 'getnetworkhashps', False, 2016)
                        interface_queue.put({'getnetworkhashps': {'blocks': g.blocks_per_day, 'value': nethash144}})
                        interface_queue.put({'getnetworkhashps': {'blocks': 2016, 'value': nethash2016}})
                    except: pass

                    try:
                        estimatefee1 = rpcrequest(rpchandle, 'estimatefee', False, 1)
                        estimatefee5 = rpcrequest(rpchandle, 'estimatefee', False, 5)
                        estimatefee = [{'blocks': 1, 'value': estimatefee1}, {'blocks': 5, 'value': estimatefee5}]
                        interface_queue.put({'estimatefee': estimatefee})
                    except: pass

            last_update = time.time()

            update_time_delta = last_update - update_time
            log('debug.log', 1, 'update done in ' + "%.3f" % update_time_delta + 's')

        if len(s):
            request_time_delta = time.time() - request_time
            log('debug.log', 1, 'interface request: done in ' + "%.3f" % request_time_delta + 's')
