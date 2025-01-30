import db

def add_item(title, description, location, user_id):
    sql = """INSERT INTO items (title, description, location, user_id) VALUES (?, ?, ?, ?)"""
    db.execute(sql, [title, description, location, user_id])