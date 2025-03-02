import sqlite3
import secrets
from flask import Flask
from flask import redirect, render_template, request, session, abort, make_response, flash
import markupsafe
import config
import items
import users
import db

app = Flask(__name__)
app.secret_key = config.secret_key

def requires_login():
    if "user_id" not in session:
        abort(403)

def check_csrf():
    if "csrf_token" not in request.form:
        abort(403)
    if request.form["csrf_token"] != session["csrf_token"]:
        abort(403)

@app.template_filter()
def show_lines(content):
    content = str(markupsafe.escape(content))
    content = content.replace("\n", "<br />")
    return markupsafe.Markup(content)

@app.route("/")
def index():
    all_items = items.get_items()
    return render_template("index.html", items=all_items)

@app.route("/search_item/")
def search_item():
    query = request.args.get("query")
    if query:
        results = items.search_items(query)
    else:
        query = ""
        results = []
    return render_template("search_item.html", query=query, results=results)

@app.route("/item/<int:item_id>")
def show_item(item_id):
    item = items.get_item(item_id)
    if not item:
        abort(404)
    classes = items.get_classes(item_id)
    applications = items.get_applications(item_id)
    sound_samples = items.get_sound_samples(item_id)
    return render_template("show_item.html", item=item, classes=classes, applications=applications, sound_samples=sound_samples)

@app.route("/sound_sample/<int:sound_sample_id>")
def show_sound_sample(sound_sample_id):
    sound_sample = items.get_sound_sample(sound_sample_id)
    if not sound_sample:
        abort(404)

    response = make_response(bytes(sound_sample))
    response.headers.set("Content-Type", "audio/wav")
    return response


@app.route("/application/<int:application_id>")
def show_application(application_id):
    application = items.get_application(application_id)
    if application:
        application = application[0]
    else:
        abort(404)
    return render_template("show_application.html", application=application)

@app.route("/new_item")
def new_item():
    requires_login()
    classes = items.get_all_classes()
    return render_template("new_item.html", classes=classes)

@app.route("/create_item", methods=["POST"])
def create_item():
    requires_login()
    check_csrf()

    title = request.form["title"]
    if not title or len(title) > 50:
        if title:
            flash("VIRHE: otsikko liian pitkä")
            return redirect("/new_item/")
        flash("VIRHE: ei otsikkoa")
        return redirect("/new_item/")
    description = request.form["description"]
    if not description or len(description) > 500:
        if description:
            flash("VIRHE: kuvaus liian pitkä")
            return redirect("/new_item/")
        flash("VIRHE: ei kuvausta")
        return redirect("/new_item/")
    location = request.form["location"]
    if len(location) > 50:
        if description:
            flash("VIRHE: paikkakunnan nimi liian pitkä")
        return redirect("/new_item/")
    user_id = session["user_id"]
    if not user_id:
        flash("VIRHE: et ole kirjautunut sisään")
        return redirect("/")

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

    item_id = db.last_insert_id()

    return redirect("/item/" + str(item_id))

@app.route("/create_application", methods=["POST"])
def create_application():
    requires_login()
    check_csrf()

    item_id = request.form["item_id"]

    description = request.form["application_desc"]
    if not description or len(description) > 500:
        if description:
            flash("VIRHE: kuvaus liian pitkä")
            return redirect("/item/" + str(item_id))
        flash("VIRHE: ei kuvausta")
        return redirect("/item/" + str(item_id))
    title = request.form["application_title"]
    if not title or len(title) > 50:
        if title:
            flash("VIRHE: otsikko liian pitkä")
            return redirect("/item/" + str(item_id))
        flash("VIRHE: ei otsikkoa")
        return redirect("/item/" + str(item_id))
    item = items.get_item(item_id)
    if not item:
        abort(404)
    user_id = session["user_id"]
    if not user_id:
        flash("VIRHE: et ole kirjautunut sisään")
        return redirect("/item/" + str(item_id))

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

    return render_template("edit_item.html", item=item, classes=classes, all_classes=all_classes)

@app.route("/sound_samples/<int:item_id>")
def edit_sound_samples(item_id):
    requires_login()

    item = items.get_item(item_id)
    if not item:
        abort(404)
    if item["user_id"] != session["user_id"]:
        abort(403)

    sound_samples = items.get_sound_samples(item_id)

    return render_template("sound_samples.html", item=item, sound_samples=sound_samples)

@app.route("/add_sound_sample", methods=["POST"])
def add_sound_sample():
    requires_login()
    check_csrf()

    item_id = request.form["item_id"]
    item = items.get_item(item_id)
    if not item:
        abort(404)
    if item["user_id"] != session["user_id"]:
        abort(403)

    file = request.files["sound_sample"]
    if not file.filename.endswith(".wav"):
        flash("VIRHE: väärä tiedostomuoto")
        return redirect("/sound_samples/" + str(item_id))

    sound_sample = file.read()
    # if len(sound_sample) > 100 * 1024:
    #    flash("VIRHE: väärä tiedostomuoto")
    #    return redirect("/sound_samples/" + str(item_id))

    items.add_sound_sample(item_id, sound_sample)
    return redirect("/sound_samples/" + str(item_id))

@app.route("/delete_sound_samples", methods=["POST"])
def delete_sound_samples():
    requires_login()
    check_csrf()

    item_id = request.form["item_id"]
    item = items.get_item(item_id)
    if not item:
        abort(404)
    if item["user_id"] != session["user_id"]:
        abort(403)

    for sound_sample_id in request.form.getlist("sound_sample_id"):
        items.remove_sound_sample(item_id, sound_sample_id)

    return redirect("/sound_samples/" + str(item_id))

@app.route("/delete_item/<int:item_id>",  methods=["GET", "POST"])
def delete_item(item_id):
    requires_login()

    item = items.get_item(item_id)
    if not item:
        abort(404)
    if item["user_id"] != session["user_id"]:
        abort(403)

    if request.method == "GET":
        return render_template("delete_item.html", item=item)

    if request.method == "POST":
        check_csrf()
        if "delete" in request.form:
            items.delete_item(item_id)
            return redirect("/")
        return redirect("/item/" + str(item_id))

@app.route("/update_item", methods=["POST"])
def update_item():
    requires_login()
    check_csrf()

    item_id = request.form["item_id"]
    item = items.get_item(item_id)
    if not item:
        abort(404)
    if item["user_id"] != session["user_id"]:
        abort(403)

    title = request.form["title"]
    if not title or len(title) > 50:
        if title:
            flash("VIRHE: otsikko liian pitkä")
            return redirect("/edit_item/" + str(item_id))
        flash("VIRHE: ei otsikkoa")
        return redirect("/edit_item/" + str(item_id))
    description = request.form["description"]
    if not description or len(description) > 500:
        if description:
            flash("VIRHE: kuvaus liian pitkä")
            return redirect("/edit_item/" + str(item_id))
        flash("VIRHE: ei kuvausta")
        return redirect("/edit_item/" + str(item_id))
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

    if request.method == "POST":
        if "update" in request.form:
            items.update_item(item_id, title, description, location, classes)
            return redirect("/item/" + str(item_id))
        return redirect("/item/" + str(item_id))

@app.route("/register")
def register():
    return render_template("register.html")

@app.route("/user/<int:user_id>")
def show_user(user_id):
    user = users.get_user(user_id)
    if not user:
        abort(404)
    return render_template("show_user.html", user=user, items=users.get_user_items(user_id))

@app.route("/create", methods=["POST"])
def create():
    username = request.form["username"]
    if not username or len(username) > 30:
        if username:
            flash("VIRHE: käyttäjätunnus liian pitkä")
            return redirect("/register")
        flash("VIRHE: syötä käyttäjätunnus")
        return redirect("/register")
    password1 = request.form["password1"]
    if not password1 or len(password1) > 30:
        if password1:
            flash("VIRHE: salasana liian pitkä")
            return redirect("/register")
        flash("VIRHE: syötä salasana")
        return redirect("/register")
    password2 = request.form["password2"]
    if password1 != password2:
        flash("VIRHE: salasanat eivät ole samat")
        return redirect("/register")

    try:
        users.create_user(username, password1)
    except sqlite3.IntegrityError:
        flash("VIRHE: tunnus on jo varattu")
        return redirect("/register")
    flash("Tunnus luotu")
    return redirect("/")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")

    if request.method == "POST":
        username = request.form["username"]
        if not username or len(username) > 30:
            if username:
                flash("VIRHE: käyttäjätunnus liian pitkä")
                return redirect("/register")
            flash("VIRHE: syötä käyttäjätunnus")
            return redirect("/register")
        password = request.form["password"]
        if not password or len(password) > 30:
            if password:
                flash("VIRHE: salasana liian pitkä")
                return redirect("/register")
            flash("VIRHE: syötä salasana")
            return redirect("/register")

        user_id = users.check_login(username, password)

        if user_id:
            session["user_id"] = user_id
            session["username"] = username
            session["csrf_token"] = secrets.token_hex(16)
            return redirect("/")
        flash("VIRHE: väärä tunnus tai salasana")
        return redirect("/login")

@app.route("/logout")
def logout():
    if "user_id" in session:
        del session["user_id"]
        del session["username"]
    return redirect("/")
