How to build PlatformIO based project
=====================================

1. [Install PlatformIO Core](https://docs.platformio.org/page/core.html)
2. Download [development platform with examples](https://github.com/platformio/platform-renesas-ra/archive/develop.zip)
3. Extract ZIP archive
4. Run these commands:

```shell
# Change directory to example
$ cd platform-renesas-ra/examples/fsp-blink

# Build project
$ pio run

# Upload firmware
$ pio run --target upload

# Clean build files
$ pio run --target clean
```

Note
----

Since this firmware does not include native USB functionality, on the Uno R4 Minima and Portenta C33, you will have to quickly double-press the reset button to enter bootloader mode again in order to upload a new firmware. The bootloader itself is **not** overwritten by this firmware.