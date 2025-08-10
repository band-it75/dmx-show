# Prolights PIXIEWASH – DMX Lighting Fixture Datasheet

## 1. Mounting & Physical Installation

* **Mounting options**: Floor-standing, hanging with bracket (M10 clamp compatible), safety cable point included
* **Bracket**: Dual bracket for angled positioning or fixed truss mounting
* **Cooling**: Fan-cooled
* **IP rating**: IP20 – suitable for indoor use
* **Dimensions (WxHxD)**: 290 × 350 × 210 mm
* **Weight**: 6.0 kg

---

## 2. User Menu & Control

* **Display**: LED with 4-button navigation
* **Control Modes**:
  * DMX512 (13 channels)
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

* **Supported DMX Modes**: 13ch Moving Head
* **DMX Connector**: 3-pin XLR in/out
* **Example Channel Map (13ch mode)**:

| CH | Function           | Range | Notes |
| -- | ------------------ | ----- | ----- |
| 1  | Pan               | 0–255 | 16-bit with CH2 |
| 2  | Pan Fine          | 0–255 |       |
| 3  | Tilt              | 0–255 | 16-bit with CH4 |
| 4  | Tilt Fine         | 0–255 |       |
| 5  | Pan/Tilt Speed    | 0–255 | 0=fast, 255=slow |
| 6  | Special Functions | 0–255 | resets and more |
| 7  | Master Dimmer     | 0–255 |       |
| 8  | Shutter           | 0–255 | closed/open/strobe |
| 9  | Red               | 0–255 |       |
| 10 | Green             | 0–255 |       |
| 11 | Blue              | 0–255 |       |
| 12 | White             | 0–255 |       |
| 13 | Color Macros      | 0–255 | preset colours |

### 3.1 Pan

* **0–255** — coarse pan across fixture range. Fine adjust on **CH2**.

### 3.2 Pan Fine

* **0–255** — 16‑bit fine pan control.

### 3.3 Tilt

* **0–255** — coarse tilt. Fine adjust on **CH4**.

### 3.4 Tilt Fine

* **0–255** — 16‑bit fine tilt control.

### 3.5 Pan/Tilt Speed

* **0–255** — movement speed, 0 fast → 255 slow.

### 3.6 Special Functions

* **0–15** — none.
* **16–31** — motor reset.
* **32–47** — dimmer reset.
* **48–255** — fixture‑specific utilities.

### 3.7 Master Dimmer

* **0–255** — global light output.

### 3.8 Shutter

* **0–31** — closed.
* **32–63** — open.
* **64–255** — strobe, slow → fast.

### 3.9 Red

* **0–255** — red LED intensity.

### 3.10 Green

* **0–255** — green LED intensity.

### 3.11 Blue

* **0–255** — blue LED intensity.

### 3.12 White

* **0–255** — white LED intensity.

### 3.13 Color Macros

* **0–255** — built‑in colour presets.

---

## 4. Electrical Specifications

* **Input Voltage**: 100–240 V AC, 50/60 Hz
* **Max Power Consumption**: 180 W
* **Power Connections**: powerCON IN/OUT
* **Power Linking**:
  * Max 6 units @ 230 V
  * Max 3 units @ 120 V
* **Thermal Range**: –10 °C to +45 °C

