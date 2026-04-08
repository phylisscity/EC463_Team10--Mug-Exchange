from machine import Pin
from simple_mfrc522 import SimpleMFRC522
import network
import time
import urequests
import ujson

# =======================================================
# CONFIG
# =======================================================
BACKEND_URL = "https://ec463-diallo-amado.onrender.com/return"
SSID = "wifiname"
PASSWORD = "wifi_pass"

LOG_FILE = "log.txt"

# =======================================================
# PINS
# =======================================================
SENSOR_PIN = 12
HALL_PIN = 11

BUZZER_PIN = 20
RED_LED_PIN = 13
GREEN_LED_PIN = 14

# RFID
SPI_ID = 0
SCK = 18
MOSI = 19
MISO = 16
CS = 17
RST = 9

# 28BYJ lock motor via ULN2003
BYJ_IN1_PIN = 21
BYJ_IN2_PIN = 22
BYJ_IN3_PIN = 26
BYJ_IN4_PIN = 27

# NEMA / DRV8825
NEMA_STEP_PIN = 2
NEMA_DIR_PIN = 3
NEMA_EN_PIN = 4

# =======================================================
# TIMING / THRESHOLDS
# =======================================================
BOOT_WIFI_DELAY_SEC = 4
WIFI_TIMEOUT_SEC = 20
HALL_WAIT_SEC = 3
SCAN_WINDOW_SEC = 3.0
LOOP_DELAY_SEC = 0.05

LOCK_STEPS = 500
BYJ_STEP_DELAY_S = 0.01

# NEMA plate movement
PLATE_DROP_STEPS = 150
PLATE_STEP_DELAY_US = 2000
PLATE_SETTLE_SEC = 0.8

# =======================================================
# LOGGING
# =======================================================
def log(message):
    timestamp = str(time.time())
    line = "[{}] {}\n".format(timestamp, message)
    print(line.strip())

    try:
        with open(LOG_FILE, "a") as f:
            f.write(line)
    except:
        pass

# =======================================================
# HARDWARE SETUP
# =======================================================
status_led = Pin("LED", Pin.OUT)

sensor = Pin(SENSOR_PIN, Pin.IN)
hall = Pin(HALL_PIN, Pin.IN, Pin.PULL_UP)

buzzer = Pin(BUZZER_PIN, Pin.OUT, value=0)
red = Pin(RED_LED_PIN, Pin.OUT, value=0)
green = Pin(GREEN_LED_PIN, Pin.OUT, value=0)

# BYJ motor pins
# Keep the same GPIOs, but use the working order.
IN1 = Pin(BYJ_IN1_PIN, Pin.OUT)
IN2 = Pin(BYJ_IN2_PIN, Pin.OUT)
IN3 = Pin(BYJ_IN3_PIN, Pin.OUT)
IN4 = Pin(BYJ_IN4_PIN, Pin.OUT)

BYJ_PINS = [IN1, IN2, IN3, IN4]

# NEMA / DRV8825 pins
nema_step = Pin(NEMA_STEP_PIN, Pin.OUT, value=0)
nema_dir = Pin(NEMA_DIR_PIN, Pin.OUT, value=0)
nema_en = Pin(NEMA_EN_PIN, Pin.OUT, value=1)

# RFID
reader = SimpleMFRC522(
    spi_id=SPI_ID,
    sck=SCK,
    mosi=MOSI,
    miso=MISO,
    cs=CS,
    rst=RST
)

# Wi-Fi
wlan = network.WLAN(network.STA_IF)

# =======================================================
# STATUS / FEEDBACK HELPERS
# =======================================================
def led_on():
    status_led.value(1)

def led_off():
    status_led.value(0)

def flash_status(duration=0.15):
    led_on()
    time.sleep(duration)
    led_off()

def flash_success():
    flash_status(0.12)
    time.sleep(0.12)
    flash_status(0.12)

def flash_error():
    flash_status(0.8)

def wifi_heartbeat():
    flash_status(0.1)

def beep(duration=0.2):
    buzzer.value(1)
    time.sleep(duration)
    buzzer.value(0)

def flash(pin, duration=0.2):
    pin.value(1)
    time.sleep(duration)
    pin.value(0)

# =======================================================
# SENSOR HELPERS
# =======================================================
def is_mug_present():
    return sensor.value() == 0

def is_door_closed():
    # 1 = no magnet
    # 0 = magnet detected
    return hall.value() == 0

# =======================================================
# WIFI
# =======================================================
def connect_wifi(timeout=WIFI_TIMEOUT_SEC):
    wlan.active(True)

    if wlan.isconnected():
        log("Wi-Fi already connected: {}".format(wlan.ifconfig()))
        led_on()
        return True

    log("Connecting to Wi-Fi...")
    wlan.connect(SSID, PASSWORD)

    start = time.time()
    while time.time() - start < timeout:
        if wlan.isconnected():
            log("Wi-Fi connected: {}".format(wlan.ifconfig()))
            led_on()
            return True

        wifi_heartbeat()
        time.sleep(0.7)

    log("Wi-Fi connection timed out")
    led_off()
    return False

def ensure_wifi():
    if wlan.isconnected():
        return True

    log("Wi-Fi lost. Reconnecting...")
    led_off()
    return connect_wifi(timeout=WIFI_TIMEOUT_SEC)

# =======================================================
# BACKEND
# =======================================================
def send_to_backend(packet):
    response = None

    try:
        log("Sending packet: {}".format(packet))

        response = urequests.post(
            BACKEND_URL,
            data=ujson.dumps(packet),
            headers={"Content-Type": "application/json"}
        )

        log("Response status: {}".format(response.status_code))
        log("Response body: {}".format(response.text))

        if 200 <= response.status_code < 300:
            flash_success()
            led_on()
            return True
        else:
            flash_error()
            led_on()
            return False

    except Exception as e:
        log("Backend send error: {}".format(e))
        flash_error()
        led_on()
        return False

    finally:
        if response:
            response.close()

# =======================================================
# 28BYJ LOCK MOTOR
# =======================================================
BYJ_SEQUENCE = [
    [1, 1, 0, 0],
    [0, 1, 1, 0],
    [0, 0, 1, 1],
    [1, 0, 0, 1]
]

locked = False

def move_byj(steps, reverse=False):
    sequence = BYJ_SEQUENCE[::-1] if reverse else BYJ_SEQUENCE

    for i in range(steps):
        step = sequence[i % 4]
        for j in range(4):
            BYJ_PINS[j].value(step[j])
        time.sleep(BYJ_STEP_DELAY_S)

    for p in BYJ_PINS:
        p.value(0)

def lock():
    global locked
    if not locked:
        time.sleep(1.5)  # brief pause before locking
        log("Locking...")
        move_byj(LOCK_STEPS)
        locked = True
        log("Door locked")


def unlock():
    global locked
    if locked:
        log("Unlocking...")
        move_byj(LOCK_STEPS, reverse=True)
        locked = False
        log("Door unlocked")

# =======================================================
# NEMA / DRV8825
# =======================================================
def nema_enable():
    nema_en.value(0)

def nema_disable():
    nema_en.value(1)

def move_nema(steps, direction=1, step_delay_us=PLATE_STEP_DELAY_US):
    nema_enable()
    nema_dir.value(1 if direction else 0)

    for _ in range(steps):
        nema_step.value(1)
        time.sleep_us(step_delay_us)
        nema_step.value(0)
        time.sleep_us(step_delay_us)

def move_plate_to_drop():
    log("Moving plate to drop...")
    move_nema(PLATE_DROP_STEPS, direction=1)
    log("Plate moved to drop")

def move_plate_home():
    log("Returning plate home...")
    move_nema(PLATE_DROP_STEPS, direction=0)
    log("Plate returned home")

# =======================================================
# HALL GATE
# =======================================================
def wait_for_door_closed(timeout=HALL_WAIT_SEC):
    log("Waiting for hall sensor confirmation...")
    start = time.time()

    while time.time() - start < timeout:
        if is_door_closed():
            log("Door confirmed by hall sensor")
            return True
        time.sleep(0.05)

    log("Hall timeout: door not confirmed")
    return False

# =======================================================
# RFID
# =======================================================
def scan_rfid(timeout=SCAN_WINDOW_SEC):
    start = time.time()

    while time.time() - start < timeout:
        if not is_mug_present():
            log("Mug removed during RFID scan")
            return False, None, ""

        try:
            rid, text = reader.read_no_block()
            if rid:
                cleaned = (text or "").strip()
                log("RFID detected: {} | {}".format(rid, cleaned))
                return True, rid, cleaned
        except Exception as e:
            log("RFID read error: {}".format(e))

        time.sleep(0.05)

    return False, None, ""

# =======================================================
# STARTUP
# =======================================================
led_off()
red.value(0)
green.value(0)
nema_disable()

log("System booting...")
time.sleep(BOOT_WIFI_DELAY_SEC)

wifi_ok = connect_wifi(timeout=WIFI_TIMEOUT_SEC)

if wifi_ok:
    led_on()
else:
    led_off()

log("Hardware initialized")
log("System ready — waiting for mugs")

# =======================================================
# MAIN LOOP
# =======================================================
processing = False
waiting_for_removal = False
printed_waiting_msg = False

while True:
    try:
        if not wlan.isconnected():
            ensure_wifi()

        if is_mug_present() and not processing and not waiting_for_removal:
            processing = True
            log("Mug detected")
            flash(green, 0.15)

            if not wait_for_door_closed():
                log("Door not confirmed, aborting cycle")
                flash(red, 0.3)
                beep(0.2)
                processing = False
                waiting_for_removal = True
                printed_waiting_msg = False
                continue

            lock()

            log("Scanning RFID...")
            success, tag_id, tag_text = scan_rfid()

            if success:
                log("RFID success")
                flash(green, 0.3)
                beep(0.1)

                packet = {
                    "mug_id": str(tag_id),
                    "rfid_data": tag_text
                }

                if ensure_wifi():
                    backend_ok = send_to_backend(packet)
                    if backend_ok:
                        log("Backend send successful")
                        flash(green, 0.15)
                    else:
                        log("Backend send failed")
                        flash(red, 0.25)
                else:
                    log("No Wi-Fi, cannot send packet")
                    flash_error()
                    flash(red, 0.25)

                move_plate_to_drop()
                time.sleep(PLATE_SETTLE_SEC)
                move_plate_home()
                nema_disable()

            else:
                log("RFID fail")
                flash(red, 0.3)
                beep(0.3)

            unlock()

            waiting_for_removal = True
            printed_waiting_msg = False
            processing = False

        if waiting_for_removal:
            if not printed_waiting_msg:
                log("Waiting for mug to be removed...")
                printed_waiting_msg = True

            if not is_mug_present():
                log("Mug removed — ready for next mug")
                waiting_for_removal = False
                printed_waiting_msg = False

        time.sleep(LOOP_DELAY_SEC)

    except Exception as e:
        log("Main loop error: {}".format(e))
        flash_error()
        flash(red, 0.25)

        try:
            unlock()
        except:
            pass

        nema_disable()
        time.sleep(1)
