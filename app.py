from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = 'secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['UPLOAD_FOLDER'] = 'static/image'
app.config['TEMPLATES_AUTO_RELOAD'] = True

db = SQLAlchemy(app)

# MODELS
class Update(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200))
    description = db.Column(db.Text)
    date = db.Column(db.String(100))
    image_file = db.Column(db.String(100))

class Club(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    description = db.Column(db.Text)
    image_file = db.Column(db.String(100))

class GalleryImage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(100))
    caption = db.Column(db.String(200))

class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200))
    description = db.Column(db.Text)
    date = db.Column(db.String(100))
    location = db.Column(db.String(200))

class BlogPost(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200))
    content = db.Column(db.Text)
    date_posted = db.Column(db.DateTime, default=datetime.utcnow)
    image_file = db.Column(db.String(100))

# AUTH DECORATOR
def login_required(func):
    from functools import wraps
    @wraps(func)
    def wrapper(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('login'))
        return func(*args, **kwargs)
    return wrapper

# ROUTES
@app.route('/')
def home():
    updates = Update.query.order_by(Update.id.desc()).all()
    clubs = Club.query.order_by(Club.id.asc()).all()
    posts = BlogPost.query.order_by(BlogPost.id.desc()).all()
    gallery_images = GalleryImage.query.order_by(GalleryImage.id.desc()).all()
    events = Event.query.order_by(Event.id.desc()).all()
    return render_template('index.html', updates=updates, clubs=clubs, posts=posts, gallery_images=gallery_images, events=events)

@app.route('/admin', methods=['GET', 'POST'])
@login_required
def admin_dashboard():
    updates = Update.query.all()
    clubs = Club.query.all()
    gallery = GalleryImage.query.all()
    events = Event.query.all()
    posts = BlogPost.query.all()
    return render_template('admin.html', updates=updates, clubs=clubs, gallery=gallery, events=events, posts=posts)

# LOGIN / LOGOUT
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form['username'] == 'admin' and request.form['password'] == 'admin':
            session['user'] = 'admin'
            return redirect(url_for('admin_dashboard'))
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('home'))

# DELETE ROUTES
@app.route('/delete/<item_type>/<int:id>')
@login_required
def delete_item(item_type, id):
    model_map = {
        'update': Update,
        'club': Club,
        'gallery': GalleryImage,
        'event': Event,
        'blog': BlogPost
    }
    if item_type in model_map:
        obj = model_map[item_type].query.get_or_404(id)
        db.session.delete(obj)
        db.session.commit()
    return redirect(url_for('admin_dashboard'))

# ADD ROUTES
@app.route('/add_update', methods=['POST'])
@login_required
def add_update():
    title = request.form['title']
    description = request.form['description']
    date = request.form['date']
    image = request.files['image']
    filename = secure_filename(image.filename)
    image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    new_update = Update(title=title, description=description, date=date, image_file=filename)
    db.session.add(new_update)
    db.session.commit()
    return redirect(url_for('admin_dashboard'))

@app.route('/add_club', methods=['POST'])
@login_required
def add_club():
    name = request.form['name']
    description = request.form['description']
    image = request.files['image']
    filename = secure_filename(image.filename)
    image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    new_club = Club(name=name, description=description, image_file=filename)
    db.session.add(new_club)
    db.session.commit()
    return redirect(url_for('admin_dashboard'))

@app.route('/add_gallery', methods=['POST'])
@login_required
def add_gallery():
    image = request.files['image']
    caption = request.form['caption']
    filename = secure_filename(image.filename)
    image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    new_image = GalleryImage(filename=filename, caption=caption)
    db.session.add(new_image)
    db.session.commit()
    return redirect(url_for('admin_dashboard'))

@app.route('/add_event', methods=['POST'])
@login_required
def add_event():
    title = request.form['title']
    description = request.form['description']
    date = request.form['date']
    location = request.form['location']
    new_event = Event(title=title, description=description, date=date, location=location)
    db.session.add(new_event)
    db.session.commit()
    return redirect(url_for('admin_dashboard'))

@app.route('/add_blog', methods=['POST'])
@login_required
def add_blog():
    title = request.form['title']
    content = request.form['content']
    image = request.files['image']
    filename = secure_filename(image.filename)
    image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    new_blog = BlogPost(title=title, content=content, image_file=filename)
    db.session.add(new_blog)
    db.session.commit()
    return redirect(url_for('admin_dashboard'))

# BLOG DETAIL ROUTE
@app.route('/blog/<int:id>')
def view_blog(id):
    post = BlogPost.query.get_or_404(id)
    related_posts = BlogPost.query.filter(BlogPost.id != id).order_by(db.func.random()).limit(3).all()
    return render_template('blog_post.html', post=post, related_posts=related_posts)

# DB INIT
@app.before_first_request
def create_tables():
    db.create_all()

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
