import socket
import re

import selectors

stopped = False


def parse_links(response):
  return set(
      re.findall(r'''(?i)href=["']?([^\s"'<>]+)''',
                 response.split(b'\r\n\r\n', 1)[1].decode('utf-8')))


class Future:
  def __init__(self) -> None:
    self.result = None
    self._callbacks = []

  def add_done_callback(self, fn):
    self._callbacks.append(fn)

  def set_result(self, result):
    self.result = result
    for fn in self._callbacks:
      fn(self)


class Task:
  def __init__(self, coroutine) -> None:
    self.coroutine = coroutine
    self.step()

  def step(self, future=None):
    try:
      if future is None:
        next_future = self.coroutine.send(None)
      else:
        next_future = self.coroutine.send(future.result)
    except StopIteration:
      return

    next_future.add_done_callback(self.step)


class Fetcher:
  def __init__(self, hostname, url, selector):
    self.hostname = hostname
    self.url = url
    self.selector = selector

    self.response = b''
    self.raw_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    self.raw_sock.setblocking(False)

  def fetch(self):
    global stopped

    # Connect
    try:
      self.raw_sock.connect((self.hostname, 443))
    except BlockingIOError:
      pass

    future = Future()

    self.selector.register(self.raw_sock.fileno(), selectors.EVENT_WRITE,
                           lambda key, mask: future.set_result(None))
    yield future

    self.selector.unregister(self.raw_sock.fileno())
    print("connected")

    stopped = True


def loop(selector):
  while not stopped:
    events = selector.select(timeout=1)
    for key, mask in events:
      callback = key.data
      callback(key, mask)


if __name__ == '__main__':
  selector = selectors.DefaultSelector()

  fetcher = Fetcher('xkcd.com', '/', selector)
  Task(fetcher.fetch())
  loop(selector)
