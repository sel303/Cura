# Copyright (c) 2017 Ultimaker B.V.
# Uranium is released under the terms of the AGPLv3 or higher.

from threading import Thread, Event
import time

from PyQt5.QtCore import Qt, QCoreApplication
from PyQt5.QtGui import QPixmap, QColor, QFont, QFontMetrics, QImage, QPen
from PyQt5.QtWidgets import QSplashScreen

from UM.Resources import Resources
from UM.Application import Application


class CuraSplashScreen(QSplashScreen):
    def __init__(self):
        super().__init__()
        self._scale = 0.7

        splash_image = QPixmap(Resources.getPath(Resources.Images, "cura.png"))
        self.setPixmap(splash_image)

        self._current_message = ""

        self._loading_image = QImage(Resources.getPath(Resources.Images, "loading.png"))
        self._loading_image = self._loading_image.scaled(30, 30, Qt.KeepAspectRatio)
        self._loading_image_rotation_angle = 0

        self._to_stop = False
        self._loading_tick_thread = LoadingTickThread(self)

    def show(self):
        super().show()
        self._loading_tick_thread.start()

    def updateLoadingImage(self):
        if self._to_stop:
            return

        self._loading_image_rotation_angle -= 10
        self.repaint()

    def drawContents(self, painter):
        if self._to_stop:
            return

        painter.save()
        painter.setPen(QColor(255, 255, 255, 255))

        version = Application.getInstance().getVersion().split("-")
        buildtype = Application.getInstance().getBuildType()
        if buildtype:
            version[0] += " (%s)" % buildtype

        # draw version text
        font = QFont()  # Using system-default font here
        font.setPointSize(34)
        painter.setFont(font)
        painter.drawText(275, 87, 330 * self._scale, 230 * self._scale, Qt.AlignLeft | Qt.AlignBottom, version[0])
        if len(version) > 1:
            font.setPointSize(12)
            painter.setFont(font)
            painter.drawText(320, 82, 330 * self._scale, 255 * self._scale, Qt.AlignLeft | Qt.AlignBottom, version[1])

        # draw the loading image
        pen = QPen()
        pen.setWidth(4 * self._scale)
        pen.setColor(QColor(255, 255, 255, 255))
        painter.setPen(pen)
        painter.drawArc(130, 380, 32 * self._scale, 32 * self._scale, self._loading_image_rotation_angle * 16, 300 * 16)

        # draw message text
        if self._current_message:
            font = QFont()  # Using system-default font here
            font.setPointSize(16)
            painter.setFont(font)
            painter.drawText(180, 243, 330 * self._scale, 230 * self._scale, Qt.AlignLeft | Qt.AlignBottom,
                             self._current_message)

        painter.restore()
        super().drawContents(painter)

    def showMessage(self, message, *args, **kwargs):
        if self._to_stop:
            return

        self._current_message = message
        self.messageChanged.emit(message)
        self.repaint()

    def close(self):
        # set stop flags
        self._to_stop = True
        self._loading_tick_thread.setToStop()
        super().close()


class LoadingTickThread(Thread):

    def __init__(self, splash):
        super().__init__(daemon = True)
        self._splash = splash
        self._to_stop = False
        self._time_interval = 0.05
        self._event = Event()

    def setToStop(self):
        self._to_stop = True
        self._event.set()

    def run(self):
        while not self._to_stop:
            self._event.wait(self._time_interval)
            if self._event.is_set():
                break

            self._splash.updateLoadingImage()
