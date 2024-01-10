"""A simple base62 encoding library.

   Any input string will be encoded to as 6 digit number in base 62.

   6 digits in base62 means 62^6 possibilities.
   Internally we further limit it to 2^32 by requesting shake_128() to
   output 4 bytes (32 bits).
   This guarantees that the limit of 62^6 will not be overflown, so there
   will be no collisions for allowed values.
"""

import hashlib


# 62 possible digits
DIGITS = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
NUM_DIGITS = 62

# this allows us to detect any unattended errors to the DIGITS string:
assert NUM_DIGITS == len(DIGITS)


def hex2base62(hex_value=""):
    """Encodes a decimal value as a base 62 number with the given DIGITS above.

       Since 62**2 > 2**32, we fix the output in 6 base62 digits.
    """
    output = []

    if (int_value := int(hex_value, 16)) > 4294967295:
        raise ValueError(f"{int_value} is too large")

    # forcefully generate 6 digits, thus padding smaller values
    for _ in range(6):
        int_value, remainder = divmod(int_value, NUM_DIGITS)
        output.append(DIGITS[remainder])
    return "".join(reversed(output))


def shake128_hexdigest(content=""):
    """Hashes a string using 'shake_128' and returns a 32 bit hash in hex.
    'shake_128' is used because it allows for an arbitrary output
    size and we are not concerned about the cryptographic security aspect.

    The number 32 is used because it's close to the desired domain:

    [A-Z][a-z][0-9] * 6 => 62**6 =~ 2**35, thus 32 bits will not overflow
    the base62 space.
    """
    h_obj = hashlib.shake_128()
    h_obj.update(content.encode("UTF-8"))

    # requests 4 bytes, thus a 32 bit output
    return h_obj.hexdigest(4)  # pylint: disable=too-many-function-args


def encode(value):
    """Encodes a given URL as a base62 value.
    """
    vhash = shake128_hexdigest(value)
    return hex2base62(vhash)
