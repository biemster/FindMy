# FindMy firmware for Telink TLSR825x (as found in Parkside Smart Powertool Batteries)
The source for `FindMy.bin` is here: https://github.com/biemster/tlsr825x_FindMy

## How to use:
`PySerial` needs to be installed, and @pvvx's flasher needs to be cloned:
```bash
git clone https://github.com/pvvx/TlsrComSwireWriter
```
Prepare the firmware with your own key:
```bash
./prep_fw.py <path to .keys file>
```
Now it's ready to be flashed:
```bash
cd TlsrComSwireWriter
python TLSR825xComFlasher.py -p /dev/ttyUSB0 -t 1000 -r wf 0 ../FindMy/Telink_TLSR825X/FindMy_XXXXXXX.bin
```

## Special thanks to:
@pvvx for his extensive work on the Telink Bluetooth MCUs, check out https://github.com/pvvx/ATC_MiThermometer!
