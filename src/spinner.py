import sys
import time
import threading

class Spinner:
    def __init__(self):
        self.spinner_active = False
        self.spinner_thread = None

    def _spinner(self):
        spinner_chars = ['-', '\\', '|', '/']
        index = 0
        while self.spinner_active:
            sys.stdout.write('\x1b[D')
            sys.stdout.write(f'{spinner_chars[index]}')
            sys.stdout.flush()
            index = (index + 1) % len(spinner_chars)
            time.sleep(0.1)

    def start(self):
        self.spinner_active = True
        sys.stdout.write('  ')
        self.spinner_thread = threading.Thread(target=self._spinner)
        self.spinner_thread.start()

    def stop(self):
        self.spinner_active = False
        self.spinner_thread.join()
        sys.stdout.write('\x1b[D')
        sys.stdout.flush()

