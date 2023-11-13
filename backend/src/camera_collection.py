from typing import List, Tuple
import numpy as np
import cv2
from datetime import datetime

from src.camera import Camera  
from src.camera_utils import CameraUtils  


class CameraCollection:
  def __init__(self, cameras: List[Camera], camera_utils: CameraUtils) -> None:
    self.cameras: List[Camera] = cameras
    self.camera_utils: CameraUtils = camera_utils

  def combine_images_to_video(self, fps: int = 30) -> None:
    def get_output_frame_size(cameras: List[Camera]) -> Tuple[int, int]:
      """Calculate the size of the output frame based on the global coordinates."""
      max_width = 0
      max_height = 0

      for cam in cameras:
          for coord in cam.global_coordinates:
              max_width = max(max_width, coord[0])
              max_height = max(max_height, coord[1])

      return max_width * self.camera_utils.upsampling_factor, max_height * self.camera_utils.upsampling_factor

    def overlay_image(large_image: np.ndarray, small_image: np.ndarray, coordinates: List[Tuple[int, int]]) -> np.ndarray:
      """Overlay small_image onto large_image at the given coordinates."""
      x_coords = [c[0] for c in coordinates]
      y_coords = [c[1] for c in coordinates]
      x_min, x_max = min(x_coords) * self.camera_utils.upsampling_factor, max(x_coords) * self.camera_utils.upsampling_factor
      y_min, y_max = min(y_coords) * self.camera_utils.upsampling_factor, max(y_coords) * self.camera_utils.upsampling_factor

      large_image[y_min:y_max, x_min:x_max] = cv2.resize(small_image, (x_max - x_min, y_max - y_min))

      return large_image

    frame_size = get_output_frame_size(self.cameras)
    time_str = datetime.now().strftime('%H:%M')
    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    file_path = f"{self.camera_utils.output_dir}output_video_{time_str}.avi"
    out = cv2.VideoWriter(file_path, fourcc, fps, frame_size)

    for frame_idx in range(len(self.cameras[0].images)):
        base_frame = np.zeros((frame_size[1], frame_size[0], 3), dtype=np.uint8)

        for cam in self.cameras:
            image = cam.images[frame_idx]
            base_frame = overlay_image(base_frame, image, cam.global_coordinates)

        out.write(base_frame)

    out.release()
    print("Finished writing to ", file_path)

  def generate_report(self) -> None:
    for camera in self.cameras:
      camera.predict()

    self.combine_images_to_video()