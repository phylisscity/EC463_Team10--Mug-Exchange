import time
import requests

TIME_IN_BETWEEN = 1
SERVER_URL = "http://localhost:3000"

MOCK_ORDERS = [
    {"mugId": "1001", "merchantName": "Saxbys", "status": "ORDER_SUBMITTED", "orderTime": "2025-10-30T00:00:05Z", "MugExchange": "Yes"},
    {"mugId": "1002", "merchantName": "Pavement", "status": "ORDER_SUBMITTED", "orderTime": "2025-10-30T00:00:10Z", "MugExchange": "Yes"},
    {"mugId": "1003", "merchantName": "Starbucks", "status": "ORDER_SUBMITTED", "orderTime": "2025-10-30T00:00:15Z", "MugExchange": "Yes"},
    {"mugId": "1004", "merchantName": "Saxbys", "status": "ORDER_SUBMITTED", "orderTime": "2025-10-30T00:00:20Z", "MugExchange": "Yes"},
    {"mugId": "1005", "merchantName": "Starbucks", "status": "ORDER_SUBMITTED", "orderTime": "2025-10-30T00:00:25Z", "MugExchange": "Yes"},
    {"mugId": "1006", "merchantName": "Pavement", "status": "ORDER_SUBMITTED", "orderTime": "2025-10-30T00:00:30Z", "MugExchange": "Yes"},
    {"mugId": "1007", "merchantName": "Starbucks", "status": "ORDER_SUBMITTED", "orderTime": "2025-10-30T00:00:35Z", "MugExchange": "Yes"},
    {"mugId": "1008", "merchantName": "Saxbys", "status": "ORDER_SUBMITTED", "orderTime": "2025-10-30T00:00:40Z", "MugExchange": "Yes"},
    {"mugId": "1005", "merchantName": "Starbucks", "status": "READY_PICKUP", "orderTime": "2025-10-30T00:00:25Z", "MugExchange": "Yes"},
    {"mugId": "1009", "merchantName": "Pavement", "status": "ORDER_SUBMITTED", "orderTime": "2025-10-30T00:00:45Z", "MugExchange": "Yes"},
    {"mugId": "1007", "merchantName": "Starbucks", "status": "READY_PICKUP", "orderTime": "2025-10-30T00:00:35Z", "MugExchange": "Yes"},
    {"mugId": "1010", "merchantName": "Starbucks", "status": "ORDER_SUBMITTED", "orderTime": "2025-10-30T00:00:50Z", "MugExchange": "Yes"},
    {"mugId": "1011", "merchantName": "Pavement", "status": "ORDER_SUBMITTED", "orderTime": "2025-10-30T00:00:55Z", "MugExchange": "Yes"},
    {"mugId": "1012", "merchantName": "Starbucks", "status": "ORDER_SUBMITTED", "orderTime": "2025-10-30T00:01:00Z", "MugExchange": "Yes"},
    {"mugId": "1013", "merchantName": "Saxbys", "status": "ORDER_SUBMITTED", "orderTime": "2025-10-30T00:01:05Z", "MugExchange": "Yes"},
    {"mugId": "1014", "merchantName": "Pavement", "status": "ORDER_SUBMITTED", "orderTime": "2025-10-30T00:01:10Z", "MugExchange": "Yes"},
    {"mugId": "1015", "merchantName": "Starbucks", "status": "ORDER_SUBMITTED", "orderTime": "2025-10-30T00:01:15Z", "MugExchange": "Yes"}
]

def generate_mock_orders(time_between_orders):
    max_time, elapsed_time = 0, 0
    for i in range(len(MOCK_ORDERS)):
        time.sleep(time_between_orders)
        start_time = time.time()
        try:
            response = requests.post(f"{SERVER_URL}/api/grubhub/webhook", json=MOCK_ORDERS[i])
            print(f"Sent order {i} to node.js server with status {response.status_code}")
        except Exception as e:
            print(f"Failed sending order via webook: {e}")
        end_time = time.time()

        elapsed_time = end_time - start_time
        if elapsed_time > max_time:
            max_time = elapsed_time
    return max_time



if __name__ == "__main__":
    max_latency = generate_mock_orders(TIME_IN_BETWEEN)
    time.sleep(5)

    stats = requests.get(f"{SERVER_URL}/test/stats").json()

    expected_mug_exchange = sum(1 for orders in MOCK_ORDERS if orders["MugExchange"] == "Yes")

    assert stats["totalReceived"] == len(MOCK_ORDERS)
    assert stats["totalMugExchange"] == expected_mug_exchange

    print(f"🎉 {TIME_IN_BETWEEN} second test passed successfully with a maximum latency of {max_latency:.2f} seconds!")
