const express = require('express');
const app = express();
const PORT = 3000;

app.use(express.json());

const mysql = require('mysql2');

const pool = mysql.createPool({
  host: 'localhost',  // or remote host
  user: 'dbuser',
  password: 'password123',
  database: 'mugexchangesystem'
});

//Endpoints go here
app.get('/', (req, res) => {
    res.send("Mug Exchange server!");
});



app.listen(PORT, () => {
    console.log(`Server running at http://localhost:${PORT}`);
});