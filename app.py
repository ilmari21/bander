import sqlite3
from flask import Flask
from flask import redirect, render_template, request, session, abort
import config
import items
import users

app = Flask(__name__)
app.secret_key = config.secret_key

@app.route("/")
def index():
    all_items = items.get_items()
    return render_template("index.html", items = all_items)

def requires_login():
    if "user_id" not in session:
        abort(403)

@app.route("/search_item/")
def search_item():
    query = request.args.get("query")
    if query:
        results = items.search_items(query)
    else:
        query = ""
        results = []
    return render_template("search_item.html", query = query, results = results)

@app.route("/item/<int:item_id>")
def show_item(item_id):
    item = items.get_item(item_id)
    if not item:
        abort(404)
    classes = items.get_classes(item_id)
    applications = items.get_applications(item_id)
    return render_template("show_item.html", item = item, classes = classes, applications = applications)

@app.route("/application/<int:application_id>")
def show_application(application_id):
    print(f"application id: {application_id}")
    application = items.get_application(application_id)
    if application:
        application = application[0]
    else:
        abort(404)
    return render_template("show_application.html", application = application)

@app.route("/new_item")
def new_item():
    requires_login()
    classes = items.get_all_classes()
    return render_template("new_item.html", classes = classes)

@app.route("/create_item", methods=["POST"])
def create_item():
    requires_login()

    title = request.form["title"]
    if not title or len(title) > 50:
        abort(403)
    description = request.form["description"]
    if not description or len(description) > 500:
        abort(403)
    location = request.form["location"]
    if len(location) > 50:
        abort(403)
    user_id = session["user_id"]

    all_classes = items.get_all_classes()

    classes = []
    for entry in request.form.getlist("classes"):
        if entry:
            class_title, class_value = entry.split(":")
            if class_title not in all_classes:
                abort(403)
            if class_value not in all_classes[class_title]:
                abort(403)
            classes.append((class_title, class_value))

    items.add_item(title, description, location, user_id, classes)

    return redirect("/")

@app.route("/create_application", methods=["POST"])
def create_application():
    requires_login()

    description = request.form["application_desc"]
    if not description or len(description) > 500:
        abort(403)
    title = request.form["application_title"]
    if not title or len(title) > 50:
        abort(403)
    item_id = request.form["item_id"]
    item = items.get_item(item_id)
    if not item:
        abort(403)
    user_id = session["user_id"]

    items.add_application(title, description, user_id, item_id)

    return redirect("/item/" + str(item_id))

@app.route("/edit_item/<int:item_id>")
def edit_item(item_id):
    requires_login()

    item = items.get_item(item_id)
    if not item:
        abort(404)
    if item["user_id"] != session["user_id"]:
        abort(403)

    all_classes = items.get_all_classes()

    classes = {}
    for item_class in all_classes:
        classes[item_class] = ""
    for entry in items.get_classes(item_id):
        classes[entry["title"]] = entry["value"]

    return render_template("edit_item.html", item = item, classes = classes, all_classes = all_classes)

@app.route("/delete_item/<int:item_id>",  methods=["GET", "POST"])
def delete_item(item_id):
    requires_login()

    item = items.get_item(item_id)
    if not item:
        abort(404)
    if item["user_id"] != session["user_id"]:
        abort(403)

    if request.method == "GET":
        return render_template("delete_item.html", item = item)

    if request.method == "POST":
        if "delete" in request.form:
            items.delete_item(item_id)
            return redirect("/")
        else:
            return redirect("/item/" + str(item_id))

@app.route("/update_item", methods=["POST"])
def update_item():
    requires_login()

    item_id = request.form["item_id"]
    item = items.get_item(item_id)
    if not item:
        abort(404)
    if item["user_id"] != session["user_id"]:
        abort(403)

    title = request.form["title"]
    if not title or len(title) > 50:
        abort(403)
    description = request.form["description"]
    if not description or len(description) > 50:
        abort(403)
    location = request.form["location"]

    all_classes = items.get_all_classes()

    classes = []
    for entry in request.form.getlist("classes"):
        if entry:
            class_title, class_value = entry.split(":")
            if class_title not in all_classes:
                abort(403)
            if class_value not in all_classes[class_title]:
                abort(403)
            classes.append((class_title, class_value))

    items.update_item(item_id, title, description, location, classes)

    return redirect("/item/" + str(item_id))

@app.route("/register")
def register():
    return render_template("register.html")

@app.route("/user/<int:user_id>")
def show_user(user_id):
    user = users.get_user(user_id)
    if not user:
        abort(404)
    return render_template("show_user.html", user = user, items = users.get_user_items(user_id))

@app.route("/create", methods=["POST"])
def create():
    username = request.form["username"]
    password1 = request.form["password1"]
    password2 = request.form["password2"]
    if password1 != password2:
        return "VIRHE: salasanat eivät ole samat"

    try:
        users.create_user(username, password1)
    except sqlite3.IntegrityError:
        return "VIRHE: tunnus on jo varattu"

    return "Tunnus luotu"

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        user_id = users.check_login(username, password)

        if user_id:
            session["user_id"] = user_id
            session["username"] = username
            return redirect("/")
        else:
            return "VIRHE: väärä tunnus tai salasana"

@app.route("/logout")
def logout():
    if "user_id" in session:
        del session["user_id"]
        del session["username"]
    return redirect("/")
