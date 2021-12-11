import asyncio
import ssl
import re
import itertools
import time

from urllib.parse import urljoin
import pprint

"""
使用 python 內建的 asyncio 分析 oracle.code-life.info 底下所有的網頁
"""

debug = False

def log(message):
  if(debug):
    print(message)


def parse_links(root_url, response):
  result = set(
      re.findall(r'''(?i)href=["']?([^\s"'<>]+)''',
                 response.split(b'\r\n\r\n', 1)[1].decode('utf-8')))

  return set(map(lambda url: urljoin(root_url, url), result))


class Fetcher:
  def __init__(self, hostname, url, callback):
    self.hostname = hostname
    self.url = url
    self.reader = None
    self.writer = None
    self.callback = callback

  async def fetch(self):
    log("Fetching {}".format(self.url))

    await self.connect()

    self.send_request()

    response = await self.read_response()
    links = parse_links(self.url, response)

    log("Fetching {} Done".format(self.url))
    self.callback(links)

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
      chunk = await self.reader.read(4096)
      if chunk:
        response += chunk
      else:
        break

    return response

class Crawler:
  def __init__(self, hostname):
    self.hostname = hostname
    self.urls = set()
    self.tasks = []

  def on_fetch_done(self, urls):
    new_urls = urls.difference(self.urls) 
    self.urls.update(new_urls)

    self._start(new_urls)

  async def start(self, start_url):
    self.urls.add(start_url)

    urls = [start_url]
    self._start(urls)

    for task in self.tasks:
      await task

  def _start(self, urls):
    for url in urls:
      fetcher = Fetcher(self.hostname, url, self.on_fetch_done)
      self.tasks.append(asyncio.create_task(fetcher.fetch()))


async def test():
  start_time = time.time()
  crawler = Crawler('oracle.code-life.info')
  await crawler.start('/')
  end_time = time.time()
  print("elapsed time: {}".format(end_time - start_time))

if __name__ == '__main__':
  asyncio.run(test())
