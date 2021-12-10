def gen_fn():
  result = yield 1
  print('======== result of yield: {}'.format(result))
  result2 = yield 2
  print('======== result of 2nd yield: {}'.format(result2))
  return 'done'


def caller_fn():
  yield from gen_fn()


def caller_fn2():
  gen = gen_fn()
  result = None
  while True:
    try:
      result = yield gen.send(result)
    except StopIteration as e:
      break


def run_caller():

  # 呼叫的時候也不是回傳 function 執行結果，而是一個 generator,
  # 它裡面會有 gi_frame, gi_code, gi_running 等屬性，來儲存 gen_fn 執行的狀態

  caller = caller_fn()
  print("type: {}".format(type(caller)))
  print(f"caller.gi_code.co_name: {caller.gi_code.co_name}")
  print(f"len(caller.gi_code.co_code): {len(caller.gi_code.co_code)}")

  try:
    print("******** 開始執行之前")
    print(f"caller.gi_frame.f_lasti: {caller.gi_frame.f_lasti}")

    print("******** Start")
    result = caller.send(None)
    print(f"result: {result}")
    print(f"caller.gi_frame.f_lasti: {caller.gi_frame.f_lasti}")

    print("******** Resume 1")
    result = caller.send("Call 1")
    print(f"result: {result}")
    print(f"caller.gi_frame.f_lasti: {caller.gi_frame.f_lasti}")

    print("******** Resume 2")
    result = caller.send("Call 2")
    print(f"result: {result}")
  except StopIteration as e:
    print("******** StopIteration")
    print(f"e.value: {e.value}")

  print("******** 執行完成")


def run_caller2():
  # 呼叫的時候也不是回傳 function 執行結果，而是一個 generator,
  # 它裡面會有 gi_frame, gi_code, gi_running 等屬性，來儲存 gen_fn 執行的狀態

  caller = caller_fn2()
  print("type: {}".format(type(caller)))
  print(f"caller.gi_code.co_name: {caller.gi_code.co_name}")
  print(f"len(caller.gi_code.co_code): {len(caller.gi_code.co_code)}")

  try:
    print("******** 開始執行之前")
    print(f"caller.gi_frame.f_lasti: {caller.gi_frame.f_lasti}")

    print("******** Start")
    result = caller.send(None)
    print(f"result: {result}")
    print(f"caller.gi_frame.f_lasti: {caller.gi_frame.f_lasti}")

    print("******** Resume 1")
    result = caller.send("Call 1")
    print(f"result: {result}")
    print(f"caller.gi_frame.f_lasti: {caller.gi_frame.f_lasti}")

    print("******** Resume 2")
    result = caller.send("Call 2")
    print(f"result: {result}")
  except StopIteration as e:
    print("******** StopIteration")
    print(f"e.value: {e.value}")

  print("******** 執行完成")


if __name__ == "__main__":
  #run_caller()
  run_caller2()