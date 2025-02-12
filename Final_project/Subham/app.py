from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

class Teacher(UserMixin, db.Model):
    teacher_id = db.Column(db.String(10), primary_key=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(60), nullable=False)

    def get_id(self):
        return self.teacher_id

@login_manager.user_loader
def load_user(user_id):
    return Teacher.query.get(user_id)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        teacher_id = request.form['teacher_id']
        name = request.form['name']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        # Check if teacher_id already exists
        existing_teacher = Teacher.query.filter_by(teacher_id=teacher_id).first()
        if existing_teacher:
            flash('Teacher ID already exists! Please login instead.', 'warning')
            return redirect(url_for('login'))

        if password != confirm_password:
            flash('Passwords do not match!', 'danger')
            return redirect(url_for('register'))

        # Hash the password and create new teacher
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        new_teacher = Teacher(teacher_id=teacher_id, name=name, password=hashed_password)
        
        try:
            db.session.add(new_teacher)
            db.session.commit()
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            flash('An error occurred during registration. Please try again.', 'danger')
            return redirect(url_for('register'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        teacher_id = request.form['teacher_id']
        password = request.form['password']
        remember = True if request.form.get('remember') else False

        teacher = Teacher.query.filter_by(teacher_id=teacher_id).first()
        if teacher and bcrypt.check_password_hash(teacher.password, password):
            login_user(teacher, remember=remember)
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid Teacher ID or Password!', 'danger')
    return render_template('login.html')

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html', name=current_user.name)

@app.route('/logout')
def logout():
    flash('Logged out successfully!', 'info')
    return redirect(url_for('login'))

@app.route('/future')
def future():
    return render_template('future.html')

@app.route('/resource')
def resource():
    return render_template('resource.html')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)