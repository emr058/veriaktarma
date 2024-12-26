from flask import Flask, render_template, request, redirect, url_for, jsonify
import firebase_admin
from firebase_admin import credentials, db
from datetime import datetime

# Firebase ayarları
cred = credentials.Certificate("serviceAccountKey.json")  # Firebase key dosyanız
firebase_admin.initialize_app(cred, {'databaseURL': 'https://studentattandence-fd186-default-rtdb.firebaseio.com/'})

app = Flask(__name__)

@app.route('/')
def admin_panel():
    ref = db.reference('students')
    students = ref.get() or {}
    return render_template('admin.html', students=students)

@app.route('/add_student', methods=['POST'])
def add_student():
    student_number = request.form['student_number']
    student_name = request.form['student_name']
    student_image = request.files['student_image']

    # Firebase'e kayıt
    ref = db.reference('students')
    ref.child(student_number).set({
        'name': student_name,
        'student_number': student_number,
        'image_url': f'images/{student_image.filename}'  # Yüklenen resim Firebase Storage'da tutulabilir
    })

    # Resim kaydetme işlemi (örnek, yerel olarak kaydetme)
    student_image.save(f'./static/images/{student_image.filename}')
    return redirect(url_for('admin_panel'))

@app.route('/delete_student/<student_number>', methods=['GET'])
def delete_student(student_number):
    ref = db.reference('students')
    ref.child(student_number).delete()
    return redirect(url_for('admin_panel'))

@app.route('/attendance')
def attendance():
    ref = db.reference('attendance')
    attendance_data = ref.get() or {}
    return jsonify(attendance_data)

if __name__ == "__main__":
    app.run(debug=True)
