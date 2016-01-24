import curses
import threading


class CursesSendThread(threading.Thread):
    def __init__(self, ncurses, callback):
        threading.Thread.__init__(self)
        self.callback = callback
        self.daemon = True

        self.ncurses = ncurses
        self.stop = threading.Event()
        self.smpRequested = threading.Event()

    def run(self):
        (height, width) = self.ncurses.chatWindow.getmaxyx()
        self.ncurses.textboxWindow.move(0, 0)

        while True:
            message = self.ncurses.textbox.edit(self.inputValidator)[:-1]
            self.ncurses.screen.refresh()

            self.__sendMessageToClient(message)
            self.callback(message)
            self.__clearChatInput()

    def inputValidator(self, char):
        if char == 21:  # Ctrl+U
            self.__clearChatInput()
        elif char == curses.KEY_HOME:
            return curses.ascii.SOH
        elif char == curses.KEY_END:
            return curses.ascii.ENQ
        elif char == curses.KEY_ENTER or char == ord('\n'):
            return curses.ascii.BEL
        else:
            return char

    def __clearChatInput(self):
        self.ncurses.textboxWindow.deleteln()
        self.ncurses.textboxWindow.move(0, 0)
        self.ncurses.textboxWindow.deleteln()

    def __sendMessageToClient(self, message):
        self.ncurses.appendMessagePrime(message)
