""" URL shortening handler tests
"""

import json
import unittest
from io import BytesIO as IO

from service import handler_factory

FAKE_URL = "http://test.com/path/file.html"


class WrapperHandler(handler_factory.AbstractUrlShorterHandler):
    """ The Wrapper class is needed so we manage the
        closing of self.wfile and suppress logging.
        When wbufsize is set to 1, wfile is a BytesIO
        instead of a SocketWriter.
    """
    wbufsize = 1

    def finish(self):
        self.wfile.flush()
        self.rfile.close()

    @property
    def base_url(self):
        return "http://bogus.com"

    def log_message(self, format, *args):  # pylint: disable=redefined-builtin
        pass


class TestUrlShorteningHandler(unittest.TestCase):
    """ Test various requests to the URL shortening handler.
    """

    def test_encoder(self):
        """ Basic successful encoder test
        """
        class MockRequest():  # pylint: disable=too-few-public-methods
            """ Mock HTTP request
            """
            # pylint: disable=unused-argument,no-self-use
            def makefile(self, *args, **kwargs):
                """ Fake request injection
                """
                tmp = {"url": FAKE_URL}
                json_content = json.dumps(tmp)
                return IO(
                    (
                        "POST /encode HTTP/1.1\n" +
                        f"Content-length: {len(json_content)}\n\n" +
                        json_content
                    ).encode("UTF-8"))

        whandler = WrapperHandler(MockRequest(), ("0.0.0.0", 8080), None)
        output = whandler.wfile.getvalue().decode("UTF-8")
        json_output = json.loads(output.split("\n")[-1])
        self.assertTrue(json_output["url"] == "http://bogus.com/40KuMk")

    def test_decoder(self):
        """ Basic successful decoder test
        """
        class MockRequest():  # pylint: disable=too-few-public-methods
            """ Mock HTTP request
            """
            # pylint: disable=unused-argument,no-self-use
            def makefile(self, *args, **kwargs):
                """ Fake request injection
                """
                return IO("GET /decode/40KuMk HTTP/1.1".encode("UTF-8"))

        handler_factory.MAP = {"40KuMk": "http://test.com/path/file.html"}
        whandler = WrapperHandler(MockRequest(), ("0.0.0.0", 8080), None)
        output = whandler.wfile.getvalue().decode("UTF-8")
        json_output = json.loads(output.split("\n")[-1])
        self.assertTrue(json_output["url"] == FAKE_URL)

    def test_redirect(self):
        """ Test 301 redirection
        """
        class MockRequest():  # pylint: disable=too-few-public-methods
            """ Mock HTTP request
            """
            # pylint: disable=unused-argument,no-self-use
            def makefile(self, *args, **kwargs):
                """ Fake request injection
                """
                return IO("GET /40KuMk HTTP/1.1".encode("UTF-8"))

        handler_factory.MAP = {"40KuMk": "http://test.com/path/file.html"}
        whandler = WrapperHandler(MockRequest(), ("0.0.0.0", 8080), None)
        output = whandler.wfile.getvalue().decode("UTF-8")
        self.assertTrue("301 Moved Permanently" in output)

    def test_incomplete_request(self):
        """ Test handling of incomplet headers
        """
        class MockRequest():  # pylint: disable=too-few-public-methods
            """ Mock HTTP request
            """
            # pylint: disable=unused-argument,no-self-use
            def makefile(self, *args, **kwargs):
                """ Fake request injection
                """
                tmp = {"url": FAKE_URL}
                json_content = json.dumps(tmp)
                return IO(
                    (
                        "POST /encode HTTP/1.1\n" +
                        json_content
                    ).encode("UTF-8"))

        whandler = WrapperHandler(MockRequest(), ("0.0.0.0", 8080), None)
        output = whandler.wfile.getvalue().decode("UTF-8")
        self.assertTrue("411 Length required" in output)

    def test_broken_json_request(self):
        """ Test invalid JSON input.
        """
        class MockRequest():  # pylint: disable=too-few-public-methods
            """ Mock HTTP request
            """
            # pylint: disable=unused-argument,no-self-use
            def makefile(self, *args, **kwargs):
                """ Fake request injection
                """
                tmp = {"url": FAKE_URL}

                # remove 2 chars to break json
                json_content = json.dumps(tmp)[:-2]

                return IO(
                    (
                        "POST /encode HTTP/1.1\n" +
                        f"Content-length: {len(json_content)}\n\n" +
                        json_content
                    ).encode("UTF-8"))

        whandler = WrapperHandler(MockRequest(), ("0.0.0.0", 8080), None)
        output = whandler.wfile.getvalue().decode("UTF-8")
        self.assertTrue("400 Bad request" in output)

    def test_missing_url_request(self):
        """ Test valid JSON with missing 'url' key.
        """
        class MockRequest():  # pylint: disable=too-few-public-methods
            """ Mock HTTP request
            """
            # pylint: disable=unused-argument,no-self-use
            def makefile(self, *args, **kwargs):
                """ Fake request injection
                """
                tmp = {"rul": FAKE_URL}
                json_content = json.dumps(tmp)
                return IO(
                    (
                        "POST /encode HTTP/1.1\n" +
                        f"Content-length: {len(json_content)}\n\n" +
                        json_content
                    ).encode("UTF-8"))

        whandler = WrapperHandler(MockRequest(), ("0.0.0.0", 8080), None)
        output = whandler.wfile.getvalue().decode("UTF-8")
        self.assertTrue("400 Bad request" in output)

    def test_missing_payload_too_large(self):
        """ Test when the provided URL is too large.
        """
        class MockRequest():  # pylint: disable=too-few-public-methods
            """ Mock HTTP request
            """
            # pylint: disable=unused-argument,no-self-use
            def makefile(self, *args, **kwargs):
                """ Fake request injection
                """
                multiplier = 2048 // len(FAKE_URL) + 1
                tmp = {"url": FAKE_URL * multiplier}
                json_content = json.dumps(tmp)
                return IO(
                    (
                        "POST /encode HTTP/1.1\n" +
                        f"Content-length: {len(json_content)}\n\n" +
                        json_content
                    ).encode("UTF-8"))

        whandler = WrapperHandler(MockRequest(), ("0.0.0.0", 8080), None)
        output = whandler.wfile.getvalue().decode("UTF-8")
        self.assertTrue("413 Payload too large" in output)
