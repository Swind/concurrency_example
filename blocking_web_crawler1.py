import socket
import re
import ssl
import pprint

def fetch(url:str):
    # SSL
    context = ssl.SSLContext(ssl.PROTOCOL_TLS)
    context.verify_mode = ssl.CERT_REQUIRED
    context.check_hostname = True
    context.load_default_certs()

    # Connect to website
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    ssl_sock = context.wrap_socket(s, server_hostname='xkcd.com')
    ssl_sock.connect(('xkcd.com', 443))

    # Send request
    ssl_sock.sendall("GET {} HTTP/1.0\r\nHost: xkcd.com\r\n\r\n".format(url).encode('ascii'))
    response = b''
    chunk = ssl_sock.recv(4096)

    while chunk:
        response += chunk
        chunk = ssl_sock.recv(4096)

    # Parse the response
    urls = set(re.findall(r'''(?i)href=["']?([^\s"'<>]+)''', response.split(b'\r\n\r\n', 1)[1].decode('utf-8')))
    return urls

if __name__ == '__main__':
    pprint.pprint(fetch("/"))
