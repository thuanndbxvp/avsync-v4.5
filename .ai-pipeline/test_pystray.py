import pystray
print("pystray version:", pystray.__version__ if hasattr(pystray, '__version__') else 'unknown')
from pystray import Icon, Menu, MenuItem
print("Has default_action?", hasattr(Icon, 'default_action'))
import inspect
# Check notify signature
try:
    sig = inspect.signature(Icon.notify)
    print("notify signature:", sig)
except Exception as e:
    print("notify signature error:", e)
