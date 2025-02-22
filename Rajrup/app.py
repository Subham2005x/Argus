from flask import Flask, render_template, request, jsonify, Blueprint, send_file
import face_recognition
import os
from datetime import datetime
import numpy as np
import json
import time
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib.units import inch
import cv2
from reportlab.platypus import Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'ImagesAttendance'

STUDENTS_FILE = 'students.json'
ATTENDANCE_FILE = 'attendance.json'


def init_files():
    # Create directories
    os.makedirs('ImagesAttendance', exist_ok=True)
    
    # Initialize files with proper structure
    for file in [STUDENTS_FILE, ATTENDANCE_FILE]:
        if not os.path.exists(file):
            with open(file, 'w') as f:
                if file == STUDENTS_FILE:
                    json.dump([], f, indent=4)
                else:
                    json.dump([], f, indent=4)
        else:
            # Validate existing files
            try:
                with open(file, 'r') as f:
                    json.load(f)
            except json.JSONDecodeError:
                # If file is corrupted, reinitialize it
                with open(file, 'w') as f:
                    json.dump([], f, indent=4)


init_files()

@app.route('/')
def home():
    return render_template('index.html')


@app.route('/register', methods=['POST'])
def register():
    try:
        name = request.form['name']
        image = request.files['image']
        img_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{name}_{datetime.datetime.now().timestamp()}.jpg")
        image.save(img_path)

        img = face_recognition.load_image_file(img_path)
        encodings = face_recognition.face_encodings(img)
        if not encodings:
            os.remove(img_path)
            return jsonify({'success': False, 'message': 'No face detected'})

        with open(STUDENTS_FILE, 'r+') as f:
            students = json.load(f)
            students.append({
                'name': name,
                'img_path': img_path,
                'encoding': encodings[0].tolist()
            })
            f.seek(0)
            json.dump(students, f)

        return jsonify({'success': True})

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

known_encodings = None
known_names = None

def load_students():
    global known_encodings, known_names
    with open(STUDENTS_FILE, 'r') as f:
        students = json.load(f)
    known_encodings = [np.array(s['encoding']) for s in students]
    known_names = [s['name'] for s in students]

@app.route('/attendance', methods=['POST'])
def mark_attendance():
    start_time = time.time()
    try:
        global known_encodings, known_names
        if known_encodings is None or known_names is None:
            load_students()
        image = request.files['image']
        temp_path = "temp.jpg"
        image.save(temp_path)
        img = face_recognition.load_image_file(temp_path)

        face_locations = face_recognition.face_locations(img, model="hog")
        face_encodings = face_recognition.face_encodings(img, face_locations)

        os.remove(temp_path)

        with open(STUDENTS_FILE, 'r') as f:
            students = json.load(f)
        known_encodings = [np.array(s['encoding']) for s in students]
        known_names = [s['name'] for s in students]

        today = datetime.datetime.now().strftime("%Y-%m-%d")
        with open(ATTENDANCE_FILE, 'r') as f:
            existing_records = [r for r in json.load(f) if r['date'] == today]
        present_students = {r['student_name'] for r in existing_records}

        results = []

        for face_encoding in face_encodings:
            matches = face_recognition.compare_faces(known_encodings, face_encoding)
            distances = face_recognition.face_distance(known_encodings, face_encoding)
            best_match = np.argmin(distances)
            name = known_names[best_match] if matches[best_match] else "Unknown"

            if name != "Unknown" and name not in present_students:
                current_time = datetime.datetime.now().strftime("%H:%M:%S")
                with open(ATTENDANCE_FILE, 'r+') as f:
                    records = json.load(f)
                    records.append({
                        'date': today,
                        'time': current_time,
                        'student_name': name,
                        'status': 'Present'
                    })
                    f.seek(0)
                    json.dump(records, f)
                present_students.add(name)
                results.append(name)
            end_time = time.time()
            print(f"Time taken: {end_time - start_time:.2f} seconds")
        return jsonify({
            'success': True,
            'names': results
        })

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/get_attendance', methods=['GET'])
def get_attendance():
    date = request.args.get('date')
    with open(ATTENDANCE_FILE, 'r') as f:
        records = json.load(f)
    filtered = [r for r in records if r['date'] == date]
    return jsonify(filtered)

@app.route('/get_attendance_percentage', methods=['GET'])
def get_attendance_percentage():
    try:
        # Get the start and end dates from the request parameters
        start_date = request.args.get('start')
        end_date = request.args.get('end')

        if not start_date or not end_date:
            return jsonify({'success': False, 'message': 'Please provide both start and end dates.'}), 400

        # Load attendance records
        with open(ATTENDANCE_FILE, 'r') as f:
            attendance_records = json.load(f)

        # Filter records within the date range
        filtered_records = [r for r in attendance_records if start_date <= r['date'] <= end_date]

        # Count the total number of days classes were held
        class_days = set([r['date'] for r in filtered_records])
        total_class_days = len(class_days)

        if total_class_days == 0:
            return jsonify({'success': False, 'message': 'No attendance records found for the selected date range.'})

        # Calculate attendance percentage for each student
        student_attendance = {}
        for record in filtered_records:
            name = record['student_name']
            if name not in student_attendance:
                student_attendance[name] = 0
            student_attendance[name] += 1

        # Total attendance percentages
        attendance_data = []
        for name, days_present in student_attendance.items():
            percentage = (days_present / total_class_days) * 100
            attendance_data.append({'name': name, 'percentage': round(percentage, 2)})

        return jsonify({'success': True, 'data': attendance_data})

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/download_attendance_pdf', methods=['GET'])
def download_attendance_pdf():
    try:
        date = request.args.get('date')
        if not date:
            return jsonify({'success': False, 'message': 'Date parameter is required'}), 400

        with open(ATTENDANCE_FILE, 'r') as f:
            records = [r for r in json.load(f) if r['date'] == date]

        if not records:
            return jsonify({'success': False, 'message': 'No attendance records found'}), 404

        # Create PDF file
        pdf_filename = f"Attendance_{date}.pdf"
        c = canvas.Canvas(pdf_filename, pagesize=letter)
        c.setFont("Helvetica", 14)
        c.drawString(200, 750, f"Attendance Report - {date}")

        c.setFont("Helvetica", 12)
        y = 700  # Starting Y position for table

        # Table Headers
        c.drawString(100, y, "Student Name")
        c.drawString(300, y, "Time")
        c.drawString(450, y, "Status")
        y -= 20  # Move downward

        # Attendance Records
        for record in records:
            c.drawString(100, y, record["student_name"])
            c.drawString(300, y, record["time"])
            c.drawString(450, y, record["status"])
            y -= 20

        c.save()  # Save PDF

        return send_file(pdf_filename, as_attachment=True)

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

rajrup = Blueprint('rajrup', __name__, 
                  template_folder='templates',
                  static_folder='static')

@rajrup.route('/attendance')
def attendance():
    department = request.args.get('department')
    try:
        # Initialize system state
        init_system_state()
        return render_template('attendance.html', department=department)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@rajrup.route('/api/system/init', methods=['POST'])
def init_system():
    try:
        # Initialize face recognition system
        known_face_encodings = []
        known_face_names = []
        
        # Load student images from ImagesAttendance directory
        image_dir = os.path.join(os.path.dirname(__file__), 'ImagesAttendance')
        for filename in os.listdir(image_dir):
            if filename.endswith((".jpg", ".jpeg", ".png")):
                image_path = os.path.join(image_dir, filename)
                student_image = face_recognition.load_image_file(image_path)
                student_encoding = face_recognition.face_encodings(student_image)[0]
                
                known_face_encodings.append(student_encoding)
                known_face_names.append(filename.split('.')[0])
        
        return jsonify({
            'success': True,
            'message': 'System initialized successfully',
            'students_loaded': len(known_face_names)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

def init_system_state():
    # Initialize any required system state
    if not os.path.exists('ImagesAttendance'):
        os.makedirs('ImagesAttendance')

@rajrup.route('/api/initialize', methods=['POST'])
def initialize_system():
    try:
        # Your initialization code here
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@rajrup.route('/api/init-attendance', methods=['POST'])
def init_attendance():
    try:
        # Your initialization logic here
        return jsonify({
            'success': True,
            'message': 'Attendance system initialized'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@rajrup.route('/api/attendance/load', methods=['POST'])
def load_attendance():
    # Add your attendance loading logic here
    data = {
        'success': True,
        'data': []  # Add your attendance data here
    }
    return jsonify(data)

@rajrup.route('/register-student', methods=['POST'])
def register_student():
    try:
        if 'image' not in request.files or 'name' not in request.form:
            return jsonify({
                'success': False,
                'message': 'Missing image or name'
            }), 400

        name = request.form['name']
        image = request.files['image']
        
        # Create directory if it doesn't exist
        os.makedirs('ImagesAttendance', exist_ok=True)
        
        # Generate unique filename with timestamp (fixed datetime usage)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        img_path = os.path.join('ImagesAttendance', f"{name}_{timestamp}.jpg")
        
        # Save the image
        image.save(img_path)

        # Load and encode face
        img = face_recognition.load_image_file(img_path)
        encodings = face_recognition.face_encodings(img)
        
        if not encodings:
            os.remove(img_path)
            return jsonify({
                'success': False,
                'message': 'No face detected in the image'
            }), 400

        # Initialize students.json if it doesn't exist
        if not os.path.exists(STUDENTS_FILE):
            with open(STUDENTS_FILE, 'w') as f:
                json.dump([], f)

        # Update students.json with current timestamp
        with open(STUDENTS_FILE, 'r+') as f:
            students = json.load(f)
            students.append({
                'name': name,
                'img_path': img_path,
                'encoding': encodings[0].tolist(),
                'registered_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # Fixed timestamp format
            })
            f.seek(0)
            json.dump(students, f, indent=4)
            f.truncate()

        return jsonify({
            'success': True,
            'message': f'Student {name} registered successfully'
        })

    except Exception as e:
        if 'img_path' in locals() and os.path.exists(img_path):
            os.remove(img_path)
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@rajrup.route('/mark-attendance', methods=['POST'])
def mark_attendance():
    try:
        if 'image' not in request.files:
            return jsonify({
                'success': False,
                'message': 'No image provided'
            }), 400

        # Load registered students
        if not os.path.exists('students.json'):
            return jsonify({
                'success': False,
                'message': 'No registered students found'
            }), 404

        with open('students.json', 'r') as f:
            students = json.load(f)

        if not students:
            return jsonify({
                'success': False,
                'message': 'No students registered in the system'
            }), 404

        # Process the image
        image = request.files['image']
        temp_path = os.path.join('ImagesAttendance', 'temp_attendance.jpg')
        image.save(temp_path)

        # Load and process the image
        frame = face_recognition.load_image_file(temp_path)
        
        # Convert to RGB if needed
        if frame.shape[2] == 4:  # If image has alpha channel
            frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2RGB)
        elif frame.shape[2] == 3 and frame[0,0,0] == frame[0,0,2]:  # If BGR
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Detect all faces
        face_locations = face_recognition.face_locations(frame)
        
        if not face_locations:
            os.remove(temp_path)
            return jsonify({
                'success': False,
                'message': 'No faces detected in the image'
            }), 400

        face_encodings = face_recognition.face_encodings(frame, face_locations)

        # Prepare known faces
        known_faces = []
        known_names = []
        for student in students:
            if 'encoding' in student and student['encoding']:
                known_faces.append(np.array(student['encoding']))
                known_names.append(student['name'])

        # Track all detected faces
        present_students = []
        unknown_count = 0
        face_detections = []

        # Process each detected face
        for face_encoding in face_encodings:
            matches = face_recognition.compare_faces(known_faces, face_encoding, tolerance=0.6)
            if True in matches:
                # Get all matching faces
                matching_indices = [i for i, match in enumerate(matches) if match]
                # Get face distances for all matches
                face_distances = face_recognition.face_distance([known_faces[i] for i in matching_indices], face_encoding)
                best_match_index = np.argmin(face_distances)
                name = known_names[matching_indices[best_match_index]]
                
                if name not in present_students:
                    present_students.append(name)
                face_detections.append({
                    'name': name,
                    'confidence': round((1 - face_distances[best_match_index]) * 100, 2)
                })
            else:
                unknown_count += 1
                face_detections.append({
                    'name': f'Unknown_{unknown_count}',
                    'confidence': 0
                })

        # Clean up
        os.remove(temp_path)

        # Record attendance with timestamp
        if present_students:
            attendance_record = {
                'date': datetime.now().strftime('%Y-%m-%d'),
                'time': datetime.now().strftime('%H:%M:%S'),
                'present': present_students,
                'total_faces': len(face_detections),
                'unknown_faces': unknown_count
            }

            # Save attendance record
            attendance_file = 'attendance.json'
            attendance_data = []
            
            if os.path.exists(attendance_file):
                with open(attendance_file, 'r') as f:
                    attendance_data = json.load(f)
            
            attendance_data.append(attendance_record)
            
            with open(attendance_file, 'w') as f:
                json.dump(attendance_data, f, indent=4)

        return jsonify({
            'success': True,
            'present': present_students,
            'face_detections': face_detections,
            'total_faces': len(face_detections),
            'unknown_faces': unknown_count
        })

    except Exception as e:
        if os.path.exists('temp_attendance.jpg'):
            os.remove('temp_attendance.jpg')
        print(f"Attendance Error: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error marking attendance: {str(e)}'
        }), 500

import os
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch

@rajrup.route('/download-attendance', methods=['POST'])
def download_attendance_report():
    pdf_path = None
    try:
        if not request.is_json:
            return jsonify({
                'success': False,
                'message': 'Invalid request format'
            }), 400

        data = request.get_json()
        if not data or 'startDate' not in data or 'endDate' not in data:
            return jsonify({
                'success': False,
                'message': 'Missing date parameters'
            }), 400

        start_date = datetime.strptime(data['startDate'], '%Y-%m-%d')
        end_date = datetime.strptime(data['endDate'], '%Y-%m-%d')

        # Load and validate attendance data
        if not os.path.exists(ATTENDANCE_FILE):
            return jsonify({
                'success': False,
                'message': 'No attendance records found'
            }), 404

        with open(ATTENDANCE_FILE, 'r') as f:
            attendance_data = json.load(f)

        # Filter records
        filtered_data = [
            record for record in attendance_data
            if start_date <= datetime.strptime(record['date'], '%Y-%m-%d') <= end_date
        ]

        if not filtered_data:
            return jsonify({
                'success': False,
                'message': 'No attendance records found for selected date range'
            }), 404

        # Create temporary directory if it doesn't exist
        temp_dir = os.path.join(os.path.dirname(__file__), 'temp')
        os.makedirs(temp_dir, exist_ok=True)

        # Generate unique filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        pdf_path = os.path.join(temp_dir, f'attendance_report_{timestamp}.pdf')

        # Create PDF
        doc = SimpleDocTemplate(
            pdf_path,
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )

        # Create report content
        elements = []
        styles = getSampleStyleSheet()

        # Add title and date range
        title = Paragraph(
            f"Attendance Report<br/>Period: {data['startDate']} to {data['endDate']}", 
            styles['Heading1']
        )
        elements.append(title)
        elements.append(Spacer(1, 20))

        # Create table
        table_data = [['Date', 'Time', 'Students Present']]
        for record in filtered_data:
            table_data.append([
                record['date'],
                record['time'],
                ', '.join(record['present'])
            ])

        table = Table(table_data, colWidths=[1.5*inch, 1.5*inch, 4*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))

        elements.append(table)
        doc.build(elements)

        return send_file(
            pdf_path,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f'attendance_report_{data["startDate"]}_to_{data["endDate"]}.pdf'
        )

    except Exception as e:
        print(f"Report generation error: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Failed to generate report: {str(e)}'
        }), 500

    finally:
        # Clean up temporary file
        if pdf_path and os.path.exists(pdf_path):
            try:
                os.remove(pdf_path)
            except Exception as e:
                print(f"Error removing temporary file: {str(e)}")

app.register_blueprint(rajrup)

if __name__ == '__main__':
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    app.run(debug=True)
