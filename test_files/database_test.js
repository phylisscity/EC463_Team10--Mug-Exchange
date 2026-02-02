import mysql from 'mysql2/promise';

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

const dbQuery = async (sql, params = []) => {
    try {
        const [result] = await pool.query(sql, params);
        return result;
    } catch (err) {
        console.error("--- DATABASE ERROR ---");
        console.error("Query:", sql);
        console.error("Params:", params);
        console.error("Error:", err.message);
        
        throw err;
    }
}

//Add new row to orders, mugID will be null until pickup
const insertOrder = async (order_num, user_id, merchant_id, username) => {
    const sqlInsert = await dbQuery(
        "INSERT INTO orders (id, user_id, merchant_id, username) VALUES (?, ?, ?, ?)",
        [order_num, user_id, merchant_id, username]
    );
    console.log("Inserted order number", order_num, "with insert ID", sqlInsert.insertId);
};

//Query info from orders table using username (use order number later)
const getOrderInfo = async (username) => {
    const rows = await dbQuery(
        "SELECT id, user_id, merchant_id FROM orders WHERE username = ?",
        [username]
    );
    console.log("Queried order info for username", username, ":", rows[0]);
    return rows[0];
};

//Update mugID in row of orders table with mugID from RFID reader
const updateOrderMugID = async (username, mugID) => {
    const sqlUpdate = await dbQuery(
        "UPDATE orders SET mug_id = ? WHERE username = ?",
        [mugID, username]
    );
    console.log("Updated username", username, "with mugID", mugID);
}

//Update mug status in mugs table
const updateMugStatusInUse = async (mugID) => {
    const sqlUpdate = await dbQuery(
        "UPDATE mugs SET status = 'in_use' WHERE id = ?",
        [mugID]
    );
    console.log("Updated mugID", mugID, "status to in_use");
};

//Use unique mugID to build payload out of order info
const getOrderByMugID = async (mugID) => {
    const rows = await dbQuery(
        "SELECT id, user_id, merchant_id FROM orders WHERE mug_id = ?",
        [mugID]
    );
    console.log("Queried order info for mugID", mugID, ":", rows[0]);
    return rows[0];
};

//Update mug status in mugs table to available
const updateMugStatusAvailable = async (mugID) => {
    const sqlUpdate = await dbQuery(
        "UPDATE mugs SET status = 'returned' WHERE id = ?",
        [mugID]
    );
    console.log("Updated mugID", mugID, "status to returned");
}

//Add a new user into database
const addUser = async (uuid, user, pass, phone) => {
    const sqlUpdate = await dbQuery(
        "INSERT INTO users (id, name, phone, password) VALUES (?, ?, ?, ?)",
        [uuid, user, phone, pass]
    );
    console.log("Added user", user);
}

//Find a user given username and password
const findUser = async (user, pass) => {
    const rows = await dbQuery(
        "SELECT id FROM users WHERE name = ? AND password = ?",
        [user, pass]
    );
    return rows[0];
}

//Add browser-specific token to user
const addUserToken = async (uid, token) => {
    const sqlUpdate = await dbQuery(
        "UPDATE users SET token = ? WHERE id = ?",
        [token, uid]
    );
    console.log("Added token ", token, " for user ", uid);
}

//Fetch user ID from token
const userFromToken = async (token) => {
    const rows = await dbQuery (
        "SELECT id FROM users WHERE token = ?",
        [token]
    );
    return rows[0];
}

//Remove user token
const removeUserToken = async (uid) => {
    const sqlUpdate = await dbQuery(
        "UPDATE users SET token = NULL WHERE id = ?",
        [uid]
    );
    console.log("Removed token for user: ", uid);
}

const getUserOrders = async (uid) => {
    const rows = await dbQuery(
        "SELECT * FROM orders WHERE user_id = ?",
        [uid]
    );
    return rows;
}

export default { 
    query, 
    insertOrder, 
    getOrderInfo, 
    updateMugStatusAvailable, 
    updateOrderMugID, 
    updateMugStatusInUse, 
    getOrderByMugID, 
    addUser, 
    findUser,
    addUserToken,
    userFromToken,
    removeUserToken,
    getUserOrders,
    pool 
};
