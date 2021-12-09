import socket
import re
import ssl
import pprint

import selectors

stopped = False


def parse_links(response):
  return set(
      re.findall(r'''(?i)href=["']?([^\s"'<>]+)''',
                 response.split(b'\r\n\r\n', 1)[1].decode('utf-8')))


class Fetcher:
  def __init__(self, hostname, url, selector):
    self.hostname = hostname
    self.url = url
    self.selector = selector

    self.response = b''
    self.raw_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    self.raw_sock.setblocking(False)

    self.waiting_reading = False

  def start(self):
    try:
      self.raw_sock.connect((self.hostname, 443))
    except BlockingIOError:
      pass

    # 當 raw_sock 可以寫的時候呼叫 self.connected
    self.selector.register(self.raw_sock.fileno(), selectors.EVENT_WRITE, self.connected)

  def connected(self, key, _):
    # convert to ssl connection
    context = ssl.SSLContext(ssl.PROTOCOL_TLS)
    context.verify_mode = ssl.CERT_REQUIRED
    context.check_hostname = True
    context.load_default_certs()

    sock = self.raw_sock
    self.sock = context.wrap_socket(sock,
                                    server_hostname=self.hostname,
                                    do_handshake_on_connect=False)

    # 當 sock 可以讀的時候呼叫 self.do_handshake
    self.selector.unregister(key.fd)
    self.selector.register(self.sock.fileno(), selectors.EVENT_WRITE, self.do_handshake)

  def do_handshake(self, key, _):
    try:
      self.sock.do_handshake()
    except ssl.SSLWantReadError:
      if not self.waiting_reading:
        self.waiting_reading = True
        self.selector.unregister(key.fd)
        self.selector.register(key.fd, selectors.EVENT_READ, self.do_handshake)

    except ssl.SSLWantWriteError:
      if self.waiting_reading:
        self.waiting_reading = False
        self.selector.unregister(key.fd)
        self.selector.register(key.fd, selectors.EVENT_WRITE, self.do_handshake)
    else:
      self.selector.unregister(key.fd)

      request = "GET {} HTTP/1.0\r\nHost: {}\r\n\r\n".format(self.url, self.hostname)
      self.sock.send(request.encode('ascii'))

      # 當 sock 可以讀的時候呼叫 self.read_response
      self.selector.register(key.fd, selectors.EVENT_READ, self.read_response)

  def read_response(self, key, _):
    global stopped

    try:
      chunk = self.sock.recv(1024)
      if chunk:
        self.response += chunk
      else:
        self.selector.unregister(key.fd)
        links = parse_links(self.response)
        self.callback(links)
        stopped = True
    except ssl.SSLWantReadError:
      # 忽略 ssl socket 的內容不足的錯誤
      pass

  def set_callback(self, callback):
    self.callback = callback


def loop(selector):
  while not stopped:
    events = selector.select(timeout=1)
    for key, mask in events:
      callback = key.data
      callback(key, mask)


def on_completed(links):
  pprint.pprint(links)


if __name__ == '__main__':
  selector = selectors.DefaultSelector()

  fetcher = Fetcher('xkcd.com', '/', selector)
  fetcher.set_callback(on_completed)
  fetcher.start()
  loop(selector)
