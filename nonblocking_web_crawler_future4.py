import socket
import re
import ssl
import pprint
import time

import selectors
from urllib.parse import urljoin

stopped = False
debug = False


def log(message):
  if debug:
    print(message)


def parse_links(root_url, response):
  result = set(
      re.findall(r'''(?i)href=["']?([^\s"'<>]+)''',
                 response.split(b'\r\n\r\n', 1)[1].decode('utf-8')))

  return set(map(lambda url: urljoin(root_url, url), result))


class Future:
  def __init__(self) -> None:
    self.result = None
    self._callback = None

  def set_done_callback(self, fn):
    self._callback = fn

  def set_result(self, result):
    self.result = result
    self._callback(self)


class Task:
  def __init__(self, coroutine) -> None:
    self.coroutine = coroutine
    self.step()
    self.done = False

  def step(self, future=None):
    try:
      if future is None:
        next_future = self.coroutine.send(None)
      else:
        next_future = self.coroutine.send(future.result)
    except StopIteration:
      self.done = True
      return

    next_future.set_done_callback(self.step)


class Fetcher:
  def __init__(self, hostname, url, callback, loop):
    self.hostname = hostname
    self.url = url
    self.callback = callback
    self.loop = loop

    self.response = b''
    self.raw_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    self.raw_sock.setblocking(False)

    self.future = Future()

  def fetch(self):
    self.loop.register(self.raw_sock.fileno(), self.future)

    yield from self.connect()
    log("connected")

    yield from self.do_handshake()
    log("do_handshake done")

    self.send_request()
    log("send request done")

    response = yield from self.read_response()
    links = parse_links(self.url, response)

    self.callback(links)
    self.loop.unregister(self.sock.fileno())

  def connect(self):
    try:
      self.raw_sock.connect((self.hostname, 443))
    except BlockingIOError:
      pass

    yield self.future

  def do_handshake(self):
    # convert to ssl connection
    context = ssl.SSLContext(ssl.PROTOCOL_TLS)
    context.verify_mode = ssl.CERT_REQUIRED
    context.check_hostname = True
    context.load_default_certs()
    self.sock = context.wrap_socket(self.raw_sock,
                                    server_hostname=self.hostname,
                                    do_handshake_on_connect=False)
    # Do handshake
    while True:
      try:
        self.sock.do_handshake()
        break
      except ssl.SSLWantReadError:
        pass
      except ssl.SSLWantWriteError:
        pass

      yield self.future

  def send_request(self):
    request = "GET {} HTTP/1.0\r\nHost: {}\r\n\r\n".format(self.url, self.hostname)
    self.sock.send(request.encode('ascii'))

  def read_response(self):
    while True:
      try:
        yield self.future

        chunk = self.sock.recv(4096)
        if chunk:
          self.response += chunk
        else:
          return self.response
      except ssl.SSLWantReadError:
        # 忽略 ssl socket 的內容不足的錯誤
        pass


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


class Loop:
  def __init__(self):
    self.selector = selectors.DefaultSelector()
    self.tasks = []
    self.futures = {}

  def create_task(self, coroutine):
    task = Task(coroutine)
    self.tasks.append(task)
    return task

  def register(self, fileno, future):
    self.selector.register(fileno, selectors.EVENT_READ | selectors.EVENT_WRITE, None)
    self.futures[fileno] = future

  def unregister(self, fileno):
    self.selector.unregister(fileno)
    del self.futures[fileno]

  def is_done(self):
    for task in self.tasks:
      if task.done is False:
        return False

    return True

  def run(self):
    while True:
      events = self.selector.select()
      for key, _ in events:
        self.futures[key.fd].set_result(None)

      if self.is_done():
        break


if __name__ == '__main__':
  loop = Loop()
  crawler = Crawler('oracle.code-life.info', loop)
  crawler.start('/')
  loop.run()
  pprint.pprint(crawler.urls)
