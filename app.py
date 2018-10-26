import requests

from flask import Flask, render_template, request, jsonify
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

app = Flask(__name__)

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
# engine = create_engine('postgres://evzazpuapjscve:ae1e41a4f5302a52848eef021e3cca397ca9cbab9665958874ecc5154261f8b7@
# ec2-184-73-169-151.compute-1.amazonaws.com:5432/d4v8ok9mo8ptre')
engine = create_engine("postgresql://maverick:1q2w3e@localhost/test")
db = scoped_session(sessionmaker(bind=engine))


# Homepage
@app.route("/")
def index():
    return render_template("base.html")


# Login Page
@app.route("/login")
def login():
    return render_template("login.html")


# Comes after logging in
@app.route("/search")
def search():
    return render_template("search.html")


# Page to show books as per search result
@app.route("/books", methods=["POST"])
def books():
    book_column = request.form.get("book_column")
    query = request.form.get("query")
    book_list = db.execute("SELECT * FROM books WHERE " + book_column + " = :query ORDER BY title",
                           {"query": query}).fetchall()

    if len(book_list):
        return render_template("booklist.html", book_list=book_list)

    elif book_column != "year":
        error_message = "We couldn't find the books you searched for."
        book_list = db.execute("SELECT * FROM books WHERE " + book_column + " LIKE :query ORDER BY title",
                               {"query": "%" + query + "%"}).fetchall()
        if not len(book_list):
            return render_template("error.html", error_message=error_message)
        message = "You might be searching for:"
        return render_template("error.html", error_message=error_message, book_list=book_list, message=message)


# Page to show specified info about book
@app.route("/books/detail/<int:book_id>", methods=["GET", "POST"])
def detail(book_id):
    book = db.execute("SELECT * FROM books WHERE id = :book_id", {"book_id": book_id}).fetchone()
    if book is None:
        return render_template("error.html", error_message="We got an invalid book id"
                                                           ". Please check for the errors and try again.")
    if request.method == "POST":
        user_id = request.form.get("user_id")
        if db.execute("SELECT id FROM users WHERE id = :user_id", {"user_id": user_id}).fetchone() is None:
            return render_template("error.html", error_message="We got an invalid user id."
                                                               " Please check for the errors and try again.")
        rating = request.form.get("rating")
        comment = request.form.get("comment")
        print(comment)
        if db.execute("SELECT id FROM reviews WHERE user_id = :user_id AND book_id = :book_id",
                      {"user_id": user_id, "book_id": book_id}).fetchone() is None:
            db.execute(
                "INSERT INTO reviews (user_id, book_id, rating, comment) VALUES (:user_id, :book_id, :rating, :comment)",
                {"book_id": book.id, "user_id": user_id, "rating": rating, "comment": comment})
        else:
            db.execute("UPDATE reviews SET comment = :comment, rating = :rating WHERE user_id = :user_id AND book_id = :book_id",
                       {"comment": comment, "rating": rating, "user_id": user_id, "book_id": book_id})
        db.commit()

    """Goodreads API"""
    # Processing the json data
    res = requests.get("https://www.goodreads.com/book/review_counts.json",
                       params={"key": "HD8qbAr9QIMZRCGGI5cEkQ", "isbns": book.isbn}).json()["books"][0]

    ratings_count = res["ratings_count"]
    average_rating = res["average_rating"]
    reviews = db.execute("SELECT * FROM reviews WHERE book_id = :book_id", {"book_id": book.id}).fetchall()
    users = []
    for review in reviews:
        user = db.execute("SELECT email FROM users WHERE id = :user_id", {"user_id": review.user_id}).fetchone()
        users.append((user[0], review))

    return render_template("detail.html", book=book, users=users,
                           ratings_count=ratings_count, average_rating=average_rating)


# Page for the website's API
@app.route("/api/<ISBN>", methods=["GET"])
def api(ISBN):
    book = db.execute("SELECT * FROM books WHERE isbn = :ISBN", {"ISBN": ISBN}).fetchone()
    if book is None:
        return render_template("error.html", error_message="We got an invalid ISBN. "
                                                           "Please check for the errors and try again.")
    reviews = db.execute("SELECT * FROM reviews WHERE book_id = :book_id", {"book_id": book.id}).fetchall()
    count = 0
    rating = 0
    for review in reviews:
        count += 1
        rating += review.rating
    if count:
        average_rating = rating / count
    else:
        average_rating = 0

    return jsonify(
        title=book.title,
        author=book.author,
        year=book.year,
        isbn=book.isbn,
        review_count=count,
        average_rscore=average_rating
    )


if __name__ == "__main__":
    app.run(debug=True)
