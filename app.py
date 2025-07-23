
from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from functools import wraps
import os
from datetime import datetime
from werkzeug.utils import secure_filename

# --- Flask App Configuration ---
app = Flask(__name__)
app.secret_key = 'your_very_secret_key_change_this'
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'database.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.path.join(basedir, 'static/image')
app.config['TEMPLATES_AUTO_RELOAD'] = True

# Optional: Disable Jinja template caching (during development)
import jinja2
app.jinja_env.cache = {}

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

db = SQLAlchemy(app)

# --- Helper Function ---
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# --- Models ---
class Update(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=False)
    date = db.Column(db.String(50))
    image_file = db.Column(db.String(100), nullable=True)

class Club(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    image_file = db.Column(db.String(100), nullable=True)

class BlogPost(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    content = db.Column(db.Text, nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    image_file = db.Column(db.String(100), nullable=True)

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

# --- Authentication ---
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

# --- Routes ---

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
    updates = Update.query.all()
    clubs = Club.query.all()
    posts = BlogPost.query.all()
    gallery_images = GalleryImage.query.all()
    events = Event.query.all()
    return render_template('admin.html', updates=updates, clubs=clubs, posts=posts, gallery_images=gallery_images, events=events)

# --- Add Routes ---

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

@app.route('/admin/gallery/add', methods=['POST'])
@login_required
def add_gallery_image():
    image_file = request.files['gallery-image']
    caption = request.form.get('gallery-caption', '')
    if image_file and allowed_file(image_file.filename):
        filename = secure_filename(image_file.filename)
        image_file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        new_image = GalleryImage(filename=filename, caption=caption)
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

# --- Delete Routes ---

@app.route('/admin/update/delete/<int:id>', methods=['POST'])
@login_required
def delete_update(id):
    item = Update.query.get_or_404(id)
    db.session.delete(item)
    db.session.commit()
    flash('Update deleted.', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/club/delete/<int:id>', methods=['POST'])
@login_required
def delete_club(id):
    item = Club.query.get_or_404(id)
    db.session.delete(item)
    db.session.commit()
    flash('Club deleted.', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/blog/delete/<int:id>', methods=['POST'])
@login_required
def delete_blog(id):
    item = BlogPost.query.get_or_404(id)
    db.session.delete(item)
    db.session.commit()
    flash('Blog post deleted.', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/gallery/delete/<int:id>', methods=['POST'])
@login_required
def delete_gallery(id):
    item = GalleryImage.query.get_or_404(id)
    db.session.delete(item)
    db.session.commit()
    flash('Gallery image deleted.', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/event/delete/<int:id>', methods=['POST'])
@login_required
def delete_event(id):
    item = Event.query.get_or_404(id)
    db.session.delete(item)
    db.session.commit()
    flash('Event deleted.', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/logout')
@login_required
def logout():
    session.clear()
    flash('You were successfully logged out.', 'success')
    return redirect(url_for('home'))

# --- Run App ---
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
