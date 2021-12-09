import asyncio
import ssl
import re
import itertools

from urllib.parse import urljoin
import pprint


def parse_links(root_url, response):
  result = set(
      re.findall(r'''(?i)href=["']?([^\s"'<>]+)''',
                 response.split(b'\r\n\r\n', 1)[1].decode('utf-8')))

  return set(map(lambda url: urljoin(root_url, url), result))


class Fetcher:
  def __init__(self, hostname, url):
    self.hostname = hostname
    self.url = url
    self.reader = None
    self.writer = None

  async def fetch(self):
    print("Fetching {}".format(self.url))
    await self.connect()
    self.send_request()
    response = await self.read_response()
    links = parse_links(self.url, response)
    print("Fetching {} Done".format(self.url))
    pprint.pprint(links)
    return links

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

class Crawler:
  def __init__(self, hostname, loop):
    self.hostname = hostname
    self.loop = loop
    self.urls = set()

  async def start(self, start_url):
    self.urls.add(start_url)

    urls = [start_url]
    tasks = []

    while urls:
      for url in urls:
        fetcher = Fetcher(self.hostname, url)
        tasks.append(self.loop.create_task(fetcher.fetch()))

      result = await asyncio.gather(*tasks)
      result = set(itertools.chain(*result))
      urls = result.difference(self.urls)
      self.urls.update(result)

    pprint.pprint(self.urls)

def run_loop():
  loop = asyncio.get_event_loop()
  crawler = Crawler('oracle.code-life.info', loop)
  loop.run_until_complete(crawler.start('/'))


if __name__ == '__main__':
  run_loop()
