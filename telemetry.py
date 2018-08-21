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

    def __init__(self, port, baudrate, items, stopbits=STOPBITS_TWO):
        self.ser = Serial(port, baudrate, stopbits=stopbits)

        self.items = items

    def close(self):
        self.ser.close()

    def _read(self, bytes=1):
        return int.from_bytes(self.ser._read(bytes), byteorder='big')

    def _read_signed(self, bytes=1):
        sign = self._read(2)
        res = self._read(bytes)
        if sign == self.MINUS:
            res *= -1
        return res

    def _write(self, data):
        self.ser._write(struct.pack('>B', data))

    def receive_float(self):
        #  Receiving raw four-byte data
        raw_data = self._read(4)

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
        len = self._read()

        #  Receiving an array type
        type = self._read()

        if type == self.FLOAT:
            #  Receiving and returning an array data
            return [self.receive_float(type) for _ in range(len)]

        #  Receiving and returning an array data
        return [self._read_signed(type) for _ in range(len)]

    def transmit_array(self, arr, type, len):
        # Transmitting an array length
        self._write(len)

        # Transmitting an array type
        self._write(type)

        # Transmitting an array items
        for item in arr:
            self._write(item)

    def data_transmit(self, item):
        self._write(self.START)

        self._write(item.get('type'))

        func = item.get('func')
        callback = func()

        if item.get('type') == self.FLOAT:
            self._write(callback)
        elif item.get('type') == self.ARRAY:
            self.transmit_array(callback, 
                                callback.get('type'),
                                len(callback))
        else:
            self._write(callback)

    def get_data(self, id):
        #  Sending identifier
        self._write(id)

        #  Receiving start identifier
        start = self._read(2)
        if start != self.START:
            return None

        #  Receiving type identifier
        type = self._read()

        #  Receiving data
        if type == self.ARRAY:
            data = self.receive_array()
        elif type == self.FLOAT:
            data = self.receive_float()
        else:
            data = self._read_signed(type)
        return data
