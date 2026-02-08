"""Air Quality 11 Click (ENS161) Python example.

This mirrors the MikroE demo flow:
- initialize the device
- apply default configuration (reset, idle, temperature/humidity, standard)
- read AQI-UBA, TVOC, eCO2, and AQI-S in a loop
"""

from __future__ import annotations

import argparse
import time

from smbus2 import SMBus

I2C_DEFAULT_ADDRESS = 0x53

REG_PART_ID = 0x00
REG_OPMODE = 0x10
REG_CONFIG = 0x11
REG_COMMAND = 0x12
REG_TEMP_IN = 0x13
REG_RH_IN = 0x15
REG_DEVICE_STATUS = 0x20
REG_DATA_AQI_UBA = 0x21
REG_DATA_ETVOC = 0x22
REG_DATA_ECO2 = 0x24
REG_DATA_AQI_S = 0x26
REG_DATA_T = 0x30
REG_DATA_RH = 0x32
REG_GPR_WRITE = 0x40
REG_GPR_READ = 0x48

AQI_UBA_BITMASK = 0x07

OPMODE_RESET = 0xF0
OPMODE_IDLE = 0x01
OPMODE_STANDARD = 0x02

PART_ID_ENS161 = 0x0161

TEMP_CALC_KC = 273.15
TEMP_CALC_MLT = 64.0
HUM_CALC_MLT = 512.0


def _read_word(bus: SMBus, address: int, reg: int) -> int:
    data = bus.read_i2c_block_data(address, reg, 2)
    return (data[1] << 8) | data[0]


def _write_word(bus: SMBus, address: int, reg: int, value: int) -> None:
    bus.write_i2c_block_data(address, reg, [value & 0xFF, (value >> 8) & 0xFF])


def airquality11_set_op_mode(bus: SMBus, address: int, op_mode: int) -> None:
    bus.write_byte_data(address, REG_OPMODE, op_mode)


def airquality11_set_measure_c(
    bus: SMBus,
    address: int,
    temperature_c: float,
    humidity_rh: float,
) -> None:
    temperature = int((temperature_c + TEMP_CALC_KC) * TEMP_CALC_MLT)
    humidity = int(humidity_rh * HUM_CALC_MLT)
    _write_word(bus, address, REG_TEMP_IN, temperature)
    _write_word(bus, address, REG_RH_IN, humidity)


def airquality11_get_aqi_uba(bus: SMBus, address: int) -> int:
    return bus.read_byte_data(address, REG_DATA_AQI_UBA) & AQI_UBA_BITMASK


def airquality11_get_tvoc(bus: SMBus, address: int) -> int:
    return _read_word(bus, address, REG_DATA_ETVOC)


def airquality11_get_co2(bus: SMBus, address: int) -> int:
    return _read_word(bus, address, REG_DATA_ECO2)


def airquality11_get_aqi_s(bus: SMBus, address: int) -> int:
    return _read_word(bus, address, REG_DATA_AQI_S)


def airquality11_display_aqi_uba(aqi_uba: int) -> None:
    if aqi_uba == 0x00:
        print(" AQI-UBA Rating: Exellent")
        print(" Hygienic Rating: No objections")
        print(" Recommendation: Target")
        print(" Exposure Limit: No limit")
    elif aqi_uba == 0x01:
        print(" AQI-UBA Rating: Good")
        print(" Hygienic Rating: No relevant objections")
        print(" Recommendation: Sufficient ventilation")
        print(" Exposure Limit: No limit")
    elif aqi_uba == 0x02:
        print(" AQI-UBA Rating: Moderate")
        print(" Hygienic Rating: Some objections")
        print(" Recommendation: Increased ventilation - Search for sources")
        print(" Exposure Limit: < 12 months")
    elif aqi_uba == 0x03:
        print(" AQI-UBA Rating: Poor")
        print(" Hygienic Rating: Major objections")
        print(" Recommendation: Intensified ventilation - Search for sources")
        print(" Exposure Limit: < 1 month")
    elif aqi_uba == 0x04:
        print(" AQI-UBA Rating: Unhealthy")
        print(" Hygienic Rating: Situation not acceptable")
        print(" Recommendation: Use only if unavoidable - Intensified ventilation recommended")
        print(" Exposure Limit: hours")
    else:
        print(" AQI-UBA Rating: Unknown")

    print("- - - - - - - - - - - - - - -")


def application_init(bus: SMBus, address: int) -> None:
    part_id = _read_word(bus, address, REG_PART_ID)
    if part_id != PART_ID_ENS161:
        raise RuntimeError(f"Unexpected PART_ID 0x{part_id:04X}")

    airquality11_set_op_mode(bus, address, OPMODE_RESET)
    time.sleep(0.1)

    airquality11_set_op_mode(bus, address, OPMODE_IDLE)
    time.sleep(0.01)

    airquality11_set_measure_c(bus, address, temperature_c=25.0, humidity_rh=50.0)
    time.sleep(0.01)

    airquality11_set_op_mode(bus, address, OPMODE_STANDARD)
    time.sleep(0.01)

    print(" Application Task ")
    print("---------------------------")


def application_task(bus: SMBus, address: int, interval_s: float) -> None:
    aqi_uba = airquality11_get_aqi_uba(bus, address)
    airquality11_display_aqi_uba(aqi_uba)
    time.sleep(0.1)

    tvoc_ppb = airquality11_get_tvoc(bus, address)
    print(f" TVOC: {tvoc_ppb} [ppb]")
    time.sleep(0.1)

    co2_ppm = airquality11_get_co2(bus, address)
    print(f" ECO2: {co2_ppm} [ppm]")
    time.sleep(0.1)

    aqi_s = airquality11_get_aqi_s(bus, address)
    print(f" AQIS: {aqi_s} [idx]")
    time.sleep(0.1)

    print("---------------------------")
    time.sleep(interval_s)


def main() -> None:
    parser = argparse.ArgumentParser(description="Air Quality 11 Click Python example")
    parser.add_argument("--bus", type=int, default=1, help="I2C bus number (default: 1)")
    parser.add_argument(
        "--address",
        type=lambda value: int(value, 0),
        default=I2C_DEFAULT_ADDRESS,
        help="I2C address in hex or decimal (default: 0x53)",
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=1.0,
        help="Delay between measurement cycles in seconds (default: 1.0)",
    )
    args = parser.parse_args()

    with SMBus(args.bus) as bus:
        application_init(bus, args.address)
        while True:
            application_task(bus, args.address, args.interval)


if __name__ == "__main__":
    main()
