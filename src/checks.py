#!/usr/bin/env python3

import glob
import os
import pathlib
import re
import shutil

from typing import Tuple

from utils import (
    directory_to_mountpoint,
    directory_on_nvme,
    find_sui_db_dir,
    parse_output,
    run_command,
)
from spinner import Spinner


# minimum limits checked by this script
MINIMUM_NET_SPEED = 1000
MINIMUM_DISK_READ_SPEED = 1000
MINIMUM_CPU_THREADS = 48
MINIMUM_MEM_TOTAL = 128000000
MINIMUM_RMEM_MAX = 104857600
MINIMUM_WMEM_MAX = 104857600
MAX_CPU_SPEED_TEST_1_SECONDS = 3.5
MAX_CPU_SPEED_TEST_2_SECONDS = 6.0


def check_clock_synchronization() -> Tuple[bool, str, str]:
  output = run_command("./check_time", "lib/bin")

  regex = re.compile("Synchronized:.*yes", re.MULTILINE)
  match = regex.search(output)

  if match:
    return (True, output, None)
  else:
    return (False, output, "clock does not appear to be synchronized")


def check_net_speed():
  # even though this is a python script is is easier to run it as a subprocess
  output = run_command("./speedtest.py", "lib/third_party")

  # this command is slow so you can use this output to test the parsing:

  #output = """
  #  Retrieving speedtest.net configuration...
  #  Testing from Local ISP (1.1.1.1)...
  #  Retrieving speedtest.net server list...
  #  Selecting best server based on ping...
  #  Hosted by KamaTera, Inc. (TinyTown USA) [5.00 km]: 10.000 ms
  #  Testing download speed................................................................................
  #  Download: 115.01 Mbit/s
  #  Testing upload speed......................................................................................................
  #  Upload: 67.65 Mbit/s
  #"""

  # now we can use it like this
  download_speed = parse_output(output, re.compile("Download: ([0-9.]+) Mbit", re.MULTILINE))
  upload_speed = parse_output(output, re.compile("Upload: ([0-9.]+) Mbit", re.MULTILINE))

  if download_speed < MINIMUM_NET_SPEED or upload_speed < MINIMUM_NET_SPEED:
    return (False, output, "both download and upload speeds must be at least {} Mbit/s".format(MINIMUM_NET_SPEED))
  else:
    return (True, output, None)


def hdparm():
  # use hdparm to check the disk speed

  # first find the sui db
  sui_db_dir = find_sui_db_dir()

  # get the mount point
  mountpoint = pathlib.Path(directory_to_mountpoint(sui_db_dir))

  # if mountpoint is attached to nvme-type disk, pass trivially
  if directory_on_nvme(mountpoint):
    return (True, f"(SKIPPING check) sui DB dir: {sui_db_dir}; mountpoint: {mountpoint}; nvme: {True}", None)

  output = run_command(f"sudo hdparm -tT --direct {mountpoint}")

  # the output of hdparm looks like this:
  # /dev/md1:
  # Timing O_DIRECT cached reads:   4452 MB in  2.00 seconds = 2226.28 MB/sec
  # Timing O_DIRECT disk reads: 5116 MB in  3.00 seconds = 1705.24 MB/sec
  #
  # parse out the cached and disk read speeds using regexes
  cached_read_speed = parse_output(output, re.compile("Timing O_DIRECT cached reads:.*= ([0-9.]+) MB/sec", re.MULTILINE))
  disk_read_speed = parse_output(output, re.compile("Timing O_DIRECT disk reads:.*= ([0-9.]+) MB/sec", re.MULTILINE))

  # convert to numbers
  cached_read_speed = float(cached_read_speed)
  disk_read_speed = float(disk_read_speed)

  # check if both numbers are above 1000 MB/s
  if disk_read_speed < MINIMUM_DISK_READ_SPEED or cached_read_speed < MINIMUM_DISK_READ_SPEED:
    return (False, output, "disk read speed must be at least {} MB/s".format(MINIMUM_DISK_READ_SPEED))
  else:
    return (True, output, None)


def check_if_sui_db_on_nvme():
  # first find the sui db
  sui_db_dir = find_sui_db_dir()

  # get the mount point
  mountpoint = pathlib.Path(directory_to_mountpoint(sui_db_dir))

  # check if mountpoint is attached to nvme-type disk
  nvme = directory_on_nvme(mountpoint)
  return (nvme, f"sui DB dir: {sui_db_dir}; mountpoint: {mountpoint}; nvme: {nvme}", None)


def check_num_cpus() -> Tuple[bool, str, str]:
  output = run_command("cat /proc/cpuinfo | grep processor | wc -l")
  return (True, output, None) if int(output) >= MINIMUM_CPU_THREADS else (False, output, "sui-node requires >= 48 CPU threads")

def check_cpu_speed() -> Tuple[bool, str, str]:
  output = run_command("./check_cpu_speed 10 10", "lib/bin")

  test_1_seconds = parse_output(output, re.compile("Test 1: average time taken: ([0-9.]+) seconds", re.MULTILINE))
  test_2_seconds = parse_output(output, re.compile("Test 2: average time taken: ([0-9.]+) seconds", re.MULTILINE))

  test_1_seconds = float(test_1_seconds)
  test_2_seconds = float(test_2_seconds)

  error = ""

  if test_1_seconds > MAX_CPU_SPEED_TEST_1_SECONDS:
    error = "Test 1 FAIL, average time greater than max, {} > {}\n".format(test_1_seconds, MAX_CPU_SPEED_TEST_1_SECONDS)

  if test_2_seconds > MAX_CPU_SPEED_TEST_2_SECONDS:
    error = error + "Test 2 FAIL, average time greater than max, {} > {}\n".format(test_2_seconds, MAX_CPU_SPEED_TEST_2_SECONDS)

  if error == "":
    return (True, output, None)
  else:
    return (False, output + "\n" + error, "Check for any CPU governors (ex power saver mode) that might throttle the CPU speed\nMake sure minimum CPU requirements are met\n")


def check_cpu_governor() -> Tuple[bool, str, str]:
    # Define the path to the scaling_governor file
    path = "/sys/devices/system/cpu/cpu*/cpufreq/scaling_governor"

    # Find all files that match the pattern
    governor_files = [f for f in glob.glob(path) if os.path.isfile(f)]

    # If there are no governor files, return True
    if not governor_files:
        return (True, "no governor detected", None)

    # Check each governor file to see if it is set to "performance"
    for file_path in governor_files:
        with open(file_path, "r") as f:
            governor = f.read().strip()

        if governor != "performance":
            return (False, governor, "CPU governor detected that is not set to performance")

    # If all governor files are set to "performance", return True
    return (True, governor, None)


def check_ram() -> Tuple[bool, str, str]:
  output = run_command("cat /proc/meminfo | grep MemTotal")
  return (True, output, None) if int(output.split()[1]) >= MINIMUM_MEM_TOTAL else (False, output, "sui-node requires >= 128G total memory")


def check_storage_space_for_suidb():
  db_dir = find_sui_db_dir()
  total, used, free = shutil.disk_usage(db_dir)
  output = "Storage space for sui db located at {} \nTotal: {} TB\nUsed: {} GB\nFree: {} GB".format(db_dir, total/(1<<40), used/(1<<30), free/(1<<30))

  if free/(1<<30) < 10:
    return False, output, "Free space left on device is very low"

  if total/(1<<40) < 1.5:
    return False, output, "Total space on device is lower than recommended 2 TB"

  return True, output, None


def check_rmem_max():
  output = run_command("cat /proc/sys/net/core/rmem_max")
  return (True, output, None) if int(output) >= MINIMUM_RMEM_MAX else (False, output, "for best network performance, increase maximum socket receive buffer size with `sysctl -w net.core.rmem_max=104857600`")


def check_wmem_max():
  output = run_command("cat /proc/sys/net/core/wmem_max")
  return (True, output, None) if int(output) >= MINIMUM_WMEM_MAX else (False, output, "for best network performance, increase maximum socket send buffer size with `sysctl -w net.core.wmem_max=104857600`")


def check_for_packet_loss():
  # Can just ping 8.8.8.8 to start?
  return (False, "not implemented", None)
