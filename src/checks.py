#!/usr/bin/env python3

import re

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
MAX_CPU_SPEED_TEST_1_SECONDS = 6.7
MAX_CPU_SPEED_TEST_2_SECONDS = 6.0


def check_clock_synchronization() -> Tuple[bool, str, str]:
  output = run_command(["./check_time"], "lib/bin")

  regex = re.compile("Synchronized:.*yes", re.MULTILINE)
  match = regex.search(output)

  if match:
    return (True, output, None)
  else:
    return (False, output, "clock does not appear to be synchronized")


def check_net_speed():
  # even though this is a python script is is easier to run it as a subprocess
  output = run_command(["./speedtest.py"], "lib/third_party")

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
  mountpoint = directory_to_mountpoint(sui_db_dir)

  # if mountpoint is attached to nvme-type disk, pass trivially
  if directory_on_nvme(mountpoint):
    return (True, f"(SKIPPING check) sui dir: {sui_db_dir}; mountpoint: {mountpoint}; nvme: {True}", None)

  output = run_command(["sudo", "hdparm", "-tT", "--direct", mountpoint])

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
  mountpoint = directory_to_mountpoint(sui_db_dir)

  # check if mountpoint is attached to nvme-type disk
  nvme = mountpoint_on_nvme(mountpoint)
  return (nvme, f"sui dir: {sui_db_dir}; mountpoint: {mountpoint}; nvme: {nvme}", None)


def check_num_cpus() -> Tuple[bool, str, str]:
  output = run_command(["cat /proc/cpuinfo | grep processor | wc -l"])
  return (True, output, None) if int(output) >= MINIMUM_CPU_THREADS else (False, output, "sui-node requires >= 48 CPU threads")

def check_cpu_speed() -> Tuple[bool, str, str]:
  output = run_command(["./check_cpu_speed 10 10"], "lib/bin")

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

def check_ram() -> Tuple[bool, str, str]:
  output = run_command(["cat /proc/meminfo | grep MemTotal"])
  return (True, output, None) if int(output.split()[1]) >= MINIMUM_MEM_TOTAL else (False, output, "sui-node requires >= 128G total memory")


def check_storage_space_for_suidb():
  return (False, "not implemented", None)


def check_for_packet_loss():
  # Can just ping 8.8.8.8 to start?
  return (False, "not implemented", None)
