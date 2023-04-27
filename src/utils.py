#!/usr/bin/env python3

import subprocess
import re
import pathlib
import os
import json

from spinner import Spinner


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


def color_print_ln(color, text):
  color(text + "\n")


def color_print(color, text, end=''):
  print(color + text + bcolors.ENDC, end=end)


  
def directory_to_mountpoint(directory: str) -> str:
  # get the mountpoint of the directory
  cmd = "findmnt -n -o SOURCE --target {}".format(directory)
  output = subprocess.run(cmd, shell=True, capture_output=True)
  output = output.stdout.decode("utf-8").strip()

  # if the output is empty then we didn't find a mountpoint
  if output == "":
    raise Exception("could not find mountpoint for {}".format(directory))

  return output


def device_path_to_device_info(device_path: pathlib.Path):
  cmd_seg_list = ["lsblk", "-JO", device_path.resolve(strict=True)]
  process = subprocess.run(cmd_seg_list, capture_output=True, check=True)

  device_info_json = process.stdout.decode("utf-8").strip()
  device_info_list = json.loads(device_info_json)["blockdevices"]

  if device_info_list:
    return device_info_list[0]
  else:
    raise RuntimeError(f"could not find device type for {device_path}")


def directory_to_device_path(dir_path: pathlib.Path):
  cmd_seg_list = ["df", "--output=source", dir_path.resolve(strict=True)]
  process = subprocess.run(cmd_seg_list, capture_output=True, check=True)

  device_output = process.stdout.decode("utf-8").strip()
  device_list = device_output.splitlines()

  if len(device_list) < 2:
      raise RuntimeError(f"could not find device path for {dir_path}")
  
  device_path = device_list[1]
  return pathlib.Path(device_path).resolve()



def directory_on_nvme(dir_path: pathlib.Path):
  device_path = directory_to_device_path(dir_path)
  device_info = device_path_to_device_info(device_path)

  return device_info["tran"] == "nvme"


# TODO: ability to pass in sui db dir on command line
def find_sui_db_dir() -> str:
  # list of possible locations of the sui db
  possible_locations = [
      "/opt/sui/db",
      "/data/sui/db",
      "/var/lib/docker/volumes/suidb",
      # insert more locations here
  ]

  # iterate through each location and check if it exists
  for location in possible_locations:
    if pathlib.Path(location).exists():
      return location

  # if we get here then we didn't find the sui db
  raise Exception("could not find sui db")


# function to run command and start/stop spinner
def run_command(cmd: str, subdir=None):
  cwd = script_dir() / subdir if subdir is not None else None

  spinner = Spinner()
  spinner.start()
  process = subprocess.run(cmd, cwd=cwd, capture_output=True, encoding="utf-8", shell=True)
  spinner.stop()

  # print stderr if there is any
  if process.stderr:
    redln("stderr:")
    redln(process.stderr)

  output = process.stdout

  return output


def script_dir():
  return pathlib.Path(__file__).parent.resolve()
  

def parse_output(output, regex):
  match = regex.search(output)
  if not match:
    raise ValueError(f"No match found for regex pattern: {regex}")
  return float(match.group(1))
