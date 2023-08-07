# Copyright 2014-present PlatformIO <contact@platformio.org>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import platform

from platformio.public import PlatformBase


class RenesasraPlatform(PlatformBase):
    def is_embedded(self):
        return True

    def configure_default_packages(self, variables, targets):
        def _configure_uploader_packages(package_name, interface_name):
            use_conditions = [
                interface_name in variables.get(option, "")
                for option in ("upload_protocol", "debug_tool")
            ]
            if variables.get("board"):
                board_config = self.board_config(variables.get("board"))
                use_conditions.extend(
                    [
                        interface_name in board_config.get(key, "")
                        for key in ("debug.default_tools", "upload.protocol")
                    ]
                )
            if not any(use_conditions) and package_name in self.packages:
                del self.packages[package_name]
            else:
                self.packages[package_name]["optional"] = False

        for package, interface in (
            ("tool-dfuutil-arduino", "dfu"),
            ("tool-bossac", "sam-ba"),
        ):
            _configure_uploader_packages(package, interface)

        frameworks = variables.get("pioframework", [])
        if "arduino" in frameworks:
            if variables.get("board") == "portenta_c33":
                self.frameworks["arduino"]["package"] = "framework-arduinorenesas-portenta"
                self.packages["framework-arduinorenesas-portenta"]["optional"] = False
            else:
                self.packages["framework-arduinorenesas-uno"]["optional"] = False
        if "fsp" in frameworks:
            self.packages["framework-renesas-fsp"]["optional"] = False
        if "cmsis" in frameworks:
            self.packages["framework-cmsis-renesas"]["optional"] = False

        return super().configure_default_packages(variables, targets)

    def get_boards(self, id_=None):
        result = super().get_boards(id_)
        if not result:
            return result
        if id_:
            return self._add_default_debug_tools(result)
        else:
            for key in result:
                result[key] = self._add_default_debug_tools(result[key])
        return result

    def _add_default_debug_tools(self, board):
        debug = board.manifest.get("debug", {})
        upload_protocols = board.manifest.get("upload", {}).get("protocols", [])
        if "tools" not in debug:
            debug["tools"] = {}

        for link in ("jlink", "cmsis-dap"):
            if link not in upload_protocols or link in debug["tools"]:
                continue

            if link == "jlink":
                assert debug.get("jlink_device"), (
                    "Missed J-Link Device ID for %s" % board.id
                )
                debug["tools"][link] = {
                    "server": {
                        "package": "tool-jlink",
                        "arguments": [
                            "-singlerun",
                            "-if",
                            "SWD",
                            "-select",
                            "USB",
                            "-device",
                            debug.get("jlink_device"),
                            "-port",
                            "2331",
                        ],
                        "executable": (
                            "JLinkGDBServerCL.exe"
                            if platform.system() == "Windows"
                            else "JLinkGDBServer"
                        ),
                    },
                    "onboard": link in debug.get("onboard_tools", []),
                }
            elif link == "cmsis-dap" and board.id in ("uno_r4_wifi", "uno_r4_minima"):
                hwids = board.get("build.hwids", [["0x2341", "0x1002"]])
                server_args = [
                    "-s",
                    # Note: only `uno_r4_wifi` variant folder contains an OpenOCD script
                    os.path.join(
                        self.get_package_dir("framework-arduinorenesas-uno") or "",
                        "variants",
                        "UNOWIFIR4",
                    ),
                    "-s",
                    "$PACKAGE_DIR/openocd/scripts",
                    "-f",
                    "openocd.cfg",
                    "-c",
                    "cmsis_dap_vid_pid %s %s" % (hwids[0][0], hwids[0][1]),
                ]

                debug["tools"][link] = {
                    "server": {
                        "package": "tool-openocd",
                        "executable": "bin/openocd",
                        "arguments": server_args,
                    },
                    # Derived from https://github.com/maxgerhardt/platform-renesas/blob/main/platform.py
                    # OpenOCD has no native flashing capabilities
                    # For the Renesas chips. We need to preload using the
                    # regular upload commands.
                    "load_cmds": "preload",
                    "init_cmds": [
                        "define pio_reset_halt_target",
                        "   monitor reset halt",
                        "end",
                        "define pio_reset_run_target",
                        "   monitor reset",
                        "end",
                        # make peripheral memory etc. readable
                        # since OpenOCD doesn't provide us with any target information (no flash driver etc.)
                        "set mem inaccessible-by-default off",
                        # fix to use hardware breakpoints of ARM CPU, not flash breakpoints. Doesn't break otherwise.
                        "mem 0 0x40000 ro",
                        "target extended-remote $DEBUG_PORT",
                        "$LOAD_CMDS",
                        "pio_reset_halt_target",
                        "$INIT_BREAK",
                    ],
                }

        board.manifest["debug"] = debug
        return board

    def configure_debug_session(self, debug_config):
        adapter_speed = debug_config.speed or "5000"
        server_options = debug_config.server or {}
        server_arguments = server_options.get("arguments", [])
        if "jlink" in server_options.get("executable", "").lower():
            server_arguments.extend(["-speed", adapter_speed])
