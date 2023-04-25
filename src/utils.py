#!/usr/bin/env python3

import subprocess
import re
import pathlib

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

  
def directory_to_mountpoint(directory: str) -> str:
  # get the mountpoint of the directory
  cmd = "findmnt -n -o SOURCE --target {}".format(directory)
  output = subprocess.run(cmd, shell=True, capture_output=True)
  output = output.stdout.decode("utf-8").strip()

  # if the output is empty then we didn't find a mountpoint
  if output == "":
    raise Exception("could not find mountpoint for {}".format(directory))

  return output


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
def run_command(cmd, subdir=None):
  if subdir is not None:
    cwd = script_dir().joinpath(subdir)
  else:
    cwd = None

  spinner = Spinner()
  spinner.start()
  output = subprocess.run(cmd, cwd=cwd, capture_output=True, shell=True)
  spinner.stop()

  # print stderr if there is any
  if output.stderr:
    redln("stderr:")
    redln(output.stderr)

  output = output.stdout.decode("utf-8")

  return output


def script_dir():
  return pathlib.Path(__file__).parent.resolve()
  

def parse_output(output, regex):
  match = regex.search(output)
  return float(match.group(1))
