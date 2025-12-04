import express from "express";
import http from "http";
import { Server } from "socket.io";
import { query, insertOrder, getUserName, updateOrderMugID, updateMugStatusAvailable, updateMugStatusInUse, getOrderByMugID, pool } from './database_test.js';

const app = express();
const IP_ADDRESS = "172.20.10.13";
const PORT = 3000;

app.use(express.json());

const server = http.createServer(app);
const io = new Server(server, {
    cors: {
        origin: '*',
    },
});

io.on('connection', (socket) => {
    console.log("Frontend connected: ", socket.id);

    socket.on('disconnect', () => {
        console.log('Frontend disconnected: ', socket.id);
    });
});

app.post('/api/grubhub/webhook', (req, res) => {
    const order = req.body;

    console.log("Webhook received", order);

    if(req.body.MugExchange == "Yes") {
    //Parse order json for UUID, merchantID, order_number, let timestamp automatically fill in with current time FOR NOW
    const UUID = order.UUID;
    const order_number = order.order_number;
    const merchant_id = order.merchant_id;
    const status = order.status;
    const username = order.username;

    const frontend_payload = {
        mugId: order_number,
        merchant_name: merchant_id,
        status: status
    };

    io.emit("orderUpdate", frontend_payload);
    
    //Add new row to orders, mugID will be null until pickup
    insertOrder(order_number, UUID, merchant_id, username); 
    
    console.log("Sent payload to websocket");
    }

    res.status(200).json({message: "Webhook received"})
});

app.post('/pickup', (req, res) => {
    console.log("Pickup endpoint hit: ", req.body);
    res.status(200).json({message: "Pickup RFID received"});

    const pickup_payload = req.body;

    const order = getUserName(pickup_payload.username);

    //Emit to frontend
    const frontend_payload = {
        UUID: order.user_id,
        merchant_name: order.merchant_id,
        mugId: order.id,
        //mugID: pickup_payload.mugID,
        status: "READY_PICKUP"
    };

    io.emit("orderUpdate", frontend_payload);
    
    
    updateOrderMugID(pickup_payload.username, pickup_payload.mug_id);

    updateMugStatusInUse(pickup_payload.mug_id);

    //Add row to events table for pickup event LATER
});

app.post('/return', (req, res) => {
    console.log("Return bin endpoint hit: ", req.body);
    res.status(200).json({message: "Return RFID received"});

    //Send query to database, use unique mugID to build payload out of order info
    const return_payload = req.body;

    const order = getOrderByMugID(return_payload.mug_id);

    //Emit to frontend
    const frontend_payload = {
        UUID: order.user_id,
        merchant_name: order.merchant_id,
        mugId: order.id,
        //mug_id: return_payload.mugID,
        status: "RETURNED"
    };
    io.emit("orderUpdate", frontend_payload);
    
   
    updateMugStatusAvailable(return_payload.mug_id);

});

app.get('/', (req, res) => {
    res.send("Mug Exchange server!");
});

//Authentication
app.get('/auth', (req, res) => {
    //
})

server.listen(PORT, IP_ADDRESS, () => {
    console.log(`Test Server running at http://${IP_ADDRESS}:${PORT}`);
});
