import pprint
import socket
import re
import ssl
import threading

import time

def create_ssl_socket(hostname):
  # SSL
  context = ssl.SSLContext(ssl.PROTOCOL_TLS)
  context.verify_mode = ssl.CERT_REQUIRED
  context.check_hostname = True
  context.load_default_certs()

  # Connect to website
  sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  ssl_socket = context.wrap_socket(sock, server_hostname=hostname)
  return ssl_socket


def parse_links(response):
  return set(
      re.findall(r'''(?i)href=["']?([^\s"'<>]+)''',
                 response.split(b'\r\n\r\n', 1)[1].decode('utf-8')))


class Fetcher:
  def __init__(self, hostname, url, callback=None):
    self.hostname = hostname
    self.url = url
    self.callback = callback

    self.response = b''
    self.sock = create_ssl_socket(hostname)

  def fetch(self):
    start_time = time.time() 
    self.sock.connect((self.hostname, 443))

    request = "GET {} HTTP/1.0\r\nHost: {}\r\n\r\n".format(self.url, self.hostname)
    self.sock.send(request.encode('ascii'))
    send_time = time.time()

    response = b''
    chunk = self.sock.recv(4096)
    while chunk:
      response += chunk
      chunk = self.sock.recv(4096)

    urls = parse_links(response)

    self.callback(urls)

class Crawler:
  def __init__(self, hostname):
    self.hostname = hostname
    self.urls = set()

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
      fetcher = Fetcher(self.hostname, url, self.on_fetch_done)
      threading.Thread(target=fetcher.fetch).start()

def test():
  start_time = time.time()

  crawler = Crawler('oracle.code-life.info')
  crawler.start('/')

  while True:
    threads = threading.enumerate()
    if len(threads) == 1:
      break

    for thread in threads:
      if thread.name != 'MainThread':
        thread.join()

  end_time = time.time()
  print("elapsed time: {}".format(end_time - start_time))


if __name__ == '__main__':
  for i in range(0, 100):
    test() 