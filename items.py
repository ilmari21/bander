import db

def add_item(title, description, location, user_id, classes):
    sql = """INSERT INTO items (title, description, location, user_id) VALUES (?, ?, ?, ?)"""
    db.execute(sql, [title, description, location, user_id])

    item_id = db.last_insert_id()

    sql = "INSERT INTO item_classes (item_id, title, value) VALUES (?, ?, ?)"
    for title, value in classes:
        db.execute(sql, [item_id, title, value])

def add_application(title, description, user_id, item_id):
    sql = """INSERT INTO applications (title, description, user_id, item_id) VALUES (?, ?, ?, ?)"""
    db.execute(sql, [title, description, user_id, item_id])

def get_items():
    sql = """SELECT items.id, items.title, users.id user_id, users.username
             FROM items, users
             WHERE items.user_id = users.id
             ORDER BY items.id DESC"""
    return db.query(sql)

def get_applications(item_id):
    sql = """SELECT id, title FROM applications WHERE item_id = ? ORDER BY id DESC"""
    return db.query(sql, [item_id])

def get_application(application_id):
    sql = """SELECT applications.id,
                    applications.title,
                    applications.description,
                    applications.item_id,
                    users.id user_id,
                    users.username
             FROM applications, users
             WHERE applications.id = ? AND
                   applications.user_id = users.id
             ORDER BY applications.id DESC"""
    return db.query(sql, [application_id])

def get_item(item_id):
    sql = """SELECT items.id,
                    items.title,
                    items.description,
                    items.location,
                    users.id user_id,
                    users.username
             FROM items, users
             WHERE items.user_id = users.id AND
                   items.id = ?"""
    result = db.query(sql, [item_id])
    return result[0] if result else None

def get_classes(item_id):
    sql = "SELECT title, value FROM item_classes WHERE item_id = ?"
    return db.query(sql, [item_id])

def get_all_classes():
    sql = "SELECT title, value FROM classes ORDER BY id"
    result = db.query(sql)

    classes = {}
    for title, value in result:
        classes[title] = []
    for title, value in result:
        classes[title].append(value)

    return classes

def get_sound_samples(item_id):
    sql = "SELECT id FROM sound_samples WHERE item_id = ?"
    return db.query(sql, [item_id])

def add_sound_sample(item_id, sound_sample):
    sql = "INSERT INTO sound_samples (item_id, sound_sample) VALUES (?, ?)"
    db.execute(sql, [item_id, sound_sample])

def get_sound_sample(sound_sample_id):
    sql = "SELECT sound_sample FROM sound_samples WHERE id = ?"
    result = db.query(sql, [sound_sample_id])
    return result[0][0] if result else None

def remove_sound_sample(item_id, sound_sample_id):
    sql = "DELETE FROM sound_samples WHERE id = ? AND item_id = ?"
    db.execute(sql, [sound_sample_id, item_id])

def update_item(item_id, title, description, location, classes):
    sql = """UPDATE items SET title = ?,
                              description = ?,
                              location = ?
                          WHERE id = ?"""
    db.execute(sql, [title, description, location, item_id])

    sql = "DELETE FROM item_classes WHERE item_id = ?"
    db.execute(sql, [item_id])

    sql = "INSERT INTO item_classes (item_id, title, value) VALUES (?, ?, ?)"
    for title, value in classes:
        db.execute(sql, [item_id, title, value])

def delete_item(item_id):
    sql = "DELETE FROM sound_samples WHERE item_id = ?"
    db.execute(sql, [item_id])
    sql = "DELETE FROM applications WHERE item_id = ?"
    db.execute(sql, [item_id])
    sql = """DELETE FROM item_classes WHERE item_id = ?"""
    db.execute(sql, [item_id])
    sql = """DELETE FROM items WHERE id = ?"""
    db.execute(sql, [item_id])

def search_items(query):
    sql = """SELECT id, title
             FROM items
             WHERE title LIKE ? OR description LIKE ?
             ORDER BY id DESC"""
    like = "%" + query + "%"
    return db.query(sql, [like, like])
