# coind-ncurses v0.0.29

For everyone who does not want to manage the BTC/BCH/BSV/BTG/LTC deamon (aka 'bitcoind') by a bloated desktop application: a python ncurses front-end for the console. Uses the JSON-RPC API.

![ScreenShot](/screenshots/coind_animated.gif)

-  Basing on the great work of azeteki (https://github.com/esotericnonsense/bitcoind-ncurses), but heavily enhanced.

## Dependencies

* Developed with python 2.7, Bitcoin Core 0.9.4
* jgarzik's python-bitcoinrpc library (https://github.com/jgarzik/python-bitcoinrpc)
* (Windows only) Python ncurses library (http://www.lfd.uci.edu/~gohlke/pythonlibs/#curses)

## Features (inherited from azeteki's version)

* Updating ticker showing bitcoind's status
* Basic block explorer with fast seeking and no external database required
* View transactions in blocks, trace back through their inputs and display scripts (best with -txindex)
* View wallet transactions (txid, transaction value, cumulative balance)
* View connected peers and chain tips
* Network bandwidth monitor
* Basic debug console functionality (WARNING: do not use for transactions)

## Additional features (of this version)

* Capability to handle several coins / daemons: BTC, BCH, BSV, BTG and also LTC (use startup parameter -m for this)
* Slightly enhanced GUI: tables and texts are dynamically placed and spaced
* Fully working wallet: you can set tx fees, view addresses and send coins
* Wallet functionality can also be completely disabled (put 'disablewallet=1' in your bitcoin.conf)
* Mempool monitor

## Installation

```
git clone https://github.com/TheOnePerson/coind-ncurses
git clone https://github.com/jgarzik/python-bitcoinrpc
mv python-bitcoinrpc/bitcoinrpc coind-ncurses/
```

Copy ~/.bitcoin/bitcoin.conf to coind-ncurses's folder, or alternatively run with the switch --config=/path/to/bitcoin.conf

This is an work-in-progess release. Expect the unexpected.

## Launch

Note that bitcoind-ncurses requires Python 2 due to the bitcoinrpc dependency.

```
$ python main.py
$ python2 main.py
```