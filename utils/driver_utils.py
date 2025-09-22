import subprocess
from typing import List


def get_installed_packages() -> List[str]:
    """Lists all installed application packages using ADB."""
    try:
        result = subprocess.run(['adb', 'shell', 'pm', 'list', 'packages'], capture_output=True, text=True, check=True)
        return [line.split(':')[1].strip() for line in result.stdout.splitlines()]
    except Exception:
        return []