import express from "express";
import http from "http";
import { Server } from "socket.io";

const app = express();
const PORT = 3000;

MOCK_ORDERS = []

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

app.get('/', (req, res) => {
    res.send("Mug Exchange server!");
});

app.post('/api/grubhub/webhook', (req, res) => {
    console.log("Webhook received", req.body);

    MOCK_ORDERS.push(req.body);

    io.emit("Order update", req.body);

    res.status(200).json({message: "Webhook received"})
});


server.listen(PORT, () => {
    console.log(`Server running at http://localhost:${PORT}`);
});