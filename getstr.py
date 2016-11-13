#!/usr/bin/env python
import global_mod as g
import curses, time
import sys

def getstr(w, y, x, password_char=""):
    window = curses.newwin(1, w, y, x)

    result = ""
    window.addstr("> ", curses.A_BOLD + curses.A_BLINK)
    window.refresh()
    window.keypad(True)
    oldcursor = 0
    global fs_encoding
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
            window.move(0, 2)
            window.clrtoeol()
            result = ""
            break

        elif character == curses.KEY_BACKSPACE or character == 127:
            if len(result):
                window.move(0, len(result)+1)
                window.delch()
                result = result[:-1]
                continue

        elif (character < 256 and (len(chr(character).strip()) > 0 or character == 32) and len(result) < w-3): # ascii range TODO: unicode
                result += chr(character)
                if password_char =="":
                    window.addstr(chr(character))
                else:
                    window.addstr(password_char)

    window.addstr(0, 0, "> ", curses.A_BOLD + curses.color_pair(3))
    window.refresh()

    try:
        curses.curs_set(oldcursor)
    except:
        pass
    window.keypad(False)
    return result

'''
  This class provides some basic support for user keyboard input
  and makes user interaction somewhat more coherent.
'''
class UserInput(object):
    
    _window = None
    _title = ""
    _y = 0
    
    def __init__(self, window, title, attribs=None):
        self._window = window
        self._title = title
        self._window.clear()
        self._draw_title(attribs)
        
    def _draw_title(self, attribs=None):
        if g.testnet:
            color = curses.color_pair(2)
        else:
            color = curses.color_pair(1)
        self._window.addstr(0, 1, g.rpc_deamon + "-ncurses " + g.version + " - " + self._title, (color + curses.A_BOLD) if attribs == None else attribs)
        self._window.refresh()
        self.nextline()
    
    def nextline(self):
        self._y += 1
        
    def addline(self, string, attribs=None, y=-1, x=1):
        y_here = self._y if y == -1 else y
        self._window.addstr(y_here, x, string, curses.A_BOLD if attribs == None else attribs)
        self._window.refresh()
        self._y = y_here + 1
    
    def getstr(self, maxwidth=-1, y=-1, x=1):
        (win_x, win_y) = self._window.getmaxyx()
        width = win_x-3 if maxwidth == -1 else maxwidth+3
        win_y = self._y if y == -1 else y
        result = sys.modules["getstr"].getstr(width, win_y, x)
        self.nextline()
        return result
    
    def continue_yesno(self, defaultyes=True, message=""):
        self.addline(("OK, do you want to continue? " if message == "" else message) + ("[Y/n]" if defaultyes else "[y/N]"), curses.color_pair(5) + curses.A_BOLD)
        result = self.getstr(3)
        if len(result.strip()) > 0:
            if result[0].upper() == 'Y':
                return True
            else:
                return False
        else:
            return True if defaultyes else False
    
    def addmessageline(self, string, attribs=None, timetowait=-1, y=-1, x=1):
        y_here = self._y + 1 if y == -1 else y
        self._window.addstr(y_here, x, string, curses.color_pair(1) + curses.A_BOLD if attribs == None else attribs)
        self._window.refresh()
        time.sleep(2.5 if timetowait == -1 else timetowait)
        self._y = y_here + 1
        
    def clear(self):
        self._window.clear()
        self._window.refresh()
