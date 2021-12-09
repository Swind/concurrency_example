import pprint
import socket
import re
import ssl

stopped = False


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
    self.sock.connect((self.hostname, 443))

    request = "GET {} HTTP/1.0\r\nHost: {}\r\n\r\n".format(self.url, self.hostname)
    self.sock.send(request.encode('ascii'))

    response = b''
    chunk = self.sock.recv(4096)
    while chunk:
      response += chunk
      chunk = self.sock.recv(4096)

    urls = parse_links(response)
    return urls


if __name__ == '__main__':
  fetcher = Fetcher('xkcd.com', '/')
  pprint.pprint(fetcher.fetch())
