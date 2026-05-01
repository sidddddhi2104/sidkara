from flask import Flask, render_template, request, redirect, session, flash
from werkzeug.utils import secure_filename
import MySQLdb.cursors
import os
import mysql.connector
from mysql.connector import Error

app = Flask(__name__)

app.secret_key = os.getenv("SECRET_KEY", "siddhi_secret_key")

# ================= MYSQL CONFIG =================
app.config['MYSQL_HOST'] = 'switchyard.proxy.rlwy.net'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'YqspPgyKSiKFiWDTEYgRvVkaRrakTntA'
app.config['MYSQL_DB'] = 'railway'
app.config['MYSQL_PORT'] = 30581
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

# Upload Folder
app.config['UPLOAD_FOLDER'] = 'uploads/custom_orders'

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def get_db_connection():
    try:
        conn = mysql.connector.connect(
            host=os.getenv("DB_HOST", "switchyard.proxy.rlwy.net"),
            user=os.getenv("DB_USER", "root"),
            password=os.getenv("DB_PASSWORD", "YqspPgyKSiKFiWDTEYgRvVkaRrakTntA"),
            database=os.getenv("DB_NAME", "railway"),
            port=int(os.getenv("DB_PORT", 30581)),
            connection_timeout=15,
            autocommit=False
        )
        print("✅ MYSQL CONNECTED SUCCESSFULLY")
        return conn

    except Error as e:
        print("❌ DATABASE CONNECTION ERROR:", e)
        return None
# ================= HOME =================
@app.route('/')
def home():
    return render_template('index.html')

# ================= WISHLIST PAGE =================

@app.route('/wishlist')
def wishlist():

    return render_template('wishlist.html')

@app.route("/welcome")
def welcome():
    return render_template("welcome.html")
# ================= PRODUCTS =================
@app.route('/products')
def products():

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM products")

    products = cursor.fetchall()

    return render_template('products.html', products=products)

# ================= PRODUCT DETAIL =================
@app.route('/product/<int:id>')
def product_detail(id):

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM products WHERE id=%s", (id,))

    product = cursor.fetchone()

    return render_template('product_detail.html', product=product)

# ================= LOGIN =================

@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':

        email = request.form['email']
        password = request.form['password']

        # ================= ADMIN LOGIN =================

        if email == "admin" and password == "admin123":

            session['admin'] = True

            flash('Admin Login Successful')

            return redirect('/admin')

        # ================= USER LOGIN =================

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM users WHERE email=%s AND password=%s",
            (email, password)
        )

        user = cursor.fetchone()

        if user:

            session['user_id'] = user[0]
            session['user_name'] = user[1]

            flash('Login Successful')

            return redirect('/')

        else:

            flash('Invalid Credentials')

            return redirect('/login')

    return render_template('login.html')
# ================= REGISTER =================
@app.route('/register', methods=['GET', 'POST'])
def register():

    if request.method == 'POST':

        conn = None
        cursor = None

        try:
            name = request.form['name']
            email = request.form['email']
            password = request.form['password']

            conn = get_db_connection()

            if conn is None:
                return "Database Connection Failed"

            cursor = conn.cursor()

            # check duplicate email
            cursor.execute("SELECT * FROM users WHERE email=%s", (email,))
            existing = cursor.fetchone()

            if existing:
                flash("Email already registered")
                return redirect('/register')

            cursor.execute(
                "INSERT INTO users(name,email,password) VALUES(%s,%s,%s)",
                (name, email, password)
            )

            conn.commit()

            print("✅ USER REGISTERED SUCCESSFULLY")

            flash('Registration Successful')
            return redirect('/login')

        except Exception as e:
            print("❌ REGISTER ERROR:", str(e))
            return f"Register Failed: {str(e)}", 500

        finally:
            if cursor:
                cursor.close()
            if conn and conn.is_connected():
                conn.close()
                print("🔒 REGISTER DB CLOSED")

    return render_template('register.html')
# ================= LOGOUT =================
@app.route('/logout')
def logout():

    session.clear()

    return redirect('/')

# ================= CART =================
@app.route('/cart')
def cart():
    return render_template('cart.html')

# ================= ADD TO CART =================
@app.route('/add-to-cart/<int:product_id>')
def add_to_cart(product_id):

    if 'loggedin' not in session:
        return redirect('/login')

    user_id = session['user_id']

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM cart WHERE user_id=%s AND product_id=%s",
        (user_id, product_id)
    )

    existing = cursor.fetchone()

    if existing:

        cursor.execute(
            "UPDATE cart SET quantity = quantity + 1 WHERE user_id=%s AND product_id=%s",
            (user_id, product_id)
        )

    else:

        cursor.execute(
            "INSERT INTO cart(user_id, product_id, quantity) VALUES(%s,%s,%s)",
            (user_id, product_id, 1)
        )

    conn.commit()

    flash('Added To Cart Successfully')

    return redirect('/products')

# ================= CHECKOUT =================
@app.route('/checkout', methods=['GET', 'POST'])
def checkout():

    if request.method == 'POST':

        fullname = request.form['fullname']
        phone = request.form['phone']
        address = request.form['address']
        total = request.form['total']

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO orders(fullname,phone,address,total) VALUES(%s,%s,%s,%s)",
            (fullname, phone, address, total)
        )

        conn.commit()

        flash('Order Placed Successfully')

        return redirect('/')

    return render_template('checkout.html')

# ================= ABOUT =================
@app.route('/about')
def about():
    return render_template('about.html')

# ================= CONTACT =================
@app.route('/contact', methods=['GET', 'POST'])
def contact():

    if request.method == 'POST':

        name = request.form['name']
        email = request.form['email']
        message = request.form['message']

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO contacts(name,email,message) VALUES(%s,%s,%s)",
            (name, email, message)
        )

        conn.commit()

        flash('Message Sent Successfully')

    return render_template('contact.html')

# ================= CUSTOM ORDER =================
@app.route('/custom-order', methods=['GET', 'POST'])
def custom_order():

    if request.method == 'POST':

        customer_name = request.form['customer_name']
        phone = request.form['phone']
        details = request.form['details']

        image = request.files['image']

        filename = secure_filename(image.filename)

        upload_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

        image.save(upload_path)

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO custom_orders(customer_name,phone,details,image) VALUES(%s,%s,%s,%s)",
            (customer_name, phone, details, filename)
        )

        conn.commit()

        flash('Custom Order Submitted Successfully')

        return redirect('/')

    return render_template('custom_order.html')

# ================= ADMIN DASHBOARD =================

@app.route('/admin')
def admin_dashboard():

    if 'admin' not in session:

        return redirect('/login')

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM products")
    products = cursor.fetchall()

    cursor.execute("SELECT * FROM orders")
    orders = cursor.fetchall()

    cursor.execute("SELECT * FROM contacts")
    contacts = cursor.fetchall()

    return render_template(
        'admin_dashboard.html',
        products=products,
        orders=orders,
        contacts=contacts
    )
# ================= ADD PRODUCT =================
@app.route('/add-product', methods=['POST'])
def add_product():

    name = request.form['name']
    category = request.form['category']
    price = request.form['price']
    description = request.form['description']

    image = request.files['image']

    filename = secure_filename(image.filename)

    image.save('static/images/' + filename)

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO products(name,category,price,description,image) VALUES(%s,%s,%s,%s,%s)",
        (name, category, price, description, filename)
    )

    conn.commit()

    flash('Product Added Successfully')

    return redirect('/admin')

# ================= DELETE PRODUCT =================
@app.route('/delete-product/<int:id>')
def delete_product(id):

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM products WHERE id=%s", (id,))

    conn.commit()

    flash('Product Deleted Successfully')

    return redirect('/admin')
# ================= ADMIN LOGIN =================

@app.route('/admin-login', methods=['GET', 'POST'])
def admin_login():

    if request.method == 'POST':

        username = request.form['username']
        password = request.form['password']

        # CHANGE THESE VALUES
        admin_username = "admin"
        admin_password = "admin123"

        if username == admin_username and password == admin_password:

            session['admin'] = True

            flash('Admin Login Successful')

            return redirect('/admin')

        else:

            flash('Invalid Admin Credentials')

            return redirect('/admin-login')

    return render_template('admin_login.html')
# ================= ADMIN PRODUCTS =================

@app.route('/admin-products')
def admin_products():

    if 'admin' not in session:
        return redirect('/login')

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM products")

    products = cursor.fetchall()

    return render_template(
        'admin-products.html',
        products=products
    )


# ================= ADMIN ORDERS =================

@app.route('/admin-orders')
def admin_orders():

    if 'admin' not in session:
        return redirect('/login')

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM orders")

    orders = cursor.fetchall()

    return render_template(
        'admin-orders.html',
        orders=orders
    )


# ================= ADMIN CONTACTS =================

@app.route('/admin-contacts')
def admin_contacts():

    if 'admin' not in session:
        return redirect('/login')

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM contacts")

    contacts = cursor.fetchall()

    return render_template(
        'admin-contacts.html',
        contacts=contacts
    )
@app.route('/testdb')
def testdb():
    try:
        conn = get_db_connection()

        if conn is None:
            return "DB Connection Failed"

        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.fetchone()

        cursor.close()
        conn.close()

        return "✅ DATABASE CONNECTED PERFECTLY"

    except Exception as e:
        return f"❌ TEST DB ERROR: {str(e)}"
# ================= RUN APP =================
if __name__ == '__main__':
    app.run(debug=True)