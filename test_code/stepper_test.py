import serial
import time

ser = serial.Serial()
ser.timeout = 1
ser.baudrate = 1843200
ser.port = '/dev/ttyACM0'
ser.open()

for i in range(101):
    desired_rot = i * 16 % 1600

    #ser.write(bytearray([0x0F, 0x06, 0x40, 0x0A]))
    ser.write(b'\x0E' + desired_rot.to_bytes(2, 'big') + b'\n')
    time.sleep(0.1)

ser.close()
