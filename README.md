# Dimmer Deck

Make your Steam Deck even dimmer.

## How does it work?

Steam OS uses [Gamescope](https://github.com/ValveSoftware/gamescope) to composite the screen. Its color management can load custom color LUT. This plugin creates a custom LUT that makes the screen even dimmer than the blacklight can.

## Known issues

- Other color management features, such as color temperature, saturation tuning and night mode, will be broken when the dimmer brightness is set, because custom LUT will replace these effects.
- The screen may flicker when the brightness is set, especially when sliding the brightness slider, because Gamescope doesn't has a mutex to keep the consistency of custom LUT.
