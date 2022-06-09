import os, math

from flask import Flask, render_template, request
from flask_login import LoginManager, login_user, login_required, logout_user, current_user, user_unauthorized
from werkzeug.utils import redirect
from flask_restful import reqparse, abort, Api, Resource
import datetime

from data import db_session
from data.meals import Meals
from data.orders import Orders
from data.users import Users
from forms.login import LoginForm

app = Flask(__name__)
api = Api(app)
order_details = {}

app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'
login_manager = LoginManager()
login_manager.init_app(app)

ORDER = []


def main():
    db_session.global_init("db/sabantuy.db")
    app.run()


@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.query(Users).get(user_id)


@app.route('/', methods=['GET', 'POST'])
def menu():
    db_sess = db_session.create_session()
    try:
        basket_user = [int(i) for i in current_user.basket.split(', ')]
    except Exception:
        basket_user = [0]
    a = []
    for i in db_sess.query(Meals).all():
        a.append(i.category)
    all_meals = {}
    for i in sorted(list(set(a)), reverse=True):
        a = []
        for m in db_sess.query(Meals).filter(
                Meals.category == i):
            a.append([m.name, len(m.name), m.pic, m.in_stock, basket_user.count(m.id), m.id])
        all_meals[i] = a
    cols = 3
    for i in all_meals:
        n = math.ceil(len(all_meals[i]) / cols)
        dr = [[] for i in range(n)]
        k = 0
        for j in range(len(all_meals[i])):
            dr[k].append(all_meals[i][j])
            if (j + 1) % cols == 0:
                k += 1
        all_meals[i] = [dr, len(dr)]
    return render_template('menu.html', all_meals=all_meals)


@app.route('/basket', methods=['GET', 'POST'])
def basket():
    db_sess = db_session.create_session()
    a = current_user.id
    b_ = None
    if not db_sess.query(Users).filter(Users.id == a).first().basket:
        return render_template('basket_empty.html')
    else:
        for u in db_sess.query(Users).filter(Users.id == a):
            b_ = [int(i) for i in u.basket.split(', ')]
        b = [db_sess.query(Meals).filter(Meals.id == i).first().name for i in b_]
        bask = {}
        for i in b:
            if i not in bask:
                bask[i] = [b.count(i)]
        return render_template('basket_meals.html', basket=bask)


@app.route('/orders_history', methods=['GET', 'POST'])
def orders_history():
    ors = []
    db_sess = db_session.create_session()
    a = 1
    for order in db_sess.query(Orders).filter(Orders.client_id == current_user.id):
        months = ['января', 'февраля', 'марта', 'апреля', 'мая', 'июня', 'июля', 'августа', 'сентября', 'октября',
                  'ноября', 'декабря']
        date_ = []
        date_.append(str(order.date.day))
        date_.append(months[order.date.month - 1])
        date_.append(str(order.date.year))
        meals_ = [int(i) for i in order.meals.split(', ')]
        meals = []
        for i in meals_:
            meals.append(db_sess.query(Meals).filter(Meals.id == i).first().name)
        bask = {}
        for i in meals:
            if i not in bask:
                bask[i] = meals.count(i)
        meal = []
        for i in bask:
            meal.append(i + "( " + str(bask[i]) + "шт. )")
        ors.append([order.id, meal, ' '.join(date_), order.is_ready, a])
        a += 1
    return render_template('orders_history.html', orders=ors[::-1])


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        if all(a.isalpha() for a in form.name.data) and all(
                a.isalpha() for a in form.surname.data) and str(form.ryad.data).isdigit() and str(form.mesto.data).isdigit():
            if db_sess.query(Users).filter(
                    Users.name == form.name.data and Users.surname == form.surname.data and Users.last_name == form.last_name.data).first():
                u = db_sess.query(Users).filter(
                    Users.name == form.name.data and Users.surname == form.surname.data and Users.last_name == form.last_name.data).first()
                u.ryad = form.ryad.data
                u.mesto = form.mesto.data
                db_sess.commit()
                login_user(u,
                           remember=form.remember_me.data)
                return redirect("/")
            user = Users()
            user.name = form.name.data
            user.surname = form.surname.data
            user.last_name = form.last_name.data
            user.ryad = form.ryad.data
            user.mesto = form.mesto.data
            db_sess.add(user)
            db_sess.commit()
            login_user(user, remember=form.remember_me.data)
            return redirect("/")
        return render_template('login.html', message='Неправильный формат данных')
    return render_template('login.html', title='Авторизация', form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/")


@app.route('/reorder/<int:id>', methods=['GET', 'POST'])
def reorder(id):
    db_sess = db_session.create_session()
    ord = db_sess.query(Orders).filter(Orders.id == id).first()
    order = Orders()
    order.client_id = ord.client_id
    order.meals = ord.meals
    ord.date = datetime.datetime.now
    db_sess = db_session.create_session()
    db_sess.add(order)
    db_sess.commit()
    return redirect('/orders_history')


@app.route('/order', methods=['GET', 'POST'])
def to_order():
    db_sess = db_session.create_session()
    if db_sess.query(Users).filter(Users.id == current_user.id).first().basket:
        user = db_sess.query(Users).filter(Users.id == current_user.id).first()
        order = Orders()
        order.client_id = current_user.id
        order.meals = user.basket
        db_sess.add(order)
        user.basket = None
        order_details['id'] = order.id
        order_details['client_name'] = user.name
        db_sess.commit()
        return redirect('/orders_history')
    return redirect('/')


@app.route('/choose/<int:id>/<int:user_id>', methods=['GET', 'POST'])
def choose(id, user_id):
    db_sess = db_session.create_session()
    for order in db_sess.query(Users).filter(Users.id == user_id):
        b = order.basket
        if not b:
            order.basket = str(id)
        else:
            order.basket = b + ', ' + str(id)
        db_sess.commit()
    return redirect('/')


if __name__ == '__main__':
    main()
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, threading=True)
