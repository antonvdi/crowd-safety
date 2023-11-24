import sys
import vlc
from PySide6.QtCore import Qt, QPoint, QPointF
from PySide6.QtGui import QPixmap, QPainter, QPolygon, QPen, QColor, QBrush
from PySide6.QtWidgets import (
    QApplication, QFrame, QPushButton, QSlider, QVBoxLayout,
    QHBoxLayout, QWidget, QFileDialog, QLabel, QGraphicsScene, QGraphicsView, QGraphicsPixmapItem, QDialog, QGraphicsPolygonItem
)
import cv2
import numpy as np

class DrawingWidget(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.polygon = []
        self.polygon_obj = []

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            x, y = event.position().toTuple()
            self.polygon.append((x, y))
            self.polygon_obj.append(QPointF(x, y))
            self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setPen(Qt.white)

        if len(self.polygon_obj) < 2:
            return

        for i in range(len(self.polygon_obj)):
            if i + 1 == len(self.polygon_obj):
                painter.drawLine(self.polygon_obj[i], self.polygon_obj[0])
                continue

            painter.drawLine(self.polygon_obj[i], self.polygon_obj[i + 1])

class VideoPlayer(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.Instance = vlc.Instance("--no-xlib")  # Use "--no-xlib" on macOS
        self.player = self.Instance.media_player_new()
        self.player_size = (1280, 720)
        self.Media = None  # Initialize Media to None

        self.init_ui()

    def init_ui(self):
        self.vlcWidget = QFrame(self)
        self.vlcWidget.setFixedSize(self.player_size[0], self.player_size[1])

        vlcLayout = QVBoxLayout(self.vlcWidget)  # Use QVBoxLayout or QHBoxLayout as needed
        vlcLayout.setContentsMargins(0, 0, 0, 0)  # Optional: remove margins if desired

        self.drawingWidget = DrawingWidget(self.vlcWidget)
        vlcLayout.addWidget(self.drawingWidget)

        self.play_button = QPushButton("Pause", self)
        self.play_button.clicked.connect(self.toggle_play)
        self.play_button.setFixedSize(80, 30)  # Set a fixed size for the button

        self.progress_slider = QSlider(Qt.Horizontal, self)
        self.progress_slider.setRange(0, 100)  # Assuming the progress is in percentage
        self.progress_slider.sliderMoved.connect(self.set_position)

        self.upload_button = QPushButton("Upload Video", self)
        self.upload_button.clicked.connect(self.upload_video)
        self.upload_button.setFixedSize(100, 30)  # Set a fixed size for the button

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.play_button)
        button_layout.addWidget(self.upload_button)
        button_layout.addStretch(1)  # Add stretch to move buttons to the left

        layout = QVBoxLayout()
        layout.addWidget(self.vlcWidget)
        layout.addLayout(button_layout)
        layout.addWidget(self.progress_slider)

        self.set_mask_button = QPushButton("Set Mask", self)
        self.set_mask_button.clicked.connect(self.set_mask)
        self.set_mask_button.setFixedSize(100, 30)
        button_layout.addWidget(self.set_mask_button)

        self.setLayout(layout)

        self.player.set_nsobject(self.vlcWidget.winId())
        self.timer = self.startTimer(200)  # Update every 200 milliseconds

    def set_mask(self):
        if not self.Media:
            return  # No video loaded
        
        video_path = self.Media.get_mrl()
        cap = cv2.VideoCapture(video_path)

        frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        original_aspect_ratio = frame_width / frame_height
        fixed_aspect_ratio = self.player_size[0] / self.player_size[1]
        if original_aspect_ratio > fixed_aspect_ratio:
            # Video is wider than 1280x720, letterboxing
            scale_width = frame_width / self.player_size[0]
            scale_height = scale_width
            vertical_offset = (self.player_size[1] - (frame_height / scale_height)) / 2
            horizontal_offset = 0
        else:
            # Video is taller than 1280x720, pillarboxing
            scale_height = frame_height / self.player_size[1]
            scale_width = scale_height
            horizontal_offset = (self.player_size[0] - (frame_width / scale_width)) / 2
            vertical_offset = 0

        widget_top_left = self.vlcWidget.geometry().topLeft()
        horizontal_offset +=  widget_top_left.x()
        vertical_offset +=  widget_top_left.y()

        scaled_polygon_mask = [
            (int((x - horizontal_offset) * scale_width), int((y - vertical_offset) * scale_height))
            for x, y in self.polygon
        ]

        mask = np.zeros((frame_height, frame_width), np.uint8)
        pts = np.array(scaled_polygon_mask, np.int32)
        cv2.fillPoly(mask, [pts], 255)

        self.poly_mask = mask
        #masked_frame = cv2.bitwise_and(frame, frame, mask=mask)

    def toggle_play(self):
        if self.player.is_playing():
            self.player.pause()
            self.play_button.setText("Play")
        else:
            self.player.play()
            self.play_button.setText("Pause")

    def set_position(self, position):
        self.player.set_position(position / 100.0)

    def upload_video(self):
        file_dialog = QFileDialog(self)
        file_dialog.setNameFilter("MP4 Files (*.mp4)")
        file_dialog.setFileMode(QFileDialog.ExistingFile)

        if file_dialog.exec_() == QFileDialog.Accepted:
            file_path = file_dialog.selectedFiles()[0]
            self.Media = self.Instance.media_new(file_path)  # Set the MRL during the upload
            self.player.set_media(self.Media)
            self.player.play()
            
    def timerEvent(self, event):
        # Update the progress bar based on the current position of the video
        if not self.player.get_length():
            return

        position = self.player.get_position()
        self.progress_slider.setValue(int(position * 100))

if __name__ == '__main__':
    app = QApplication(sys.argv)
    player = VideoPlayer()
    player.show()
    sys.exit(app.exec_())
