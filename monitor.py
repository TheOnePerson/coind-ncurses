#!/usr/bin/env python
import curses, time, math

import global_mod as g
import footer
import os

def draw_window(state, old_window, rpc_queue, do_clear = True):

    window = curses.newwin(g.y - 1, g.x, 0, 0)

    if do_clear:
        old_window.clear()
        old_window.refresh()

    # display load average
    load_avg = os.getloadavg()
    g.addstr_rjust(window, 1, "Load avg: " + "{:.2f}".format(load_avg[0]) + " / " + "{:.2f}".format(load_avg[1]) + " / " + "{:.2f}".format(load_avg[2]), curses.A_BOLD, 1)

    if 'version' in state:
        if state['testnet'] == 1:
            color = curses.color_pair(2)
            window.addstr(1, 1, g.rpc_deamon + " v" + state['version'] + " (testnet)", color + curses.A_BOLD)
            unit = g.coin_unit_test
        else:
            color = curses.color_pair(1)
            window.addstr(1, 1, g.rpc_deamon + " v" + state['version'] + " ", color + curses.A_BOLD)
            unit = g.coin_unit
        window.addstr(0, 1, g.rpc_deamon + "-ncurses " + g.version, color + curses.A_BOLD)

    if 'peers' in state:
        if state['peers'] > 0:
            color = 0
        else:
            color = curses.color_pair(3)
        g.addstr_ljust(window, 0, str(state['peers']) + " peers", color + curses.A_BOLD, 0, 10, 4)
        
    if 'balance' in state:
        balance_string = "%0.8f" % state['balance'] + " " + unit
        if 'unconfirmedbalance' in state:
            if state['unconfirmedbalance'] != 0:
                balance_string += " (+" + "%0.8f" % state['unconfirmedbalance'] + " unconf)"
        g.addstr_ljust(window, 1, balance_string, curses.A_BOLD, 0, 10, 4)
        
    if 'mininginfo' in state:
        height = str(state['mininginfo']['blocks'])
        if height in state['blocks']:
            blockdata = state['blocks'][str(height)]

            if 'new' in blockdata:
                window.attrset(curses.A_REVERSE + curses.color_pair(5) + curses.A_BOLD)
                blockdata.pop('new')

            window.addstr(3, 1, "{:7d}".format(int(height)) + ": " + str(blockdata['hash']))
            window.addstr(4, 1, "{:,d}".format(int(blockdata['size'])) + " bytes (" + "{:,.2f}".format(float(blockdata['size']/1024)) + " KB)       ")
            tx_count = len(blockdata['tx'])
            bytes_per_tx = blockdata['size'] / tx_count
            window.addstr(5, 1, "Transactions: " + "{:,d}".format(int(tx_count)) + " (" + "{:,d}".format(int(bytes_per_tx)) + " bytes/tx)")

            if 'coinbase_amount' in blockdata:
                block_subsidy = float(g.reward_base / (2 ** (state['mininginfo']['blocks'] // g.halving_blockamount)))
                
                if block_subsidy:
                    coinbase_amount = float(blockdata['coinbase_amount'])
                    total_fees = float(coinbase_amount) - block_subsidy # assumption, mostly correct

                    if coinbase_amount > 0:
                        fee_percentage = "%0.2f" % ((total_fees / coinbase_amount) * 100)
                        coinbase_amount_str = "%0.8f" % coinbase_amount
                        window.addstr(7, 1, "Total block reward: " + coinbase_amount_str + " " + unit + " (" + fee_percentage + "% fees)")

                    if tx_count > 1:
                        tx_count -= 1 # the coinbase can't pay a fee
                        fees_per_tx = (total_fees / tx_count) * 1000
                        fees_per_kb = ((total_fees * 1024) / blockdata['size']) * 1000
                        total_fees_str = "%0.8f" % total_fees + " " + unit
                        fees_per_tx = "%0.5f" % fees_per_tx + " m" + unit + "/tx"
                        fees_per_kb = "%0.5f" % fees_per_kb + " m" + unit + "/KB"
                        window.addstr(8, 1, "Fees: " + total_fees_str + " (avg " +  fees_per_tx + ", ~" + fees_per_kb + ")")


            g.addstr_rjust(window, 4, "Block timestamp: " + time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(blockdata['time'])), curses.A_NORMAL, 1)
            
            if state['lastblocktime'] == 0:
                recvdelta_string = "        "
            else:
                recvdelta = int(time.time() - state['lastblocktime'])
                m, s = divmod(recvdelta, 60)
                h, m = divmod(m, 60)
                recvdelta_string = "{:02d}:{:02d}:{:02d}".format(h,m,s)

            stampdelta = int(time.time() - blockdata['time'])
            if stampdelta > 3600*3: # probably syncing if it's three hours old
                stampdelta_string = "             (syncing)"
            elif stampdelta > 0:
                m, s = divmod(stampdelta, 60)
                h, m = divmod(m, 60)
                d, h = divmod(h, 24)
                stampdelta_string = "({:d}d {:02d}:{:02d}:{:02d} by stamp)".format(d,h,m,s)
            else:
                stampdelta_string = "     (stamp in future)"

            g.addstr_rjust(window, 5, "Age: " + recvdelta_string + " " + stampdelta_string, curses.A_NORMAL, 1)
            # window.addstr(5, 38, "Age: " + recvdelta_string + " " + stampdelta_string)

            if 'chainwork' in blockdata:
                log2_chainwork = math.log(int(blockdata['chainwork'], 16), 2)
                try:
                    window.addstr(14, 1, "Chain work: 2**" + "%0.6f" % log2_chainwork)
                except:
                    print(log2_chainwork)

        diff = int(state['mininginfo']['difficulty'])
        window.addstr(10, 1, "Diff:        " + "{:,d}".format(diff))

    for block_avg in state['networkhashps']:
        index = 10

        if block_avg == 'diff':
            pass
        elif block_avg == 2016:
            index += 1
        elif block_avg == g.blocks_per_day:
            index += 2
        else:
            break

        rate = state['networkhashps'][block_avg]
        if block_avg != 'diff':
            nextdiff = (rate*600)/(2**32)
            if state['testnet'] == 1:
                nextdiff *= 2 # testnet has 1200 est. block interval, not 600
            try:
                window.addstr(index, 1, "Est (" + str(block_avg).rjust(4) + "): ~" + "{:,d}".format(int(nextdiff)))
            except:
                window.addstr(index, 1, "Est (" + str(block_avg).rjust(4) + "): ~" + "{:,d}".format(int(nextdiff)))

        if rate > 10**18:
            rate /= 10**18
            suffix = " EH/s"
        elif rate > 10**12:
            rate /= 10**12
            suffix = " TH/s"
        else:
            rate /= 10**6
            suffix = " MH/s"
        try:
            rate_string = "{:9.4f}".format(float(rate)) + suffix
            g.addstr_rjust(window, index, "Hashrate (" + str(block_avg).rjust(4) + "): " + rate_string.rjust(13), curses.A_NORMAL, 1)
        except:
            g.addstr_rjust(window, index, "Hashrate (" + str(block_avg).rjust(4) + "): ?????????????", curses.A_NORMAL, 1)
        # window.addstr(index, 38, "Hashrate (" + str(block_avg).rjust(4) + "): " + rate_string.rjust(13))
        index += 1

        pooledtx = state['mininginfo']['pooledtx']
        g.addstr_rjust(window, 14, "Mempool transactions: " + "{:5,d}".format(int(pooledtx)), curses.A_NORMAL, 1)
        # window.addstr(14, 38, "Mempool transactions: " + "% 5d" % pooledtx)

    if 'totalbytesrecv' in state:
        recvmb = "{:,.2f}".format(float(state['totalbytesrecv']*1.0/1048576))
        sentmb = "{:,.2f}".format(float(state['totalbytessent']*1.0/1048576))
        recvsent_string = "D/U: " + recvmb + " / " + sentmb + " MB"
        g.addstr_rjust(window, 0, recvsent_string, curses.A_BOLD, 1)
        # window.addstr(0, 43, recvsent_string.rjust(30), curses.A_BOLD)

    if 'estimatefee' in state:
        string = "estimatefee:"
        for item in state['estimatefee']:
            if item['value'] > 0:
                string += " (" + str(item['blocks']) + ")" + "%4.2f" % (item['value']*1000) + " m" + unit
        if len(string) > 12:
            g.addstr_rjust(window, 15, string, curses.A_NORMAL, 1)
            # window.addstr(15, 38, string)

    if 'mininginfo' in state:
        errors = state['mininginfo']['errors']
        if len(errors):
            if state['y'] < 20:
                y = state['y'] - 3
            else:
                y = 17
            window.addstr(y, 1, errors[:72], curses.color_pair(5) + curses.A_BOLD + curses.A_REVERSE)
            window.addstr(y+1, 1, errors[72:142].rjust(72), curses.color_pair(5) + curses.A_BOLD + curses.A_REVERSE)

    window.refresh()
    footer.draw_window(state, rpc_queue)
