#!/usr/bin/env python3

import subprocess
import re
import pathlib
import os
import json
import logging
import functools

from spinner import Spinner
from invocation import capture_function_invocation


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

def directory_to_mountpoint(directory: str) -> str:
  # get the mountpoint of the directory
  output = run_command(f"findmnt -n -o SOURCE --target {directory}").strip()

  # if the output is empty then we didn't find a mountpoint
  if not output:
    raise Exception(f"could not find mountpoint for {directory}")

  return output


def device_path_to_device_info(device_path: pathlib.Path):
  device_path = device_path.resolve(strict=True)

  device_info_json = run_command(f"lsblk -JO {device_path}", check=True).strip()
  device_info_list = json.loads(device_info_json)["blockdevices"]

  if device_info_list:
    return device_info_list[0]
  else:
    raise RuntimeError(f"could not find device type for {device_path}")


def directory_to_device_path(dir_path: pathlib.Path):
  dir_path = dir_path.resolve(strict=True)

  device_output = run_command(f"df --output=source {dir_path}", check=True).strip()
  device_list = device_output.splitlines()

  if len(device_list) < 2:
      raise RuntimeError(f"could not find device path for {dir_path}")
  
  device_path = device_list[1]
  return pathlib.Path(device_path).resolve()



def directory_on_nvme(dir_path: pathlib.Path):
  device_path = directory_to_device_path(dir_path)
  device_info = device_path_to_device_info(device_path)

  return device_info["tran"] == "nvme"

CACHED_SUIDB_DIR = None

# TODO: ability to pass in sui db dir on command line
def find_sui_db_dir() -> str:
  global CACHED_SUIDB_DIR
  if not CACHED_SUIDB_DIR:
    CACHED_SUIDB_DIR = find_sui_db_dir_impl()
  return CACHED_SUIDB_DIR

def find_sui_db_dir_impl() -> str:
  # look for a running sui node and use its config path
  output = run_command(f"ps ax | grep 'sui-nod[e]' | grep -o '[-]-config-path [^ ]*' | cut -d' ' -f2")
  if output:
    # open the config file, search for a line that starts with 'db-path:'
    config_path = output.strip()
    logging.debug(f"-- found sui node config path: {config_path}")
    config_path = pathlib.Path(config_path).resolve(strict=True)
    with open(config_path, "r") as f:
      for line in f:
        if line.startswith("db-path:"):
          sui_db_dir = line.split(":", 1)[1].strip()
          logging.debug(f"-- found sui db dir: {sui_db_dir}")
          return sui_db_dir

  # search for it with find
  output = run_command("find / -maxdepth 6 -type d -name authorities_db 2> /dev/null | head -1")
  if output:
    return output.strip()

  # as a last resort, try some possible known locations of the sui db
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
def run_command(cmd: str, subdir=None, *, check=False):
  cwd = script_dir() / subdir if subdir else None

  logging.debug("-- run_command: " + cmd)
  logging.debug("-- -- cwd: " + str(cwd))

  spinner = Spinner()
  spinner.start()
  process = subprocess.run(cmd, check=check, cwd=cwd, capture_output=True, encoding="utf-8", shell=True)
  spinner.stop()

  # print stderr if there is any
  if process.stderr:
    redln("stderr:")
    redln(process.stderr)

  logging.debug("-- -- stdout: " + json.dumps(process.stdout))
  logging.debug("-- -- stderr: " + json.dumps(process.stderr))

  return process.stdout


def script_dir():
  return pathlib.Path(__file__).parent.resolve()
  

@functools.lru_cache
@capture_function_invocation(output="invocation.log")
def parse_output(output, regex):
  match = regex.search(output)
  if not match:
    raise ValueError(f"RegexError\nRegex: {regex}\nOutput:\n{output}\nThe regex pattern could not be found in the output!")
  return float(match.group(1))
