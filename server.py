"""Movie Ratings."""

from jinja2 import StrictUndefined

from flask import (Flask, render_template, redirect, request, flash,
                   session, jsonify)
from flask_debugtoolbar import DebugToolbarExtension

from model import User, Rating, Movie, connect_to_db, db


app = Flask(__name__)

# Required to use Flask sessions and the debug toolbar
app.secret_key = "ABC"

# Normally, if you use an undefined variable in Jinja2, it fails
# silently. This is horrible. Fix this so that, instead, it raises an
# error.
app.jinja_env.undefined = StrictUndefined


@app.route('/')
def index():
    """Homepage."""

    return render_template("homepage.html")


@app.route("/register", methods=["GET"])
def register_form():
    """Renders registration form"""

    return render_template("register_form.html")


@app.route("/register-process", methods=["POST"])
def register_process():
    """Takes in four inputs via POST request and returns redirect to hompage.
    Adds new user to the database if they don't exist."""

    email = request.form.get("email")
    password = request.form.get("password")
    age = request.form.get("age")
    zipcode = request.form.get("zipcode")

    if (User.query.filter_by(email=email).all()) == []:
        new_user = User(email=email, password=password, age=age,
                        zipcode=zipcode)

        db.session.add(new_user)
        db.session.commit()

    #TBD: create edge case handling in case user does exist


    return redirect("/")


@app.route("/login", methods=["GET"])
def login_form():
    """Renders login template"""
    return render_template("login.html")


@app.route("/login-process", methods=["POST"])
def login_process():
    """Takes in email and password via post request and returns a redirect to
    either homepage or login page"""

    email = request.form.get("email")
    password = request.form.get("password")

    user_object = User.query.filter_by(email=email).first()

    # If user exists and password is correct, redirect to homepage
    if user_object and (user_object.password == password):
        session["user_id"] = user_object.user_id
        flash('You were successfully logged in')
        return redirect("/")
    # If either email or password incorrect, show message to user.
    else:
        flash("This combination of username and password doesn't exist")
        return redirect("/login")


@app.route("/users")
def user_list():
    """Show list of users."""

    users = User.query.all()
    return render_template("user_list.html", users=users)


@app.route("/logout", methods=["POST"])
def logout_process():
    """Takes in a post request to logout and returns redirect to homepage."""
    del session["user_id"]
    flash('You were successfully logged out')
    return redirect("/")


@app.route("/user/<user_id>")
def display_user_profile(user_id):
    """Takes in URL input for user_id and renders that users profile."""

    user_object = User.query.filter_by(user_id=user_id).one()

    return render_template("user_profile.html", user=user_object)


@app.route("/movies")
def movie_list():
    """Show list of movies."""
    movies = Movie.query.order_by("title").all()
    return render_template("movie_list.html", movies=movies)


@app.route("/movie/<movie_id>")
def display_movie_profile(movie_id):
    """Takes in URL input for movie_id and renders that movie profile."""

    movie_object = Movie.query.filter_by(movie_id=movie_id).one()

    user_id = session.get("user_id")

    if user_id:
        user_rating = Rating.query.filter_by(movie_id=movie_id,
                                             user_id=user_id).first()
    else:
        user_rating = None

    rating_scores = [r.score for r in movie_object.ratings]
    try:
        avg_rating = float(sum(rating_scores)) / len(rating_scores)
    except ZeroDivisionError:
        avg_rating = None

    prediction = None

    if (not user_rating) and user_id:
        user = User.query.get(user_id)
        if user:
            prediction = user.predict_rating(movie_object)

    return render_template(
        "movie_details.html",
        movie=movie_object,
        user_rating=user_rating,
        average=avg_rating,
        prediction=prediction
        )


@app.route("/rating-process/<movie_id>", methods=["POST"])
def rate_process(movie_id):
    """Takes in single inputs via POST request and returns redirect to movie
    details. Adds new rating to the database or updates existing record."""

    movie_id = movie_id
    rating = int(request.form.get("rating"))
    user_id = session.get("user_id")
    existing_rating = Rating.query.filter(Rating.user_id == user_id,
                                          Rating.movie_id == movie_id).first()

    if existing_rating:
        existing_rating.score = rating

    else:
        new_rating = Rating(movie_id=movie_id, user_id=user_id, score=rating)
        db.session.add(new_rating)

    db.session.commit()

    return redirect("/movie/" + movie_id)


if __name__ == "__main__":
    # We have to set debug=True here, since it has to be True at the
    # point that we invoke the DebugToolbarExtension
    app.debug = True
    app.jinja_env.auto_reload = app.debug  # make sure templates, etc. are not cached in debug mode

    connect_to_db(app)

    # Use the DebugToolbar
    DebugToolbarExtension(app)


    app.run(port=5000, host='0.0.0.0')
