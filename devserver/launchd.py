import logging
import os
import plistlib
import subprocess
import sys
from pathlib import Path

logger = logging.getLogger(__name__)


# Custom type to allow outputting Path objects
class Writer(plistlib._PlistWriter):
    def write_value(self, value):
        if isinstance(value, Path):
            self.simple_element("string", str(value))
        else:
            super().write_value(value)


def install(label):
    path = Path.home() / "Library" / "LaunchAgents" / (label + ".plist")
    logs = Path.home() / "Library" / "Logs" / (label + ".log")
    # https://launchd.info/
    pl = {
        "Label": label,
        "RunAtLoad": True,
        "StandardOutPath": logs,
        "StandardErrorPath": logs,
        "EnvironmentVariables": {"PATH": os.environ["PATH"]},
        "ProgramArguments": [
            Path(sys.argv[0]).absolute(),
            "web",
            "--port",
            "7999",
        ],
    }

    with path.open("wb+") as fp:
        logger.info("Writing to %s", fp.name)
        Writer(fp).write(pl)

    logger.info("Unload %s", path)
    subprocess.check_call(["launchctl", "unload", path])
    logger.info("Load %s", path)
    subprocess.check_call(["launchctl", "load", path])
    return path
