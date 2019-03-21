import time
import random

times = []

for id in range(0x10000+10111, 0xfffff, 10111):
    random.seed(id)
    time_to_enter_hang = random.randint(0, 28800)
    print('%d: %d' % (id, time_to_enter_hang))
    times.append(time_to_enter_hang)

times.sort()
print(times)
