import express from "express";
import http from "http";
import { Server } from "socket.io";

const app = express();
const PORT = 3000;

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

//Testing portion
let stats = { totalReceived: 0, totalMugExchange: 0 };
app.get('/test/stats', (req, res) => {
    res.json(stats);
})

app.post('/api/grubhub/webhook', (req, res) => {
    const order = req.body;

    console.log("Webhook received", order);
    stats["totalReceived"] += 1;

    if(req.body.MugExchange == "Yes") {
    MOCK_ORDERS.push(order);

    const emittedAt = Date.now();

    const payload = {
        ...order,
        emittedAt,
    };

    io.emit("orderUpdate", payload);
    console.log("Sent payload to websocket");
    stats["totalMugExchange"] += 1;
    }

    res.status(200).json({message: "Webhook received"})
});

app.get('/', (req, res) => {
    res.send("Mug Exchange server!");
});

server.listen(PORT, "10.239.162.7", () => {
    console.log(`Server running at http://10.239.162.7:${PORT}`);
});