import torch
import sys
import os
import importlib.util

model_wrapper_abs_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

model_py_path = os.path.join(model_wrapper_abs_path, 'CrowdCounting-SASNet', 'model.py')

if not os.path.isfile(model_py_path):
    raise ImportError("The specified path for model.py does not exist: {}".format(model_py_path))

spec = importlib.util.spec_from_file_location("model", model_py_path)
model = importlib.util.module_from_spec(spec)

spec.loader.exec_module(model)

class Model:
  def __init__(self, model_path: str, use_pretrained: bool, block_size: int) -> None:
    self.block_size: int = block_size
    class ArgsWrapper:
        block_size: int = self.block_size

    args: ArgsWrapper = ArgsWrapper()

    self.model: torch.nn.Module = model.SASNet(use_pretrained, args).cuda()
    self.model.load_state_dict(torch.load(model_path))

  def get_model(self) -> torch.nn.Module:
    return self.model