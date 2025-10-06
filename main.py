import os
import struct
from typing import Any, List

import decky
import asyncio

logger = decky.logger

LUT1D_SIZE = 4096
LUT3D_SIZE = 17

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


def quantize(x: float) -> int:
    return int(round(x * 65535))


def generate_lut1d(output: str, brightness: float):
    if brightness < 0 or brightness > 1:
        logger.error("Invalid brightness")
        raise ValueError("Brightness must be between 0 and 1")
    to_unit = lambda i: i / (LUT1D_SIZE - 1) * brightness
    with open(output, "wb") as f:
        for x in range(LUT1D_SIZE):
            bs = struct.pack(
                "<HHHH",
                quantize(to_unit(x)),
                quantize(to_unit(x)),
                quantize(to_unit(x)),
                0,
            )
            f.write(bs)


def generate_lut3d(output: str, brightness: float):
    if brightness < 0 or brightness > 1:
        logger.error("Invalid brightness")
        raise ValueError("Brightness must be between 0 and 1")
    to_unit = lambda i: i / (LUT3D_SIZE - 1) * brightness
    with open(output, "wb") as f:
        for b in range(LUT3D_SIZE):
            for g in range(LUT3D_SIZE):
                for r in range(LUT3D_SIZE):
                    bs = struct.pack(
                        "<HHHH",
                        quantize(to_unit(r)),
                        quantize(to_unit(g)),
                        quantize(to_unit(b)),
                        0,
                    )
                    f.write(bs)


async def set_xprop(display: str, prop_name: str, prop_type: str, prop_value: Any):
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
    proc = await asyncio.subprocess.create_subprocess_exec(*cmd)
    await proc.wait()
    if proc.returncode != 0:
        logger.error(f"Failed to set xprop, cmd: {cmd}")
        stdout, stderr = await proc.communicate()
        logger.error(f"stdout: {stdout}")
        logger.error(f"stderr: {stderr}")
        raise Exception("Failed to set xprop")


async def remove_xprop(display: str, prop_name: str):
    cmd = [
        "xprop",
        "-root",
        "-d",
        display,
        "-remove",
        prop_name,
    ]
    proc = await asyncio.subprocess.create_subprocess_exec(*cmd)
    await proc.wait()
    if proc.returncode != 0:
        logger.error(f"Failed to remove xprop, cmd: {cmd}")
        stdout, stderr = await proc.communicate()
        logger.error(f"stdout: {stdout}")
        logger.error(f"stderr: {stderr}")
        raise Exception("Failed to set xprop")

lut3d_path = os.path.abspath(
    os.path.join(decky.DECKY_PLUGIN_RUNTIME_DIR, "dim.lut3d")
)
lut1d_path = os.path.abspath(
    os.path.join(decky.DECKY_PLUGIN_RUNTIME_DIR, "dim.lut1d")
)

class Plugin:
    async def activate(self):
        logger.info("Activating")
        self.displays = get_steam_displays()
        self.first_run = True
        generate_lut3d(lut3d_path, 1.0)
        logger.info(f"Found steam displays: {self.displays}")

    async def prepare(self):
        logger.info("Preparing")
        for display in self.displays:
            await set_xprop(display, "GAMESCOPE_COMPOSITE_FORCE", "8c", 1)
        await set_xprop(display, "GAMESCOPE_COLOR_3DLUT_OVERRIDE", "8u", lut3d_path)

    async def set_brightness(self, brightness: float):
        if self.first_run:
            self.first_run = False
            await self.prepare()

        generate_lut1d(lut1d_path, brightness)
        for display in self.displays:
            await set_xprop(
                display, "GAMESCOPE_COLOR_SHAPERLUT_OVERRIDE", "8u", lut1d_path
            )

    async def reset(self):
        logger.info("Resetting")
        self.first_run = True
        for display in self.displays:
            await remove_xprop(display, "GAMESCOPE_COMPOSITE_FORCE")
            await remove_xprop(display, "GAMESCOPE_COLOR_SHAPERLUT_OVERRIDE")
            await remove_xprop(display, "GAMESCOPE_COLOR_3DLUT_OVERRIDE")

    async def _unload(self):
        logger.info("Unloading")
        if not self.first_run:
            await self.reset()

    async def _uninstall(self):
        logger.info("Uninstalling")
        if not self.first_run:
            await self.reset()
