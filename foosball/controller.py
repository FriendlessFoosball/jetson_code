import zmq
import multiprocessing as mp
import time
import serial

from struct import pack, unpack

def convertToBytes(b):
    # Returns a list of 2 bytes in little endian format
    # Just truncates the value - assumes that value fits inside a short
    # little = [value & (0xFF), (value >> 8) & 0xFF]
    # return [hex(b) for b in little]

    # b = value.to_bytes(2, 'big')
    # return [b[0], b[1]]

    s = pack('>h', b)
    return [s[0], s[1]]

def convertToInt(b):
    # Return signed int from array of little endian bytes
    # lower = int(bytes[0], 16)
    # upper = int(bytes[1], 16) << 8
    # value = upper | lower
    # if ((value >> 15) & 0x1 == 1):
    #     value = value - 2**16
    # return value

    return unpack('>h', b)[0]

def controller_ps(shutdown, infd, outfd, hwm):
    ser = serial.Serial()
    ser.timeout = 1
    ser.baudrate = 1843200
    ser.port = '/dev/ttyACM0'
    ser.open()

    context = zmq.Context()

    socket = context.socket(zmq.SUB)
    socket.setsockopt(zmq.RCVHWM, 10)
    # socket.bind('tcp://localhost:5558')
    socket.connect(infd)
    socket.subscribe('')

    out_s = context.socket(zmq.PUB)
    out_s.setsockopt(zmq.SNDHWM, 10)
    out_s.bind(outfd)

    command = {
        "move_zero": 0,
        "set_zero": 1,
        "set_speed": 2,
        "set_position": 3,
        "get_position": 4,
        "set_all_positions": 5,
        "set_all_speeds": 6,
        "get_all_positions": 7
    }
    motors = ["goalie_lin", "offense_lin", "goalie_ang", "offense_ang"]

    while not shutdown.is_set():
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
        if 'command' not in item:
            continue
        
        if item['command'] not in command:
            continue

        comm_num = command[item["command"]]
        arr = []
        if comm_num < 5:
            val = 0
            motor = 0
            for i in range(len(motors)):
                if motors[i] in item:
                    val = item[motors[i]]
                    motor = i
            first_byte = comm_num * 4 + motor
            first_byte = first_byte.to_bytes(1, "big")[0]
            arr = [first_byte]
            arr.extend(convertToBytes(val))

        elif comm_num < 7:
            first_byte = comm_num * 4
            first_byte = first_byte.to_bytes(1, "big")[0]
            arr = [first_byte]
            for motor in motors:
                arr.extend(convertToBytes(item[motor]))
        else:
            first_byte = comm_num * 4
            first_byte = first_byte.to_bytes(1, "big")[0]
            arr = [first_byte]
        arr.append(0x0A)
        ser.write(bytearray(arr))
        print(f"Sent {arr}")

        time.sleep(0.0001)

        if comm_num == 4 or comm_num == 7:
            if comm_num == 4:
                info = ser.read(2)
            else:
                info = ser.read(8)
            motor_positions = []
            for i in range(0, len(info), 2):
                motor_positions.append(convertToInt(info[i:i+2]))
            # Send motor_positions to main jetson processing
            out_s.send_pyobj(motor_positions)

    ser.close()

class Controller:
    hwm = 10

    def __init__(self, infd, outfd):
        self.infd = infd
        self.outfd = outfd
        self.shutdown = mp.Event()
        self.psargs = (self.shutdown, self.infd, self.outfd, self.hwm)
        self.ps = None

    def start(self):
        if self.ps is not None:
            raise RuntimeError("Controller already running!")

        self.ps = mp.Process(target=controller_ps, args=self.psargs)
        self.ps.daemon = True
        self.ps.start()
        print(self)

    def stop(self):
        if self.ps is None:
            raise RuntimeError("Controller not running")

        self.shutdown.set()
        self.ps.join()
        self.ps = None
        self.shutdown.clear()

    def __repr__(self):
        rpr = "-------Controller-------\n"
        rpr += f"OUT: {self.outfd}\n"
        rpr += f"HWM: {self.hwm}\n"

        return rpr

if __name__ == "__main__":
    for val in [-1600, 1600, -1593, 1929, -2823, 1, 202, 0, -1]:
        a = convertToBytes(val)
        print(a)
        b = convertToInt(a)
        print(b)