import sys
from PySide6.QtWidgets import QApplication, QWidget, QComboBox, QVBoxLayout, QLabel, QHBoxLayout, QPushButton, QSlider, QFileDialog, QTextEdit
from PySide6.QtMultimediaWidgets import QVideoWidget
from PySide6.QtMultimedia import QMediaPlayer
from PySide6.QtCore import Qt, QUrl, QSize, QPoint
from PySide6.QtGui import QPainter, QPolygon, QColor, QPen, QPalette, QColor, QImage, QPixmap
import cv2
import numpy as np  
import locale
import tempfile
from colormaps import colormaps

locale.setlocale(locale.LC_ALL, 'da_DK')

class InfoWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.textEdit = QTextEdit()

        layout = QVBoxLayout()
        layout.addWidget(self.textEdit)
        self.setLayout(layout)

    def update_info(self, pixel_sum_total, pixel_sum_masked):
        info_text = f"Total Pixel Sum: {locale.format_string('%d', pixel_sum_total, grouping=True).replace(',', '.')}\n"
        info_text += f"Masked Area Pixel Sum: {locale.format_string('%d', pixel_sum_masked, grouping=True).replace(',', '.')}\n"
        self.textEdit.setText(info_text)


class FloatingOverlay(QWidget):
    def __init__(self, video_widget, parent=None):
        super().__init__(parent, Qt.Window | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.video_widget = video_widget  # Reference to the video widget
        self.setPalette(QPalette(QColor(0, 0, 0, 0)))  # Semi-transparent
        self.setAutoFillBackground(True)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)  # Click-through

        self.click_positions = []
        self.relative_click_positions = []  # Store relative positions

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            if self.isClickWithinVideoArea(event.pos()) and self.video_widget.sizeHint().width() > -1:
                self.click_positions.append(event.pos())

                # Calculate and store the relative position
                relative_x, relative_y = self.getRelativePosition(event.pos())
                self.relative_click_positions.append((relative_x, relative_y))

                self.update()  # Request a repaint

    def getAspectRatios(self):
        widget_width = self.video_widget.width()
        widget_height = self.video_widget.height()
        widget_aspect_ratio = widget_width / widget_height

        video_width = self.video_widget.sizeHint().width()
        video_height = self.video_widget.sizeHint().height()

        video_aspect_ratio = video_width / video_height

        return widget_aspect_ratio, video_aspect_ratio

    def getRelativePosition(self, position):
        widget_width = self.video_widget.width()
        widget_height = self.video_widget.height()

        widget_aspect_ratio, video_aspect_ratio = self.getAspectRatios()

        if widget_aspect_ratio > video_aspect_ratio:
            display_width = widget_height * video_aspect_ratio
            offset_x = (widget_width - display_width) / 2
            return (position.x() - offset_x) / display_width, position.y() / widget_height
        else:
            display_height = widget_width / video_aspect_ratio
            offset_y = (widget_height - display_height) / 2
            return position.x() / widget_width, (position.y() - offset_y) / display_height

    def isClickWithinVideoArea(self, position):
        widget_width = self.video_widget.width()
        widget_height = self.video_widget.height()

        widget_aspect_ratio, video_aspect_ratio = self.getAspectRatios()

        if widget_aspect_ratio > video_aspect_ratio:
            display_width = widget_height * video_aspect_ratio
            offset_x = (widget_width - display_width) / 2
            return offset_x <= position.x() <= widget_width - offset_x
        else:
            display_height = widget_width / video_aspect_ratio
            offset_y = (widget_height - display_height) / 2
            return offset_y <= position.y() <= widget_height - offset_y


    def updateClickPositions(self):
        self.click_positions.clear()
        widget_width = self.video_widget.width()
        widget_height = self.video_widget.height()

        widget_aspect_ratio, video_aspect_ratio = self.getAspectRatios()

        # Determine the actual video display area
        if widget_aspect_ratio > video_aspect_ratio:
            display_height = widget_height
            display_width = display_height * video_aspect_ratio
            offset_x = (widget_width - display_width) / 2
            offset_y = 0
        else:
            display_width = widget_width
            display_height = display_width / video_aspect_ratio
            offset_x = 0
            offset_y = (widget_height - display_height) / 2

        for rel_pos in self.relative_click_positions:
            new_x = rel_pos[0] * display_width + offset_x
            new_y = rel_pos[1] * display_height + offset_y
            self.click_positions.append(QPoint(new_x, new_y))

        self.update() 


    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        if self.click_positions:
            # Draw the polygon
            pen = QPen(QColor(255, 0, 0), 2)  # Red color, 2px thick
            painter.setPen(pen)
            polygon = QPolygon(self.click_positions)
            painter.drawPolygon(polygon)

    def clear_mask(self):
        self.click_positions.clear()
        self.relative_click_positions.clear()
        self.update()


class VideoPlayer(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.player = QMediaPlayer()

        self.videoWidget = QVideoWidget(self)
        self.videoWidget.setMinimumSize(QSize(1, 1))

        self.overlay = FloatingOverlay(self.videoWidget)  # Pass the video widget reference
        self.overlay.show()

        self.infoWidget = InfoWidget()

        self.play_button = QPushButton("Play")
        self.play_button.clicked.connect(self.toggle_play)

        self.progress_slider = QSlider(Qt.Horizontal)
        self.progress_slider.sliderMoved.connect(self.set_position)

        self.upload_button = QPushButton("Upload Video")
        self.upload_button.clicked.connect(self.upload_video)

        self.clear_mask_button = QPushButton("Clear Mask")
        self.clear_mask_button.clicked.connect(self.clear_mask)

        self.update_info_button = QPushButton("Update Info")
        self.update_info_button.clicked.connect(self.update_info)

        self.dropdown_menu = QComboBox()
        self.dropdown_menu.addItems(colormaps.keys()) 
        self.dropdown_menu.setCurrentIndex(2)

        # Create a layout for the dropdown and upload button
        upload_layout = QHBoxLayout()
        upload_layout.addWidget(self.dropdown_menu)
        upload_layout.addWidget(self.upload_button)

        self.heatmap_scale_label = QLabel(self)

        videoLayout = QHBoxLayout()
        videoLayout.addWidget(self.videoWidget, 6)
        videoLayout.addWidget(self.heatmap_scale_label, 1)
        # Use the upload_layout instead of adding the upload_button directly
        vlayout = QVBoxLayout()
        vlayout.addLayout(videoLayout)
        vlayout.addWidget(self.play_button)
        vlayout.addWidget(self.progress_slider)
        vlayout.addLayout(upload_layout)  # Add the combined layout of dropdown and button
        vlayout.addWidget(self.clear_mask_button)
        vlayout.addWidget(self.update_info_button)

        hlayout = QHBoxLayout()
        hlayout.addLayout(vlayout, 3)
        hlayout.addWidget(self.infoWidget, 1)

        self.setLayout(hlayout)

        self.player.setVideoOutput(self.videoWidget)

        self.polygon_mask = []

    def update_info(self):
        if self.original_file_path:
            time_in_ms = self.player.position()

            cap = cv2.VideoCapture(self.original_file_path, 0)

            if not cap.isOpened():
                print("Error: Unable to open video")
                return

            cap.set(cv2.CAP_PROP_POS_MSEC, time_in_ms)

            ret, frame = cap.read()

            if not ret:
                print("Error: Unable to read the frame")
                cap.release()
                return
            
            if len(self.overlay.relative_click_positions) == 0:
                pixel_sum_masked = 0
            else:
                height, width = frame.shape[:2]

                # Get relative click positions and convert them to absolute positions
                relative_positions = self.overlay.relative_click_positions
                absolute_positions = [(int(x * width), int(y * height)) for x, y in relative_positions]

                # Create a mask with the same dimensions as the frame
                mask = np.zeros(frame.shape, dtype=np.uint8)

                # Define a polygon with the absolute positions
                polygon = np.array(absolute_positions, np.int32)
                cv2.fillPoly(mask, [polygon], (255, 255, 255))

                masked_frame = cv2.bitwise_and(frame, mask)

                pixel_sum_masked = masked_frame.sum() / 1000

            pixel_sum = frame.sum() / 1000

            cap.release()

            self.infoWidget.update_info(pixel_sum, pixel_sum_masked)

    def showEvent(self, event):
        super().showEvent(event)
        self.updateOverlayGeometry()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.updateOverlayGeometry()
        self.overlay.updateClickPositions()

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
        new_position = position / 100 * self.player.duration()
        self.player.setPosition(new_position)

    def preprocess_frame(self, frame, upscale_factor):
        # Convert frame to grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Apply the JET colormap
        processed_frame = cv2.applyColorMap(gray, colormaps[self.dropdown_menu.currentText()])

        # Determine the new dimensions
        new_width = int(processed_frame.shape[1] * upscale_factor)
        new_height = int(processed_frame.shape[0] * upscale_factor)
        new_dimensions = (new_width, new_height)

        # Upscale the image
        upscaled_frame = cv2.resize(processed_frame, new_dimensions, interpolation=cv2.INTER_NEAREST)

        return upscaled_frame


    def preprocess_video(self, input_path, output_path, upscale_factor=20):
        # Open the video file
        cap = cv2.VideoCapture(input_path)

        # Get properties of the video
        codec = int(cap.get(cv2.CAP_PROP_FOURCC))  # Codec of the video
        frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)*upscale_factor)  # Width of the frames
        frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)*upscale_factor)  # Height of the frames
        frame_rate = cap.get(cv2.CAP_PROP_FPS)  # Frame rate

        # Define the codec and create VideoWriter object
        out = cv2.VideoWriter(output_path, codec, frame_rate, (frame_width, frame_height))

        while cap.isOpened():
            ret, frame = cap.read()
            if ret:
                # Apply heatmap to the frame
                processed_frame = self.preprocess_frame(frame, upscale_factor)

                # Write the processed frame
                out.write(processed_frame)
            else:
                break

        # Release everything
        cap.release()
        out.release()

    def create_heatmap_scale(self):
        # Number of discrete colors and colorbar dimensions
        num_colors = 256
        bar_width = 50
        bar_height = 500

        # Create an image with a vertical gradient
        gradient = np.linspace(1, 0, num_colors).reshape(num_colors, 1)
        gradient = np.repeat(gradient, bar_width, axis=1)
        gradient = cv2.resize(gradient, (bar_width, bar_height), interpolation=cv2.INTER_LINEAR)
        gradient = (255 * gradient).astype(np.uint8)

        colorbar_img = cv2.applyColorMap(gradient, colormaps[self.dropdown_menu.currentText()])

        # Create a white canvas for the labels
        label_width = 100
        full_img = 255 * np.ones((bar_height+label_width, bar_width + label_width, 3), dtype=np.uint8)
        full_img[50:50+bar_height, :bar_width, :] = colorbar_img

        # Add labels
        step = int(bar_height / 10)
        value_range = np.linspace(255 / 50, 0, bar_height+1)
        for i in range(0, bar_height+step, step):
            value = value_range[i]
            text = f"{value:.2f}"
            cv2.putText(full_img, text, (bar_width + 10, i + 55), cv2.FONT_HERSHEY_DUPLEX, 0.5, (0, 0, 0), 1, cv2.LINE_AA)

        return full_img
    
    def convert_cv_qt(self, cv_img):
        """Convert from an opencv image to QPixmap"""
        rgb_image = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        convert_to_Qt_format = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
        return QPixmap.fromImage(convert_to_Qt_format)


    def upload_video(self):
        file_dialog = QFileDialog(self)
        file_dialog.setNameFilter("Video Files (*.avi)")
        file_dialog.setFileMode(QFileDialog.ExistingFile)

        if file_dialog.exec_() == QFileDialog.Accepted:
            self.original_file_path = file_dialog.selectedFiles()[0]

            # Create a temporary file for the processed video
            with tempfile.NamedTemporaryFile(delete=False, suffix='.avi') as temp_file:
                processed_file_path = temp_file.name

            # Process the video
            self.preprocess_video(self.original_file_path, processed_file_path)

            # Set the processed video as the source
            self.player.setSource(QUrl.fromLocalFile(processed_file_path))
            self.player.pause()

        heatmap_scale_image = self.create_heatmap_scale()
        self.heatmap_scale_label.setPixmap(self.convert_cv_qt(heatmap_scale_image))


    def clear_mask(self):
        self.overlay.clear_mask()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    player = VideoPlayer()
    player.show()

    sys.exit(app.exec_())