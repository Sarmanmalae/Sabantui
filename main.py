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
from forms.register import RegisterForm

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



@app.route('/menu', methods=['GET', 'POST'])
def menu():
    db_sess = db_session.create_session()
    try:
        basket_user = [int(i) for i in current_user.basket.split(', ')]
    except Exception:
        basket_user = [0]
    a = []
    for i in db_sess.query(Meals).filter(Meals.shop_id == db_sess.query(ShopNow).first().shop_id).all():
        a.append(i.category)
    all_meals = {}
    for i in sorted(list(set(a)), reverse=True):
        a = []
        for m in db_sess.query(Meals).filter(
                Meals.category == i and Meals.shop_id == db_sess.query(ShopNow).first().shop_id):
            a.append([m.name, m.price, m.pic, m.in_stock, basket_user.count(m.id), m.id])
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
    n = db_sess.query(ShopNow).first().shop_id
    shop_name = db_sess.query(Shops).filter(Shops.id == n).first().name
    return render_template('menu.html', all_meals=all_meals, shop_name=shop_name,
                           shop_id=db_sess.query(ShopNow).filter(ShopNow.shop_id == n).first().shop_id)


# @app.route('/admins_adding_cafe', methods=['GET', 'POST'])
# def add_admins():
#     form = RegisterForm()
#     if form.validate_on_submit():
#         if form.password.data != form.password_again.data:
#             return render_template('admins_adding.html', title='Добавление админов',
#                                    form=form,
#                                    message="Пароли не совпадают")
#         db_sess = db_session.create_session()
#         if db_sess.query(Users).filter(Users.number == form.number.data).first() or db_sess.query(Users).filter(
#                 Users.number == form.number.data).first():
#             return render_template('admins_adding.html', title='Добавление админов',
#                                    form=form,
#                                    message="Такой админ уже есть")
#         user = Users(
#             name=form.name.data,
#             number=form.number.data,
#             owner=form.owner.data
#         )
#         user.set_password(form.password.data)
#         user.admin = True
#         db_sess.add(user)
#         db_sess.commit()
#         return redirect('/')
#     return render_template('admins_adding.html', title='Регистрация админов', form=form)
#

@app.route('/basket', methods=['GET', 'POST'])
def basket():
    db_sess = db_session.create_session()
    a = current_user.id
    b_ = None
    if not db_sess.query(Users).filter(Users.id == a).first().basket:
        n = db_sess.query(ShopNow).first().shop_id
        shop_name = db_sess.query(Shops).filter(Shops.id == n).first().name
        return render_template('basket_empty.html', shop_name=shop_name)
    else:
        for u in db_sess.query(Users).filter(Users.id == a):
            b_ = [int(i) for i in u.basket.split(', ')]
        b = [db_sess.query(Meals).filter(Meals.id == i).first().name for i in b_]
        bask = {}
        for i in b:
            if i not in bask:
                bask[i] = [b.count(i), db_sess.query(Meals).filter(Meals.name == i).first().price]
        all_price = 0
        for i in bask:
            for j in range(bask[i][0]):
                all_price += bask[i][1]
        n = db_sess.query(ShopNow).first().shop_id
        shop_name = db_sess.query(Shops).filter(Shops.id == n).first().name
        return render_template('basket_meals.html', basket=bask, all_price=all_price, shop_name=shop_name)


@app.route('/orders_history', methods=['GET', 'POST'])
def orders_history():
    ors = []
    db_sess = db_session.create_session()
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
        ors.append([order.id, meal, ' '.join(date_), order.is_ready, order.itog_price])
    n = db_sess.query(ShopNow).first().shop_id
    shop_name = db_sess.query(Shops).filter(Shops.id == n).first().name
    return render_template('orders_history.html', orders=ors[::-1], shop_name=shop_name)


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        if len(str(form.number.data)) != 11 or not str(form.number.data).isdigit():
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Неверный формат номера")
        elif form.password.data != form.password_again.data:
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Пароли не совпадают")
        db_sess = db_session.create_session()
        if db_sess.query(Users).filter(Users.number == form.number.data).first():
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Такой пользователь уже есть")
        user = Users(
            name=form.name.data,
            number=form.number.data
        )
        user.set_password(form.password.data)
        db_sess.add(user)
        db_sess.commit()
        return redirect('/menu')
    db_sess = db_session.create_session()
    n = db_sess.query(ShopNow).first().shop_id
    shop_name = db_sess.query(Shops).filter(Shops.id == n).first().name
    return render_template('register.html', title='Регистрация', form=form, shop_name=shop_name)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        n = db_sess.query(ShopNow).first().shop_id
        shop_name = db_sess.query(Shops).filter(Shops.id == n).first().name
        user = db_sess.query(Users).filter(Users.number == form.number.data).first()
        if len(str(form.number.data)) != 11 or not str(form.number.data).isdigit():
            return render_template('login.html',
                                   message="Неправильный формат номера",
                                   form=form, shop_name=shop_name)
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect("/menu")
        return render_template('login.html',
                               message="Неправильный логин или пароль",
                               form=form, shop_name=shop_name)
    db_sess = db_session.create_session()
    n = db_sess.query(ShopNow).first().shop_id
    shop_name = db_sess.query(Shops).filter(Shops.id == n).first().name
    return render_template('login.html', title='Авторизация', form=form, shop_name=shop_name)


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
    order.itog_price = ord.itog_price
    ord.date = datetime.datetime.now
    db_sess = db_session.create_session()
    db_sess.add(order)
    db_sess.commit()
    return redirect('/')


@app.route('/del/<name>', methods=['GET', 'POST'])
def delete(name):
    db_sess = db_session.create_session()
    meal = db_sess.query(Meals).filter(Meals.name == name).first()
    user = db_sess.query(Users).filter(Users.id == current_user.id).first()
    bask = [int(i) for i in user.basket.split(', ')]
    i = bask.index(meal.id)
    del bask[i]
    if bask:
        user.basket = ', '.join(str(i) for i in bask)
    else:
        user.basket = None
    db_sess.commit()
    return redirect('/basket')


@app.route('/order', methods=['GET', 'POST'])
def to_order():
    db_sess = db_session.create_session()
    if db_sess.query(Users).filter(Users.id == current_user.id).first().basket:
        user = db_sess.query(Users).filter(Users.id == current_user.id).first()
        order = Orders()
        order.client_id = current_user.id
        order.meals = user.basket
        price = []
        for i in [int(i) for i in user.basket.split(', ')]:
            price.append(db_sess.query(Meals).filter(Meals.id == i).first().price)
        order.itog_price = sum(price)
        order.shop_id = db_sess.query(ShopNow).first().shop_id
        order.shop_order_num = len(
            db_sess.query(Orders).filter(Orders.shop_id == db_sess.query(ShopNow).first().shop_id).all()) + 1
        db_sess.add(order)
        user.basket = None
        order_details['id'] = order.id
        order_details['client_name'] = user.name
        db_sess.commit()
        return redirect('/basket')
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
    return redirect('/menu')


@app.route('/change_menu', methods=['GET', 'POST'])
def change_menu():
    db_sess = db_session.create_session()
    try:
        basket_user = [int(i) for i in current_user.basket.split(', ')]
    except Exception:
        basket_user = [0]
    a = []
    for i in db_sess.query(Meals).filter(Meals.shop_id == db_sess.query(ShopNow).first().shop_id).all():
        a.append(i.category)
    all_meals = {}
    for i in sorted(list(set(a)), reverse=True):
        a = []
        for m in db_sess.query(Meals).filter(
                Meals.category == i and Meals.shop_id == db_sess.query(ShopNow).first().shop_id):
            a.append([m.name, m.price, m.pic, m.in_stock, basket_user.count(m.id), m.id])
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
    n = db_sess.query(ShopNow).first().shop_id
    shop_name = db_sess.query(Shops).filter(Shops.id == n).first().name
    return render_template('change_menu.html', all_meals=all_meals, shop_name=shop_name,
                           shop_id=db_sess.query(ShopNow).filter(ShopNow.id == n).first().shop_id)


@app.route('/delete_meal/<int:num>', methods=['GET', 'POST'])
def delete_meal(num):
    db_sess = db_session.create_session()
    db_sess.query(Meals).filter(Meals.id == num).delete()
    db_sess.commit()
    return redirect('/change_menu')


@app.route('/add_meal', methods=['GET', 'POST'])
def add_meal():
    form = MealAddingForm()
    db_sess = db_session.create_session()
    n = db_sess.query(ShopNow).first().shop_id
    shop_name = db_sess.query(Shops).filter(Shops.id == n).first().name
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        if db_sess.query(Meals).filter(Meals.name == form.name.data).first():
            return render_template('meal_adding.html', title='Регистрация', form=form,
                                   message="Такой пункт уже есть в меню", shop_name=shop_name,
                                   shop_id=db_sess.query(ShopNow).filter(ShopNow.id == n).first().shop_id)
        meal = Meals()
        meal.name = form.name.data
        meal.price = form.price.data
        meal.category = form.category.data
        meal.in_stock = form.in_stock.data
        meal.shop_id = db_sess.query(ShopNow).first().shop_id
        a = form.pic.data
        with open(f'static/img/{a.filename}', 'wb') as f:
            f.write(a.read())
        meal.pic = a.filename
        db_sess.add(meal)
        db_sess.commit()
        return redirect('/')
    n = db_sess.query(ShopNow).first().shop_id
    return render_template('meal_adding.html', title='Регистрация', form=form, shop_name=shop_name,
                           shop_id=db_sess.query(ShopNow).filter(ShopNow.id == n).first().shop_id)


if __name__ == '__main__':
    main()
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, threading=True)
