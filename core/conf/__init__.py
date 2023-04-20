from .common import *

try:
    exec(f'from .{ENV} import *')
    print(f"Configuration loaded from conf/{ENV}.py")
except ImportError:
    print(f"Configuration file not found in conf/{ENV}.py")
    exit(1)
