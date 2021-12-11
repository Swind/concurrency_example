import pprint
import socket
import re
import ssl

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

    urls = parse_links(response)
    parse_time = time.time()

    print(f"Connect: {connect_time - start_time:.10f}s")
    print(f"Send: {send_time - connect_time:.10f}s")
    print(f"Read: {read_time - send_time:.10f}s")
    print(f'Parse: {parse_time - read_time:.10f}s')
    return urls


if __name__ == '__main__':
  fetcher = Fetcher('oracle.code-life.info', '/')
  #fetcher = Fetcher('github.com', '/')
  urls = fetcher.fetch()
  #pprint.pprint(urls)
