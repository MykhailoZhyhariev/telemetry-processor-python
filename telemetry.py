from serial import Serial, STOPBITS_TWO
import struct


class Telemetry:
    #  Types of a data
    ONE_BYTE  = 1
    TWO_BYTE  = 2
    FOUR_BYTE = 4
    ARRAY     = 5
    FLOAT     = 6
    #  Start identifier
    START     = 33000
    #  Sign identifiers
    MINUS     = 33001
    PLUS      = 33002

    def __init__(self, port, baudrate, stopbits=STOPBITS_TWO):
        self.ser = Serial(port, baudrate, stopbits=stopbits)

    def close(self):
        self.ser.close()

    def read(self, bytes=1):
        return int.from_bytes(self.ser.read(bytes), byteorder='big')

    def read_signed(self, bytes=1):
        sign = self.read(2)
        res = self.read(bytes)
        if sign == self.MINUS:
            res *= -1
        return res

    def write(self, data):
        self.ser.write(struct.pack('>B', data))

    def receive_float(self):
        #  Receiving raw four-byte data
        raw_data = self.read(4)

        #  Getting sign from received raw digit
        sign = raw_data // (2 ** 31) & 0xFF
        #  Getting exponenta from received raw digit
        exponenta = raw_data // (2 ** 23) & 0xFF
        #  Getting mantissa from received raw digit
        mantissa = raw_data & 0x7FFFFF

        #  Calculating float digit and return it
        a = mantissa / (2 ** 23)
        return ((-1) ** sign) * (1 + a) * (2 ** (exponenta - 127))


    def receive_array(self):
        #  Receiving an array length
        len = self.read()

        #  Receiving an array type
        type = self.read()

        if type == self.FLOAT:
            #  Receiving and returning an array data
            return [self.receive_float(type) for _ in range(len)]

        #  Receiving and returning an array data
        return [self.read_signed(type) for _ in range(len)]

    def get_data(self, id):
        #  Sending identifier
        self.write(id)

        #  Receiving start identifier
        start = self.read(2)
        if start != self.START:
            return None

        #  Receiving type identifier
        type = self.read()

        #  Receiving data
        if type == self.ARRAY:
            data = self.receive_array()
        elif type == self.FLOAT:
            data = self.receive_float()
        else:
            data = self.read_signed(type)
        return data
