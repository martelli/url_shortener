## Running the code
After fetching the repository, simply run:

`python3 path/to/repo/short-url-izwgji/shortlink.py`

Alternatively, the python file can be make executable:

`chmod +x path/to/repo/short-url-izwgji/shortlink.py`
and then run it directly:
`path/to/repo/short-url-izwgji/shortlink.py`

The CLI accepts a few arguments:
```
./shortlink.py --help
usage: shortlink.py [-h] [--address ADDRESS] [--port PORT] [--baseurl BASEURL]

URL shortening HTTP service

options:
  -h, --help         show this help message and exit
  --address ADDRESS  IP address to bind to
  --port PORT        IP port to listen at
  --baseurl BASEURL  Base URL to build the shortened version
  ```

*Address*: IP address to bind to (eg: `127.0.0.1` or `0.0.0.0`).
*Port*: TCP port to listen at (default `8000`).
*BaseUrl*: base URL to be prefixed to the encoded token. This is to allow the service to run behind a reverse proxy without the need to mangle the URL returned to the client (default `http://short.est`).
In the default case, the server will listen at the address `0.0.0.0:8000` and reply with short URLs in the form `http://short.est/<token>`.

As an example, if we only had a public IP address with no port redirection, we'd call:
```
./shortlink.py --baseurl http://12.34.56.78:8000
```
And the generated URL would be like: `http://12.34.56.78:8000/0PtJR0`.

## Manual Testing
Testing was done with `curl`:

```
$ ./shortlink.py
Listening on address: 0.0.0.0:8000
```
/encode:
```
curl -v -d '{"url": "https://chat.openai.com/chat"}' http://localhost:8000/encode
*   Trying 127.0.0.1:8000...
* Connected to localhost (127.0.0.1) port 8000 (#0)
> POST /encode HTTP/1.1
> Host: localhost:8000
> User-Agent: curl/7.81.0
> Accept: */*
> Content-Length: 39
> Content-Type: application/x-www-form-urlencoded
>
* Mark bundle as not supporting multiuse
* HTTP 1.0, assume close after body
< HTTP/1.0 200 OK
< Server: BaseHTTP/0.6 Python/3.10.6
< Date: Wed, 22 Mar 2023 04:29:56 GMT
< Content-type: application/json
<
* Closing connection 0
{"url": "http://short.est/0PtJR0"}
```
/decode:
```
curl -v  http://localhost:8000/decode/0PtJR0
*   Trying 127.0.0.1:8000...
* Connected to localhost (127.0.0.1) port 8000 (#0)
> GET /decode/0PtJR0 HTTP/1.1
> Host: localhost:8000
> User-Agent: curl/7.81.0
> Accept: */*
>
* Mark bundle as not supporting multiuse
* HTTP 1.0, assume close after body
< HTTP/1.0 200 OK
< Server: BaseHTTP/0.6 Python/3.10.6
< Date: Wed, 22 Mar 2023 04:27:39 GMT
< Content-type: application/json
<
* Closing connection 0
{"url": "https://chat.openai.com/chat"}
```
Redirection:
```
 curl -v  http://localhost:8000/0PtJR0
*   Trying 127.0.0.1:8000...
* Connected to localhost (127.0.0.1) port 8000 (#0)
> GET /0PtJR0 HTTP/1.1
> Host: localhost:8000
> User-Agent: curl/7.81.0
> Accept: */*
>
* Mark bundle as not supporting multiuse
* HTTP 1.0, assume close after body
< HTTP/1.0 301 Moved Permanently
< Server: BaseHTTP/0.6 Python/3.10.6
< Date: Wed, 22 Mar 2023 04:27:57 GMT
< Location: https://chat.openai.com/chat
<
<html><head><title>http://short.est service</title></head>
* Closing connection 0
<body><a href="https://chat.openai.com/chat">moved here</a></body></html>
```
Debugging:
```
curl -v  http://localhost:8000/debug
```
```
Listening on address: 0.0.0.0:8000
127.0.0.1 - - [22/Mar/2023 05:27:15] "POST /encode HTTP/1.1" 200 -
127.0.0.1 - - [22/Mar/2023 05:27:39] "GET /decode/0PtJR0 HTTP/1.1" 200 -
127.0.0.1 - - [22/Mar/2023 05:27:57] "GET /0PtJR0 HTTP/1.1" 301 -
127.0.0.1 - - [22/Mar/2023 05:28:33] ===== start map dump =====
127.0.0.1 - - [22/Mar/2023 05:28:33] 0PtJR0: https://chat.openai.com/chat
127.0.0.1 - - [22/Mar/2023 05:28:33] ===== end map dump =====
127.0.0.1 - - [22/Mar/2023 05:28:33] "GET /debug HTTP/1.1" 200 -
```

## Automated testing
From the main directory, run:

```
$ python3 -m unittest discover .
................
----------------------------------------------------------------------
Ran 16 tests in 0.001s

OK
```

## Linter & PEP-8
I've used a standart, non-tuned linter:

```
pylint --enable-all-extensions service/*py lib/*py shortlink.py

------------------------------------
Your code has been rated at 10.00/10

```

Also ran the `pep8` tool on the code:
```
$ pep8 -v service/*py lib/*py shortlink.py
checking service/handler_factory.py
checking service/__init__.py
checking service/test_handler.py
checking lib/base62.py
checking lib/__init__.py
checking lib/test_base62.py
checking shortlink.py
```

## Comments

I've implemented the requested `/encode` and `/decode` endpoints. Both will output content as JSON and also the `encode` endpoint accepts input as JSON only.

Additionally, added the /debug (for inspecting memory contents) and /<key> to allow for browser redirection testing.

I'll leave comments here since I did coding on two sprints and basically commited once I was satisfied. This caused me to miss leaving the full work history  through the commits and therefore I'm explaining some of it here.

I've started with the encoding algorithm, for which I've used a sponge hash function. This allowed me to specify how large the hash output would be and thus control how many characters would be used in the short URL building.

The math is the following:
From the example (`GeAi9K`) I've assumed the encoding must be a sequence of 6 of  any of [`upper`, `lower`, `digit`]. In other words, it's an encoding of all the possible values: 26 upper + 26 lower + 10 digits = 62. So 6 chars means 62^6 combinations. The closest integral power of 16 (hex) is 8 (since `math.log(62***2), 16) = 8.93...`). By limiting the hash domain to `16^8` (or better, `2^32`) we ensure that 6 chars on the 62 char alphabet are enough to represent the full space.
The `shake_128()` hash function was then used to output 4 bytes and a base convertion with 6 steps is done to convert from base16 to base62. By using necessarily 6 steps we guarantee that the output is zero padded to 6 chars.

After I was happy with the library, I wrote some the unit tests. Some values are hardcoded so we can detect if something changed that caused the implementation to return a different encoding.

The next step was to write the handler. This was straightforward with some back and forth manual testing with curl. The initial version didn't have the abstract property, which was added later to support passing the `base_url` as a CLI parameter. The simple http library is very basic and I've resorted to adding only the minimal needed headers. Since I used them for testing, I left the `/debug` and `/<key>` endpoints as part of the implementation. Everything else will return a 404 (not found) or 400 (bad request) to the client. The 404 is also returned if the encoded key doesn't map to an existing URL.
For the `/encode` POST endpoint, I've added some basic error handling so malformed JSON or missing headers will return an error 400 to the client.

The code was kept simple and, if scalability was a concern, we could some form of sharding to the base62 library to allow the distribution of the service in multiple nodes.

For storage, I'm using a simple dictionary in memory. Since python has the GIL, the dictionary operations used in this code are atomic.

## CAVEATS

Since the python `simpleHTTP` server is very basic, one can run into issues when accessing the service with the Chrome browser. Chrome is know for holding the connection open for optimization and the simple http server doesn't like it.
