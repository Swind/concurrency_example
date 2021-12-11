import asyncio
import ssl
import re

"""
使用 python 內建的 asyncio 實做 Fetcher
"""


def parse_links(response):
  return set(
      re.findall(r'''(?i)href=["']?([^\s"'<>]+)''',
                 response.split(b'\r\n\r\n', 1)[1].decode('utf-8')))


class Fetcher:
  def __init__(self, hostname, url, loop):
    self.hostname = hostname
    self.url = url
    self.loop = loop
    self.reader = None
    self.writer = None

  async def fetch(self):
    await self.connect()
    print("connected")

    self.send_request()
    print("do_handshake done")

    response = await self.read_response()
    print("send request done")

    links = parse_links(response)
    print(links)

  async def connect(self):
    context = ssl.SSLContext(ssl.PROTOCOL_TLS)
    context.verify_mode = ssl.CERT_REQUIRED
    context.check_hostname = True
    context.load_default_certs()

    # connect and do handshake
    self.reader, self.writer = await asyncio.open_connection(self.hostname, 443, ssl=context)

  def send_request(self):
    request = "GET {} HTTP/1.0\r\nHost: {}\r\n\r\n".format(self.url, self.hostname)

    # send request
    self.writer.write(request.encode('ascii'))

  async def read_response(self):
    response = b''
    # read response
    while True:
      chunk = await self.reader.read(1024)
      if chunk:
        response += chunk
      else:
        break

    return response


def run_loop():
  loop = asyncio.get_event_loop()
  fetcher = Fetcher('oracle.code-life.info', '/', loop)
  loop.run_until_complete(fetcher.fetch())


if __name__ == '__main__':
  run_loop()
