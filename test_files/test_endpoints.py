import requests

SERVER_IP_ADDRESS = "localhost"
url = f'http://{SERVER_IP_ADDRESS}:3000'

def send_mock_order():
    response = requests.post(f'{url}/api/grubhub/webhook', json={
        "UUID": "1001", 
        "merchant_id": 1234, 
        "order_number": 5678, 
        "username": "Phyo H", 
        "MugExchange": "Yes",
        "Item": "Drink 1",
        "status": "ORDER_SUBMITTED"})

    print("Status Code:", response.status_code)
    print("Response Body:", response.json())

def send_pickup():
    response = requests.post(f'{url}/pickup', json={
        "mug_id": "4545",
        "username": "Phyo H"
    })

    print("Status Code:", response.status_code)
    print("Response Body:", response.json())

def send_return():
    response = requests.post(f'{url}/return', json={
        "mug_id": "4545"
    })

    print("Status Code:", response.status_code)
    print("Response Body:", response.json())

send_mock_order()
#send_pickup()
#send_return()

