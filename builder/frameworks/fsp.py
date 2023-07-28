from os.path import isdir, join

from SCons.Script import DefaultEnvironment

env = DefaultEnvironment()
platform = env.PioPlatform()
board = env.BoardConfig()
variant = board.get("build.variant")

env.SConscript("_bare.py")

FRAMEWORK_DIR = platform.get_package_dir("framework-renesas-fsp")
assert isdir(FRAMEWORK_DIR)

env.Append(
    CFLAGS=[
        "-std=gnu11"
    ],

    CPPDEFINES=[
        "_RENESAS_RA_"
    ],

    CXXFLAGS=[
        "-std=gnu++17",
        "-fno-use-cxa-atexit"
    ],

    CPPPATH=[
        join(FRAMEWORK_DIR, "fsp", "inc"),
        join(FRAMEWORK_DIR, "fsp", "inc", "api"),
        join(FRAMEWORK_DIR, "fsp", "inc", "instances"),
        join(FRAMEWORK_DIR, "fsp", "src"),
        join(FRAMEWORK_DIR, "fsp", "src", "r_sce"),
        join(FRAMEWORK_DIR, "fsp", "src", "r_sce", "common"),
        join(FRAMEWORK_DIR, "fsp", "inc", "arm", "CMSIS_5", "CMSIS", "Core", "Include"),
        join(FRAMEWORK_DIR, "variants", variant),
        join(FRAMEWORK_DIR, "variants", variant, "includes", "ra_gen"),
        join(FRAMEWORK_DIR, "variants", variant, "includes", "ra_cfg", "fsp_cfg"),
        join(FRAMEWORK_DIR, "variants", variant, "includes", "ra_cfg", "fsp_cfg", "bsp"),
        join(FRAMEWORK_DIR, "variants", variant, "tmp_gen_c_files")
    ],
    LINKFLAGS=[
        "--specs=nano.specs"
    ],
    LIBPATH=[
        join(FRAMEWORK_DIR, "variants", variant)
    ],
    LDSCRIPT_PATH=join(FRAMEWORK_DIR, "variants", variant, "fsp.ld")
)

libs = []

# Extracted from ArduinoCore-Renesas\extras\e2studioProjects\Santiago\configuration.xml "raComponentSelection"
sublibs_uno_r4_x = ["r_adc", "r_agt", "r_cgc", "r_dac", "r_doc", "r_dmac", "r_dtc",
                    "r_elc", "r_gpt", "r_icu", "r_iic_master", "r_iic_slave", "r_ioport",
                    "r_kint", "r_lpm", "r_rtc", "r_sce/crypto_procedures/src/sce5", "r_sce5_ra4",
                    "r_sci_i2c", "r_sci_spi", "r_sci_uart", "r_spi", "r_usb_basic", "r_usb_pcdc",
                    "r_wdt", "r_can", "r_flash_lp", "rm_vee_flash"]
# Extracted from ArduinoCore-Renesas\extras\e2studioProjects\portenta_h33_lib
sublibs_portenta_c33 = ["r_adc", "r_agt", "r_canfd", "r_cgc", "r_crc", "r_dac", "r_dmac", "r_dtc",
                        "r_elc", "r_ether_phy", "r_ether", "r_flash_hp", "r_gpt", "r_icu", "r_iic_master",
                        "r_iic_slave", "r_ioport", "r_lpm", "r_qspi", "r_rtc",
                        "r_sce_protected/crypto_procedures/src/sce9", "r_sci_i2c", "r_sci_spi",
                        "r_sci_uart", "r_spi", "r_ssi", "r_usb_basic", "r_usb_pcdc", "r_usb_composite",
                        "r_wdt", "rm_adpcm_decoder", "r_sdhi"]
# This is always built
src_filter = [
    "-<*>",
    "+<bsp/cmsis>",
    "+<bsp/mcu/all>"
]
if board.get("build.mcu", "").lower().startswith("ra4m1"):
    src_filter.append("+<bsp/mcu/ra4m1>") # Uno R4 (Minima, WiFI)
else:
    src_filter.append("+<bsp/mcu/ra6m5>") # Portenta
if board.id in ("uno_r4_minima", "uno_r4_wifi"):
    src_filter.extend(["+<" + sublib + ">" for sublib in sublibs_uno_r4_x])
    env.Append(CPPPATH=[
        join(FRAMEWORK_DIR, "fsp", "src", "bsp", "mcu", "ra4m1"),
        join(FRAMEWORK_DIR, "fsp", "src", "r_sce", "crypto_procedures", "src", "sce5", "plainkey", "public", "inc"),
        join(FRAMEWORK_DIR, "fsp", "src", "r_sce", "crypto_procedures", "src", "sce5", "plainkey", "private", "inc")
    ])
    env.Append(CPPDEFINES=[
        ("_RA_CORE", "CM4")
    ])
elif board.id == "portenta_c33":
    src_filter.extend(["+<" + sublib + ">" for sublib in sublibs_portenta_c33])
    env.Append(CPPPATH=[
        join(FRAMEWORK_DIR, "fsp", "src", "bsp", "mcu", "ra6m5"),
        join(FRAMEWORK_DIR, "fsp", "src", "r_sce", "crypto_procedures", "src", "sce9", "plainkey", "public", "inc"),
        join(FRAMEWORK_DIR, "fsp", "src", "r_sce", "crypto_procedures", "src", "sce9", "plainkey", "private", "inc"),
        join(FRAMEWORK_DIR, "fsp", "src", "r_sce_protected", "crypto_procedures_protected", "src", "sce9", "inc", "api"),
        join(FRAMEWORK_DIR, "fsp", "src", "r_sce_protected", "crypto_procedures_protected", "src", "sce9", "inc", "instances"),
        join(FRAMEWORK_DIR, "fsp", "src", "r_sce_protected", "crypto_procedures_protected", "src", "sce9", "private", "inc"),
        join(FRAMEWORK_DIR, "fsp", "src", "r_sce_protected", "crypto_procedures_protected", "src", "sce9", "public", "inc"),
        join(FRAMEWORK_DIR, "variants", variant, "includes", "ra_cfg", "driver")
    ])
    env.Append(CPPDEFINES=[
        ("_RA_CORE", "CM33")
    ])

# Build the FSP framework
libs.append(env.BuildLibrary(
    join("$BUILD_DIR", "FSPFramework"),
    join(FRAMEWORK_DIR, "fsp", "src"),
    src_filter
    )
)
# Build the glue files
libs.append(env.BuildLibrary(
    join("$BUILD_DIR", "FSPFrameworkVariant"),
    join(FRAMEWORK_DIR, "variants", variant, "tmp_gen_c_files")))

env.Prepend(LIBS=libs)
