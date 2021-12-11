import socket
import re
import ssl
import pprint
import time

"""
使用傳統的 socket 去取得 https://oracle.code-life.info/ 的內容
"""

def fetch(hostname: str, url: str):
  start_time = time.time()

  # SSL
  context = ssl.SSLContext(ssl.PROTOCOL_TLS)
  context.verify_mode = ssl.CERT_REQUIRED
  context.check_hostname = True
  context.load_default_certs()

  # Connect to website
  s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  ssl_sock = context.wrap_socket(s, server_hostname=hostname)
  ssl_sock.connect((hostname, 443))

  # Send request
  ssl_sock.sendall("GET {} HTTP/1.0\r\nHost: {}\r\n\r\n".format(url, hostname).encode('ascii'))
  response = b''
  chunk = ssl_sock.recv(4096)

  while chunk:
    response += chunk
    chunk = ssl_sock.recv(4096)
  
  connection_time = time.time() 

  # Parse the response
  urls = set(
      re.findall(r'''(?i)href=["']?([^\s"'<>]+)''',
                 response.split(b'\r\n\r\n', 1)[1].decode('utf-8')))

  parser_time = time.time()

  print(f"Connection: {connection_time - start_time}")
  print(f"Parse: {parser_time - connection_time}")

  return urls


if __name__ == '__main__':
  fetch('oracle.code-life.info', '/')
