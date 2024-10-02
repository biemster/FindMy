ch592 FindMy firmware
=======================

## Installation
The ELF can be flashed to the CH592 using [wchisp](https://github.com/ch32-rs/wchisp). (Enter the CH592 bootloader by holding down BOOT when connecting it using USB).\
Also `chprog` (pip install chprog) supports the ch592 now, and since I'm a big fan of @wagiminator's work I will update these instructions soon to use that.

## Preparation
1. Replace the dummy key in the firmware using the `prep_fw.py` script like this: `./prep_fw.py <path to .keys file>`
2. Flash the new `FindMy_XXXXXXX.bin` file using `wchisp`
