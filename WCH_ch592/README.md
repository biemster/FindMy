ch592 FindMy firmware
=======================

## Installation
The `.bin` can be flashed to the CH592 using [chprog](https://github.com/wagiminator/MCU-Flash-Tools). (Enter the CH592 bootloader by holding down BOOT when connecting it using USB).

## Preparation
1. Replace the dummy key in the firmware using the `prep_fw.py` script like this (adv-interval is optional, the broadcasting interval in seconds [allowed values are 2,3,5,10,20,30]):
```bash
./prep_fw.py --keyfile=<path to .keys file> --adv-interval=5
```
2. Flash the new `FindMy_XXXXXXX.bin` file using `chprog FindMy_XXXXXXX`
