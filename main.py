import os
import struct
import subprocess
from typing import Any, List

import decky

logger = decky.logger

# Gain is applied to linear light, while the slider is in gamma-encoded space
DISPLAY_GAMMA = 2.2
# A gain of 0 would flatten the shaper LUT that gamescope builds its 3D LUT from
MIN_GAIN = 0.0001

def get_steam_displays() -> List[str]:
    displays = []
    for pid in os.listdir("/proc"):
        if not pid.isdigit():
            continue
        try:
            with open(f"/proc/{pid}/cmdline", "rb") as f:
                if not f.read().split(b"\0")[0].endswith(b"steam"):
                    continue
                logger.debug(f"Found steam process: {pid}")
            with open(f"/proc/{pid}/environ", "rb") as f:
                for line in f.read().split(b"\0"):
                    if not line.startswith(b"DISPLAY="):
                        continue
                    display = line.split(b"=")[1].decode()
                    if display not in displays:
                        displays.append(display)
                    logger.debug(f"Found steam display: {display}")
        except:
            pass
    return displays


def brightness_to_gain(brightness: float) -> float:
    if brightness < 0 or brightness > 1:
        logger.error("Invalid brightness")
        raise ValueError("Brightness must be between 0 and 1")
    return max(brightness**DISPLAY_GAMMA, MIN_GAIN)


def float_to_cardinal(x: float) -> int:
    # Gamescope reads float atoms by reinterpreting the 32-bit cardinal's bits
    return struct.unpack("<I", struct.pack("<f", x))[0]


def set_xprop(display: str, prop_name: str, prop_type: str, prop_value: Any):
    cmd = [
        "xprop",
        "-root",
        "-d",
        display,
        "-f",
        prop_name,
        prop_type,
        "-set",
        prop_name,
        str(prop_value),
    ]
    ret = subprocess.call(cmd)
    if ret != 0:
        logger.error(f"Failed to set xprop, cmd: {cmd}")
        raise Exception("Failed to set xprop")


def remove_xprop(display: str, prop_name: str):
    cmd = [
        "xprop",
        "-root",
        "-d",
        display,
        "-remove",
        prop_name,
    ]
    ret = subprocess.call(cmd)
    if ret != 0:
        logger.error(f"Failed to set xprop, cmd: {cmd}")
        raise Exception("Failed to set xprop")

def set_sdr_gain(display: str, gain: float):
    set_xprop(display, "GAMESCOPE_SDR_INPUT_GAIN", "32c", float_to_cardinal(gain))


class Plugin:
    async def activate(self):
        logger.info("Activating")
        self.displays = get_steam_displays()
        self.first_run = True
        logger.info(f"Found steam displays: {self.displays}")

    def prepare(self):
        logger.info("Preparing")
        self.first_run = False
        for display in self.displays:
            set_xprop(display, "GAMESCOPE_COMPOSITE_FORCE", "8c", 1)

    async def set_brightness(self, brightness: float):
        if self.first_run:
            self.prepare()

        gain = brightness_to_gain(brightness)
        for display in self.displays:
            set_sdr_gain(display, gain)

    async def reset(self):
        logger.info("Resetting")
        self.first_run = True
        for display in self.displays:
            remove_xprop(display, "GAMESCOPE_COMPOSITE_FORCE")
            # Don't remove this one: gamescope reads a missing atom as a gain of 0
            set_sdr_gain(display, 1.0)

    async def _unload(self):
        logger.info("Unloading")
        if not self.first_run:
            await self.reset()
