# Prolights LumiPar 7 UTRI – DMX Lighting Fixture Datasheet

## 1. Mounting & Physical Installation

* **Mounting options**: Floor-standing, hanging with bracket (M10 clamp compatible), safety cable point included
* **Bracket**: Dual bracket for angled positioning or fixed truss mounting
* **Cooling**: Passive
* **IP rating**: IP20 – suitable for indoor use
* **Dimensions (WxHxD)**: 220 × 190 × 110 mm
* **Weight**: 2.8 kg

---

## 2. User Menu & Control

* **Display**: LED with 4-button navigation
* **Control Modes**:
  * DMX512 (8 channels)
  * Manual mode (set static values)
  * Auto mode (built-in programs with speed control)
  * IR remote (optional)
  * Master/slave (sync multiple units)
* **Menu Settings**:
  * DMX address
  * Channel mode
  * Dimmer curve
  * Strobe/auto speed
  * Wireless config (if applicable)

---

## 3. DMX Parameters

* **Supported DMX Modes**: 8ch Standard
* **DMX Connector**: 3-pin XLR in/out
* **Example Channel Map (8ch mode)**:

| CH | Function       | Range | Notes |
| -- | -------------- | ----- | ----- |
| 1  | Red            | 0–255 |       |
| 2  | Green          | 0–255 |       |
| 3  | Blue           | 0–255 |       |
| 4  | Color Macros   | 0–255 | presets 16–255 |
| 5  | Strobe         | 0–255 | open 0–15, strobe 16–255 |
| 6  | Programs       | 0–255 | built-in fades and sounds |
| 7  | Master Dimmer  | 0–255 |       |
| 8  | Dimmer Speed   | 0–255 | mode selection |

### 3.1 Red

* **0–255** — red LED intensity.

### 3.2 Green

* **0–255** — green LED intensity.

### 3.3 Blue

* **0–255** — blue LED intensity.

### 3.4 Color Macros

* **0–15** — manual RGB from **CH1–CH3**.
* **16–255** — static colour presets.

### 3.5 Strobe

* **0–15** — open.
* **16–255** — strobe effect, slow → fast.

### 3.8. Programs

**0–31 — No function (manual RGB / static color)**

* **Midpoint to use:** 16
* **What it does:** Disables auto programs. Output follows **Ch1–3** (RGB) for manual mixes. If **Ch4 ≥ 16**, a built‑in static **Color Macro** is used instead of manual RGB.
* **Pairs with:** **Ch5** (strobe overlay) works normally; **Ch6/Ch7** have no effect here. 

**32–63 — Pulse 0→100% (fade‑in “breath”)**

* **Midpoint to use:** 48
* **What it does:** Repeats a smooth fade from black up to full, then snaps back to black.
* **Color source:** Your currently selected color (manual RGB on Ch1–3, or a macro from Ch4).
* **Speed:** **Ch6** controls the pulse rate (lower = slower).
* **Notes:** Works nicely as a subtle “breathing” backlight; avoid heavy strobe on Ch5 at the same time unless you *want* a double‑flash feel. 

**64–95 — Pulse 100%→0 (fade‑out)**

* **Midpoint to use:** 80
* **What it does:** Starts at full and fades to black, then jumps back to full.
* **Color source / Speed:** same logic as above (Ch1–4 set color; **Ch6** sets rate). 

**96–127 — Pulse 100%→0→100% (triangular)**

* **Midpoint to use:** 112
* **What it does:** Symmetrical up‑and‑down pulse (full → black → full).
* **Color source / Speed:** as above (Ch1–4 for color; **Ch6** for rate).
* **Notes:** This reads as the smoothest “breathing” variant because the slope up and down are matched. 

**128–159 — Colors Fade (auto fade)**

* **Midpoint to use:** 144
* **What it does:** Crossfades through internal color presets automatically.
* **Speed:** **Ch6** controls how long each fade takes.
* **Interplay:** Ch1–3 are ignored while this is active; **Ch5** can still overlay a strobe; **Ch7** is ignored. (Color selection is fixture‑defined; use this when you want motion without programming color steps.) 

**160–191 — 3 Colors Snap (auto)**

* **Midpoint to use:** 176
* **What it does:** Hard cuts through a 3‑color set (typical primaries on this class of fixture).
* **Speed:** **Ch6** sets dwell time between snaps.
* **Interplay:** Ch1–3 are ignored; **Ch5** strobe can overlay; **Ch7** ignored. 

**192–223 — 7 Colors Snap (auto)**

* **Midpoint to use:** 208
* **What it does:** Hard cuts through a broader 7‑color set (the standard primaries/secondaries + white mix on RGB fixtures).
* **Speed:** **Ch6** sets the step rate.
* **Interplay:** Ch1–3 ignored; **Ch5** overlays; **Ch7** ignored.

**224–255 — Sound Control (sound‑active)**

* **Midpoint to use:** 240
* **What it does:** Reacts to the internal mic—typically snapping/fading with the beat.
* **Sensitivity:** **Ch7** becomes active here. Values **0–10** = sound off; **11–255** = adjust mic sensitivity (higher values give a stronger reaction range; exact scaling is fixture‑defined). You can also set Snd1/Snd2 and an on‑fixture sensitivity (u0–u100) from the menu for standalone use.
* **Speed:** **Ch6** is generally ignored; the beat drives timing.
* **Notes:** If response is weak, raise Ch7 and/or increase the room’s bass content; the manual’s sound‑mode section describes the mic settings.

### 3.9 Master Dimmer

* **0–255** — overall output level for all colours.

### 3.10 Dimmer Speed

* **0–63** — instant.
* **64–127** — fast fades.
* **128–191** — medium fades.
* **192–255** — slow fades.

## 4. Electrical Specifications

* **Input Voltage**: 100–240 V AC, 50/60 Hz
* **Max Power Consumption**: 60 W
* **Power Connections**: IEC IN/OUT
* **Power Linking**:
  * Max 15 units @ 230 V
  * Max 8 units @ 120 V
* **Thermal Range**: –10 °C to +45 °C

