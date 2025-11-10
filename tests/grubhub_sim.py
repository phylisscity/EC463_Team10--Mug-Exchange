from datetime import datetime, timedelta
import time
import requests

WEBHOOK_URL = "http://localhost:3000/api/grubhub/webhook"

# Mock data to simulate "orders" from Grubhub
MOCK_ORDERS = [
    {
    "orderId": "1001",
    "merchantName": "Starbucks",
    "status": "IN_PROGRESS",
    "orderTime": "2025-10-30T00:00:05Z",
    "MugExchange": "Yes" 
    },
    {
    "orderId": "1001",
    "merchantName": "Starbucks",
    "status": "IN_PROGRESS",
    "orderTime": "2025-10-30T00:00:05Z",
    "MugExchange": "Yes" 
    },
    {
    "orderId": "1001",
    "merchantName": "Starbucks",
    "status": "IN_PROGRESS",
    "orderTime": "2025-10-30T00:00:05Z",
    "MugExchange": "Yes" 
    },
]

merchant_list = ["Starbucks", "Pavement", "Saxby's"]
is_mug_exchange = ["Yes", "No"]

def generate_mock_orders():
    order_counter = 1001
    time_counter = "2025-10-30T00:00:05Z"

    #time.sleep(10)
    while len(MOCK_ORDERS) < 10:
        time.sleep(3)

        new_order = {
            "orderId": str(order_counter),
            "merchantName": "Starbucks",
            "status": "IN_PROGRESS",
            "orderTime": time_counter,
            "MugExchange": "Yes" 
        }

        MOCK_ORDERS.append(new_order)
        print(f"[+] Added mock order: {new_order}")
        order_counter += 1
        
        new_time = datetime.strptime(time_counter, "%Y-%m-%dT%H:%M:%SZ") + timedelta(seconds = 3)
        time_counter = new_time.strftime("%Y-%m-%dT%H:%M:%SZ")

        try:
            response = requests.post(WEBHOOK_URL, json=new_order)
            print(f"Sent order to node.js server with status {response.status_code}")
        except Exception as e:
            print(f"Failed sending order via webook: {e}")



if __name__ == "__main__":
    generate_mock_orders()
