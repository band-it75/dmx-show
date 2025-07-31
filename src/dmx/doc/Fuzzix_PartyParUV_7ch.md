# Fuzzix PartyPar UV – DMX Lighting Fixture Datasheet

## 1. Mounting & Physical Installation

* **Mounting options**: Floor-standing or truss mounting with dual bracket
* **Cooling**: Passive
* **IP rating**: IP20 – indoor use only
* **Dimensions (WxHxD)**: 210 × 220 × 110 mm
* **Weight**: 2.5 kg

---

## 2. User Menu & Control

* **Display**: LED with 4-button navigation
* **Control Modes**:
  * DMX512 (7 channels)
  * Manual mode for static colours
  * Auto programs with speed control
  * Master/slave syncing

---

## 3. DMX Parameters

* **Supported DMX Modes**: 7ch Standard
* **DMX Connector**: 3-pin XLR in/out
* **Example Channel Map (7ch mode)**:

| Ch. | Function | 8-bit value range | Effect / comment |
| ---: | ----------------------------- | ----------------- | ---------------------------------------------------------- |
| **1** | **Master dimmer** | 0–255 | Global intensity (0 %–100 %) ([sonomateriel.com][1]) |
| **2** | UV section 1 (front quadrant) | 0–255 | Individual intensity (0 %–100 %) ([sonomateriel.com][1]) |
| **3** | UV section 2 | 0–255 | Individual intensity (0 %–100 %) ([sonomateriel.com][1]) |
| **4** | UV section 3 | 0–255 | Individual intensity (0 %–100 %) ([sonomateriel.com][1]) |
| **5** | UV section 4 (rear quadrant) | 0–255 | Individual intensity (0 %–100 %) ([sonomateriel.com][1]) |
| **6** | Strobe | 0 | No strobe |
|       |        | 1–255 | Strobe, **slow → fast** ([sonomateriel.com][1]) |
| **7** | Macro / auto‑program selector | 1–17 | UV 1 only |
|       |                               | 18–35 | UV 2 only |
|       |                               | 36–53 | UV 3 only |
|       |                               | 54–71 | UV 4 only |
|       |                               | 72–89 | UV 1 + UV 2 |
|       |                               | 90–107 | UV 2 + UV 3 |
|       |                               | 108–125 | UV 1 + UV 3 |
|       |                               | 126–127 | All UV sections on |
|       |                               | 128–220 | **Jump (hard change)** program, slow → fast |
|       |                               | 221–255 | **Fade** program, slow → fast ([sonomateriel.com][1]) |

---

## 4. Electrical Specifications

* **Input Voltage**: 100–240 V AC, 50/60 Hz
* **Max Power Consumption**: 50 W
* **Power Connections**: IEC IN/OUT
* **Thermal Range**: –10 °C to +40 °C

[1]: https://sonomateriel.com/amfile/file/download/file/1689/product/4022/ "Manual - MAX PartyPar UV 12x1W UV DMX"
