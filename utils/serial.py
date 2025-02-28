import sys
import serial
import glob

from typing import List

import serial.serialutil
from .entities import Colony

class SerialWrapper:
    def __init__(self):
        self.ser = None

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
            except (OSError, serial.SerialException):
                pass
        return result
    
    def get_serial_message(self, colonies: List[Colony]):
        return ''.join(["%.4f,%.4f"%(i.getOffset().x, i.getOffset().y) for i in colonies])

    def sendData(self, data):
        if self.ser is not None:
            data += "\n"
            print(data, end='')
            try:
                self.ser.write(data.encode())
            except serial.serialutil.SerialTimeoutException:
                print("Serial Timeout")
