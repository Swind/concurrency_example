import pprint
import socket
import re
import ssl

import time
from urllib.parse import urljoin

"""
用 blocking socket 分析 oracle.code-life.info 底下所有的網頁
"""

def parse_links(root_url, response):
  result = set(
      re.findall(r'''(?i)href=["']?([^\s"'<>]+)''',
                 response.split(b'\r\n\r\n', 1)[1].decode('utf-8')))

  return set(map(lambda url: urljoin(root_url, url), result))

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


class Fetcher:
  def __init__(self, hostname, url):
    self.hostname = hostname
    self.url = url

    self.response = b''
    self.sock = create_ssl_socket(hostname)

  def fetch(self):
    start_time = time.time() 
    self.sock.connect((self.hostname, 443))
    connect_time = time.time()

    request = "GET {} HTTP/1.0\r\nHost: {}\r\n\r\n".format(self.url, self.hostname)
    self.sock.send(request.encode('ascii'))
    send_time = time.time()

    response = b''
    chunk = self.sock.recv(4096)
    while chunk:
      response += chunk
      chunk = self.sock.recv(4096)
    read_time = time.time()

    urls = parse_links(self.url, response)
    parse_time = time.time()

    return urls


if __name__ == '__main__':
  start_time = time.time()

  result = set()
  result.add('/')

  url_queue = ['/']
  for url in url_queue:
    fetcher = Fetcher('oracle.code-life.info', url)
    new_urls = fetcher.fetch()
    new_urls = new_urls.difference(result)
    result.update(new_urls)
    url_queue.extend(new_urls)

  pprint.pprint(result)
  end_time = time.time()
  print("elapsed time: {}".format(end_time - start_time))


