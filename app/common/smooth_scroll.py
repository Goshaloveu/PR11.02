# coding:utf-8
from collections import deque
from enum import Enum
from math import cos, pi

from PyQt6.QtCore import QDateTime, Qt, QTimer, QPoint
from PyQt6.QtGui import QWheelEvent
from PyQt6.QtWidgets import QApplication, QScrollArea, QAbstractScrollArea


class SmoothScroll:
    """ Scroll smoothly """

    def __init__(self, widget: QScrollArea, orient=Qt.Vertical):
        """
        Parameters
        ----------
        widget: QScrollArea
            scroll area to scroll smoothly

        orient: Orientation
            scroll orientation
        """
        self.widget = widget
        self.orient = orient
        self.fps = 60
        self.duration = 400
        self.stepsTotal = 0
        self.stepRatio = 1.5
        self.acceleration = 1
        self.lastWheelEvent = None
        self.scrollStamps = deque()
        self.stepsLeftQueue = deque()
        self.smoothMoveTimer = QTimer(widget)
        self.smoothMode = SmoothMode.LINEAR
        self.smoothMoveTimer.timeout.connect(self.__smoothMove)

    def setSmoothMode(self, smoothMode):
        """ set smooth mode """
        self.smoothMode = smoothMode

    def wheelEvent(self, e):
        if self.smoothMode == SmoothMode.NO_SMOOTH or abs(e.angleDelta().y()) % 120 != 0:
            QAbstractScrollArea.wheelEvent(self.widget, e)
            return

        # push current time to queque
        now = QDateTime.currentDateTime().toMSecsSinceEpoch()
        self.scrollStamps.append(now)
        while now - self.scrollStamps[0] > 500:
            self.scrollStamps.popleft()

        # adjust the acceration ratio based on unprocessed events
        accerationRatio = min(len(self.scrollStamps) / 15, 1)
        if not self.lastWheelEvent:
            self.lastWheelEvent = QWheelEvent(e)
        else:
            self.lastWheelEvent = e

        # get the number of steps
        self.stepsTotal = self.fps * self.duration / 1000

        # get the moving distance corresponding to each event
        delta = e.angleDelta().y() * self.stepRatio
        if self.acceleration > 0:
            delta += delta * self.acceleration * accerationRatio

        # form a list of moving distances and steps, and insert it into the queue for processing.
        self.stepsLeftQueue.append([delta, self.stepsTotal])

        # overflow time of timer: 1000ms/frames
        self.smoothMoveTimer.start(1000 / self.fps)

    def __smoothMove(self):
        """ scroll smoothly when timer time out """
        totalDelta = 0

        # Calculate the scrolling distance of all unprocessed events,
        # the timer will reduce the number of steps by 1 each time it overflows.
        for i in self.stepsLeftQueue:
            totalDelta += self.__subDelta(i[0], i[1])
            i[1] -= 1

        # If the event has been processed, move it out of the queue
        while self.stepsLeftQueue and self.stepsLeftQueue[0][1] == 0:
            self.stepsLeftQueue.popleft()

        # construct wheel event
        if self.orient == Qt.Vertical:
            p = QPoint(0, totalDelta)
            bar = self.widget.verticalScrollBar()
        else:
            p = QPoint(totalDelta, 0)
            bar = self.widget.horizontalScrollBar()

        e = QWheelEvent(
            self.lastWheelEvent.pos(),
            self.lastWheelEvent.globalPos(),
            QPoint(),
            p,
            round(totalDelta),
            self.orient,
            self.lastWheelEvent.buttons(),
            Qt.NoModifier
        )

        # send wheel event to app
        QApplication.sendEvent(bar, e)

        # stop scrolling if the queque is empty
        if not self.stepsLeftQueue:
            self.smoothMoveTimer.stop()

    def __subDelta(self, delta, stepsLeft):
        """ get the interpolation for each step """
        m = self.stepsTotal / 2
        x = abs(self.stepsTotal - stepsLeft - m)

        res = 0
        if self.smoothMode == SmoothMode.NO_SMOOTH:
            res = 0
        elif self.smoothMode == SmoothMode.CONSTANT:
            res = delta / self.stepsTotal
        elif self.smoothMode == SmoothMode.LINEAR:
            res = 2 * delta / self.stepsTotal * (m - x) / m
        elif self.smoothMode == SmoothMode.QUADRATI:
            res = 3 / 4 / m * (1 - x * x / m / m) * delta
        elif self.smoothMode == SmoothMode.COSINE:
            res = (cos(x * pi / m) + 1) / (2 * m) * delta

        return res


class SmoothMode(Enum):
    """ Smooth mode """
    NO_SMOOTH = 0
    CONSTANT = 1
    LINEAR = 2
    QUADRATI = 3
    COSINE = 4

