#!/usr/bin/env python

###############################################################################
# bitcoind-ncurses by Amphibian
# thanks to jgarzik for bitcoinrpc
# wumpus and kylemanna for configuration file parsing
# all the users for their suggestions and testing
# and of course the bitcoin dev team for that bitcoin gizmo, pretty neat stuff
###############################################################################

import multiprocessing, argparse, signal

import global_mod as g

import rpc
import interface
import config

def interrupt_signal(signal, frame):
    s = {'stop': "Interrupt signal caught"}
    interface_queue.put(s)

def debug(rpc_queue):
    # coinbase testnet transaction for debugging
    #s = {'txid': "cfb8bc436ca1d8b8b2d324a9cb2ef097281d2d8b54ba4239ce447b31b8757df2"}
    # tx with 1001 inputs, 1002 outputs 
    s = {'txid': 'e1dc93e7d1ee2a6a13a9d54183f91a5ae944297724bee53db00a0661badc3005'}
    rpc_queue.put(s)

if __name__ == '__main__':
    # initialise queues
    interface_queue = multiprocessing.Queue()
    rpc_queue = multiprocessing.Queue()

    # parse commandline arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--config",
                        help="path to config file (i.e. bitcoin.conf|litecoin.conf)",
                        default="bitcoin.conf")
    parser.add_argument("-m", "--mode",
                        help="coin mode, either BTC (default), BCH, BSV, BTG, or LTC",
                        default="BTC")
    args = parser.parse_args()

    # get coin mode
    try:
        g.coinmode = args.mode.upper()
    except:
        g.coinmode = g.get_default_coinmode()
    g.init_coinmode()
    
    # parse config file
    try:
        cfg = config.read_file(args.config)
    except IOError:
        cfg = {}
        s = {'stop': "configuration file [" + args.config + "] does not exist or could not be read"}
        interface_queue.put(s)

    # initialise interrupt signal handler (^C)
    signal.signal(signal.SIGINT, interrupt_signal)

    # start RPC thread
    rpc_process = multiprocessing.Process(target=rpc.loop, args = (interface_queue, rpc_queue, cfg))
    rpc_process.daemon = True
    rpc_process.start()

    #debug(rpc_queue)

    # main loop
    interface.main(interface_queue, rpc_queue)

    # ensure RPC thread exits cleanly
    rpc_process.join()
