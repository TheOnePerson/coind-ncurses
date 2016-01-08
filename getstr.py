#!/usr/bin/env python
import curses

def getstr(w, y, x):
    window = curses.newwin(1, w, y, x)

    result = ""
    window.addstr("> ", curses.A_BOLD + curses.A_BLINK)
    window.refresh()
    window.keypad(True)
    oldcursor = 0
    try:
        oldcursor = curses.curs_set(1)
    except:
        pass

    while True:
        try:
            character = -1
            while (character < 0):
                character = window.getch()
        except:
            break

        if character == curses.KEY_ENTER or character == ord('\n'):
            break

        elif character == 27:      # ESC
            result = ""
            break

        elif character == curses.KEY_BACKSPACE or character == 127:
            if len(result):
                window.move(0, len(result)+1)
                window.delch()
                result = result[:-1]
                continue

        elif (137 > character > 31 and len(result) < w-3): # ascii range TODO: unicode
                result += chr(character)
                window.addstr(chr(character))

    window.addstr(0, 0, "> ", curses.A_BOLD + curses.color_pair(3))
    window.refresh()

    try:
        curses.curs_set(oldcursor)
    except:
        pass
    window.keypad(False)
    return result
