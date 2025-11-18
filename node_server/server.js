import express from "express";
import http from "http";
import { Server } from "socket.io";

const app = express();
const PORT = 3000;
const IP_ADDRESS = "192.168.221.43";

let MOCK_ORDERS = [];

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
    console.log("Webhook received", req.body);

    if(req.body.MugExchange == "Yes") {
    MOCK_ORDERS.push(req.body);
    io.emit("orderUpdate", req.body);
    }

    res.status(200).json({message: "Webhook received"})
});

app.post('/return', (req, res) => {
    console.log("Return bin endpoint hit: ", req.body);
    res.status(200).json({message: "RFID received"});
});

app.get('/', (req, res) => {
    res.send("Mug Exchange server!");
});

server.listen(PORT, IP_ADDRESS, () => {
    console.log(`Server running at http://${IP_ADDRESS}:${PORT}`);
});