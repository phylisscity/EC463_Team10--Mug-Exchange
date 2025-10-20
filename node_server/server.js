const express = require('express');
const app = express();
const PORT = 3000;

app.use(express.json());

//Endpoints go here
app.get('/', (req, res) => {
    res.send("Mug Exchange server!");
});



app.listen(PORT, () => {
    console.log(`Server running at http://localhost:${PORT}`);
});