import bluetooth

eph_id = [
    0x11,0x22,0x33,0x44,0x55,0x66,0x77,0x88,0x99,0xab,
    0xba,0x99,0x88,0x77,0x66,0x55,0x44,0x33,0x22,0x11,
]

interval_ms = 300
# https://developers.google.com/nearby/fast-pair/specifications/extensions/fmdn#advertised-frames table 8
findmy_google = [
    0x02, # Length
    0x01, # Flags data type value
    0x06, # Flags data
    0x18, # Length (no hashed flags since we don't use unwanted tracking protection or battery level indication
    0x16, # Service data data type value
    0xAA, # 16-bit service UUID
    0xFE, # ...
    0x40, # FMDN frame type with unwanted tracking protection mode indication (0x40=off, 0x41=on)
    # no hashed flags byte since we don't use unwanted tracking protection or battery level indication
] + eph_id

ble = bluetooth.BLE()
ble.active(True)
ble.gap_advertise(interval_ms *1000, adv_data=bytes(findmy_google))
