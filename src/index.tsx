import {
  PanelSection,
  PanelSectionRow,
  staticClasses,
  SliderField,
  ToggleField,
  Unregisterable,
} from "@decky/ui";
import {
  callable,
  definePlugin,
  toaster,
} from "@decky/api"
import { useState, useEffect } from "react";
import { LuSun, LuSunMoon } from "react-icons/lu";
import { localizationManager, L } from "./i18n";
import { t } from 'i18next';

const DIMMER_BRIGHTNESS_DELTA = 0.05;
const TOAST_TIMEOUT = 1000;

let lastSystemBrightness = 0.;
let lastDimmerBrightness = 1.;
let pluginChangedBrightness = false;

let setUiBrightnessCallback = (_: number) => { };

let unregisterBrightnessCallback: Unregisterable | null = null;

const backendSetBrightness = callable<[number], void>("set_brightness");
const backendReset = callable<[], void>("reset");
const backendActivate = callable<[], void>("activate");

const clampBrightness = (value: number) => Math.min(Math.max(value, 0.), 1.);

const setBrightness = (value: number) => {
  value = clampBrightness(value);
  console.log(`Setting dimmer brightness to ${value}`);
  lastDimmerBrightness = value;
  setUiBrightnessCallback(value);
  if (value == 1.)
    backendReset();
  else
    backendSetBrightness(value);
};

const onBrightnessChangedCallback = (value: { flBrightness: number; }) => {
  const brightness = value.flBrightness;
  console.log(`Brightness changed to ${brightness}`);
  if (lastSystemBrightness <= 0.) {
    if (brightness > 0.) {
      // increase dimmer brightness
      if (lastDimmerBrightness !== 1.) {
        window.SteamClient.System.Display.SetBrightness(0.);
        pluginChangedBrightness = true;
        setBrightness(lastDimmerBrightness + DIMMER_BRIGHTNESS_DELTA);
        if (lastDimmerBrightness === 1.) {
          toaster.toast({
            title: "Dimmer Brightness",
            body: "OFF",
            icon: <LuSun />,
            duration: TOAST_TIMEOUT,
            expiration: TOAST_TIMEOUT,
          });
        }
      }
    } else {
      // decrease dimmer brightness
      if (pluginChangedBrightness) {
        pluginChangedBrightness = false;
        lastSystemBrightness = brightness;
        return;
      }
      if (lastDimmerBrightness === 1.) {
        toaster.toast({
          title: "Dimmer Brightness",
          body: "ON",
          icon: <LuSunMoon />,
          duration: TOAST_TIMEOUT,
          expiration: TOAST_TIMEOUT,
        });
      }
      setBrightness(lastDimmerBrightness - DIMMER_BRIGHTNESS_DELTA);
    }
  }
  lastSystemBrightness = brightness;
}
const setShortcutControl = (enabled: boolean) => {
  if (enabled && unregisterBrightnessCallback === null)
    unregisterBrightnessCallback =
      window.SteamClient.System.Display.RegisterForBrightnessChanges(onBrightnessChangedCallback);
  else if (!enabled && unregisterBrightnessCallback !== null) {
    unregisterBrightnessCallback.unregister();
    unregisterBrightnessCallback = null;
  }
}

function Content() {
  const [uiBrightness, setUiBrightness] = useState(lastDimmerBrightness);
  const [uiShortcutControl, setUiShortcutControl] = useState(
    localStorage.getItem("dimmer_deck.shortcut") === "true"
  );

  useEffect(() => {
    setUiBrightnessCallback = (value) => {
      setUiBrightness(value);
    };
    return () => {
      setUiBrightnessCallback = (_: number) => { };
    };
  }, []);

  useEffect(() => {
    localStorage.setItem("dimmer_deck.shortcut", uiShortcutControl ? "true" : "false");
    setShortcutControl(uiShortcutControl);
  }, [uiShortcutControl]);

  return (
    <>
      <PanelSection title={t(L.BRIGHTNESS)}>
        <PanelSectionRow>
          <SliderField
            label={t(L.DIMMER_BRIGHTNESS)}
            value={uiBrightness}
            step={0}
            max={1}
            min={0}
            onChange={setBrightness}
          />
        </PanelSectionRow>
      </PanelSection>
      <PanelSection title={t(L.CONTROL)}>
        <PanelSectionRow>
          <ToggleField
            label={t(L.ENABLE_SHORTCUT_CONTROL)}
            description={t(L.ENABLE_SHORTCUT_CONTROL_DESC)}
            checked={uiShortcutControl}
            onChange={setUiShortcutControl}
          />
        </PanelSectionRow>
      </PanelSection>
    </>
  );
};

export default definePlugin(() => {
  localizationManager.init();
  backendActivate();
  setShortcutControl(localStorage.getItem("dimmer_deck.shortcut") === "true");

  return {
    // The name shown in various decky menus
    name: "Dimmer Deck",
    // The element displayed at the top of your plugin's menu
    titleView: <div className={staticClasses.Title}>Dimmer Deck</div>,
    // The content of your plugin's menu
    content: <Content />,
    // The icon displayed in the plugin list
    icon: <LuSunMoon />,
    onDismount() {
      setShortcutControl(false);
      backendReset();
    },
  };
});
