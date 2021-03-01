import zmq
import multiprocessing as mp
import time
import serial

def convertToBytes(value):
    # Returns a list of 2 bytes in little endian format
    # Just truncates the value - assumes that value fits inside a short
    little = [value & (0xFF), (value >> 8) & 0xFF]
    return [hex(b) for b in little]

def convertToInt(bytes):
    # Return signed int from array of little endian bytes
    lower = int(bytes[0], 16)
    upper = int(bytes[1], 16) << 8
    value = upper | lower
    if ((value >> 15) & 0x1 == 1):
        value = value - 2**16
    return value

def serial_recv(endpoint):
    ser = serial.Serial()
    ser.timeout = 1
    ser.baudrate = 1843200
    ser.port = '/dev/tty.usbmodem14201'
    ser.open()
    context = zmq.Context()
    socket = context.socket(zmq.SUB)
    socket.setsockopt(zmq.RCVHWM, 10)
    socket.bind('tcp://localhost:5558')
    socket.subscribe('')

    command = {
        "move_zero": 0,
        "set_zero": 1,
        "set_speed": 2,
        "set_position": 3,
        "get_position": 4,
        "set_all_positions": 5,
        "set_all_speeds": 6,
        "get_all_speeds": 7
    }
    motors = ["x_val", "y_val", "z_val", "a_val"]
    while True:
        """
            Item is structured like dictionary:
                KEY         VALUE
                commmand    "move_zero", "set_zero", "set_speed", "set_position", "get_position", "set_all_positions", "set_all_speeds", "get_all_speeds"
                x_val       value (int)
                y-val       value (int)
                z_val       value (int)
                a_val       value (int)
            Each motor must be included if you want to send or receive info for that motor
        """
        item = socket.recv_pyobj()
        comm_num = item["command"]
        arr = []
        if comm_num < 5:
            val = 0
            motor = 0
            for i in range(len(motors)):
                if motors[i] in item:
                    val = item[motors[i]]
                    motor = i
            first_byte = comm_num * 4 + motor
            first_byte = first_byte.to_bytes(1, "big")
            arr = [first_byte]
            arr.extend(convertToBytes(val))

        else:
            first_byte = comm_num * 4
            first_byte = first_byte.to_bytes(1, "big")
            arr = [first_byte]
            for motor in motors:
                arr.extend(convertToBytes(item[motors]))
        arr.append(0x0A)
        ser.write(bytearray(arr))

        time.sleep(0.0001)

        if comm_num == 4 or comm_num == 7:
            if comm_num == 4:
                info = [hex(i) for i in ser.read(2)]
            else:
                info = [hex(i) for i in ser.read(8)]
            motor_positions = []
            for i in range(0, len(info), 2):
                motor_positions.append(convertToInt(info[i:i+2]))
            # TODO: Send motor_positions to main jetson processing

class SerialInterface:
    hwm = 10

    def __init__(self, endpoint, framerate=50, is_jetson=True):
        self.outfd = endpoint
        self.shutdown = mp.Event()
        self.psargs = (self.shutdown, self.outfd, self.hwm, framerate, is_jetson)
        self.ps = None

    def start(self):
        if self.ps is not None:
            raise RuntimeError("Serial Interface already running!")

        self.ps = mp.Process(target=serial_recv, args=self.psargs)
        self.ps.daemon = True
        self.ps.start()
        print(self)

    def stop(self):
        if self.ps is None:
            raise RuntimeError("Serial Interface not running")

        self.shutdown.set()
        self.ps.join()
        self.ps = None
        self.shutdown.clear()

    def __repr__(self):
        rpr = "-------Serial Interface-------\n"
        rpr += f"OUT: {self.outfd}\n"
        rpr += f"HWM: {self.hwm}\n"

        return rpr

if __name__ == "__main__":
    for val in [-1600, 1600, -1593, 1929, -2823, 1, 202, 0, -1]:
        a = convertToBytes(val)
        print(a)
        b = convertToInt(a)
        print(b)