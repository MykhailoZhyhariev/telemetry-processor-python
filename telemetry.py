from serial import Serial, STOPBITS_TWO
import struct


class Telemetry:
    """`Telemetry` is a library for simple data transfer between devices on different data protocols. This version using Serial interface.

    Parameters
    ----------
    port : String
        Port name of the serial interface.
    baudrate : Integer
        Serial BAUDRATE.
    items : An array of the dicts
        Telemetry item. Contains: `id`, `type`, `data`, `func`, `info` keys.
    stopbits : Integer
        Number of stopbits.

    Attributes
    ----------
    ser : Object
        Serial interface object.
    items : List of the dicts.
        Telemetry items.

    """

    # Types of a data
    ONE_BYTE  = 1
    TWO_BYTE  = 2
    FOUR_BYTE = 4
    ARRAY     = 5
    FLOAT     = 6
    # Start identifier
    START     = 33000
    # Sign identifiers
    MINUS     = 33001
    PLUS      = 33002

    def __init__(self, port, baudrate, items, stopbits=STOPBITS_TWO):
        self.ser = Serial(port, baudrate, stopbits=stopbits)
        self.items = items

    def close(self):
        """
        Close Serial connection.
        """

        self.ser.close()

    def _read(self, bytes=1):
        """Reading data unsing Serial interface. For internal use only.

        Parameters
        ----------
        bytes : Integer
            Number of bytes the data.

        Returns
        -------
        type Byte, Integer,
            N-bytes data.

        """

        return int.from_bytes(self.ser._read(bytes), byteorder='big')


    def _read_signed(self, bytes=1):
        """Transforming negative data to positive. For internal use only.

        Parameters
        ----------
        bytes : Integer
            Number of bytes the data.

        Returns
        -------
        type Byte, Integer,
            N-bytes data.

        """

        # Reading two-byte "sign" identifier
        sign = self._read(2)
        # Reading n-bytes data
        res = self._read(bytes)
        # If sign is "MINUS" transform received data
        if sign == self.MINUS:
            res *= -1
        return res

    def _write(self, data):
        """Writing data using Serial interface.

        Parameters
        ----------
        data : Whatever you want :)
            Transmitting data.

        """

        self.ser._write(struct.pack('>B', data))

    def receive_float(self):
        """Receiving float digit.

        Returns
        -------
        type Float
            Received float digit.

        """

        # Receiving raw four-byte data
        raw_data = self._read(4)

        # Getting sign from received raw digit
        sign = raw_data // (2 ** 31) & 0xFF
        # Getting exponenta from received raw digit
        exponenta = raw_data // (2 ** 23) & 0xFF
        # Getting mantissa from received raw digit
        mantissa = raw_data & 0x7FFFFF

        # Calculating float digit and return it
        a = mantissa / (2 ** 23)
        return ((-1) ** sign) * (1 + a) * (2 ** (exponenta - 127))

    def receive_array(self):
        """Receiving an array.

        Returns
        -------
        type Array
            Received an array.

        """

        # Receiving an array length
        len = self._read()

        # Receiving an array type
        type = self._read()

        # Initialize an array data variable
        arr = None

        if type == self.FLOAT:
            # Receiving and returning an array data
            arr = [self.receive_float(type) for _ in range(len)]

        # Receiving and returning an array data
        arr = [self._read_signed(type) for _ in range(len)]

        # Return dict with all data information
        return {
            'data': arr,
            'type': type,
            'length': len
        }

    def transmit_array(self, arr, type, len):
        """Transmitting an array.

        Parameters
        ----------
        arr : Array
            Data array
        type : Integer
            An array items type (one-byte, two-byte, etc...)
        len : Integer
            An array length

        """

        # Transmitting an array length
        self._write(len)

        # Transmitting an array type
        self._write(type)

        # Transmitting an array items
        for item in arr:
            self._write(item)

    def data_transmit(self, item):
        """Transmitting Telemetry data.

        Parameters
        ----------
        item : Dict,
            Telemetry item that will be transmit.
            Contains: `type`, `id`, `data`, `info` keys.

        """

        # Transmitting "start" identifier
        self._write(self.START)

        # Transmitting data type identifier
        self._write(item.get('type'))

        # Getting callback function from telemetry item and call it
        func = item.get('func')
        callback = func()

        # Check data type and use a special function if a type is "float" or "array"
        if item.get('type') == self.FLOAT:
            self._write(callback)
        elif item.get('type') == self.ARRAY:
            self.transmit_array(callback.get('data'),
                                callback.get('type'),
                                callback.get('len'))
        else:
            self._write(callback)

    def stream_data(self):
        """
        Listening the Rx wire and transmitting data on request.
        """

        # Receiving data identifier
        id = self._read(2)

        for item in self.items:
            # Find telemetry item with right identifier
            if item.get('id') == id:
                # Transmitting the data
                self.data_transmit(item)

    def get_data(self, id):
        """Getting telemetry data after transmitting identifier.

        Parameters
        ----------
        id : Integer
            Data identifier.

        Returns
        -------
        type Dict
            Telemetry item that has been received.
            Contains: `type`, `data`, `info` keys.

        """

        # Sending identifier
        self._write(id)

        # Receiving start identifier
        start = self._read(2)
        if start != self.START:
            return None

        # Receiving type identifier
        type = self._read()

        # Initialize variable for array information
        arr_info = None

        # Receiving data
        if type == self.ARRAY:
            data = self.receive_array()

            # Making array info dict
            arr_info = {
                'type': data.get('type'),
                'length': data.get('length')
            }

            # Reinitialize array data
            data = data.get('data')
        elif type == self.FLOAT:
            data = self.receive_float()
        else:
            data = self._read_signed(type)

        # Returning dict with all received information
        return {
            'data': data,
            'type': type,
            'info': arr_info
        }
