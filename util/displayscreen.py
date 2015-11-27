# vim: ts=8 sts=4 sw=4 expandtab

import curses

class CursesStdIO:
    """fake fd to be registered as a reader with the twisted reactor.
       Curses classes needing input should extend this"""

    def fileno(self):
        """ We want to select on FD 0 """
        return 0

    def doRead(self):
        """called when input is ready"""

    def logPrefix(self): return 'CursesClient'

class Screen(CursesStdIO):
    def __init__(self, stdscr):
        self.timer = 0
        self.statusText = "TEST CURSES APP -"
        self.searchText = ''
        self.stdscr = stdscr

        # set screen attributes
        self.stdscr.nodelay(1) # this is used to make input calls non-blocking
        curses.cbreak()
        self.stdscr.keypad(1)
        curses.curs_set(0)     # no annoying mouse cursor

        self.rows, self.cols = self.stdscr.getmaxyx()
        self.lines = []

        curses.start_color()

        # create color pair's 1 and 2
        curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_WHITE)
        curses.init_pair(2, curses.COLOR_CYAN, curses.COLOR_BLACK)

        self.paintStatus(self.statusText)
        self.stdscr.refresh()

    def connectionLost(self, reason):
        self.close()

    def addLine(self, text):
        """ add a line to the internal list of lines"""

        self.lines.append(text)
        while len(self.lines) > 10:
            del self.lines[0]
        self.redisplayLines()

    def redisplayLines(self):
        """ method for redisplaying lines
            based on internal list of lines """

        self.stdscr.clear()
        self.paintStatus(self.statusText)
        i = 0
        index = len(self.lines) - 1
        while i < (self.rows - 3) and index >= 0:
            self.stdscr.addstr(self.rows - 3 - i, 0, self.lines[index],
                               curses.color_pair(2))
            i = i + 1
            index = index - 1
        self.stdscr.refresh()

    def paintStatus(self, text):
        if len(text) > self.cols: raise TextTooLongError
        self.stdscr.addstr(self.rows-2,0,text + ' ' * (self.cols-len(text)),
                           curses.color_pair(1))
        # move cursor to input line
        self.stdscr.move(self.rows-1, self.cols-1)

    def doRead(self):
        """ Input is ready! """
        curses.noecho()
        self.timer = self.timer + 1
        c = self.stdscr.getch() # read a character

        if c == curses.KEY_BACKSPACE:
            print "curses KEY_BACKSPACE"
            self.searchText = self.searchText[:-1]

        elif c == curses.KEY_ENTER or c == 10:
            self.addLine(self.searchText)
            # for testing too
            try: self.sendLine(self.searchText)
            except: pass
            self.stdscr.refresh()
            self.searchText = ''

        elif c == curses.KEY_RESIZE:
            print "curses KEY_RESIZE"
            self.rows, self.cols = self.stdscr.getmaxyx()
            self.redisplayLines()
            self.paintStatus(self.statusText)
            self.stdscr.refresh()

        elif c >= curses.KEY_MIN and c <= curses.KEY_MAX:
            return

        else:
            if len(self.searchText) >= self.cols-2:
                return
            self.searchText = self.searchText + chr(c)

        self.stdscr.addstr(self.rows-1, 0,
                           self.searchText + (' ' * (
                           self.cols-len(self.searchText)-2)))
        self.stdscr.move(self.rows-1, len(self.searchText))
        self.paintStatus(self.statusText + ' %d' % len(self.searchText))
        self.stdscr.refresh()

    def sendLine(self, txt):
        pass

    def close(self):
        """ clean up """

        curses.nocbreak()
        self.stdscr.keypad(0)
        curses.echo()
        curses.endwin()

def device_display():
    global stdscr
    try:
        import datetime
        now = datetime.datetime.now()
        str = now.date().isoformat() + " " + now.time().isoformat()
        stdscr.addstr(12, 25, "Time: %s" % str)
    except:
        pass
    stdscr.refresh()

if __name__ == '__main__':
    global stdscr
    from twisted.internet.task import LoopingCall
    from twisted.internet import reactor
    from twisted.python import log

    log.startLogging(open("/tmp/displayscreen.log", "w"))
    stdscr = curses.initscr()
    screen = Screen(stdscr)
    lc = LoopingCall(device_display)
    lc.start(0.250)
    reactor.addReader(screen) # add screen object as a reader to the reactor
    reactor.run()
