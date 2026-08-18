import mysql.connector as db
import bcrypt

def get_connection():
    return db.connect(host="localhost", user="root", passwd="mysql", database="flights")

def migrate_passwords():
    con = get_connection()
    cur = con.cursor()

    # fetch all users
    cur.execute("SELECT user_id, password_hash FROM users")
    users = cur.fetchall()

    for user_id, plain_password in users:
        # check if it’s already hashed (bcrypt hashes always start with $2b$)
        if plain_password.startswith("$2b$"):
            continue  # already hashed

        # hash the old plain-text password
        hashed = bcrypt.hashpw(plain_password.encode("utf-8"), bcrypt.gensalt())

        # update row with hashed password
        cur.execute("UPDATE users SET password_hash=%s WHERE user_id=%s", (hashed.decode("utf-8"), user_id))

    con.commit()
    con.close()
    print("✅ All plain-text passwords migrated to hashed format.")

if __name__ == "__main__":
    migrate_passwords()
