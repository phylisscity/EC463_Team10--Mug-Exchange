import express from "express";
import http from "http";
import { Server } from "socket.io";
import db from './database_test.js';
import 'dotenv/config';
import cors from "cors";
import crypto from "crypto";

const app = express();
const IP_ADDRESS = "localhost";
const PORT = 3000;

app.use(cors());
app.use(express.json());

const server = http.createServer(app);
const io = new Server(server, {
    cors: {
        origin: '*',
    },
});

io.use(async (socket, next) => {
    const token = socket.handshake.auth?.token;
    console.log("Token for socket authentication is: ", token);

    if (!token) {
    return next(new Error("No auth token"));
    }

    const user_data = await db.userFromToken(token);
    console.log(user_data);
    const uid = user_data.id;

    if (!uid) {
        console.error("Error: No UID");
        return next(new Error("Invalid auth token"));
    }

    socket.user = uid;

    next();
});

io.on('connection', (socket) => {
    socket.join(socket.user);
    console.log("User ", socket.user, " connected");

    socket.on('disconnect', async () => {
        console.log('Frontend disconnected: ', socket.id);
        await db.removeUserToken(socket.user);
    });
});

app.post('/api/grubhub/webhook', async (req, res) => {
    const order = req.body;

    console.log("Webhook received", order);

    if(req.body.MugExchange == "Yes") {
    //Parse order json for UUID, merchantID, order_number, let timestamp automatically fill in with current time FOR NOW
    const UUID = order.UUID;
    const order_number = order.order_number;
    const merchant_id = order.merchant_id;
    const status = order.status;
    const username = order.username;
    const item = order.Item;
    
    //Use this code later when the frontend should show when a ME order is in progress
    /*
    const frontend_payload = {
        orderId: order_number,
        mugId: mug_id,
        merchant_name: merchant_id,
        status: status,
        Item: item
    };

    io.emit("orderUpdate", frontend_payload);
    */

    //Add new row to orders, mugID will be null until pickup
    await db.insertOrder(order_number, UUID, merchant_id, username); 
    
    console.log("Sent payload to websocket");
    }
    
    res.status(200).json({message: "Webhook received"})
});

app.post('/pickup', async (req, res) => {
    console.log("Pickup endpoint hit: ", req.body);
    res.status(200).json({message: "Pickup RFID received"});

    const pickup_payload = req.body;

    const order = await db.getOrderInfo(pickup_payload.username);

    //Emit to frontend
    const frontend_payload = {
        UUID: order.user_id,
        merchant_name: order.merchant_id,
        mugId: order.id,
        status: "READY_PICKUP"
    };

    io.to(order.user_id).emit("orderUpdate", frontend_payload);
    
    await db.updateOrderMugID(pickup_payload.username, pickup_payload.mug_id);
    await db.updateMugStatusInUse(pickup_payload.mug_id);

    //Add row to events table for pickup event LATER
});

app.post('/return', async (req, res) => {
    console.log("Return bin endpoint hit: ", req.body);
    res.status(200).json({message: "Return RFID received"});

    //Send query to database, use unique mugID to build payload out of order info
    const return_payload = req.body;

    const order = await db.getOrderByMugID(return_payload.mug_id);

    //Emit to frontend
    const frontend_payload = {
        UUID: order.user_id,
        merchant_name: order.merchant_id,
        mugId: order.id,
        //mug_id: return_payload.mugID,
        status: "RETURNED"
    };
    io.to(order.user_id).emit("orderUpdate", frontend_payload);
    
   await db.updateMugStatusAvailable(return_payload.mug_id);

});

app.get('/', (req, res) => {
    res.send("Mug Exchange server!");
});

//Authentication
app.post('/signup', async (req, res) => {
    const { user, pass, phone } = req.body;
    const uuid = crypto.randomUUID();
    await db.addUser(uuid, user, pass, phone);

    res.status(200).json({ success: true, message: "User registered" });
});

app.post('/login', async (req, res) => {
    console.log("Login endpoint hit");
    const {username, password} = req.body;
    console.log("Username is", username, "password is ", password);
    const uid = await db.findUser(username, password);
    console.log("UID IS: ", uid);

    if (!uid) {
    return res.status(401).json({ error: "Invalid credentials" });
    }

    const token = crypto.randomUUID();
    await db.addUserToken(uid.id, token);
    const orders = await db.getUserOrders(uid.id);
    console.log(orders);
    /*
        Order -
        mugID:
        cafeID:
        status:
    */
    res.json({ token: token, orders: orders });
});


server.listen(PORT, IP_ADDRESS, () => {
    console.log(`Test Server running at http://${IP_ADDRESS}:${PORT}`);
});

/*
TO DO:
- Implement log out
- Implement deleting users in frontend and database
- Order should be a weak entity
*/