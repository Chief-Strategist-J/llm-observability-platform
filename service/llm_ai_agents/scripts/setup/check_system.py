import psutil
import yaml
import argparse
import sys
import os

try:
    import pynvml
    HAS_NVML = True
except ImportError:
    HAS_NVML = False

def get_sys_info():
    mem = psutil.virtual_memory()
    info = {
        "ram_gb": mem.total / (1024**3),
        "available_ram_gb": mem.available / (1024**3),
        "vram_gb": 0,
        "gpus": []
    }
    
    if HAS_NVML:
        try:
            pynvml.nvmlInit()
            device_count = pynvml.nvmlDeviceGetCount()
            for i in range(device_count):
                handle = pynvml.nvmlDeviceGetHandleByIndex(i)
                mem_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
                gpu_name = pynvml.nvmlDeviceGetName(handle)
                info["gpus"].append({
                    "name": gpu_name,
                    "vram_gb": mem_info.total / (1024**3),
                    "free_vram_gb": mem_info.free / (1024**3)
                })
                info["vram_gb"] = max(info["vram_gb"], mem_info.total / (1024**3))
        except Exception as e:
            pass
            
    return info

def check_resources(config_path):
    if not os.path.exists(config_path):
        return False

    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    model_resources = config.get('model', {}).get('resources', {})
    min_ram = model_resources.get('min_ram_gb', 0)
    min_vram = model_resources.get('min_vram_gb', 0)
    accelerator = model_resources.get('accelerator', 'cpu')
    
    sys_info = get_sys_info()
    
    if accelerator == "cuda":
        if sys_info['vram_gb'] < min_vram:
            return False
    
    if sys_info['ram_gb'] < min_ram:
        return False
        
    return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    args = parser.parse_args()
    
    if not check_resources(args.config):
        sys.exit(1)
    sys.exit(0)
