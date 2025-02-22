from flask import Flask, render_template, redirect, url_for, request, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from datetime import datetime
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
import sys
import os
from datetime import datetime

# Add the parent directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from Rajrup.app import rajrup

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Register the blueprint with correct paths
app.register_blueprint(rajrup, 
                      url_prefix='/rajrup',
                      template_folder='../Rajrup/templates',
                      static_folder='../Rajrup/static')

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

@app.route('/logout', methods=['POST'])
@login_required
def logout():
    logout_user()  # Add this line to properly log out the user
    flash('Logged out successfully!', 'info')
    return redirect(url_for('login'))

@app.route('/future')
def future():
    return render_template('future.html')

@app.route('/resource')
def resource():
    return render_template('resource.html')


# CRUD operations for classes
class Class(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    student_count = db.Column(db.Integer, nullable=False)
    teacher_id = db.Column(db.String(10), db.ForeignKey('teacher.teacher_id'), nullable=False)

class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    class_id = db.Column(db.Integer, db.ForeignKey('class.id'), nullable=False)
    encoding = db.Column(db.PickleType, nullable=True)  # Store face encoding
    image_path = db.Column(db.String(200), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    class_id = db.Column(db.Integer, db.ForeignKey('class.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    time = db.Column(db.Time, nullable=False)
    status = db.Column(db.Boolean, default=True)  # True for present

@app.route('/api/classes', methods=['GET'])
@login_required
def get_classes():
    classes = Class.query.filter_by(teacher_id=current_user.teacher_id).all()
    class_list = [{
        "id": cls.id, 
        "name": cls.name,
        "studentCount": cls.student_count
    } for cls in classes]
    return jsonify(class_list)

@app.route('/api/classes', methods=['POST'])
@login_required
def add_class():
    data = request.json
    if 'name' not in data or 'studentCount' not in data:
        return jsonify({"error": "Name and student count are required"}), 400
    
    new_class = Class(
        name=data['name'],
        student_count=data['studentCount'],
        teacher_id=current_user.teacher_id
    )
    db.session.add(new_class)
    db.session.commit()
    return jsonify({
        "id": new_class.id,
        "name": new_class.name,
        "studentCount": new_class.student_count
    }), 201

@app.route('/api/classes/<int:id>', methods=['PUT'])
@login_required
def update_class(id):
    data = request.json
    cls = Class.query.get_or_404(id)
    if cls.teacher_id != current_user.teacher_id:
        return jsonify({"error": "Unauthorized"}), 403
    
    if 'name' not in data or 'studentCount' not in data:
        return jsonify({"error": "Name and student count are required"}), 400
    
    cls.name = data['name']
    cls.student_count = data['studentCount']
    db.session.commit()
    return jsonify({
        "id": cls.id,
        "name": cls.name,
        "studentCount": cls.student_count
    })

@app.route('/api/classes/<int:id>', methods=['DELETE'])
@login_required
def delete_class(id):
    cls = Class.query.get_or_404(id)
    if cls.teacher_id != current_user.teacher_id:
        return jsonify({"error": "Unauthorized"}), 403
    db.session.delete(cls)
    db.session.commit()
    return jsonify({"message": "Class deleted successfully"}), 200

@app.route('/live-attendance/<department>')
@login_required
def live_attendance(department):
    try:
        # Use url_for to generate the correct URL for attendance.html
        return redirect(url_for('rajrup.attendance', department=department))
    except Exception as e:
        print(f"Redirection error: {str(e)}")
        flash('Error accessing attendance system', 'error')
        return redirect(url_for('dashboard'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)