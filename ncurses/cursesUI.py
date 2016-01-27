#!/usr/bin/env python
import curses
import curses.ascii
import curses.textpad
import os
import signal
import time
import datetime

from cursesInputDialog import CursesInputDialog
from cursesSendThread import CursesSendThread


class NcursesUI(object):
    def __init__(self, read_callback, write_callback):
        self.read_callback = read_callback
        self.write_callback = write_callback

    def start(self):
        curses.wrapper(self.run)

    def stop(self):
        if self.connectionManager is not None:
            self.connectionManager.disconnectFromServer()

        # Give the send thread time to get the disconnect messages out before
        # exiting and killing the thread
        time.sleep(.25)

        curses.endwin()

    def __restart(self):
        self.__drawUI()

        self.connectedNick = None
        self.inRecveiveLoop = False
        self.clientConnectError = False

        self.errorRaised.clear()
        self.postConnectToServer()

    def run(self, screen):
        self.screen = screen
        (self.height, self.width) = self.screen.getmaxyx()

        self.__drawUI()

        self.nick = ""

        self.sender = CursesSendThread(self, self.write_callback)
        self.sender.start()
        self.postConnectToServer()

    def __drawUI(self):
        # Change the colors, clear the screen and set the overall border
        self.__setColors()
        self.screen.clear()
        self.screen.border(0)

        # Create the chat log and chat input windows
        self.makeChatWindow()
        self.makeChatInputWindow()

    def postConnectToServer(self):
        self.__receiveMessageLoop()

    def postMessage(self, command, sourceNick, payload):
        self.messageQueue.put((command, sourceNick, payload))

    def __receiveMessageLoop(self):
        self.inRecveiveLoop = True

        while True:
            # Keyboard interrupts are ignored unless a timeout is specified
            # See http://bugs.python.org/issue1360
            message = self.read_callback()

            if message is not None:
                self.appendMessagePrime(message)
            time.sleep(0.1)

    def appendMessagePrime(self, message):
        prefix = "(%s): " % (datetime.datetime.fromtimestamp(time.time(
        )).strftime('%Y-%m-%d %H:%M:%S'))
        self.appendMessage(prefix, message, curses.color_pair(2))

    def appendMessage(self, prefix, message, color):
        (height, width) = self.chatWindow.getmaxyx()

        # Put the received data in the chat window
        try:
            self.chatWindow.scroll(1)
            self.chatWindow.addstr(height - 1, 0, prefix, color)
            self.chatWindow.addstr(height - 1, len(prefix), message)
        except TypeError as e:
            print("STARTING ERROR MESSAGE")
            print(repr(message))
            print(e)

        # Move the cursor back to the chat input window
        # self.textboxWindow.move(0, 0)

        self.chatWindow.refresh()
        self.textboxWindow.refresh()

    def __startSendThread(self):
        # Add a hint on how to display the options menu
        self.screen.addstr(0, 5, "Ctrl+U for options")
        self.screen.refresh()

        # Show the now chatting message
        self.appendMessage('', "Now chatting with %s" % self.connectedNick,
                           curses.color_pair(0))

        self.sendThread = CursesSendThread(self)
        self.sendThread.start()

    def clientReady(self, nick):
        self.connectedNick = nick
        self.statusWindow.setText(nick)

        self.clientConnected.acquire()
        self.clientConnected.notify()
        self.clientConnected.release()

    def setSmpAnswer(self, answer):
        self.connectionManager.respondSMP(self.connectedNick, answer)

    def __handleClientConnectingError(self):
        self.clientConnectError = True
        self.clientConnected.acquire()
        self.clientConnected.notify()
        self.clientConnected.release()

    def __setColors(self):
        if curses.has_colors():
            curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)
            curses.init_pair(2, curses.COLOR_RED, curses.COLOR_BLACK)
            curses.init_pair(3, curses.COLOR_CYAN, curses.COLOR_BLACK)
            curses.init_pair(4, curses.COLOR_BLACK, curses.COLOR_GREEN)
            self.screen.bkgd(curses.color_pair(1))

    def makeChatWindow(self):
        self.chatWindow = self.screen.subwin(self.height - 4, self.width - 2,
                                             1, 1)
        self.chatWindow.scrollok(True)

    def makeChatInputWindow(self):
        self.textboxWindow = self.screen.subwin(1, self.width - 36,
                                                self.height - 2, 1)

        self.textbox = curses.textpad.Textbox(self.textboxWindow,
                                              insert_mode=True)
        curses.textpad.rectangle(self.screen, self.height - 3, 0,
                                 self.height - 1, self.width - 35)
        self.textboxWindow.move(0, 0)

    def showOptionsMenuWindow(self):
        numMenuEntires = 5
        menuWindow = self.screen.subwin(numMenuEntires + 2, 34, 3,
                                        self.width / 2 - 14)

        # Enable arrow key detection for this window
        menuWindow.keypad(True)

        pos = 1

        while True:
            # Redraw the border on each loop in case something is shown on top
            # of this window
            menuWindow.border(0)

            # Disable the cursor
            curses.curs_set(0)

            while True:
                item = 1
                menuWindow.addstr(item, 1, str(item) + ".| End current chat ",
                                  curses.color_pair(4) if pos == item else
                                  curses.color_pair(1))
                item += 1
                menuWindow.addstr(item, 1, str(item) + ".| Authenticate chat",
                                  curses.color_pair(4) if pos == item else
                                  curses.color_pair(1))
                item += 1
                menuWindow.addstr(item, 1, str(item) + ".| Show help        ",
                                  curses.color_pair(4) if pos == item else
                                  curses.color_pair(1))
                item += 1
                menuWindow.addstr(item, 1, str(item) + ".| Close menu       ",
                                  curses.color_pair(4) if pos == item else
                                  curses.color_pair(1))
                item += 1
                menuWindow.addstr(item, 1, str(item) + ".| Quit application ",
                                  curses.color_pair(4) if pos == item else
                                  curses.color_pair(1))

                menuWindow.refresh()
                key = menuWindow.getch()
                if key == curses.KEY_DOWN and pos < numMenuEntires:
                    pos += 1
                elif key == curses.KEY_UP and pos > 1:
                    pos -= 1
                # Wrap around from top of menu
                elif key == curses.KEY_UP and pos == 1:
                    pos = numMenuEntires
                # Wrap around from bottom of menu
                elif key == curses.KEY_DOWN and pos == numMenuEntires:
                    pos = 1
                # Enter key
                elif key == ord('\n'):
                    break

            # Process the selected option
            if pos == 1:
                self.connectionManager.closeChat(self.connectedNick)
                menuWindow.clear()
                menuWindow.refresh()
                self.__restart()
            elif pos == 2:
                if self.connectionManager is None:
                    return

                question = CursesInputDialog(self.screen, "Question: ").show()
                answer = CursesInputDialog(self.screen,
                                           "Answer (case senstitive): ").show()

                self.connectionManager.getClient(
                    self.connectedNick).initiateSMP(question, answer)
            elif pos == 3:
                pass
            elif pos == 4:
                # Move the cursor back to the chat input textbox
                self.textboxWindow.move(0, 0)
                break
            elif pos == 5:
                os.kill(os.getpid(), signal.SIGINT)

        # Re-enable the cursor
        curses.curs_set(2)

        # Get rid of the accept window
        menuWindow.clear()
        menuWindow.refresh()

    def __quitApp(self):
        os.kill(os.getpid(), signal.SIGINT)


if __name__ == "__main__":
    ui = NcursesUI()  # add in callbacks here
    ui.start()
