import struct

def read_as(format, file):
    """
    Frontend to struct.unpack with automatic size inference.
    Always operates in little-endian.

    Passing `format="string"` will make it read a single null-terminated string
    from the file's current position.
    """
    if format == "string":
        text = ""
        buffer = file.read(1)
        while buffer != b"\x00":
            text += buffer.decode('ascii') # probably unsafe
            buffer = file.read(1)
        return text

    size = 0
    known_sizes = {
        "c": 1,
        "b": 1, "B": 1,
        "?": 1,
        "h": 2, "H": 2,
        "i": 4, "I": 4,
        "l": 4, "L": 4,
        "q": 8, "Q": 8,
        "e": 2, "f": 4,
        "d": 8
    }
    for i in format:
        size += known_sizes.get(i, 0)
    return struct.unpack("<"+format, file.read(size))

def write_as(format, contents, file):
    """
    Frontend to struct.pack that always operates in little-endian.

    Passing `format="string"` will make it read a single null-terminated string
    from the file's current position.
    
    contents is a tuple
    """
    if format == "string":
        file.write( contents.encode("ascii") )
        return file.write( b"\x00" )
    
    return file.write( struct.pack("<"+format, *contents) )

def read_as_single(format, file):
    """
    If the `read_as` format is a single character it'll still
    return a tuple. This function turns it into a single value.
    """
    return read_as(format, file)[0]

