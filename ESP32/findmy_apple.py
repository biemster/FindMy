from machine import base_mac_addr
import binascii
import bluetooth

adv_key_b64 = 'EiM0RVZneImaq7zN3u/+7dzLuqmYh3ZlVEMyIQ=='
interval_ms = 300

public_key = list(binascii.a2b_base64(adv_key_b64))
if public_key[0] % 2:
    print('ERROR: The first byte of the public key has to be an even number,')
    print('due to limitations of the base MAC address on ESP32.')
    print('Setting the MAC address will fail.')
    print('To resolve this just generate a new key pair, since 50% of keys are affected')

findmy_apple = [
    0x1e, # Length (30)
    0xff, # Manufacturer Specific Data (type 0xff)
    0x4c, 0x00, # Company ID (Apple)
    0x12, 0x19, # Offline Finding type and length
    0x00, # State
] + public_key[-22:] + [
    0x00, # First two bits
    0x00, # Hint (0x00)
]

ble_mac = [public_key[0] | 0xc0] + public_key[1:6]
findmy_apple[29] = public_key[0] >> 6

base_mac_addr(bytearray(ble_mac[:-1] + [ble_mac[-1] -2]))

ble = bluetooth.BLE()
ble.active(True)
ble.gap_advertise(interval_ms *1000, adv_data=bytes(findmy_apple))
