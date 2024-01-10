""" URL shortening HTTP handler implementation
"""

import abc
import json
import urllib.parse as urlparse
import http.server as http

from lib import base62

# the limit below was arbitrarily derived by looking at various
# limits imposed by browsers, frameworks, servers and CDNs.
# 2048 is a conservative lower bound.
MAX_URL_LENGTH = 2048

# Global mapping 'database'
MAP = {}


class AbstractUrlShorterHandler(http.BaseHTTPRequestHandler,
                                metaclass=abc.ABCMeta):
    """ URL shortening abstract handler class.
        The concrete version needs to implement the `base_url()` method.
        This allows us to pass a base URL argument to the concrete handler.
    """
    @property
    @abc.abstractmethod
    def base_url(self):
        """ Abstract property
        """

    def do_POST(self):  # pylint: disable=invalid-name
        """ Accept a POST with the path /encode only.
            Everything else will result in a 404.
            A valid request is in JSON format as
            {'url': 'http://yyy.com'}
            If the request is valid, encode the URL
            and store it in the global dictionary.
        """
        if self.path != "/encode":
            self.ret_code(404, "Not found")
            return

        try:
            content_length = int(self.headers["Content-Length"])
        except TypeError:
            self.log_message("Missing content length: '%s'", self.headers)
            self.ret_code(411, "Length required")
            return

        if content_length > MAX_URL_LENGTH:
            self.ret_code(413, "Payload too large")
            return

        doc = self.rfile.read(content_length)

        try:
            json_content = json.loads(doc)
        except json.decoder.JSONDecodeError:
            self.log_message("Malformed JSON request: %s", doc.decode("UTF-8"))
            self.ret_code(400, "Bad request")
            return

        try:
            url = json_content["url"]
        except KeyError:
            self.log_message("Missing url in JSON request: %s",
                             doc.decode("UTF-8"))
            self.ret_code(400, "Bad request")
            return

        key = base62.encode(url)
        MAP[key] = url
        link = urlparse.urljoin(self.base_url, key)
        self.ret_json(link)

    def do_GET(self):  # pylint: disable=invalid-name
        """ When receiving a GET request, we evaluate its route.
        If in the form of /decode/<key>, we return as json
        containing the referred URL.
        If in the form of /<key>, we issue a redirect.
        If the request it /debug, dump the memory content to the console.
        For everything else, we reply with a 404.
        """
        path_tokens = self.path.split("/")

        if self.path == "/debug":
            self.ret_debug()
            return

        key_position = 1  # we assume the /<key> by default
        ret_func = self.ret_redirect
        if path_tokens[1] == "decode":
            ret_func = self.ret_json
            key_position = 2

        # return 404 if not in the format /<key> or if key is not found:
        if len(path_tokens) > key_position + 1 or \
                not (link := MAP.get(path_tokens[key_position])):
            self.ret_code(404, "Not found")
            return

        ret_func(link)

    def ret_redirect(self, link):
        """ Redirect the browser to the encoded URL
        """
        self.send_response(301)
        self.send_header("Location", link)
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        self.wfile.write(f"""<html><head><title>{self.base_url} service</title>
</head><body>
a href="{link}">moved here</a>
</body></html>""".encode("UTF-8"))

    def ret_code(self, code, message):
        """ Return a HTTP code and message to the client
        """
        self.send_response_only(code, message)
        self.end_headers()

    def ret_json(self, link):
        """ Return a json containing the decoded URL.
        """
        response = {"url": link}
        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(response).encode("UTF-8"))

    def ret_debug(self):
        """ Empty return, just for debugging purposes.
        """
        self.log_message("===== start map dump =====")
        for key, value in MAP.items():
            self.log_message("%s: %s", key, value)
        self.log_message("===== end map dump =====")

        self.send_response(200)
        self.end_headers()


def get_handler(baseurl):
    """ Returns a concrete handler where the base URL is defined.
    """
    class UrlShorterHandler(AbstractUrlShorterHandler):
        """ Concrete URL shortening class
        """
        @property
        def base_url(self):
            """ Base URL for short URL building.
            """
            return baseurl

    return UrlShorterHandler
