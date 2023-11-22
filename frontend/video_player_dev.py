import sys
import vlc
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap, QPainter
from PySide6.QtWidgets import (
    QApplication, QFrame, QPushButton, QSlider, QVBoxLayout,
    QHBoxLayout, QWidget, QFileDialog, QLabel, QGraphicsScene, QGraphicsView, QGraphicsPixmapItem, QDialog
)
import os

class SnapshotDialog(QDialog):
    def __init__(self, image_path):
        super().__init__()

        self.init_ui(image_path)

    def init_ui(self, image_path):
        self.setWindowTitle("Snapshot Viewer")

        self.image_label = QLabel(self)
        pixmap = QPixmap(image_path)
        self.image_label.setPixmap(pixmap)

        self.scene = QGraphicsScene()
        self.scene.addItem(QGraphicsPixmapItem(pixmap))

        self.view = QGraphicsView(self.scene)
        self.view.setRenderHint(QPainter.Antialiasing, True)

        layout = QVBoxLayout()
        layout.addWidget(self.view)
        self.setLayout(layout)

class VideoPlayer(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.Instance = vlc.Instance("--no-xlib")  # Use "--no-xlib" on macOS
        self.player = self.Instance.media_player_new()
        self.Media = None  # Initialize Media to None

        self.init_ui()

        self.last_snapshot_path = None  # Variable to store the most recent snapshot path

    def init_ui(self):
        self.vlcWidget = QFrame(self)
        self.vlcWidget.setFixedSize(1280, 720)

        self.play_button = QPushButton("Play", self)
        self.play_button.clicked.connect(self.toggle_play)
        self.play_button.setFixedSize(80, 30)  # Set a fixed size for the button

        self.snapshot_button = QPushButton("Take Snapshot", self)
        self.snapshot_button.clicked.connect(self.take_snapshot)
        self.snapshot_button.setFixedSize(120, 30)
        self.snapshot_button.setEnabled(False)  # Initially disabled

        self.open_snapshot_button = QPushButton("Open Last Snapshot", self)
        self.open_snapshot_button.clicked.connect(self.open_last_snapshot)
        self.open_snapshot_button.setFixedSize(150, 30)
        self.open_snapshot_button.setEnabled(False)  # Initially disabled

        self.progress_slider = QSlider(Qt.Horizontal, self)
        self.progress_slider.setRange(0, 100)  # Assuming the progress is in percentage
        self.progress_slider.sliderMoved.connect(self.set_position)

        self.upload_button = QPushButton("Upload Video", self)
        self.upload_button.clicked.connect(self.upload_video)
        self.upload_button.setFixedSize(100, 30)  # Set a fixed size for the button

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.play_button)
        button_layout.addWidget(self.snapshot_button)
        button_layout.addWidget(self.open_snapshot_button)
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
            self.snapshot_button.setEnabled(True)
            self.open_snapshot_button.setEnabled(True)
        else:
            self.player.play()
            self.play_button.setText("Pause")
            self.snapshot_button.setEnabled(False)
            self.open_snapshot_button.setEnabled(False)

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
            self.snapshot_button.setEnabled(True)

    def take_snapshot(self):
        if self.Media is not None:
            # Get the video size
            video_width, video_height = self.player.video_get_size()

            # Specify the directory to save the snapshot
            snapshot_directory = os.path.join(os.path.dirname(os.path.abspath(__file__)), "snapshots")

            # Take snapshot with the video's width and height
            video_frame = self.player.video_take_snapshot(0, snapshot_directory, video_width, video_height)

            if video_frame:
                image_path = video_frame.decode("utf-8")
                self.last_snapshot_path = image_path  # Store the most recent snapshot path
                snapshot_dialog = SnapshotDialog(image_path)
                snapshot_dialog.exec_()

    def open_last_snapshot(self):
        if self.last_snapshot_path:
            file_dialog = QFileDialog(self)
            file_dialog.setWindowTitle("Open Last Snapshot")
            file_dialog.setFileMode(QFileDialog.ExistingFile)
            file_dialog.setNameFilter("Image Files (*.png *.jpg *.bmp *.jpeg);;All Files (*)")

            if file_dialog.exec_() == QFileDialog.Accepted:
                selected_file = file_dialog.selectedFiles()[0]
                snapshot_dialog = SnapshotDialog(selected_file)
                snapshot_dialog.exec_()

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
