import sys
import vlc
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap, QPainter
from PySide6.QtWidgets import (
    QApplication, QFrame, QPushButton, QSlider, QVBoxLayout,
    QHBoxLayout, QWidget, QFileDialog, QLabel, QGraphicsScene, QGraphicsView, QGraphicsPixmapItem, QDialog
)
import os

class VideoPlayer(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.Instance = vlc.Instance("--no-xlib")  # Use "--no-xlib" on macOS
        self.player = self.Instance.media_player_new()
        self.Media = None  # Initialize Media to None

        self.init_ui()

        self.polygon_mask = []

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self.vlcWidget.geometry().contains(event.pos()):
            x, y = event.x(), event.y()
            widget_top_left = self.vlcWidget.geometry().topLeft()
            self.polygon_mask.append((x - widget_top_left.x(), y - widget_top_left.y()))

    def init_ui(self):
        self.vlcWidget = QFrame(self)
        self.vlcWidget.setFixedSize(1280, 720)

        self.play_button = QPushButton("Play", self)
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

        self.setLayout(layout)

        self.player.set_nsobject(self.vlcWidget.winId())
        self.timer = self.startTimer(200)  # Update every 200 milliseconds

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
