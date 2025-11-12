from machine import Pin
import time

sensor = Pin(15, Pin.IN)   # receiver black wire
buzzer = Pin(16, Pin.OUT)  # buzzer + wire

print("System ready! Break the beam to beep.")
while True:
    if sensor.value() == 0:       # beam broken
        buzzer.value(1)           # turn buzzer on
        time.sleep(0.3)
        buzzer.value(0)           # turn it off
    else:
        buzzer.value(0)
    time.sleep(0.05)
