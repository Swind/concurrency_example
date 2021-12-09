def gen_fn():
  result = yield 1
  print('======== result of yield: {}'.format(result))
  result2 = yield 2
  print('======== result of 2nd yield: {}'.format(result2))
  return 'done'


# Generator 跟一般的 function 不同，當 function 內有 yield 存在時，
# 它會變成 generator function
generator_bit = 1 << 5
print("generator_bit: {}".format(bool(gen_fn.__code__.co_flags & generator_bit)))

# 呼叫的時候也不是回傳 function 執行結果，而是一個 generator,
# 它裡面會有 gi_frame, gi_code, gi_running 等屬性，來儲存 gen_fn 執行的狀態
gen = gen_fn()
print("type: {}".format(type(gen)))
print(f"gen.gi_code.co_name: {gen.gi_code.co_name}")
print(f"len(gen.gi_code.co_code): {len(gen.gi_code.co_code)}")

try:
  print("******** 開始執行之前")
  print(f"gen.gi_frame.f_lasti: {gen.gi_frame.f_lasti}")

  print("******** Start")
  result = gen.send(None)
  print(f"result: {result}")
  print(f"gen.gi_frame.f_lasti: {gen.gi_frame.f_lasti}")

  print("******** Resume 1")
  result = gen.send("Call 1")
  print(f"result: {result}")
  print(f"gen.gi_frame.f_lasti: {gen.gi_frame.f_lasti}")

  print("******** Resume 2")
  result = gen.send("Call 2")
  print(f"result: {result}")
except StopIteration as e:
  print("******** StopIteration")
  print(f"e.value: {e.value}")

print("******** 執行完成")