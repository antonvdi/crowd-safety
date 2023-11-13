from torch.utils.data import Dataset
from typing import Optional, Tuple, Callable
import torch
import cv2

class VideoFrameDataset(Dataset):
  def __init__(
    self,
    video_path: str,
    transform: Optional[Callable] = None,
    frame_interval: int = 300,
    target_resolution: Tuple[int, int] = (1920, 1080)
  ) -> None:
    self.video_path: str = video_path
    self.cap: cv2.VideoCapture = cv2.VideoCapture(video_path)
    self.transform: Optional[Callable] = transform
    self.frame_interval: int = frame_interval
    self.target_resolution: Tuple[int, int] = target_resolution
    self.total_frames: int = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))

  def __len__(self) -> int:
    return self.total_frames // self.frame_interval

  def __getitem__(self, idx: int) -> torch.Tensor:
    frame_index: int = idx * self.frame_interval
    self.cap.set(cv2.CAP_PROP_POS_FRAMES, frame_index)
    ret: bool
    frame: np.ndarray
    ret, frame = self.cap.read()

    if not ret:
      raise ValueError("Failed to read frame from the video.")

    frame = cv2.resize(frame, self.target_resolution, interpolation=cv2.INTER_LINEAR)

    if self.transform:
      frame = self.transform(frame)

    return frame.float()

  def __del__(self) -> None:
    if self.cap.isOpened():
      self.cap.release()
