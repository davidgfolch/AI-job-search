"""Minimal CRX3 header reader used to derive a stable extension ID."""
import hashlib
import struct


def crx3_public_key(crx_path):
    data = crx_path.read_bytes()
    if data[:4] != b"Cr24":
        raise ValueError(f"Chrome did not produce a CRX: {crx_path}")
    version, header_len = struct.unpack("<II", data[4:12])
    if version != 3:
        raise ValueError(f"CRX version {version} is not supported; Chrome must pack CRX3")
    for field, value in _fields(data[12:12 + header_len]):
        if field == 2 and isinstance(value, bytes):
            for inner, payload in _fields(value):
                if inner == 1 and isinstance(payload, bytes):
                    return payload
    raise ValueError("CRX3 header contains no RSA public key")


def extension_id(public_key):
    digest = hashlib.sha256(public_key).hexdigest()[:32]
    return "".join(chr(ord("a") + int(char, 16)) for char in digest)


def _varint(data, index):
    value, shift = 0, 0
    while True:
        byte = data[index]
        index += 1
        value |= (byte & 127) << shift
        shift += 7
        if not byte & 128:
            return value, index


def _fields(data):
    index = 0
    while index < len(data):
        key, index = _varint(data, index)
        field, wire = key >> 3, key & 7
        if wire == 0:
            value, index = _varint(data, index)
        elif wire == 2:
            length, index = _varint(data, index)
            value = data[index:index + length]
            index += length
        else:
            raise ValueError(f"Unsupported protobuf wire type {wire} in CRX3 header")
        yield field, value
