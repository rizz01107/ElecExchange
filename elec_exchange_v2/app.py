from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3, os, hashlib, uuid, random, string
from functools import wraps

app = Flask(__name__)
app.secret_key = 'elec_exchange_gcuf_2024'

DB            = os.path.join(os.path.dirname(__file__), 'database.db')
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'static', 'uploads')

def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    if os.path.exists(DB):
        return
    conn = get_db()
    c = conn.cursor()
    c.executescript('''
        CREATE TABLE users (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT NOT NULL,
            email       TEXT UNIQUE NOT NULL,
            phone       TEXT,
            password    TEXT NOT NULL,
            role        TEXT DEFAULT 'user',
            is_verified INTEGER DEFAULT 0,
            verify_code TEXT DEFAULT '',
            joined      TEXT DEFAULT CURRENT_DATE
        );
        CREATE TABLE products (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id        INTEGER,
            title          TEXT NOT NULL,
            description    TEXT,
            price          REAL NOT NULL,
            category       TEXT,
            condition_info TEXT DEFAULT 'Good',
            image          TEXT DEFAULT '',
            status         TEXT DEFAULT 'available',
            created_at     TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE transactions (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            buyer_id       INTEGER,
            seller_id      INTEGER,
            product_id     INTEGER,
            amount         REAL,
            payment_method TEXT DEFAULT 'Cash on Delivery',
            status         TEXT DEFAULT 'pending',
            refund_status  TEXT DEFAULT 'none',
            created_at     TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE reviews (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            reviewer_id INTEGER,
            product_id  INTEGER,
            rating      INTEGER,
            comment     TEXT,
            created_at  TEXT DEFAULT CURRENT_TIMESTAMP
        );
    ''')

    pwd = hash_password('password')
    c.execute("INSERT INTO users (name,email,phone,password,role,is_verified) VALUES (?,?,?,?,?,?)",
              ('Admin','admin@elec.com','03001234567',pwd,'admin',1))
    c.execute("INSERT INTO users (name,email,phone,password,role,is_verified) VALUES (?,?,?,?,?,?)",
              ('Ali Khan','ali@gmail.com','03111234567',pwd,'user',1))
    c.execute("INSERT INTO users (name,email,phone,password,role,is_verified) VALUES (?,?,?,?,?,?)",
              ('Sara Ahmed','sara@gmail.com','03211234567',pwd,'user',1))

    sample = [
        (2,'Samsung Galaxy A32','6 mahine purana, box ke saath',35000,'Mobile','Good'),
        (2,'Dell Laptop Core i5','2 saal purana, charger samet',55000,'Laptop','Fair'),
        (3,'Canon DSLR Camera','2 lens ke saath, bag bhi',45000,'Camera','Excellent'),
        (3,'JBL Bluetooth Speaker','Kam use hua, original box',8000,'Audio','Good'),
        (2,'iPad Mini 5th Gen','Screen perfect, battery 90%',40000,'Tablet','Good'),
        (3,'Sony 43" Smart TV','4K, remote samet',65000,'TV','Fair'),
    ]
    for s in sample:
        c.execute("INSERT INTO products (user_id,title,description,price,category,condition_info) VALUES (?,?,?,?,?,?)", s)

    conn.commit()
    conn.close()

def hash_password(p):
    return hashlib.sha256(p.encode()).hexdigest()

def gen_code():
    return ''.join(random.choices(string.digits, k=6))

def login_required(f):
    @wraps(f)
    def d(*a,**kw):
        if 'user_id' not in session: return redirect(url_for('login'))
        return f(*a,**kw)
    return d

def admin_required(f):
    @wraps(f)
    def d(*a,**kw):
        if session.get('role') != 'admin': return redirect(url_for('index'))
        return f(*a,**kw)
    return d

# ── HOME ──────────────────────────────────────────────────────────
@app.route('/')
def index():
    cat  = request.args.get('cat','')
    cond = request.args.get('cond','')
    sort = request.args.get('sort','newest')
    db   = get_db()
    q    = "SELECT p.*,u.name as seller FROM products p JOIN users u ON p.user_id=u.id WHERE p.status='available'"
    params = []
    if cat:  q += " AND p.category=?";        params.append(cat)
    if cond: q += " AND p.condition_info=?";  params.append(cond)
    q += " ORDER BY " + ("p.price ASC" if sort=='price_asc' else "p.price DESC" if sort=='price_desc' else "p.id DESC")
    products = db.execute(q, params).fetchall()
    cats     = db.execute("SELECT DISTINCT category FROM products WHERE status='available' ORDER BY category").fetchall()
    db.close()
    return render_template('index.html', products=products, cats=cats,
                           selected_cat=cat, selected_cond=cond, sort=sort)

# ── REGISTER + VERIFY ─────────────────────────────────────────────
@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        name  = request.form['name'].strip()
        email = request.form['email'].strip()
        phone = request.form['phone'].strip()
        pwd   = request.form['password']
        cpwd  = request.form['confirm_password']
        if not name or not email or not pwd:
            flash('All required fields must be filled!','danger')
        elif pwd != cpwd:
            flash('Passwords do not match!','danger')
        elif len(pwd) < 6:
            flash('Password must be at least 6 characters!','danger')
        else:
            db = get_db()
            if db.execute("SELECT id FROM users WHERE email=?",(email,)).fetchone():
                flash('This email is already registered!','danger')
                db.close()
            else:
                code = gen_code()
                db.execute("INSERT INTO users (name,email,phone,password,verify_code) VALUES (?,?,?,?,?)",
                           (name,email,phone,hash_password(pwd),code))
                db.commit(); db.close()
                flash(f'Account created! Your verification code is: {code}  (In a real app, this would be sent via email)', 'info')
                return redirect(url_for('verify', email=email))
    return render_template('register.html')

@app.route('/verify', methods=['GET','POST'])
def verify():
    email = request.args.get('email','')
    if request.method == 'POST':
        email = request.form['email']
        code  = request.form['code'].strip()
        db    = get_db()
        user  = db.execute("SELECT * FROM users WHERE email=?",(email,)).fetchone()
        if user and user['verify_code'] == code:
            db.execute("UPDATE users SET is_verified=1, verify_code='' WHERE email=?",(email,))
            db.commit(); db.close()
            flash('Account verified successfully! Please login.','success')
            return redirect(url_for('login'))
        db.close()
        flash('Invalid verification code!','danger')
    return render_template('verify.html', email=email)

# ── LOGIN / LOGOUT ────────────────────────────────────────────────
@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        email = request.form['email'].strip()
        pwd   = request.form['password']
        db    = get_db()
        user  = db.execute("SELECT * FROM users WHERE email=? AND password=?",
                           (email, hash_password(pwd))).fetchone()
        db.close()
        if user:
            if not user['is_verified']:
                flash('Please verify your account first!','warning')
                return redirect(url_for('verify', email=email))
            session['user_id']   = user['id']
            session['user_name'] = user['name']
            session['role']      = user['role']
            return redirect(url_for('admin_dashboard') if user['role']=='admin' else url_for('index'))
        flash('Invalid email or password!','danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# ── PRODUCT ───────────────────────────────────────────────────────
@app.route('/product/<int:pid>', methods=['GET','POST'])
def product(pid):
    db  = get_db()
    p   = db.execute("SELECT pr.*,u.name as seller_name,u.phone as seller_phone FROM products pr JOIN users u ON pr.user_id=u.id WHERE pr.id=?", (pid,)).fetchone()
    if not p: flash('Product not found!','danger'); return redirect(url_for('index'))
    reviews    = db.execute("SELECT r.*,u.name FROM reviews r JOIN users u ON r.reviewer_id=u.id WHERE r.product_id=? ORDER BY r.id DESC",(pid,)).fetchall()
    avg_row    = db.execute("SELECT AVG(rating) FROM reviews WHERE product_id=?",(pid,)).fetchone()
    avg_rating = round(avg_row[0],1) if avg_row[0] else None
    msg_type = msg_text = ''

    if request.method == 'POST' and session.get('user_id'):
        action = request.form.get('action')
        if action == 'buy':
            if session['user_id'] == p['user_id']:
                msg_type,msg_text = 'danger','You cannot buy your own product!'
            elif p['status'] != 'available':
                msg_type,msg_text = 'danger','This product is no longer available.'
            elif db.execute("SELECT id FROM transactions WHERE buyer_id=? AND product_id=?",(session['user_id'],pid)).fetchone():
                msg_type,msg_text = 'info','You have already placed a request for this product!'
            else:
                pm = request.form.get('payment_method','Cash on Delivery')
                db.execute("INSERT INTO transactions (buyer_id,seller_id,product_id,amount,payment_method) VALUES (?,?,?,?,?)",
                           (session['user_id'],p['user_id'],pid,p['price'],pm))
                db.commit()
                msg_type,msg_text = 'success',f"Order placed successfully! Contact seller at: {p['seller_phone']}"
        elif action == 'review':
            db.execute("INSERT INTO reviews (reviewer_id,product_id,rating,comment) VALUES (?,?,?,?)",
                       (session['user_id'],pid,int(request.form.get('rating',3)),request.form.get('comment','').strip()))
            db.commit()
            reviews    = db.execute("SELECT r.*,u.name FROM reviews r JOIN users u ON r.reviewer_id=u.id WHERE r.product_id=? ORDER BY r.id DESC",(pid,)).fetchall()
            avg_row    = db.execute("SELECT AVG(rating) FROM reviews WHERE product_id=?",(pid,)).fetchone()
            avg_rating = round(avg_row[0],1) if avg_row[0] else None
            msg_type,msg_text = 'success','Review submitted successfully!'
    elif request.method == 'POST':
        return redirect(url_for('login'))

    db.close()
    return render_template('product.html', p=p, reviews=reviews, avg_rating=avg_rating, msg_type=msg_type, msg_text=msg_text)

# ── SEARCH ────────────────────────────────────────────────────────
@app.route('/search')
def search():
    q    = request.args.get('q','').strip()
    cat  = request.args.get('cat','')
    db   = get_db()
    results = []
    if q or cat:
        sq = "SELECT p.*,u.name as seller FROM products p JOIN users u ON p.user_id=u.id WHERE p.status='available'"
        params = []
        if q:   sq += " AND (p.title LIKE ? OR p.description LIKE ? OR p.category LIKE ?)"; params+=[f'%{q}%']*3
        if cat: sq += " AND p.category=?"; params.append(cat)
        results = db.execute(sq+' ORDER BY p.id DESC', params).fetchall()
    cats = db.execute("SELECT DISTINCT category FROM products WHERE status='available' ORDER BY category").fetchall()
    db.close()
    return render_template('search.html', results=results, q=q, cat=cat, cats=cats)

# ── ADD PRODUCT ───────────────────────────────────────────────────
@app.route('/add-product', methods=['GET','POST'])
@login_required
def add_product():
    if request.method == 'POST':
        img = ''
        file = request.files.get('image')
        if file and file.filename:
            ext = file.filename.rsplit('.',1)[-1].lower()
            if ext in ['jpg','jpeg','png','gif','webp']:
                img = f"{uuid.uuid4().hex}.{ext}"
                file.save(os.path.join(UPLOAD_FOLDER, img))
        db = get_db()
        db.execute("INSERT INTO products (user_id,title,description,price,category,condition_info,image) VALUES (?,?,?,?,?,?,?)",
                   (session['user_id'], request.form['title'].strip(), request.form['description'].strip(),
                    float(request.form['price']), request.form['category'], request.form['condition_info'], img))
        db.commit(); db.close()
        flash('Product listed successfully!','success')
        return redirect(url_for('index'))
    return render_template('add_product.html')

# ── USER PROFILE ──────────────────────────────────────────────────
@app.route('/user/profile', methods=['GET','POST'])
@login_required
def profile():
    db   = get_db()
    user = db.execute("SELECT * FROM users WHERE id=?",(session['user_id'],)).fetchone()
    if request.method == 'POST':
        name=request.form['name'].strip(); phone=request.form['phone'].strip()
        new_p=request.form.get('new_pass','').strip()
        if new_p:
            if hash_password(request.form.get('cur_pass','')) != user['password']:
                flash('Current password is incorrect!','danger'); db.close()
                return render_template('user/profile.html', user=user)
            db.execute("UPDATE users SET name=?,phone=?,password=? WHERE id=?",(name,phone,hash_password(new_p),session['user_id']))
        else:
            db.execute("UPDATE users SET name=?,phone=? WHERE id=?",(name,phone,session['user_id']))
        db.commit(); session['user_name']=name; flash('Profile updated successfully!','success')
        user = db.execute("SELECT * FROM users WHERE id=?",(session['user_id'],)).fetchone()
    db.close()
    return render_template('user/profile.html', user=user)

@app.route('/user/listings')
@login_required
def my_listings():
    db = get_db()
    if request.args.get('delete'):
        db.execute("DELETE FROM products WHERE id=? AND user_id=?",(int(request.args['delete']),session['user_id'])); db.commit(); flash('Product deleted successfully!','success')
    if request.args.get('sold'):
        db.execute("UPDATE products SET status='sold' WHERE id=? AND user_id=?",(int(request.args['sold']),session['user_id'])); db.commit()
    products = db.execute("SELECT * FROM products WHERE user_id=? ORDER BY id DESC",(session['user_id'],)).fetchall()
    db.close()
    return render_template('user/my_listings.html', products=products)

@app.route('/user/orders')
@login_required
def my_orders():
    db = get_db()
    orders = db.execute("SELECT t.*,p.title,p.category,u.name as seller_name,u.phone as seller_phone FROM transactions t JOIN products p ON t.product_id=p.id JOIN users u ON t.seller_id=u.id WHERE t.buyer_id=? ORDER BY t.id DESC",(session['user_id'],)).fetchall()
    db.close()
    return render_template('user/my_orders.html', orders=orders)

@app.route('/user/orders/refund/<int:tid>')
@login_required
def request_refund(tid):
    db = get_db()
    t  = db.execute("SELECT * FROM transactions WHERE id=? AND buyer_id=?",(tid,session['user_id'])).fetchone()
    if t and t['status']=='completed' and t['refund_status']=='none':
        db.execute("UPDATE transactions SET refund_status='requested' WHERE id=?",(tid,)); db.commit()
        flash('Refund request submitted! Admin will review it.','info')
    db.close()
    return redirect(url_for('my_orders'))

# ── ADMIN ─────────────────────────────────────────────────────────
@app.route('/admin')
@login_required
@admin_required
def admin_dashboard():
    db = get_db()
    stats = {
        'users':     db.execute("SELECT COUNT(*) FROM users WHERE role='user'").fetchone()[0],
        'products':  db.execute("SELECT COUNT(*) FROM products").fetchone()[0],
        'available': db.execute("SELECT COUNT(*) FROM products WHERE status='available'").fetchone()[0],
        'orders':    db.execute("SELECT COUNT(*) FROM transactions").fetchone()[0],
        'pending':   db.execute("SELECT COUNT(*) FROM transactions WHERE status='pending'").fetchone()[0],
        'refunds':   db.execute("SELECT COUNT(*) FROM transactions WHERE refund_status='requested'").fetchone()[0],
    }
    recent = db.execute("SELECT p.*,u.name as seller FROM products p JOIN users u ON p.user_id=u.id ORDER BY p.id DESC LIMIT 8").fetchall()
    db.close()
    return render_template('admin/dashboard.html', stats=stats, recent=recent)

@app.route('/admin/users')
@login_required
@admin_required
def admin_users():
    db = get_db()
    if request.args.get('delete'): db.execute("DELETE FROM users WHERE id=? AND role='user'",(int(request.args['delete']),)); db.commit()
    if request.args.get('verify'): db.execute("UPDATE users SET is_verified=1 WHERE id=?",(int(request.args['verify']),)); db.commit()
    users = db.execute("SELECT * FROM users ORDER BY id").fetchall()
    db.close()
    return render_template('admin/users.html', users=users)

@app.route('/admin/products')
@login_required
@admin_required
def admin_products():
    db = get_db()
    if request.args.get('delete'): db.execute("DELETE FROM products WHERE id=?",(int(request.args['delete']),)); db.commit()
    products = db.execute("SELECT p.*,u.name as seller FROM products p JOIN users u ON p.user_id=u.id ORDER BY p.id DESC").fetchall()
    db.close()
    return render_template('admin/products.html', products=products)

@app.route('/admin/transactions')
@login_required
@admin_required
def admin_transactions():
    db = get_db()
    if request.args.get('complete'):
        tid=int(request.args['complete'])
        t=db.execute("SELECT product_id FROM transactions WHERE id=?",(tid,)).fetchone()
        db.execute("UPDATE transactions SET status='completed' WHERE id=?",(tid,))
        if t: db.execute("UPDATE products SET status='sold' WHERE id=?",(t['product_id'],))
        db.commit(); flash('Transaction marked as completed!','success')
    if request.args.get('refund'):
        db.execute("UPDATE transactions SET refund_status='approved',status='refunded' WHERE id=?",(int(request.args['refund']),)); db.commit(); flash('Refund approved successfully!','success')
    txns = db.execute("SELECT t.*,p.title,b.name as buyer,s.name as seller FROM transactions t JOIN products p ON t.product_id=p.id JOIN users b ON t.buyer_id=b.id JOIN users s ON t.seller_id=s.id ORDER BY t.id DESC").fetchall()
    db.close()
    return render_template('admin/transactions.html', txns=txns)

if __name__ == '__main__':
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    init_db()
    print("ElecExchange is running!")
    print("Open browser: http://127.0.0.1:5000")
    print("Admin: admin@elec.com / password")
    print("User:  ali@gmail.com  / password")
    app.run(debug=True)
