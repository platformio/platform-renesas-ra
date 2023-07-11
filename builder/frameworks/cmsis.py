from os.path import isdir, join

from SCons.Script import DefaultEnvironment

env = DefaultEnvironment()
platform = env.PioPlatform()
board = env.BoardConfig()

env.SConscript("_bare.py")

FRAMEWORK_DIR = platform.get_package_dir("framework-cmsis-renesas")
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
        join(FRAMEWORK_DIR, "CMSIS", "Core", "Include"),
        join(FRAMEWORK_DIR, "Device", "RENESAS", "Include"),
        join(FRAMEWORK_DIR, "Device", "RENESAS", "Source"),
    ],
    LINKFLAGS=[
        "--specs=nano.specs"
    ],
    LIBPATH=[
        join(FRAMEWORK_DIR, "variants", board.get("build.variant"))
    ],
    LDSCRIPT_PATH=join(FRAMEWORK_DIR, "variants", board.get("build.variant"), "fsp.ld")
)

if board.id == "portenta_c33":
    env.Append(CPPDEFINES=[("BSP_MCU_GROUP_RA6M5", 1)])
else:
    env.Append(CPPDEFINES=[("BSP_MCU_GROUP_RA4M1", 1)])

libs = []

libs.append(env.BuildLibrary(
    join("$BUILD_DIR", "CMSISFramework"),
    join(FRAMEWORK_DIR, "Device", "RENESAS", "Source"))
)

env.Prepend(LIBS=libs)
