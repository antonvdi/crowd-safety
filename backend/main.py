from src.camera_collection import CameraCollection
from src.camera_utils import CameraUtils
from src.camera import Camera
from src.model_wrapper import Model
from src.video_frame_dataset import VideoFrameDataset
import cv2

class GLOBAL_CONFIG:
  FRAME_INTERVAL: int = 300
  BATCH_SIZE: int = 1
  MODEL_PATH: str = "/work/weights/SHHA.pth"
  OUTPUT_DIR: str = "/work/output/"
  USE_PRETRAINED: bool = True
  BLOCK_SIZE: int = 32
  LOG_PARAMETER: int = 1000
  HEATMAP_ALPHA: int = 50
  UPSAMPLING_FACTOR: int = 1
  COLOR_MAP = None
  #COLOR_MAP = cv2.COLORMAP_JET

model = Model(GLOBAL_CONFIG.MODEL_PATH,
              GLOBAL_CONFIG.USE_PRETRAINED,
              GLOBAL_CONFIG.BLOCK_SIZE).get_model()
local_coords = [(797, 293), (287, 653), (1761, 1040), (1734, 411)]
global_coords = [(0, 0), (0, 80), (100, 80), (100, 0)]

camera_utils = CameraUtils(GLOBAL_CONFIG.HEATMAP_ALPHA,
                           GLOBAL_CONFIG.OUTPUT_DIR,
                           GLOBAL_CONFIG.UPSAMPLING_FACTOR,
                           GLOBAL_CONFIG.COLOR_MAP)

camera = Camera("/work/input/DJI_0461_trimmed.MP4",
                local_coords,
                global_coords,
                model,
                GLOBAL_CONFIG.FRAME_INTERVAL,
                GLOBAL_CONFIG.BATCH_SIZE,
                GLOBAL_CONFIG.LOG_PARAMETER,
                camera_utils
                )

camera_collection = CameraCollection([camera], camera_utils)
camera_collection.generate_report()