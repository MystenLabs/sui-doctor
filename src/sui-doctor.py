#!/usr/bin/env python3

import traceback
import pathlib
import logging
import json

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
  check_rmem_max,
  check_wmem_max,
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
  run_command,
)


commands = [
    check_clock_synchronization,
    check_net_speed,
    hdparm,
    check_num_cpus,
    check_cpu_speed,
    check_ram,
    check_storage_space_for_suidb,
    check_rmem_max,
    check_wmem_max,
    # check_for_packet_loss,
    check_cpu_governor
]

def build_tools() -> None:
  run_command("make", "lib")


# main
if __name__ == "__main__":
  logging.basicConfig(filename="sui-doctor.log", encoding="utf8", level=logging.DEBUG, filemode="w")
  boldln("building tools...")
  build_tools()

  for cmd in commands:
    logging.info("Running check: {}".format(cmd.__name__))
    bold("\nRunning command: {}".format(cmd.__name__))

    try:
      (status, output, detail) = cmd()
      logging.info("status: " + str(status))
      logging.info("output: " + json.dumps(output))
      logging.info("detail: " + json.dumps(detail))
    except Exception as e:
      logging.info("command failed: " + json.dumps(traceback.format_exc()))
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
