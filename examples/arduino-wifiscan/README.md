How to build PlatformIO based project
=====================================

1. [Install PlatformIO Core](https://docs.platformio.org/page/core.html)
2. Download [development platform with examples](https://github.com/platformio/platform-renesas-ra/archive/develop.zip)
3. Extract ZIP archive
4. Run these commands:

```shell
# Change directory to example
$ cd platform-renesas-ra/examples/arduino-wifiscan

# Build project
$ pio run

# Upload firmware
$ pio run --target upload

# Build specific environment
$ pio run -e uno_r4_wifi

# Upload firmware for the specific environment
$ pio run -e uno_r4_wifi --target upload

# Clean build files
$ pio run --target clean
```
