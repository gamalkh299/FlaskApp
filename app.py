from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os

# Initialize Flask App
app = Flask(__name__)
app.config['SECRET_KEY'] = 'YourSecretKey'
app.config['UPLOAD_FOLDER'] = 'uploads'

# Flask-Login Setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Static User Data
users = {
    "doctor": {"password": generate_password_hash("doctor123"), "role": "doctor"},
    "student": {"password": generate_password_hash("student123"), "role": "student"}
}
# Temporary storage for feedback (in a real app, use a database)

feedback_data = {}


class User(UserMixin):
    def __init__(self, username):
        self.id = username
        self.role = users[username]['role']

@login_manager.user_loader
def load_user(user_id):
    if user_id in users:
        return User(user_id)

# Routes
@app.route('/')
@login_required
def index():
    return render_template('index.html', role=current_user.role)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username in users and check_password_hash(users[username]['password'], password):
            user = User(username)
            login_user(user)
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password')
    return render_template('login.html')

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload_file():
    if current_user.role == 'student':
        if request.method == 'POST':
            file = request.files['file']
            if file:
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                return redirect(url_for('index'))
        return render_template('upload.html', role=current_user.role)
    else:
        flash('Only students can upload images.')
        return redirect(url_for('index'))

@app.route('/my_images')
@login_required
def my_images():
    if current_user.role == 'student':
        image_files = os.listdir(app.config['UPLOAD_FOLDER'])
        images_feedback = [(file, feedback_data.get(file, "No feedback yet."))
                           for file in image_files]
        return render_template('my_images.html', images_feedback=images_feedback)
    else:
        flash('Only students can view their images.')
        return redirect(url_for('index'))

@app.route('/view_images')
@login_required
def view_images():
    if current_user.role == 'doctor':
        image_files = os.listdir(app.config['UPLOAD_FOLDER'])
        image_urls = [url_for('uploaded_file', filename=file) for file in image_files]
        return render_template('view_images.html', image_urls=image_urls)
    else:
        flash('Only doctors can view images.')
        return redirect(url_for('index'))

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


# Updated feedback route to store feedback
@app.route('/feedback/<filename>', methods=['GET', 'POST'])
@login_required
def feedback(filename):
    if current_user.role == 'doctor':
        if request.method == 'POST':
            feedback = request.form.get('feedback')
            feedback_data[filename] = feedback  # Store feedback
            flash(f'Feedback submitted for {filename}')
            return redirect(url_for('view_images'))
        return render_template('feedback.html', filename=filename)
    else:
        flash('Only doctors can provide feedback.')
        return redirect(url_for('index'))

# New route for students to view feedback
@app.route('/view_feedback/<filename>')
@login_required
def view_feedback(filename):
    if current_user.role == 'student':
        image_feedback = feedback_data.get(filename, "No feedback yet.")
        return render_template('view_feedback.html', filename=filename, feedback=image_feedback)
    else:
        flash('Only students can view feedback.')
        return redirect(url_for('index'))


if __name__ == '__main__':
    # Ensure upload folder exists
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])

    app.run(debug=True)
