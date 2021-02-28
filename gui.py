from subprocess import run, PIPE, STDOUT
import tkinter as tk
from tkinter import messagebox
import re
from threading import Thread
from concurrent.futures import ThreadPoolExecutor


DEVICE_PATH = '/dev/i2c-1'
BRIGHTNESS_ADDRESS = '0x10'
CONTRAST_ADDRESS = '0x12'


executor = ThreadPoolExecutor(max_workers=1)
sliders = []


class BrightnessSlider:
    def __init__(self, root, address):
        self.root = root
        self.address = address
        self._job = None
        self.slider = tk.Scale(root, from_=0, to=100, orient=tk.HORIZONTAL, command=self.updateValue)
        self.slider.pack()

        self.slider.set(0)

        self.future = executor.submit(self.read_remote_value, address)

    def checkInitFuture(self):
        if self.future.done():
            print(self.future.result())
            self.slider.set(self.future.result())
            return True
        return False

    def read_remote_value(self, address):
        command = ['ddccontrol', '-r', address, f'dev:{DEVICE_PATH}']
        result = run(command, stdout=PIPE, stderr=STDOUT)
        output = result.stdout.decode('utf-8')
        if result.returncode:
            messagebox.showerror(title=f'Read {address} failed', message=output)
            return 0
        m = re.search(r'Control 0x\d+: \+\/(\d+)\/100', output, flags=re.MULTILINE)
        if not m:
            return 0
        return int(m.group(1))

    def set_remote_value(self, address, value):
        command = ['ddccontrol', '-r', address, '-w', str(value), f'dev:{DEVICE_PATH}']
        result = run(command, stdout=PIPE, stderr=STDOUT)
        output = result.stdout.decode('utf-8')
        if result.returncode:
            messagebox.showerror(title=f'Read {address} failed', message=output)
            return 0

    def updateValue(self, event):
        if self._job:
            self.root.after_cancel(self._job)
        self._job = self.root.after(1000, self._set_value)

    def _set_value(self):
        self._job = None
        new_value = self.slider.get()
        print("new value:", new_value)
        self.set_remote_value(self.address, new_value)


class MainFrame(tk.Frame):
    def __init__(self, parent):
        super(MainFrame, self).__init__(parent)
        self.root = parent
        self._job = None

        self.label = tk.Label(self, text="Brightness")
        self.label.pack(padx=20, pady=20)
        self.slider = BrightnessSlider(self, BRIGHTNESS_ADDRESS)
        sliders.append(self.slider)

        self.label = tk.Label(self, text="Contrast")
        self.label.pack(padx=20, pady=20)
        self.slider = BrightnessSlider(self, CONTRAST_ADDRESS)
        sliders.append(self.slider)


def tick():
    global sliders
    print('.')
    to_remove = []
    for slider in sliders:
        if slider.checkInitFuture():
            print('done')
            to_remove.append(slider)

    sliders = [slider for slider in sliders if slider not in to_remove]
    if sliders:
        root.after(100, tick)


if __name__ == "__main__":
    root = tk.Tk()

    main = MainFrame(root)
    main.pack(fill="both", expand=True)

    root.after(100, tick)
    root.mainloop()

# TODO: handler error messages
# set value on thread as well
