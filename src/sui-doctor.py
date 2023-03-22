#!/usr/bin/env python3

import subprocess
import re
import pathlib

def script_dir():
  return pathlib.Path(__file__).parent.resolve()

def build_tools():
  dir = script_dir().joinpath("lib")
  subprocess.run(["make"], cwd=dir)

def check_clock_synchronization():
  dir = script_dir().joinpath("lib/bin")
  output = subprocess.run(["./check_time"], cwd=dir, capture_output=True)

  regex = re.compile("Synchronized:.*yes", re.MULTILINE)
  match = regex.search(output.stdout.decode("utf-8"))

  if match:
    return (True, output)
  else:
    return (False, output)


commands = [
    check_clock_synchronization,
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

def bold(text):
  print(bcolors.BOLD + text + bcolors.ENDC)

def green(text):
  print(bcolors.OKGREEN + text + bcolors.ENDC)

def red(text):
  print(bcolors.FAIL + text + bcolors.ENDC)

def yellow(text):
  print(bcolors.WARNING + text + bcolors.ENDC)

# main
if __name__ == "__main__":
  bold("building tools...")
  build_tools()

  for cmd in commands:
    bold("\nRunning command: {}".format(cmd.__name__))

    (status, output) = cmd()
    output = output.stdout.decode("utf-8")

    if status:
      bold("check passed")
      green(output)
    else:
      red("check failed")
      yellow(output)
