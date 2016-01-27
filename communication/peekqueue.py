#!/usr/bin/env python
from Queue import Queue

# Subclass of Queue which allows peeking of the next value.


class PeekQueue(Queue):

    # returns the current head of the queue without modifying it.
    def peek(self):
        try:
            return self.queue[0]
        except IndexError:
            return None
