import os
from flask import (
    Flask, flash, render_template,
    request, redirect, session, url_for)
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
import math
if os.path.exists("env.py"):
    import env


app = Flask(__name__)

app.config["MONGO_DBNAME"] = os.environ.get("MONGO_DBNAME")
app.config["MONGO_URI"] = os.environ.get("MONGO_URI")
app.secret_key = os.environ.get("SECRET_KEY")

mongo = PyMongo(app)


@app.route("/")
@app.route("/get_books/new_books")
@app.route("/get_books/new_books/<int:page>")
def books_new(page=1):
    books = list(mongo.db.books.find().sort("_id", -1))
    genres = mongo.db.genres.find().sort("genres", 1)

    if page == 1:
        booklist = books[0:10]
    else:
        first = page * 10 - 10
        last = first + 10
        booklist = books[first:last]
    counter = math.ceil((len(books))/(10))

    return render_template(
        "books.html", books=booklist, genres=genres, pages=counter)


@app.route("/search", methods=["GET", "POST"])
def search():
    genres = mongo.db.genres.find().sort("genres", 1)

    booklist = list(mongo.db.books.find(
        {"$text": {"$search": request.form.get("query")}}))
    return render_template(
        "books.html", books=booklist, genres=genres, post=True)


@app.route("/get_books/a-to-z")
@app.route("/get_books/a-to-z/<int:page>")
def books_a_to_z(page=1):
    books = list(mongo.db.books.find().sort("book_name", 1))
    genres = mongo.db.genres.find().sort("genres", 1)

    if page == 1:
        booklist = books[0:10]
    else:
        first = page * 10 - 10
        last = first + 10
        booklist = books[first:last]
    counter = math.ceil((len(books))/(10))

    return render_template(
        "books-a-to-z.html", books=booklist, genres=genres, pages=counter)


@app.route("/get_books/z-to-a")
@app.route("/get_books/z-to-a/<int:page>")
def books_z_to_a(page=1):
    books = list(mongo.db.books.find().sort("book_name", -1))
    genres = mongo.db.genres.find().sort("genres", 1)

    if page == 1:
        booklist = books[0:10]
    else:
        first = page * 10 - 10
        last = first + 10
        booklist = books[first:last]
    counter = math.ceil((len(books))/(10))

    return render_template(
        "books-z-to-a.html", books=booklist, genres=genres, pages=counter)


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        # check if username already exists
        existing_user = mongo.db.users.find_one(
            {"username": request.form.get("username").lower()})

        # if user exists
        if existing_user:
            flash("Username already exists")
            return redirect(url_for("register"))

        # else
        register = {
            "username": request.form.get("username").lower(),
            "password": generate_password_hash(request.form.get("password"))
        }
        mongo.db.users.insert_one(register)

        # put user into session cookie
        session["user"] = request.form.get("username").lower()
        flash("Registration successful")
        return render_template("login.html")
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    # check if username already exists in db
    if request.method == "POST":
        existing_user = mongo.db.users.find_one(
            {"username": request.form.get("username").lower()})

        if existing_user:
            # make sure hashed password equals user input
            if check_password_hash(
                existing_user["password"], request.form.get("password")):
                    session["user"] = request.form.get("username").lower()
                    flash("Welcome, {}".format(
                        request.form.get("username")))
                    return redirect(url_for(
                        "profile", username=session["user"]))
            # if pw input != hashed password
            else:
                flash("Password and/or Username is incorrect")
                return redirect(url_for("login"))
        # if username does not exist in db
        else:
            flash("Username and/or Password incorrect")
            return redirect(url_for("login"))

    return render_template("login.html")


@app.route("/profile/<username>", methods=["GET", "POST"])
def profile(username):
    # get the session user's username from db
    username = mongo.db.users.find_one(
        {"username": session["user"]})["username"]
    # if true then return users profile
    if session["user"]:
        return render_template("profile.html", username=username)
    # if untrue return user back to login
    return redirect(url_for("login"))


@app.route("/logout")
def logout():
    # remove user from session cookies
    flash("You have been logged out")
    session.pop("user")
    return redirect(url_for("login"))


@app.route("/bookpage/<book_name>")
def bookpage(book_name):
    get_book = mongo.db.books.find_one({"book_name": book_name})
    return render_template(
        "bookpage.html", get_book=get_book)


@app.route("/add_book", methods=["GET", "POST"])
def add_book():
    if request.method == "POST":
        is_upvoted = "on" if request.form.get("is_upvoted") else "off"
        book = {
            "genre_name": request.form.get("genre_name"),
            "book_name": request.form.get("book_name"),
            "author": request.form.get("author"),
            "image_url": request.form.get("image_url"),
            "description": request.form.get("description"),
            "buy_url": request.form.get("buy_url"),
            "is_upvoted": is_upvoted,
            "created_by": session["user"],
        }
        mongo.db.books.insert_one(book)
        flash("Book Successfully Added")
        return redirect(url_for("books_new"))

    genres = mongo.db.genres.find().sort("genre_name", 1)
    return render_template("add_book.html", genres=genres)


@app.route("/edit_book/<book_name>/<id>", methods=["GET", "POST"])
def edit_book(book_name, id):
    if request.method == "POST":
        is_upvoted = "on" if request.form.get("is_upvoted") else "off"
        save = {
            "genre_name": request.form.get("genre_name"),
            "book_name": request.form.get("book_name"),
            "author": request.form.get("author"),
            "image_url": request.form.get("image_url"),
            "description": request.form.get("description"),
            "buy_url": request.form.get("buy_url"),
            "is_upvoted": is_upvoted,
            "created_by": session["user"]
        }
        mongo.db.books.update({"_id": ObjectId(id)}, save)
        flash("Book Successfully Updated")

    get_book = mongo.db.books.find_one({"_id": ObjectId(id)})
    genres = mongo.db.genres.find().sort("genre_name", 1)
    return render_template(
        "edit_book.html", get_book=get_book, genres=genres, id=id)


@app.route("/delete_book/<book_name>/<id>")
def delete_book(book_name, id):
    mongo.db.books.remove({"_id": ObjectId(id)})
    flash("Book has sucessfully been deleted")
    return redirect(url_for("books_new"))


@app.route("/bookpage/<book_name>", methods=["POST"])
def review_book(book_name):
    get_book = mongo.db.books.find_one({"book_name": book_name})
    reviews = get_book.get("review")
    if request.method == "POST":
        if reviews:
            for review in reviews:
                if review["username"] == session["user"]:
                    flash("You have already reviewed this book.")
                    return redirect(url_for(
                        "bookpage", book_name=get_book.get("book_name")))
        mongo.db.books.update_one(
            {"_id": ObjectId(get_book["_id"])}, {
                "$addToSet": {"review": {
                    "description": request.form.get("review"),
                    "username": session["user"]}}})
        flash("review saved")
    return redirect(url_for("bookpage", book_name=get_book.get("book_name")))


@app.route("/get_genres")
def get_genres():
    genres = list(mongo.db.genres.find().sort("genre_name", 1))
    return render_template("genres.html", genres=genres)


@app.route("/add_genre", methods=["GET", "POST"])
def add_genre():
    if request.method == "POST":
        genre = {
            "genre_name": request.form.get("genre_name")
        }
        mongo.db.genres.insert_one(genre)
        flash("New Genre Added")
        return redirect(url_for("get_genres"))

    return render_template("add_genre.html")


@app.route("/edit_genre/<genre_id>", methods=["GET", "POST"])
def edit_genre(genre_id):
    if request.method == "POST":
        save = {
            "genre_name": request.form.get("genre_name")
        }
        mongo.db.genres.update({"_id": ObjectId(genre_id)}, save)
        flash("Genre Successfully Updated")
        return redirect(url_for("get_genres"))

    genre = mongo.db.genres.find_one({"_id": ObjectId(genre_id)})
    return render_template("edit_genre.html", genre=genre)


@app.route("/delete_genre/<genre_id>")
def delete_genre(genre_id):
    mongo.db.genres.remove({"_id": ObjectId(genre_id)})
    flash("Genre Successfully Deleted")
    return redirect(url_for("get_genres"))


if __name__ == "__main__":
    app.run(host=os.environ.get("IP"),
            port=int(os.environ.get("PORT")),
            debug=True)
