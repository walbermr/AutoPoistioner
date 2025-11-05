import sys
import serial
import glob
import threading
import re

from typing import List, Tuple

import serial.serialutil
from .entities import Colony

class SerialWrapper:
    closeEvent = threading.Event()
    updateFinishedEvent = threading.Event()
    dataLock = threading.Lock()

    def __init__(self):
        self.ser = None
        self.data_buffer:List[str] = []
        self.correction_buffer:List[Tuple[float, float]] = []
        self._current_idx = 0
        self._adjust_point_pattern = re.compile(r"P = \([0-9]+\.[0-9]+, [0-9]+\.[0-9]+\)\n")

    def open_serial(self, device):
        print("Opening Serial")
        try:
            self.ser = serial.Serial(device, 115200, write_timeout = 1)
        except Exception as e:
            print(e)

    def get_available_ports(self):
        """ Lists serial port names

            :raises EnvironmentError:
                On unsupported or unknown platforms
            :returns:
                A list of the serial ports available on the system
        """
        if sys.platform.startswith('win'):
            ports = ['COM%s' % (i + 1) for i in range(256)]
        elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
            # this excludes your current terminal "/dev/tty"
            ports = glob.glob('/dev/tty[A-Za-z]*')
        elif sys.platform.startswith('darwin'):
            ports = glob.glob('/dev/tty.*')
        else:
            raise EnvironmentError('Unsupported platform')

        result = []
        for port in ports:
            try:
                s = serial.Serial(port)
                s.close()
                result.append(port)
            except (OSError, serial.SerialException) as e:
                print(e)
        return result
    
    def get_serial_message(self, colonies: List[Colony]):
        return ["(%.4f,%.4f)"%(i.getOffset().x, i.getOffset().y) for i in colonies]
    
    def on_close(self):
        self.closeEvent.set()

    def setPoints(self, colonies: List[Colony]):
        data = self.get_serial_message(colonies)
        with SerialWrapper.dataLock:
            self.data_buffer = data
            self._current_idx = 0

    def sendData(self, data):
        if self.ser is not None and data is not None:
            data = "PT" + data + "\n"
            print("Data sent:", data)
            try:
                self.ser.write(data.encode())
            except serial.serialutil.SerialTimeoutException:
                print("Serial Timeout")

    def serialMain(self):
        while True:
            if self.closeEvent.isSet():
                return

            if len(self.correction_buffer) == len(self.data_buffer):
                self.updateFinishedEvent.set()
            
            if self.ser is not None and self.ser.is_open:
                control_byte = self.ser.readline().decode("ascii")
                print(control_byte)

                if control_byte == 'ENTER\n':
                    # get next msg
                    with SerialWrapper.dataLock:
                        if self._current_idx < len(self.data_buffer):
                            serial_data = self.data_buffer[self._current_idx]
                            self._current_idx += 1
                        else:
                            serial_data = None
                    
                    self.sendData(serial_data)

                elif self._adjust_point_pattern.match(control_byte):
                    print("Adjusting point... ", end="")

                    if self._current_idx - 1 < 0:
                        print("point adjustment error: %d - 1 < 0" %(self._current_idx))

                    new_point = eval(control_byte[4:-1])
                    with SerialWrapper.dataLock:
                        self.correction_buffer.append(new_point)
                    
                    print("point fixed.")
