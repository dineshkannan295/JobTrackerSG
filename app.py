import os
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'change_this_secret')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///' + os.path.join(BASE_DIR, 'database.db'))
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# --- Models ---
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    full_name = db.Column(db.String(120), nullable=True)
    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), default='staff')  # 'admin' or 'staff'

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Job(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    reference_no = db.Column(db.String(120), unique=True, nullable=False)
    importer_name = db.Column(db.String(200), nullable=False)
    received_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    allocated_to_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    status = db.Column(db.String(50), default='Pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)

    allocated_to = db.relationship('User', backref='jobs')

# --- Login manager ---
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- Routes ---
@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('dashboard'))
        flash('Invalid username or password', 'danger')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    # filters
    status = request.args.get('status')
    allocated = request.args.get('allocated')
    q = request.args.get('q')

    jobs = Job.query
    if status:
        jobs = jobs.filter_by(status=status)
    if allocated:
        jobs = jobs.join(User).filter(User.username == allocated)
    if q:
        likeq = f\"%{q}%\"
        jobs = jobs.filter((Job.reference_no.ilike(likeq)) | (Job.importer_name.ilike(likeq)))

    jobs = jobs.order_by(Job.created_at.desc()).all()
    users = User.query.order_by(User.username).all()
    return render_template('dashboard.html', jobs=jobs, users=users)

@app.route('/jobs/add', methods=['GET', 'POST'])
@login_required
def add_job():
    users = User.query.order_by(User.username).all()
    if request.method == 'POST':
        ref = request.form['reference_no'].strip()
        importer = request.form['importer_name'].strip()
        received_time = request.form.get('received_time')
        allocated_to = request.form.get('allocated_to') or None
        status = request.form.get('status', 'Pending')

        if not ref or not importer:
            flash('Reference and Importer name are required', 'danger')
            return redirect(url_for('add_job'))

        if Job.query.filter_by(reference_no=ref).first():
            flash('Reference already exists', 'danger')
            return redirect(url_for('add_job'))

        if received_time:
            try:
                received_dt = datetime.fromisoformat(received_time)
            except Exception:
                received_dt = datetime.utcnow()
        else:
            received_dt = datetime.utcnow()

        job = Job(reference_no=ref, importer_name=importer, received_time=received_dt, status=status)
        if allocated_to:
            user = User.query.filter_by(username=allocated_to).first()
            if user:
                job.allocated_to = user
        db.session.add(job)
        db.session.commit()
        flash('Job added', 'success')
        return redirect(url_for('dashboard'))

    return render_template('add_job.html', users=users)

@app.route('/jobs/<int:job_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_job(job_id):
    job = Job.query.get_or_404(job_id)
    users = User.query.order_by(User.username).all()
    if request.method == 'POST':
        job.importer_name = request.form['importer_name'].strip()
        job.status = request.form.get('status', job.status)
        allocated_to = request.form.get('allocated_to') or None
        if allocated_to:
            user = User.query.filter_by(username=allocated_to).first()
            job.allocated_to = user
        else:
            job.allocated_to = None
        job.updated_at = datetime.utcnow()
        db.session.commit()
        flash('Job updated', 'success')
        return redirect(url_for('dashboard'))
    return render_template('edit_job.html', job=job, users=users)

@app.route('/users')
@login_required
def users_page():
    if current_user.role != 'admin':
        flash('Only admin can access users page', 'danger')
        return redirect(url_for('dashboard'))
    users = User.query.order_by(User.username).all()
    return render_template('users.html', users=users)

@app.route('/users/add', methods=['POST'])
@login_required
def add_user():
    if current_user.role != 'admin':
        return jsonify({'error': 'Forbidden'}), 403
    data = request.form
    username = data.get('username')
    full_name = data.get('full_name')
    password = data.get('password')
    role = data.get('role', 'staff')
    if not username or not password:
        return jsonify({'error': 'Username and password required'}), 400
    if User.query.filter_by(username=username).first():
        return jsonify({'error': 'User exists'}), 400
    u = User(username=username, full_name=full_name, password_hash=generate_password_hash(password), role=role)
    db.session.add(u)
    db.session.commit()
    return redirect(url_for('users_page'))

# --- Utility to initialize DB and seed users ---
@app.cli.command('initdb')
def initdb_command():
    \"\"\"Initialize the database and seed users\"\"\"
    db.drop_all()
    db.create_all()
    # create admin (using admin/admin123 per user request)
    admin = User(username='admin', full_name='Administrator', password_hash=generate_password_hash('admin123'), role='admin')
    db.session.add(admin)

    # seed 25 staff users (total 26 including admin)
    for i in range(1, 26):
        uname = f'user{i:02d}'
        full = f'Staff {i:02d}'
        pw = f'Pass{i:02d}!'
        u = User(username=uname, full_name=full, password_hash=generate_password_hash(pw), role='staff')
        db.session.add(u)

    db.session.commit()
    print('Initialized the database and seeded users. Admin credentials: username=admin, password=admin123')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=True)
