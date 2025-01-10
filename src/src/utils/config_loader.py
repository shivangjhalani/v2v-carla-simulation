import yaml
import os
from typing import Dict, Any

def load_config(config_path: str) -> Dict[str, Any]:
    """Load configuration from YAML file"""
    try:
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Config file not found: {config_path}")
            
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
            
        if not config:
            raise ValueError("Empty configuration file")
            
        return config
        
    except Exception as e:
        raise RuntimeError(f"Error loading config: {e}")
