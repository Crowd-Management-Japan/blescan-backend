from enum import Enum
from typing import Dict, Any
import logging
from . import cloud_config

class ConfigType(Enum):
    ALL = 0
    BLESCAN = "blescan_config.json"
    CLOUD = "cloud.json"

class _Configs:
    CloudConfig: cloud_config.CloudConfig = None

Configs = _Configs()

def init_config(base_dir='res/config'):
    Configs.CloudConfig = cloud_config.CloudConfig(f"{base_dir}/{ConfigType.CLOUD.value}")
