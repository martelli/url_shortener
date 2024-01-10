""" base62 conformity tests
"""
import unittest

import lib.base62 as b62


class TestBase62(unittest.TestCase):
    """ base62 testing class
    """

    def test_alphabet_size(self):
        """ Ensure that the contract of 62 digits is honored.
        """
        self.assertTrue(len(b62.DIGITS) == 62)
        self.assertTrue(b62.NUM_DIGITS == 62)

    def test_hex_digest_length(self):
        """ Any call to shake128_hexdigit() must return 8 characters
        """
        hexd = b62.shake128_hexdigest("bogus")
        self.assertTrue(len(hexd) == 8)

    def test_hex_digest_empty(self):
        """ The hex value for the empty string is known.
        """
        hexd = b62.shake128_hexdigest("")
        self.assertTrue(hexd == "7f9c2ba4")

    def test_hex_digest_large(self):
        """ The hex value for the following random string is known.
        """
        hexd = b62.shake128_hexdigest(
                    "vkdjhvfdnklsdfahlkfvsgfasdnlkasdfgsdfaklgvsdf")
        self.assertTrue(hexd == "2378c647")

    def test_hex2base62_empty(self):
        """ Empty strings must raise when converting to base62.
        """
        self.assertRaises(ValueError, b62.hex2base62, "")

    def test_hex2base62_none(self):
        """ 'None' must raise when converting to base62.
        """
        self.assertRaises(ValueError, b62.hex2base62)

    def test_hex2base62_invalid(self):
        """ Invalid hex must raise when converting to base62.
        """
        self.assertRaises(ValueError, b62.hex2base62, "FF00CG")

    def test_hex2base62_int(self):
        """ Numeric types must also raise when converting to base62.
        """
        self.assertRaises(TypeError, b62.hex2base62, 1)

    def test_hex2base62_large_input(self):
        """ Hex values larger than 0xFFFFFFFF will raise an exception.
        """
        enc = b62.hex2base62("FFFFFFFF")
        self.assertTrue(enc == "4GFfc3")
        self.assertRaises(ValueError, b62.hex2base62, "100000000")

    def test_hex2base62_short_input(self):
        """ Any short hex value will result in a zero padded base62 value.
        """
        enc = b62.hex2base62("1")
        self.assertTrue(enc == "000001")
