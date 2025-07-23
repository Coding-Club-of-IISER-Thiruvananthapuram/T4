# Save this as: app.py
from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from functools import wraps
import os
from datetime import datetime
from werkzeug.utils import secure_filename

# --- App & Database Configuration ---
app = Flask(__name__)
app.secret_key = 'your_very_secret_key_change_this'
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'database.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# NEW: Configuration for file uploads
app.config['UPLOAD_FOLDER'] = os.path.join(basedir, 'static/image')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

db = SQLAlchemy(app)

# --- Helper Function ---
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# --- Database Models ---
class Update(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=False)
    date = db.Column(db.String(50))
    image_file = db.Column(db.String(100), nullable=True) # NEW

class Club(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    image_file = db.Column(db.String(100), nullable=True) # NEW

class BlogPost(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    content = db.Column(db.Text, nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    image_file = db.Column(db.String(100), nullable=True) # NEW

# ... (Gallery and Event models remain the same) ...
class GalleryImage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(100), nullable=False)
    caption = db.Column(db.String(200), nullable=True)

class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=False)
    date = db.Column(db.String(50))
    location = db.Column(db.String(100))


# --- Authentication & Routes (mostly the same) ---
ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD = 'password123'

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            flash('Please log in to access this page.', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def home():
    updates = Update.query.order_by(Update.id.desc()).all()
    clubs = Club.query.order_by(Club.id.asc()).all()
    posts = BlogPost.query.order_by(BlogPost.id.desc()).all()
    gallery_images = GalleryImage.query.order_by(GalleryImage.id.desc()).all()
    events = Event.query.order_by(Event.id.desc()).all()
    return render_template('index.html', updates=updates, clubs=clubs, posts=posts, gallery_images=gallery_images, events=events)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form['username'] == ADMIN_USERNAME and request.form['password'] == ADMIN_PASSWORD:
            session['logged_in'] = True
            flash('You were successfully logged in!', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid credentials. Please try again.', 'danger')
    return render_template('login.html')

@app.route('/admin')
@login_required
def admin_dashboard():
    return render_template('admin.html')


# --- Form Handling Routes (UPDATED) ---

@app.route('/admin/update/add', methods=['POST'])
@login_required
def add_update():
    title = request.form['update-title']
    description = request.form['update-description']
    date = request.form['update-date']
    image_file = request.files['update-image']
    
    filename = None
    if image_file and allowed_file(image_file.filename):
        filename = secure_filename(image_file.filename)
        image_file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

    new_update = Update(title=title, description=description, date=date, image_file=filename)
    db.session.add(new_update)
    db.session.commit()
    flash('New update has been added successfully!', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/club/add', methods=['POST'])
@login_required
def add_club():
    name = request.form['club-name']
    description = request.form['club-description']
    image_file = request.files['club-image']

    filename = None
    if image_file and allowed_file(image_file.filename):
        filename = secure_filename(image_file.filename)
        image_file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

    new_club = Club(name=name, description=description, image_file=filename)
    db.session.add(new_club)
    db.session.commit()
    flash('New club has been added successfully!', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/blog/add', methods=['POST'])
@login_required
def add_blog():
    title = request.form['blog-title']
    content = request.form['blog-content']
    image_file = request.files['blog-image']

    filename = None
    if image_file and allowed_file(image_file.filename):
        filename = secure_filename(image_file.filename)
        image_file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

    new_post = BlogPost(title=title, content=content, image_file=filename)
    db.session.add(new_post)
    db.session.commit()
    flash('New blog post has been published!', 'success')
    return redirect(url_for('admin_dashboard'))

# ... (Gallery and Event routes remain the same) ...
@app.route('/admin/gallery/add', methods=['POST'])
@login_required
def add_gallery_image():
    image_file = request.files['gallery-image']
    if image_file and allowed_file(image_file.filename):
        filename = secure_filename(image_file.filename)
        image_file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        new_image = GalleryImage(filename=filename, caption=request.form['gallery-caption'])
        db.session.add(new_image)
        db.session.commit()
        flash('New gallery image has been added!', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/event/add', methods=['POST'])
@login_required
def add_event():
    new_event = Event(
        title=request.form['event-title'],
        description=request.form['event-description'],
        date=request.form['event-date'],
        location=request.form['event-location']
    )
    db.session.add(new_event)
    db.session.commit()
    flash('New event has been added successfully!', 'success')
    return redirect(url_for('admin_dashboard'))


@app.route('/logout')
@login_required
def logout():
    session.clear()
    flash('You were successfully logged out.', 'success')
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)
