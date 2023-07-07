# Renesas RA: development platform for [PlatformIO](https://platformio.org)

[![Build Status](https://github.com/platformio/platform-renesas-ra/workflows/Examples/badge.svg)](https://github.com/platformio/platform-renesas-ra/actions)

Renesas Advanced (RA) 32-bit microcontrollers with the Arm Cortex-M33, -M23 and -M4 processor cores deliver key advantages compared to competitive Arm Cortex-M MCUs by providing stronger embedded security, superior CoreMark performance and ultra-low power operation.

* [Home](https://registry.platformio.org/platforms/platformio/renesas-ra) (home page in the PlatformIO Registry)
* [Documentation](https://docs.platformio.org/page/platforms/renesas-ra.html) (advanced usage, packages, boards, frameworks, etc.)

# Usage

1. [Install PlatformIO](https://platformio.org)
2. Create PlatformIO project and configure a platform option in [platformio.ini](https://docs.platformio.org/page/projectconf.html) file:

## Stable version

```ini
[env:stable]
platform = renesas-ra
board = ...
...
```

## Development version

```ini
[env:development]
platform = https://github.com/platformio/platform-renesas-ra.git
board = ...
...
```

# Configuration

Please navigate to [documentation](https://docs.platformio.org/page/platforms/renesas-ra.html).
