import selectors
import socket
import ssl

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

class AsyncSocket:
  def __init__(self, hostname):
    self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    self.sock.setblocking(False)
    self.future = Future()
    self.hostname = hostname

  def get_fd(self):
    return self.sock

  def on_read(self):
    self.future.set_result(None)

  def on_write(self):
    self.future.set_result(None)

  def get_future(self):
    return self.future

  def connect(self):
    try:
      self.sock.connect((self.hostname, 443))
    except BlockingIOError:
      pass

    yield self.future

    yield from self._do_handshake()

  def _do_handshake(self):
    # convert to ssl connection
    context = ssl.SSLContext(ssl.PROTOCOL_TLS)
    context.verify_mode = ssl.CERT_REQUIRED
    context.check_hostname = True
    context.load_default_certs()
    self.sock = context.wrap_socket(self.sock,
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

  def read(self):
    response = b''
    while True:
      try:
        yield self.future # 等待 Read 事件, 當有 READ 的事件時，就會被 Resume
        chunk = self.sock.recv(4096)
        if chunk:
          response += chunk
        else:
          return response
      except ssl.SSLWantReadError:
        # 忽略 ssl socket 的內容不足的錯誤
        pass

  def write(self, message):
    self.sock.write(message) 

class Loop:
  def __init__(self):
    self.selector = selectors.DefaultSelector()
    self.tasks = []

  def create_socket(self, hostname):
    socket = AsyncSocket(hostname)
    self.selector.register(socket.get_fd(), selectors.EVENT_READ | selectors.EVENT_WRITE, socket)
    return socket

  def create_task(self, coroutine):
    task = Task(coroutine)
    self.tasks.append(task)
    return task

  def is_done(self):
    for task in self.tasks:
      if task.done is False:
        return False

    return True

  def run(self):
    while True:
      events = self.selector.select()
      for key, mask in events:
        socket = key.data
        if mask | selectors.EVENT_READ:
          socket.on_read()
        elif mask | selectors.EVENT_WRITE:
          socket.on_write()

      if self.is_done():
        break

