# Save this as: app.py
from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from functools import wraps
import os
from datetime import datetime
from werkzeug.utils import secure_filename

# --- App & Database Configuration ---
app = Flask(__name__)
app.secret_key = 'your_very_secret_key_change_this_later'
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'database.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.path.join(basedir, 'static/image')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

db = SQLAlchemy(app)

# --- Helper Function ---
def allowed_file(filename):
    """Checks if a file's extension is allowed."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# --- Database Models ---
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
ADMIN_PASSWORD = 'password123' # In a real app, use a more secure method

def login_required(f):
    """Decorator to ensure a user is logged in."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            flash('Please log in to access this page.', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# --- Main Routes ---
@app.route('/')
def home():
    """Renders the public homepage with all content."""
    updates = Update.query.order_by(Update.id.desc()).all()
    clubs = Club.query.order_by(Club.name.asc()).all()
    posts = BlogPost.query.order_by(BlogPost.date_posted.desc()).all()
    gallery_images = GalleryImage.query.order_by(GalleryImage.id.desc()).all()
    events = Event.query.order_by(Event.id.desc()).all()
    return render_template('index.html', updates=updates, clubs=clubs, posts=posts, gallery_images=gallery_images, events=events)

@app.route('/blog/<int:id>')
def view_blog(id):
    """Displays a single blog post and related posts."""
    post = BlogPost.query.get_or_404(id)
    related_posts = BlogPost.query.filter(BlogPost.id != id).order_by(db.func.random()).limit(3).all()
    return render_template('blog_post.html', post=post, related_posts=related_posts)

# --- Admin & Auth Routes ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    """Handles admin login."""
    if request.method == 'POST':
        if request.form['username'] == ADMIN_USERNAME and request.form['password'] == ADMIN_PASSWORD:
            session['logged_in'] = True
            flash('You were successfully logged in!', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid credentials. Please try again.', 'danger')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    """Logs the admin out."""
    session.clear()
    flash('You were successfully logged out.', 'success')
    return redirect(url_for('home'))

@app.route('/admin')
@login_required
def admin_dashboard():
    """Displays the admin dashboard with all manageable content."""
    updates = Update.query.order_by(Update.id.desc()).all()
    clubs = Club.query.order_by(Club.name.asc()).all()
    posts = BlogPost.query.order_by(BlogPost.date_posted.desc()).all()
    gallery_images = GalleryImage.query.order_by(GalleryImage.id.desc()).all()
    events = Event.query.order_by(Event.id.desc()).all()
    return render_template('admin.html', updates=updates, clubs=clubs, posts=posts, gallery_images=gallery_images, events=events)

# --- ADD CONTENT ROUTES ---
@app.route('/admin/update/add', methods=['POST'])
@login_required
def add_update():
    title = request.form['update-title']
    description = request.form['update-description']
    date = request.form['update-date']
    image_file = request.files.get('update-image')

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
    image_file = request.files.get('club-image')

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
    image_file = request.files.get('blog-image')

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
    image_file = request.files.get('gallery-image')
    if image_file and allowed_file(image_file.filename):
        filename = secure_filename(image_file.filename)
        image_file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        new_image = GalleryImage(filename=filename, caption=request.form.get('gallery-caption'))
        db.session.add(new_image)
        db.session.commit()
        flash('New gallery image has been added!', 'success')
    else:
        flash('Invalid file type for gallery image.', 'danger')
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

# --- DELETE CONTENT ROUTE (CORRECTED) ---
@app.route('/delete/<item_type>/<int:id>', methods=['POST']) # Added methods=['POST']
@login_required
def delete_item(item_type, id):
    """Deletes an item from the database permanently."""
    model_map = {
        'update': Update,
        'club': Club,
        'gallery': GalleryImage,
        'event': Event,
        'blog': BlogPost
    }
    
    if item_type in model_map:
        Model = model_map[item_type]
        obj_to_delete = Model.query.get_or_404(id)

        # If the object has an image, try to delete it from the filesystem
        image_path = None
        if hasattr(obj_to_delete, 'image_file') and obj_to_delete.image_file:
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], obj_to_delete.image_file)
        elif hasattr(obj_to_delete, 'filename'): # For GalleryImage
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], obj_to_delete.filename)
        
        if image_path and os.path.exists(image_path):
            try:
                os.remove(image_path)
            except OSError as e:
                flash(f"Error deleting image file: {e}", "danger")

        # Delete the record from the database and commit the change
        db.session.delete(obj_to_delete)
        db.session.commit()
        flash(f'{item_type.capitalize()} has been deleted successfully.', 'success')
    else:
        flash('Invalid item type for deletion.', 'danger')
        
    return redirect(url_for('admin_dashboard'))

# --- Run the App ---
if __name__ == "__main__":
    with app.app_context():
        # This will create the database and tables if they don't exist
        db.create_all()
    # Use environment variable for port, default to 5000
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
