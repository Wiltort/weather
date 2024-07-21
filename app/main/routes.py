from flask import render_template, flash, redirect, url_for
from flask_login import current_user, login_user, logout_user
import sqlalchemy as sa
from app import db
from app.main.forms import LoginForm, CityForm
from app.models import User, City, Forecast_request
from app.utils.weather import get_coordinates, get_weather
from app.main import bp


@bp.route("/", methods=["GET", "POST"])
@bp.route("/index", methods=["GET", "POST"])
def index():
    form = LoginForm()
    city_form = CityForm()
    city = None
    temp_data = None
    daily_weather = None
    if form.validate_on_submit():
        user = db.session.scalar(
            sa.select(User).where(User.username == form.username.data)
        )
        if user is None:
            new_user = User(username=form.username.data)
            new_user.set_password(form.password.data)
            db.session.add(new_user)
            db.session.commit()
            flash(f"Добро пожаловать, {new_user.username}!")
            login_user(new_user, remember=form.remember_me.data)
        elif not user.check_password(form.password.data):
            flash("Пароль неверный!")
        else:
            login_user(user, remember=form.remember_me.data)
    if city_form.validate_on_submit():
        flash("Город {}".format(city_form.name.data))
        city = city_form.name.data
        coordinates = get_coordinates(city)
        if coordinates is None:
            flash("Город не найден")
        else:
            dbcity = db.session.scalar(
                sa.select(City).where(City.name == city.lower())
            )
            if dbcity is None:
                dbcity = City(name=city.lower())
                db.session.add(dbcity)
                db.session.commit()
            if current_user.is_authenticated:
                forecast = Forecast_request(from_user=current_user, city=dbcity)
                db.session.add(forecast)
                db.session.commit()
            hourly_weather, daily_weather = get_weather(coordinates=coordinates)
            temp_data = hourly_weather[["date", "temperature_2m"]].to_dict(orient="records")
    return render_template(
        "index.html",
        title="Введите город",
        form=form,
        city_form=city_form,
        city=city,
        authenticated=current_user.is_authenticated,
        user=current_user,
        temp_data=temp_data,
        weather_data=daily_weather
    )


@bp.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("main.index"))
