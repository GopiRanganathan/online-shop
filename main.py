from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash, abort
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, relationship
from flask_login import UserMixin, login_user, LoginManager, current_user, logout_user, login_required
import MySQLdb
from flask_mail import Mail, Message
import pyotp
from functools import wraps
from sqlalchemy import func
import stripe
from datetime import datetime
from dotenv import load_dotenv
import os


# HoodHaven
load_dotenv()
app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_KEY')
otp_secret_key = pyotp.random_base32()
app.config['MAIL_SERVER']='smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = "hoodhavenjackets@gmail.com"
app.config['MAIL_PASSWORD'] = os.environ.get('PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = "hoodhavenjackets@gmail.com"
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
mail = Mail(app)
app.config['TEMPLATES_AUTO_RELOAD'] = True
stripe.api_key = os.environ.get('STRIPE_KEY')

app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DB_URI')

class Base(DeclarativeBase):
  pass

db = SQLAlchemy(app, model_class=Base)

class User(db.Model, UserMixin):
    __tablename__ = "Users"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=False, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    ph_no = db.Column(db.String(20), unique=False, nullable=True)
    address = db.Column(db.String(500), unique=False, nullable=True)
    cart = relationship('Cart', back_populates='user')
    favourite = relationship('Favourite', back_populates='user')
    order = relationship('Order', back_populates='user')

class Product(db.Model):
    __tablename__ = "Products"
    id = db.Column(db.Integer, primary_key=True)
    price_id = db.Column(db.String(100), nullable=True)
    p_name = db.Column(db.String(200), unique=False, nullable=False)
    category = db.Column(db.String(50), unique=False, nullable=False)
    color = db.Column(db.String(50), unique=False, nullable=False)
    price = db.Column(db.Integer, unique=False, nullable=False)
    xs = db.Column(db.Integer, unique=False, nullable=False)
    s = db.Column(db.Integer, unique=False, nullable=False)
    m = db.Column(db.Integer, unique=False, nullable=False)
    l = db.Column(db.Integer, unique=False, nullable=False)
    xl = db.Column(db.Integer, unique=False, nullable=False)
    xxl = db.Column(db.Integer, unique=False, nullable=False)
    image = db.Column(db.String(400), unique=False, nullable=False)
    cart = relationship('Cart', back_populates='product')
    favourite = relationship('Favourite', back_populates='product')
    order = relationship('Order', back_populates='product')


class Cart(db.Model):
    __tablename__ = "Carts"
    id = db.Column(db.Integer, primary_key=True)
    user = relationship('User', back_populates='cart')
    user_id = db.Column(db.Integer, db.ForeignKey('Users.id'))
    product = relationship('Product', back_populates='cart')
    product_id = db.Column(db.Integer, db.ForeignKey('Products.id'))
    size = db.Column(db.String(5), unique=False, nullable=False)
    quantity = db.Column(db.Integer, unique=False, nullable=False)


class Favourite(db.Model):
    __tablename__ = "Favourites"
    id = db.Column(db.Integer, primary_key=True)
    user = relationship('User', back_populates='favourite')
    user_id = db.Column(db.Integer, db.ForeignKey('Users.id'))
    product = relationship('Product', back_populates='favourite')
    product_id = db.Column(db.Integer, db.ForeignKey('Products.id'))
  


class Order(db.Model):
    __tablename__ = "Orders"
    id = db.Column(db.Integer, primary_key=True)
    user = relationship('User', back_populates='order')
    user_id = db.Column(db.Integer, db.ForeignKey('Users.id'))
    product = relationship('Product', back_populates='order')
    product_id = db.Column(db.Integer, db.ForeignKey('Products.id'))
    size = db.Column(db.String(5), unique=False, nullable=False)
    quantity = db.Column(db.Integer, unique=False, nullable=False)
    date = db.Column(db.DateTime, unique=False, nullable=False)
    State = db.Column(db.String(50), unique=False, nullable=False)



with app.app_context():
    db.create_all()

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'signup'
login_manager.login_message_category='danger'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)

def admin_only(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.id != 1:
            return abort(403)
        return f(*args, **kwargs)
    return decorated_function

def send_mail(to,subject, message):
    msg = Message(subject,  recipients=[to])
    msg.body = message
    mail.send(msg)

def generate_otp():
    totp = pyotp.TOTP(otp_secret_key)
    return totp.now()

@app.route('/')
def home():
    products = db.session.execute(db.select(Product)).scalars()
    fav_pid=[]
    cart_count=0
    if current_user.is_active:
        favourites = db.session.execute(db.select(Favourite).where(Favourite.user_id==current_user.id)).scalars()
        fav_pid = [item.product_id for item in favourites]
        cart_count = db.session.query(Cart).filter(Cart.user_id == current_user.id).count()
    return render_template('index.html', products=products, favs=fav_pid, cart=cart_count , active=current_user.is_active)

@app.route('/category/<cat>')
def category(cat):
    products=db.session.execute(db.select(Product).where(Product.category==cat)).scalars()
    if current_user.is_active:
        cart_count = db.session.query(Cart).filter(Cart.user_id == current_user.id).count()
    return render_template('category.html', products=products, active=current_user.is_active, cart=cart_count)

@app.route('/item/<int:pid>')
def item(pid):
    product = db.session.execute(db.select(Product).where(Product.id==pid)).scalar()
    fav = db.session.execute(db.select(Favourite).where(Favourite.product_id == pid)).scalar()
    is_fav=False
    if fav:
        is_fav=True
    if current_user.is_active:
        cart_count = db.session.query(Cart).filter(Cart.user_id == current_user.id).count()

    return render_template('item.html', product=product, active=current_user.is_active, fav=is_fav, cart=cart_count)

@app.route('/cart')
@login_required
def cart():
        products = db.session.execute(db.select(Cart).where(Cart.user_id == current_user.id)).scalars()

        products_list=[{'product': db.session.execute(db.select(Product).where(Product.id==product.product_id)).scalar(), 'size': product.size, 'quantity':product.quantity, 'id':product.id} for product in products ]

        total=0
        for item in products_list:
            total += item['product'].price * item['quantity']
        if current_user.is_active:
            cart_count = db.session.query(Cart).filter(Cart.user_id == current_user.id).count()

        return render_template('cart.html', products=products_list, total=total, active=current_user.is_active, cart=cart_count)
  

@app.route("/add-to-cart", methods=['POST'])
@login_required
def add_to_cart():
    data=request.json
    pid=data['pid']
    size=data['size']
    is_in_cart = db.session.execute(db.select(Cart).where(Cart.product_id==pid, Cart.size==size, Cart.user_id==current_user.id)).scalar()
    if is_in_cart:
        is_in_cart.quantity += 1
        db.session.commit()
        flash('Added to Cart', 'success')
        return redirect(url_for('cart')), 200
    else:
        new_item = Cart(
            user_id=current_user.id,
            product_id=pid,
            size=size,
            quantity=1
        )
        db.session.add(new_item)
        db.session.commit()
        flash('Added to Cart', 'success')
        return redirect(url_for('cart')), 200

@app.route("/delete_cart/<int:cid>")
def delete_from_cart(cid):
    citem = db.session.query(Cart).filter_by(id=cid).scalar()
    db.session.delete(citem)
    db.session.commit()
    return redirect(url_for('cart'))

@app.route("/wishlist")
@login_required
def favourites():
    products = db.session.execute(db.select(Favourite).where(Favourite.user_id == current_user.id)).scalars()
    products_list=[ db.session.execute(db.select(Product).where(Product.id==product.product_id)).scalar() for product in products ]
    if current_user.is_active:
        cart_count = db.session.query(Cart).filter(Cart.user_id == current_user.id).count()
    return render_template('favourites.html', products=products_list, active=current_user.is_active, cart=cart_count)

@app.route("/add_to_wishlist/<int:pid>")
@login_required
def add_to_wishlist(pid):
    is_fav = db.session.execute(db.select(Favourite).where(Favourite.product_id == pid, Favourite.user_id==current_user.id)).scalar()
    if is_fav:
        db.session.delete(is_fav)
        db.session.commit()
        flash('Removed from Wishlist', 'success')
        return redirect(url_for('home'))
    
    favs = Favourite(user_id=current_user.id, product_id=pid)
    db.session.add(favs)
    db.session.commit()
    flash('Added to Wishlist', 'success')
    return redirect(url_for('home'))

@app.route('/add', methods=['POST', 'GET'])
@admin_only
def add():
    if request.method == 'POST':
        data = request.json
        print('data retrived')
        new_product = Product(
            p_name=data.get('name'),
            category = data.get('category'),
            color = data.get('color'),
            price = data.get('price'),
            xs = data.get('xs_qty'), 
            s = data.get('s_qty'),
            m = data.get('m_qty'),
            l = data.get('l_qty'),
            xl = data.get('xl_qty'),
            xxl = data.get('xxl_qty'),
            image = data.get('image_url')
        )
        db.session.add(new_product)
        db.session.commit()
    return render_template('add.html', active=current_user.is_active)

@app.route('/SignUp', methods=['POST', 'GET'])
def signup():
    if request.method == 'POST':
        if request.form.get('otp'):
            otp = request.form.get('otp')
            name = request.form.get("username")
            email = request.form.get("email")
            user = User.query.filter_by(email=email).first() 


            if 'otp' in session and otp == session['otp']:
                if not user:
                    new_user = User(
                        name=name,
                        email=email
                    )
                    db.session.add(new_user)
                    db.session.commit()
                    flash('Account created successfully!','success')
                    login_user(new_user)
                else:
                    login_user(user)
                    flash('Successfully logged in!', 'success')
                return redirect(url_for('home'))
            else:
                flash('Invalid OTP! Please try again.','danger')
        else:
            name = request.form.get("username")
            email = request.form.get("email")
            session['otp'] = generate_otp()
            send_mail(email,"OTP Verification", "Your OTP is : "+str(session['otp']))
            flash('OTP has sent successfully!', 'success')
            return render_template("signup.html", email=email, name=name)
    return render_template("signup.html", active=current_user.is_active)



@app.route('/search', methods=['POST'])
def search():
    if request.method=='POST':
        data=request.form.get('query')
        query = data.lower().split(' ')
  
    
        pids=[]
        for word in query:
            color = db.session.execute(db.select(Product).where(func.lower(Product.color)==word)).scalars()
            names = db.session.execute(db.select(Product).where(func.lower(Product.p_name).contains(word))).scalars()
            categories = db.session.execute(db.select(Product).where(func.lower(Product.category)==word)).scalars()

          
            if categories:
                for item in categories:
                    pids.append(item.id)
            if color:
                for item in color:
                    pids.append(item.id)
            if names:
                for item in names:
                    pids.append(item.id)
      
        products = db.session.query(Product).filter(Product.id.in_(pids)).all()
        flash(f'Results for {data}', 'info')
        if current_user.is_active:
            cart_count = db.session.query(Cart).filter(Cart.user_id == current_user.id).count()

        return render_template('category.html', products=products, active=current_user.is_active, cart=cart_count)




@app.route('/checkout', methods=['POST'])
@login_required
def create_checkout_session():
    address=''
    if request.method=='POST':
        address+=f"{request.form.get('fullname')}, "
        address+=f"{request.form.get('buildingno')}, "
        address+=f"{request.form.get('street')}, "
        address+=f"{request.form.get('city')}, "
        address+=f"{request.form.get('state')}, "
        address+=f"{request.form.get('pincode')}."
        phone_num = request.form.get('phno')
        
        user = db.session.execute(db.select(User).where(User.id==current_user.id)).scalar()
        user.address=address
        user.ph_no=phone_num
        db.session.commit()

        cart_items = db.session.execute(db.select(Cart).where(Cart.user_id==current_user.id)).scalars()
        items=[{'price':db.session.execute(db.select(Product).where(Product.id==item.product_id)).scalar().price_id, 'quantity':item.quantity} for item in cart_items]
  
      
        try:
            checkout_session = stripe.checkout.Session.create(
                line_items=items,
                mode='payment',
                success_url="http://127.0.0.1:5000" + url_for('success', session="success"),
                cancel_url="http://127.0.0.1:5000"+url_for('cancel'),
            )
            # 4000003560000123 TEST CARD FOR INDIA
        except Exception as e:
            return str(e)

        return redirect(checkout_session.url, code=303)

@app.route('/success')
@login_required
def success():
    session = request.args.get('session')
    if not session:
        return redirect(url_for('cancel'))
    cart_items = db.session.execute(db.select(Cart).where(Cart.user_id==current_user.id)).scalars()
    for item in cart_items:
        new_order = Order(
            user_id=current_user.id,
            product_id=item.product_id,
            size=item.size,
            quantity=item.quantity,
            date=datetime.now(),
            State='order placed'
        )
        db.session.add(new_order)
        db.session.delete(item)

        db.session.commit()
    user=db.session.execute(db.select(User).where(User.id==current_user.id)).scalar()
    message=f"Hi {user.name}, thanks for shopping with us. You can expect delivery in 5 to 7 days.\n\nYour order shipping to:\n{user.address}. \n\nFor more query, email us."
    send_mail(user.email, "Order Confirmed!", message)
    if current_user.is_active:
        cart_count = db.session.query(Cart).filter(Cart.user_id == current_user.id).count()

    return render_template('success.html', active=current_user.is_active, cart=cart_count)

@app.route('/cancel')
def cancel():
    if current_user.is_active:
        cart_count = db.session.query(Cart).filter(Cart.user_id == current_user.id).count()

    return render_template('cancel.html', active=current_user.is_active, cart=cart_count)

@app.route('/orders')
@login_required
def order():
    products = db.session.execute(db.select(Order).where(Order.user_id == current_user.id)).scalars()
    products_list=[{'product': db.session.execute(db.select(Product).where(Product.id==product.product_id)).scalar(), 'size': product.size, 'quantity':product.quantity, 'id':product.id, 'state':product.State} for product in products ]
    if current_user.is_active:
        cart_count = db.session.query(Cart).filter(Cart.user_id == current_user.id).count()

    return render_template('order.html', active=current_user.is_active ,products=products_list,cart=cart_count)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("successfully logged out", 'success')
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)
