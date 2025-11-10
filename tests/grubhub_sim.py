from datetime import datetime, timedelta
import time
import requests

WEBHOOK_URL = "http://localhost:3000/api/grubhub/webhook"

# Mock data to simulate "orders" from Grubhub
MOCK_ORDERS = []

def generate_mock_orders():
    order_counter = 1001
    time_counter = "2025-10-30T00:00:05Z"

    #time.sleep(10)
    while True:
        time.sleep(5)

        new_order = {
            "orderId": str(order_counter),
            "merchantID": "1",
            "status": "IN_PROGRESS",
            "orderDate": time_counter,
            "items": [
            {"name": "Burger", "quantity": 2, "price": 9.99},
            {"name": "Fries", "quantity": 1, "price": 3.49}
            ],
        "total": 23.47
        }

        MOCK_ORDERS.append(new_order)
        print(f"[+] Added mock order: {new_order}")
        order_counter += 1
        
        new_time = datetime.strptime(time_counter, "%Y-%m-%dT%H:%M:%SZ") + timedelta(seconds = 5)
        time_counter = new_time.strftime("%Y-%m-%dT%H:%M:%SZ")

        try:
            response = requests.post(WEBHOOK_URL, json=new_order)
            print(f"Sent order to node.js server with status {response.status_code}")
        except Exception as e:
            print(f"Failed sending order via webook: {e}")



if __name__ == "__main__":
    generate_mock_orders()
