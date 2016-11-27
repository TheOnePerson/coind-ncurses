#!/usr/bin/env python
import curses, time

import global_mod as g
import footer

def draw_window(state, window, rpc_queue = None, do_clear = True):

    if do_clear:
        window.clear()
        window.refresh()

    win_header = curses.newwin(3, g.x, 0, 0)

    if 'peerinfo' in state:
        win_header.addstr(0, 1, "Connected peers: " + str(len(state['peerinfo'])), curses.A_BOLD)
        g.addstr_rjust(win_header, 0, "(UP/DOWN: scroll, P: refresh)", curses.A_BOLD, 1)
        win_header.addstr(2, 1, "  Node IP               Version", curses.A_BOLD + curses.color_pair(5))
        header = "Recv MB Sent MB    Time      Height"
        win_header.addstr(2, (g.x - len(header) - 1 if g.x <= 95 else 94 - len(header)), header, curses.A_BOLD + curses.color_pair(5))
        draw_peers(state)

    else:
        if rpc_queue.qsize() > 0:
            g.addstr_cjust(win_header, 0, "...waiting for peer information being processed...", curses.A_BOLD + curses.color_pair(3))
        else:
            win_header.addstr(0, 1, "no peer information loaded", curses.A_BOLD + curses.color_pair(3))
            win_header.addstr(1, 1, "press 'P' to refresh", curses.A_BOLD)

    win_header.refresh()
    footer.draw_window(state, rpc_queue)

def draw_peers(state):
    window_height = g.y - 4
    max_x = 95 if g.x > 95 else g.x
    win_peers = curses.newwin(window_height, max_x, 3, 0)

    offset = state['peerinfo_offset']

    for index in xrange(offset, offset + window_height):
        if index < len(state['peerinfo']):
            peer = state['peerinfo'][index]

            condition = (index == offset + window_height - 1) and (index + 1 < len(state['peerinfo']))
            condition = condition or ((index == offset) and (index > 0))

            if condition:
                # scrolling up or down is possible
                win_peers.addstr(index - offset, 3, "...")

            else:
                if peer['inbound']:
                    win_peers.addstr(index-offset, 1, 'I')

                elif 'syncnode' in peer:
                    if peer['syncnode']:
                        # syncnodes are outgoing only
                        win_peers.addstr(index-offset, 1, 'S')

                addr_str = peer['addr'].replace(".onion","").replace(":" + g.node_port,"").replace(":" + g.node_port_test,"").strip("[").strip("]")

                # truncate long ip addresses (ipv6)
                addr_str = (addr_str[:19] + '..') if len(addr_str) > 21 else addr_str

                win_peers.addstr(index-offset, 3, addr_str)
                win_peers.addstr(index-offset, 25, peer['subver'].strip("/").replace("Satoshi:","Sat")[:16])

                mbrecv = "{: 7.1f}".format(float(peer['bytesrecv']) / 1048576)
                mbsent = "{: 7.1f}".format(float(peer['bytessent']) / 1048576)

                win_peers.addstr(index-offset, max_x - 36, mbrecv)
                win_peers.addstr(index-offset, max_x - 28, mbsent)

                timedelta = int(time.time() - peer['conntime'])
                m, s = divmod(timedelta, 60)
                h, m = divmod(m, 60)
                d, h = divmod(h, 24)

                time_string = ""
                if d:
                    time_string += ("%d" % d + "d").rjust(3) + " "
                    time_string += "%02d" % h + ":"
                elif h:
                    time_string += "%02d" % h + ":"
                time_string += "%02d" % m + ":"
                time_string += "%02d" % s

                win_peers.addstr(index-offset, max_x - 21, time_string.rjust(12))

                if 'synced_headers' in peer:
                    win_peers.addstr(index-offset, max_x - 8, str(peer['synced_headers']).rjust(7))

    win_peers.refresh()
