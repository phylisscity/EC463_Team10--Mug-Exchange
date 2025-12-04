import mysql from 'mysql2';

const pool = mysql.createPool({
  host: 'localhost',  // or remote host
  user: 'root',
  password: 'Zj59!xtoa218sado',
  port: 3306,
  database: 'mug_exchange',
  waitForConnections: true,
  connectionLimit: 10,
  database: 'mug_exchange'
});

async function query(sql, params) {
  const [rows] = await pool.promise().query(sql, params);
  return rows;
}

//Add new row to orders, mugID will be null until pickup
const insertOrder = async (order_num, user_id, merchant_id, username) => {
const [sqlInsert] = await pool.query(
    "INSERT INTO orders (id, user_id, merchant_id, username) VALUES (?, ?, ?, ?)",
    [order_num, user_id, merchant_id, username]
);
console.log("Inserted order number", order_num, "with insert ID", sqlInsert.insertId);
};

//Query info from orders table using username (use order number later)
const getUserName = async (username) => {
  const [rows] = await pool.query(
      "SELECT id, user_id, merchant_id FROM orders WHERE username = ?",
      [username]
  );
  console.log("Queried order info for username", username, ":", rows[0]);
  return rows[0];
};

//Update mugID in row of orders table with mugID from RFID reader
const updateOrderMugID = async (username, mugID) => {
    const [sqlUpdate] = await pool.query(
        "UPDATE orders SET mug_id = ? WHERE username = ?",
        [mugID, username]
    );
    console.log("Updated username", username, "with mugID", mugID);
}

//Update mug status in mugs table
const updateMugStatusInUse = async (mugID) => {
    const [sqlUpdate] = await pool.query(
        "UPDATE mugs SET status = 'in_use' WHERE id = ?",
        [mugID]
    );
    console.log("Updated mugID", mugID, "status to in_use");
};

//Use unique mugID to build payload out of order info
const getOrderByMugID = async (mugID) => {
    const [rows] = await pool.query(
        "SELECT id, user_id, merchant_id FROM orders WHERE mug_id = ?",
        [mugID]
    );
    console.log("Queried order info for mugID", mugID, ":", rows[0]);
    return rows[0];
};

//Update mug status in mugs table to available
const updateMugStatusAvailable = async (mugID) => {
    const [sqlUpdate] = await pool.query(
        "UPDATE mugs SET status = 'available' WHERE id = ?",
        [mugID]
    );
    console.log("Updated mugID", mugID, "status to available");
}

export { query, insertOrder, getUserName, updateMugStatusAvailable, updateOrderMugID, updateMugStatusInUse, getOrderByMugID };



