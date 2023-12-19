import os
from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, FloatField
from wtforms.validators import DataRequired, NumberRange
import requests

IMG_LINK = 'https://image.tmdb.org/t/p/w500'
API_KEY = os.environ['API_KEY']
TMDB_ENDPOINT = 'https://api.themoviedb.org/3/search/movie'

db = SQLAlchemy()
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///movie.db"
app.config['SECRET_KEY'] = os.environ['SECRET_KEY']
Bootstrap(app)
db.init_app(app)


def find_movie(title):
    params = {
        "api_key": API_KEY,
        'query': title
    }
    response = requests.get(TMDB_ENDPOINT, params=params)
    data = response.json()
    return data['results']


def find_movie_by_id(movie_id):
    endpoint = f'https://api.themoviedb.org/3/movie/{movie_id}'
    params = {
        "api_key": API_KEY
    }
    res = requests.get(endpoint, params=params)
    data = res.json()
    return data


# Table DB
class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String, nullable=True)
    year = db.Column(db.Integer, nullable=True)
    description = db.Column(db.String, nullable=True)
    rating = db.Column(db.Float, nullable=True)
    ranking = db.Column(db.Integer)
    review = db.Column(db.String, nullable=True)
    img = db.Column(db.String, nullable=True)


# Edit Form
class EditForm(FlaskForm):
    rating = FloatField('Your Rating Out of 10 e.g. 7.5', validators=[NumberRange(min=1, max=10)])
    review = StringField('Your Review')
    submit = SubmitField('Edit')


# Add Form
class AddForm(FlaskForm):
    title = StringField('Movie Title', validators=[DataRequired()])
    submit = SubmitField('Add Movie')


@app.route("/")
def home():
    movies = db.session.execute(db.select(Movie).order_by(Movie.rating.desc())).scalars()
    n = 1
    for movie in movies:
        movie.ranking = n
        n += 1
        db.session.add(movie)
        db.session.commit()
    movies = db.session.execute(db.select(Movie).order_by(Movie.rating.desc())).scalars()
    return render_template("index.html", movies=movies)


@app.route('/add', methods=['GET', 'POST'])
def add():
    form = AddForm()
    if form.validate_on_submit():
        title = form.title.data
        movie_list = find_movie(title)
        length = len(movie_list)
        return render_template("select.html", movie_list=movie_list, len=length)
    return render_template("add.html", form=form)


@app.route("/make/<movie_id>", methods=['POST', 'GET'])
def make_a_card(movie_id):
    movie = find_movie_by_id(movie_id)
    if movie['poster_path'] is None:
        img_link = 'https://www.shortlist.com/media/images/2019/05/the-30-coolest-alternative-movie-posters-ever-2-1556670563-K61a-column-width-inline.jpg'
    else:
        img_link = IMG_LINK + movie['poster_path']
    movie = Movie(
        title=movie['original_title'],
        year=movie['release_date'][0:4],
        img=img_link,
        description=movie['overview']
    )
    db.session.add(movie)
    db.session.commit()
    new_id = movie.id
    return redirect(url_for('edit', movie_id=new_id))


@app.route("/edit/<int:movie_id>", methods=['GET', 'POST'])
def edit(movie_id):
    form = EditForm()
    movie = db.session.execute(db.select(Movie).where(Movie.id == movie_id)).scalar()
    if form.validate_on_submit():
        movie.rating = form.rating.data
        movie.review = form.review.data
        db.session.add(movie)
        db.session.commit()
        return redirect(url_for('home'))
    title = movie.title
    return render_template("edit.html", movie_id=movie_id, title=title, form=form)


@app.route('/delete/<int:movie_id>')
def delete(movie_id):
    movie = db.get_or_404(Movie, movie_id)
    db.session.delete(movie)
    db.session.commit()
    return redirect(url_for('home'))


with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)
