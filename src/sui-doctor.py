#!/usr/bin/env python3

import subprocess
import re
import pathlib

from typing import Tuple

from spinner import Spinner

def script_dir():
  return pathlib.Path(__file__).parent.resolve()

def build_tools():
  dir = script_dir().joinpath("lib")
  subprocess.run(["make"], cwd=dir)

# TODO: ability to pass in sui db dir on command line
def find_sui_db_dir() -> str:
  # list of possible locations of the sui db
  possible_locations = [
      "/opt/sui/db",
      "/data/sui/db",
      # insert more locations here
  ]

  # iterate through each location and check if it exists
  for location in possible_locations:
    if pathlib.Path(location).exists():
      return location

  # if we get here then we didn't find the sui db
  raise Exception("could not find sui db")

def directory_to_mountpoint(directory: str) -> str:
  # get the mountpoint of the directory
  cmd = "findmnt -n -o SOURCE --target {}".format(directory)
  output = subprocess.run(cmd, shell=True, capture_output=True)
  output = output.stdout.decode("utf-8").strip()

  # if the output is empty then we didn't find a mountpoint
  if output == "":
    raise Exception("could not find mountpoint for {}".format(directory))

  return output

def check_clock_synchronization():
  output = run_command(["./check_time"], "lib/bin")

  regex = re.compile("Synchronized:.*yes", re.MULTILINE)
  match = regex.search(output)

  if match:
    return (True, output, None)
  else:
    return (False, output, "clock does not appear to be synchronized")


# function to run command and start/stop spinner
def run_command(cmd, subdir=None):
  if subdir is not None:
    cwd = script_dir().joinpath(subdir)
  else:
    cwd = None

  spinner = Spinner()
  spinner.start()
  output = subprocess.run(cmd, cwd=cwd, capture_output=True)
  spinner.stop()

  # print stderr if there is any
  if output.stderr:
    redln("stderr:")
    redln(output.stderr)

  output = output.stdout.decode("utf-8")

  return output


def parse_output(output, regex):
  match = regex.search(output)
  return float(match.group(1))

MINIMUM_NET_SPEED = 1000

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
  if disk_read_speed < 1000 or cached_read_speed < 1000:
    return (False, output, "disk read speed must be at least 1000 MB/s")
  else:
    return (True, output, None)

def check_if_sui_db_on_nvme():
  return (False, "not implemented", None)

def check_num_cpus():
  return (False, "not implemented", None)

def check_ram():
  return (False, "not implemented", None)

def check_storage_space_for_suidb():
  return (False, "not implemented", None)

def check_for_packet_loss():
  # Can just ping 8.8.8.8 to start?
  return (False, "not implemented", None)

commands = [
    check_clock_synchronization,
    check_net_speed,
    hdparm,
    check_if_sui_db_on_nvme,
    check_num_cpus,
    check_ram,
    check_storage_space_for_suidb,
    check_for_packet_loss,
]

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def boldln(text):
  bold(text + "\n")

# bold but without a newline:
def bold(text):
  print(bcolors.BOLD + text + bcolors.ENDC, end="")

def greenln(text):
  green(text + "\n")

def green(text):
  print(bcolors.OKGREEN + text + bcolors.ENDC, end="")

def redln(text):
  red(text + "\n")

def red(text):
  print(bcolors.FAIL + text + bcolors.ENDC, end="")

def yellowln(text):
  yellow(text + "\n")

def yellow(text):
  print(bcolors.WARNING + text + bcolors.ENDC, end="")


# main
if __name__ == "__main__":
  boldln("building tools...")
  build_tools()

  for cmd in commands:
    bold("\nRunning command: {}".format(cmd.__name__))

    try:
      (status, output, detail) = cmd()
    except Exception as e:
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
