import sys
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QSlider, QFileDialog, QLabel, QStackedLayout
from PySide6.QtMultimediaWidgets import QVideoWidget
from PySide6.QtMultimedia import QMediaPlayer
from PySide6.QtCore import Qt, QUrl, QSize
from PySide6.QtGui import QPainter, QPolygon, QColor, QPen, QPalette, QColor, QFont

class FloatingOverlay(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent, Qt.Window | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setPalette(QPalette(QColor(0, 0, 0, 0)))  # Semi-transparent
        self.setAutoFillBackground(True)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)  # Click-through

        self.click_positions = []

    def resizeEvent(self, event):
        super().resizeEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.click_positions.append(event.pos())
            print(f"Clicked at: {event.pos()}")  # For debugging
            self.update()  # Request a repaint

    def paintEvent(self, event):
        super().paintEvent(event)  # Call the base class paint event
        painter = QPainter(self)
        if self.click_positions:
            # Draw the polygon
            pen = QPen(QColor(255, 0, 0), 2)  # Red color, 2px thick
            painter.setPen(pen)
            polygon = QPolygon(self.click_positions)
            painter.drawPolygon(polygon)

    def clearPolygon(self):
        self.click_positions.clear()
        self.update()


class VideoPlayer(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.player = QMediaPlayer()
        self.videoWidget = QVideoWidget(self)
        self.videoWidget.setMinimumSize(QSize(1, 1))

        self.overlay = FloatingOverlay()
        self.overlay.show()

        self.play_button = QPushButton("Play")
        self.play_button.clicked.connect(self.toggle_play)

        self.progress_slider = QSlider(Qt.Horizontal)
        self.progress_slider.sliderMoved.connect(self.set_position)

        self.upload_button = QPushButton("Upload Video")
        self.upload_button.clicked.connect(self.upload_video)

        self.set_mask_button = QPushButton("Set Mask")
        self.set_mask_button.clicked.connect(self.set_mask)

        layout = QVBoxLayout()

        layout.addWidget(self.videoWidget)
        layout.addWidget(self.play_button)
        layout.addWidget(self.progress_slider)
        layout.addWidget(self.upload_button)
        layout.addWidget(self.set_mask_button)

        self.setLayout(layout)

        self.player.setVideoOutput(self.videoWidget)

        self.polygon_mask = []

    def showEvent(self, event):
        super().showEvent(event)
        self.updateOverlayGeometry()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.updateOverlayGeometry()

    def moveEvent(self, event):
        super().moveEvent(event)
        self.updateOverlayGeometry()

    def closeEvent(self, event):
        self.overlay.close()  # Close the overlay when VideoPlayer is closed
        super().closeEvent(event)  # Continue with the normal closing process

    def updateOverlayGeometry(self):
        video_geometry = self.videoWidget.geometry()
        global_position = self.videoWidget.mapToGlobal(video_geometry.topLeft())

        self.overlay.setGeometry(global_position.x()-video_geometry.x(), global_position.y()-video_geometry.y(), video_geometry.width(), video_geometry.height())

    def toggle_play(self):
        if self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.player.pause()
            self.play_button.setText("Play")
        else:
            self.player.play()
            self.play_button.setText("Pause")

    def set_position(self, position):
        self.player.setPosition(position)

    def upload_video(self):
        file_dialog = QFileDialog(self)
        file_dialog.setNameFilter("Video Files (*.mp4 *.avi *.mkv)")
        file_dialog.setFileMode(QFileDialog.ExistingFile)

        if file_dialog.exec_() == QFileDialog.Accepted:
            file_path = file_dialog.selectedFiles()[0]
            self.player.setSource(QUrl.fromLocalFile(file_path))
            self.player.play()

    def set_mask(self):
        # Assuming video resolution is needed to calculate relative positions
        video_size = self.videoWidget.sizeHint()
        if video_size.isValid():
            original_width, original_height = video_size.width(), video_size.height()
            for pos in self.videoWidget.click_positions:
                relative_x = pos.x() / self.videoWidget.width() * original_width
                relative_y = pos.y() / self.videoWidget.height() * original_height

                print(f"Relative Position: ({relative_x}, {relative_y})")  # For debugging
                self.polygon_mask.append((relative_x, relative_y))

        self.videoWidget.clearPolygon()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    player = VideoPlayer()
    player.show()
    sys.exit(app.exec_())