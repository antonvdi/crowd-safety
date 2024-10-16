import numpy as np
import cv2

class CameraUtils:
  def __init__(self, heatmap_alpha: int, output_dir: str, upsampling_factor: int, color_map: int) -> None:
    self.heatmap_alpha: int = heatmap_alpha
    self.output_dir: str = output_dir
    self.upsampling_factor: int = upsampling_factor
    self.color_map: int = color_map

  def correct_fisheye_distortion(self, image: np.ndarray, distortionParameter: float) -> np.ndarray:
    h, w = image.shape[:2]

    camera_matrix = np.array([[w / 2.0, 0, w / 2.0],
                              [0, w / 2.0, h / 2.0],
                              [0, 0, 1]], dtype=np.float32)

    dist_coeffs = np.array([distortionParameter, 0, 0, 0, 0], dtype=np.float32)

    corrected_image = cv2.undistort(image, camera_matrix, dist_coeffs)

    return corrected_image

  def correct_perspective(self, matrix: np.ndarray, corner_matrix: np.ndarray) -> np.ndarray:
    pt_A = corner_matrix[0]
    pt_B = corner_matrix[1]
    pt_C = corner_matrix[2]
    pt_D = corner_matrix[3]

    width_AD = np.sqrt(((pt_A[0] - pt_D[0]) ** 2) + ((pt_A[1] - pt_D[1]) ** 2))
    width_BC = np.sqrt(((pt_B[0] - pt_C[0]) ** 2) + ((pt_B[1] - pt_C[1]) ** 2))
    maxWidth = max(int(width_AD), int(width_BC))


    height_AB = np.sqrt(((pt_A[0] - pt_B[0]) ** 2) + ((pt_A[1] - pt_B[1]) ** 2))
    height_CD = np.sqrt(((pt_C[0] - pt_D[0]) ** 2) + ((pt_C[1] - pt_D[1]) ** 2))
    maxHeight = max(int(height_AB), int(height_CD))

    input_pts = np.float32([pt_A, pt_B, pt_C, pt_D])
    output_pts = np.float32([[0, 0],
                            [0, maxHeight - 1],
                            [maxWidth - 1, maxHeight - 1],
                            [maxWidth - 1, 0]])

    # Compute the perspective transform M
    M = cv2.getPerspectiveTransform(input_pts,output_pts)

    out = cv2.warpPerspective(matrix,M,(maxWidth, maxHeight),flags=cv2.INTER_LINEAR)

    return out

  def downsample_image(self, matrix: np.ndarray, scale_factor: int) -> np.ndarray:
    # Calculate the dimensions of the downscaled array with padding
    new_height = matrix.shape[0] // scale_factor + (matrix.shape[0] % scale_factor > 0)
    new_width = matrix.shape[1] // scale_factor + (matrix.shape[1] % scale_factor > 0)

    # Initialize the downscaled array with zeros
    downscaled_array = np.zeros((new_height, new_width), dtype=matrix.dtype)

    # Iterate through the downscaled array and calculate the sum of the pixels
    for i in range(new_height):
      for j in range(new_width):
        row_start = i * scale_factor
        row_end = min((i + 1) * scale_factor, matrix.shape[0])
        col_start = j * scale_factor
        col_end = min((j + 1) * scale_factor, matrix.shape[1])
        downscaled_array[i, j] = np.sum(matrix[row_start:row_end, col_start:col_end])

    return downscaled_array

  def upsample_image(self, matrix: np.ndarray) -> np.ndarray:
    height, width = matrix.shape

    new_height = int(height * self.upsampling_factor)
    new_width = int(width * self.upsampling_factor)

    upscaled_image = cv2.resize(matrix, (new_width, new_height), interpolation=cv2.INTER_NEAREST)

    return upscaled_image

  def make_heatmap(self, matrix: np.ndarray) -> np.ndarray:
    scaled_map = np.uint8(cv2.convertScaleAbs(matrix, alpha=self.heatmap_alpha / 1000))
    if not self.color_map:
      final_map = np.stack((scaled_map,)*3, axis=-1)
      return final_map

    return cv2.applyColorMap(scaled_map, self.color_map)

  def add_graphics(self, picture: np.ndarray, count: int) -> np.ndarray:
    cv2.putText(picture, f'Predicted Count: {count}', (50, 50),
                cv2.FONT_HERSHEY_SIMPLEX, 1,
                (255, 255, 255), 2)

    if not self.color_map:
      return picture

    # Number of discrete colors and colorbar dimensions
    num_colors = 256
    bar_width = 50
    bar_height = picture.shape[0]  # This can be equal to num_colors if you want a one-to-one ratio

    # Create an image with a vertical gradient
    gradient = np.linspace(1, 0, num_colors).reshape(num_colors, 1)
    gradient = np.repeat(gradient, bar_width, axis=1)  # bar_width is the width of the colorbar
    gradient = cv2.resize(gradient, (bar_width, bar_height), interpolation=cv2.INTER_LINEAR)
    gradient = (255 * gradient).astype(np.uint8)

    colorbar_img = cv2.applyColorMap(gradient, self.color_map)

    # Create a white canvas for the labels
    label_width = 100  # Width of the area for the labels
    full_img = 255 * np.ones((bar_height, bar_width + label_width, 3), dtype=np.uint8)
    full_img[:, :bar_width, :] = colorbar_img  # Place the colorbar on the canvas

    # Define the step and range for the labels
    step = int(bar_height / 10)  # Adjust step for the number of labels you want
    value_range = np.linspace(255 / self.heatmap_alpha, 0, bar_height)

    # Add labels
    for i in range(0, bar_height, step):
      value = value_range[i]
      text = f"{value:.2f}"
      cv2.putText(
        full_img,
        text,
        (bar_width + 10, i + 5),
        cv2.FONT_HERSHEY_DUPLEX,
        0.5,
        (0, 0, 0),
        1,
        cv2.LINE_AA,
      )

    combined_image = np.concatenate((picture, full_img), axis=1)

    return combined_image