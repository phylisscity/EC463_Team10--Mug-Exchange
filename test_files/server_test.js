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

  if (!token) {
    return next(new Error("No auth token"));
  }

  const uid = await db.userFromToken(token);

  if (!uid) {
    return next(new Error("Invalid auth token"));
  }

  socket.user = uid;

  next();
});

io.on('connection', (socket) => {
    console.log("User ", socket.user, " connected");

    socket.on('disconnect', () => {
        console.log('Frontend disconnected: ', socket.id);
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

    const frontend_payload = {
        orderId: order_number,
        mugId: mug_id,
        merchant_name: merchant_id,
        status: status,
        Item: item
    };

    io.emit("orderUpdate", frontend_payload);
    
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
        //mugID: pickup_payload.mugID,
        status: "READY_PICKUP"
    };

    io.emit("orderUpdate", frontend_payload);
    
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
    io.emit("orderUpdate", frontend_payload);
    
   await db.updateMugStatusAvailable(return_payload.mug_id);

});

app.get('/', (req, res) => {
    res.send("Mug Exchange server!");
});

//Authentication
app.post('/signup', async (req, res) => {
    const { user, pass, phone } = req.body;
    await db.addUser(user, pass, phone);

    res.status(200).json({ success: true, message: "User registered" });
});

app.post('/login', async (req, res) => {
    console.log("Login endpoint hit");
    const {username, password} = req.body;
    const uid = await db.findUser(username, password);
    console.log("UID IS: ", uid);

    if (!uid) {
    return res.status(401).json({ error: "Invalid credentials" });
    }

    const token = crypto.randomUUID();
    await db.addUserToken(uid, token);
    res.json({ token });
});


server.listen(PORT, IP_ADDRESS, () => {
    console.log(`Test Server running at http://${IP_ADDRESS}:${PORT}`);
});

/*
TO DO:
- Change primary key of users table to not be random UUID instead of auto-increment
- Implement deleting users in frontend and database
*/