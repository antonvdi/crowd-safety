from typing import List, Tuple, Optional
import torch
import torch.nn
import numpy as np
import torchvision.transforms as standard_transforms
from torch.utils.data import DataLoader
import gc

from src.camera_utils import CameraUtils 
from src.video_frame_dataset import VideoFrameDataset  

class Camera:
  def __init__(
    self,
    video_path: str,
    local_coordinates: List[Tuple[int, int]],
    global_coordinates: List[Tuple[int, int]],
    model: torch.nn.Module,
    frame_interval: int,
    batch_size: int,
    log_parameter: int,
    camera_utils: CameraUtils,
    distortion_parameters: Optional[float] = None
  ) -> None:
    self.video_path: str = video_path
    self.frame_interval: int = frame_interval
    self.batch_size: int = batch_size
    self.local_coordinates: List[Tuple[int, int]] = local_coordinates
    self.global_coordinates: List[Tuple[int, int]] = global_coordinates
    self.distortion_parameters: Optional[float] = distortion_parameters
    self.model: torch.nn.Model = model  # Use specific model type if known
    self.log_parameter: int = log_parameter
    self.camera_utils: CameraUtils = camera_utils

    self.predicted_counts: List[float] = []
    self.images: List[np.ndarray] = []

  def get_video_dataloader(self) -> DataLoader:
    transform = standard_transforms.Compose([
        standard_transforms.ToTensor(),
        standard_transforms.Normalize(mean=[0.485, 0.456, 0.406],
                                      std=[0.229, 0.224, 0.225]),
    ])
    dataset = VideoFrameDataset(self.video_path, transform=transform, frame_interval=self.frame_interval)
    dataloader = DataLoader(dataset=dataset,
                            batch_size=self.batch_size,
                            num_workers=0,
                            shuffle=False,
                            drop_last=False,
                            pin_memory=True)
    return dataloader

  def predict(self) -> None:
    torch.cuda.empty_cache()
    gc.collect()

    dataloader = self.get_video_dataloader()

    for img in dataloader:
      img = img.cuda()

      with torch.no_grad():
        self.model.eval()
        pred_map = self.model(img)
      pred_map = pred_map.data.cpu().numpy()

      for i_img in range(pred_map.shape[0]):
        pred_cnt = np.sum(pred_map[i_img]) / self.log_parameter
        self.predicted_counts.append(pred_cnt)
        print(f'Predicted Count: {pred_cnt}')

        # Extract the first channel (grayscale) from the density map
        grayscale_map = pred_map[i_img][0]

        if self.distortion_parameters and len(self.distortion_parameters) > 0:
          undistorted_map = self.camera_utils.correct_fisheye_distortion(grayscale_map, self.distortion_parameters[0])
        else:
          undistorted_map = grayscale_map

        corrected_map = self.camera_utils.correct_perspective(undistorted_map, self.local_coordinates)

        width_after = self.global_coordinates[3][0] - self.global_coordinates[0][0]
        scale_factor = int(corrected_map.shape[1] / width_after)

        downsampled_map = self.camera_utils.downsample_image(corrected_map, scale_factor)

        upsampled_map = self.camera_utils.upsample_image(downsampled_map)

        heatmap = self.camera_utils.make_heatmap(upsampled_map)

        self.images.append(heatmap)

      del pred_map
      del heatmap
      del pred_cnt
      torch.cuda.empty_cache()