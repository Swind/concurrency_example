from libs import loop as Loop
from urllib.parse import urljoin
import re

def parse_links(root_url, response):
  result = set(
      re.findall(r'''(?i)href=["']?([^\s"'<>]+)''',
                 response.split(b'\r\n\r\n', 1)[1].decode('utf-8')))

  return set(map(lambda url: urljoin(root_url, url), result))

class Fetcher:
  def __init__(self, hostname, url, callback, loop:Loop):
    self.hostname = hostname
    self.url = url
    self.callback = callback
    self.socket = loop.create_socket(self.hostname)

  def fetch(self):
    yield from self.socket.connect()

    request = "GET {} HTTP/1.0\r\nHost: {}\r\n\r\n".format(self.url, self.hostname).encode('ascii')
    self.socket.write(request)

    response = yield from self.socket.read()
    links = parse_links(self.url, response)
    self.callback(links)

class Crawler:
  def __init__(self, hostname, loop):
    self.hostname = hostname
    self.urls = set()
    self.loop = loop

  def on_fetch_done(self, urls):
    new_urls = urls.difference(self.urls)
    self.urls.update(new_urls)

    self._start(new_urls)

  def start(self, start_url):
    self.urls.add(start_url)

    urls = [start_url]
    self._start(urls)

  def _start(self, urls):
    for url in urls:
      fetcher = Fetcher(self.hostname, url, self.on_fetch_done, self.loop)
      self.loop.create_task(fetcher.fetch())


if __name__ == "__main__":
  import pprint

  loop = Loop.Loop()
  crawler = Crawler("oracle.code-life.info", loop)
  crawler.start('/')
  loop.run()
  pprint.pprint(crawler.urls)