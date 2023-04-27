#!/usr/bin/env python3

import traceback
import subprocess
import pathlib

from typing import Tuple

from spinner import Spinner

from checks import (
  check_clock_synchronization,
  check_net_speed,
  hdparm,
  check_if_sui_db_on_nvme,
  check_num_cpus,
  check_ram,
  check_storage_space_for_suidb,
  check_for_packet_loss,
  check_cpu_speed,
  check_cpu_governor
)
from utils import (
  bold,
  boldln,
  bcolors,
  greenln,
  redln,
  yellowln,
  script_dir,
)


commands = [
    check_clock_synchronization,
    check_net_speed,
    hdparm,
    # check_if_sui_db_on_nvme, # There is NO value to this check
    check_num_cpus,
    check_cpu_speed,
    check_ram,
    check_storage_space_for_suidb,
    check_for_packet_loss,
    check_cpu_governor
]

def build_tools() -> None:
  dir = script_dir().joinpath("lib")
  subprocess.run(["make"], cwd=dir)


# main
if __name__ == "__main__":
  boldln("building tools...")
  build_tools()

  for cmd in commands:
    bold("\nRunning command: {}".format(cmd.__name__))

    try:
      (status, output, detail) = cmd()
    except Exception as e:
      print(traceback.format_exc())
      (status, output, detail) = (False, "command failed with exception: {}".format(e), "")

    if status:
      greenln("   [PASSED]")
      greenln(output)
    else:
      redln("   [FAILED]")
      if detail is not None:
        redln("  " + detail)
      else:
        redln("")
      yellowln(output)
