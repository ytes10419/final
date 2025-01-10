import sqlite3

def register_user(username, password):
    role = "admin" if username == "admin" else "user"
    conn = sqlite3.connect("audiobook.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                   (username, password, role))
    conn.commit()
    conn.close()

def login_user(username, password):
    conn = sqlite3.connect("audiobook.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
    user = cursor.fetchone()
    conn.close()
    return user


def add_page(title, content, audio_file, image_url,page_number,user_id):
    conn = sqlite3.connect("audiobook.db")
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO pages (title, content, audio_file,image_url, page_number, user_id)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (title, content, audio_file,image_url, page_number,user_id))
    conn.commit()
    conn.close()