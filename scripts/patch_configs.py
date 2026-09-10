#!/usr/bin/env python3
"""Patch ESP32Marauder esp32_marauder/configs.h with BPM Circuits targets.

The patch is intentionally anchor-based instead of line-number-based so that
normal upstream insertions do not break it. If an expected anchor disappears,
the script exits with an error instead of silently producing an unknown build.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys


TARGET_DEFINES = """  //#define BPMCIRCUITS_FEBERIS
  //#define BPMCIRCUITS_FEBERIS_PRO
"""

HARDWARE_NAMES = """  #elif defined(BPMCIRCUITS_FEBERIS)
    #define HARDWARE_NAME \"Feberis\"
  #elif defined(BPMCIRCUITS_FEBERIS_PRO)
    #define HARDWARE_NAME \"Feberis Pro\"
"""

BOARD_FEATURES = """  #ifdef BPMCIRCUITS_FEBERIS
    //#define FLIPPER_ZERO_HAT
    //#define HAS_MINI_KB
    //#define HAS_BATTERY
    #define HAS_BT
    //#define HAS_BUTTONS
    #define HAS_NEOPIXEL_LED
    //#define HAS_PWR_MGMT
    //#define HAS_SCREEN
    //#define HAS_MINI_SCREEN
    //#define HAS_SD
    //#define USE_SD
    //#define HAS_TEMP_SENSOR
    //#define HAS_GPS
    #define HAS_NIMBLE_2
    #define HAS_IDF_3
    //#define HAS_DIRECT_UPLOAD
  #endif

  #ifdef BPMCIRCUITS_FEBERIS_PRO
    //#define FLIPPER_ZERO_HAT
    //#define HAS_MINI_KB
    //#define HAS_BATTERY
    #define HAS_BT
    //#define HAS_BUTTONS
    #define HAS_NEOPIXEL_LED
    //#define HAS_PWR_MGMT
    //#define HAS_SCREEN
    //#define HAS_MINI_SCREEN
    //#define HAS_SD
    //#define USE_SD
    //#define HAS_TEMP_SENSOR
    #define HAS_GPS
    #define HAS_NIMBLE_2
    #define HAS_IDF_3
    //#define HAS_DIRECT_UPLOAD
  #endif
"""

GPS_CONFIG = """    #elif defined(BPMCIRCUITS_FEBERIS_PRO)
      #define GPS_SERIAL_INDEX 1
      #define GPS_TX 4
      #define GPS_RX 13
"""


def insert_once(text: str, anchor: str, insertion: str, label: str) -> str:
    count = text.count(anchor)
    if count != 1:
        raise RuntimeError(
            f"Expected exactly one anchor for {label}, found {count}. "
            "Upstream configs.h likely changed; patch aborted."
        )
    return text.replace(anchor, insertion + anchor, 1)


def validate(text: str) -> None:
    required = [
        "//#define BPMCIRCUITS_FEBERIS",
        "//#define BPMCIRCUITS_FEBERIS_PRO",
        '#define HARDWARE_NAME "Feberis"',
        '#define HARDWARE_NAME "Feberis Pro"',
        "#ifdef BPMCIRCUITS_FEBERIS",
        "#ifdef BPMCIRCUITS_FEBERIS_PRO",
        "#elif defined(BPMCIRCUITS_FEBERIS_PRO)\n      #define GPS_SERIAL_INDEX 1\n      #define GPS_TX 14\n      #define GPS_RX 13",
    ]
    missing = [item for item in required if item not in text]
    if missing:
        raise RuntimeError("Patch validation failed; missing: " + ", ".join(missing))


def patch(path: Path) -> None:
    text = path.read_text(encoding="utf-8")

    # Idempotent behavior: if both custom targets are already present, only
    # validate them. This is useful when re-running locally.
    if "BPMCIRCUITS_FEBERIS" in text or "BPMCIRCUITS_FEBERIS_PRO" in text:
        validate(text)
        print(f"{path}: BPM Circuits patch already present and valid")
        return

    # 1) Board target switches.
    text = insert_once(
        text,
        "  //// END BOARD TARGETS",
        TARGET_DEFINES,
        "BOARD TARGETS",
    )

    # 2) Hardware names. Scope to the HARDWARE NAMES block so a generic #else
    # elsewhere cannot be selected accidentally.
    start = text.find("  //// HARDWARE NAMES")
    end = text.find("  //// END HARDWARE NAMES")
    if start == -1 or end == -1 or end <= start:
        raise RuntimeError("Could not locate HARDWARE NAMES block")
    hw = text[start:end]
    hw_anchor = '  #else\n    #define HARDWARE_NAME "ESP32"'
    if hw.count(hw_anchor) != 1:
        raise RuntimeError("Unexpected HARDWARE NAMES structure; patch aborted")
    hw = hw.replace(hw_anchor, HARDWARE_NAMES + hw_anchor, 1)
    text = text[:start] + hw + text[end:]

    # 3) Feature declarations immediately before END BOARD FEATURES.
    text = insert_once(
        text,
        "  //// END BOARD FEATURES",
        BOARD_FEATURES,
        "BOARD FEATURES",
    )

    # 4) GPS mapping for Feberis Pro. Work only inside the GPS block and insert
    # as the final board-specific branch, before the outer HAS_GPS #else.
    gps_start = text.find("  //// GPS STUFF")
    gps_end = text.find("  //// END GPS STUFF")
    if gps_start == -1 or gps_end == -1 or gps_end <= gps_start:
        raise RuntimeError("Could not locate GPS STUFF block")
    gps = text[gps_start:gps_end]
    gps_anchor = "    #endif\n  #else\n    #define mac_history_len 100"
    if gps.count(gps_anchor) != 1:
        raise RuntimeError("Unexpected GPS STUFF structure; patch aborted")
    gps = gps.replace(gps_anchor, GPS_CONFIG + gps_anchor, 1)
    text = text[:gps_start] + gps + text[gps_end:]

    validate(text)
    path.write_text(text, encoding="utf-8")
    print(f"Patched {path} successfully")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "path",
        nargs="?",
        default="esp32_marauder/configs.h",
        help="Path to ESP32Marauder configs.h",
    )
    args = parser.parse_args()

    path = Path(args.path)
    if not path.is_file():
        print(f"File not found: {path}", file=sys.stderr)
        return 2

    try:
        patch(path)
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
