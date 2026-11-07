# Dimmer Deck

Make your Steam Deck even dimmer.

## How does it work?

Steam OS uses [Gamescope](https://github.com/ValveSoftware/gamescope) to composite the screen. This plugin sets Gamescope's SDR input gain, which makes the screen even dimmer than the backlight can. The gain is part of Gamescope's own color pipeline, so night mode, color temperature and saturation tuning keep working.

## Known issues

- HDR content is not dimmed.
