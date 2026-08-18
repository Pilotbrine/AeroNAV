import mysql.connector as db
import bcrypt

def get_connection():
    return db.connect(host="localhost", user="root", passwd="mysql", database="flights")

def register(username, password, role="user"):
    con = get_connection()
    cur = con.cursor()

    # hash the password before saving
    hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())

    cur.execute(
        "INSERT INTO users (username, password_hash, role) VALUES (%s, %s, %s)",
        (username, hashed.decode("utf-8"), role),
    )
    con.commit()
    con.close()
    print(f"✅ User {username} registered as {role}")

def login(username, password):
    con = get_connection()
    cur = con.cursor()
    cur.execute("SELECT user_id, password_hash, role FROM users WHERE username=%s", (username,))
    user = cur.fetchone()
    con.close()

    if user and bcrypt.checkpw(password.encode("utf-8"), user[1].encode("utf-8")):
        print(f"✅ Login successful as {user[2]}")
        return {"user_id": user[0], "username": username, "role": user[2]}
    else:
        print("❌ Invalid username or password")
        return None

