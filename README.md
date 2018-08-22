Description
------------

Telemetry is a library for simple data transfer between devices on different data protocols. This version using Serial interface.

You also can use the version of [this library](https://github.com/MikhailZhyhariev/telemetry-processor) that has been writing using `C` language.

Star this repository, if it turned out to be useful to you. Thank you :)

Supported devices:
-   orangePi;
-   raspberryPi;
-   etc...

Supported protocols:
-   UART;


Initialize and usage
--------------------

To initialize, you should make an array of dicts, that contains keys:
-   `id` - An integer value that library using to separate data;
-   `type` - The data type (one-byte, two-byte, etc...);
-   `func` - Callback function that will be called before transmitting data;
-   `info` - Dict that contains information about an array. Contains `length` and `type` keys. You should use it if a data type is `ARRAY`;

Example code initialization module:
```
# Callback functions
def one_byte_func():
    return 1

def float_func():
    return 4.5

def list_func():
    return [1, 2, 3]

# List of items
items = [
    {
        'id': 0,
        'type': Telemetry.ONE_BYTE,
        'func': one_byte_func
    },
    {
        'id': 1,
        'type': Telemetry.FLOAT,
        'func': float_func
    },
    {
        'id': 2,
        'type': Telemetry.ARRAY,
        'func': list_func,
        'info': {
            'type': Telemetry.ONE_BYTE,
            'length': 3
        }
    },
]

telemetry = Telemetry('PORT', 9600, items)
```

To transfer data, you need to use the `Telemetry.stream_data` function, that returns the received identifier.

On the receiving side, you need to use the function `Telemetry.get_data`, which takes an identifier, and returns a `dict` that contains the received data.


Data types
----------

Available type of a data:
-   `ONE_BYTE`
-   `TWO_BYTE`
-   `FOUR_BYTE`
-   `ARRAY`
-   `FLOAT`
