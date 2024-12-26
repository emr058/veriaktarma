from flask import Flask, request, jsonify
import os
import cv2
import firebase_admin
from firebase_admin import credentials, db
from datetime import datetime

app = Flask(__name__)

# Firebase bağlantısı
cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred, {'databaseURL': "https://studentattandence-fd186-default-rtdb.firebaseio.com/"})
students_ref = db.reference('students')
attendance_ref = db.reference('attendance')

UPLOAD_FOLDER = './uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)  # Upload klasörünü oluştur

# Yüz tanıma fonksiyonu
def detect_face(image_path):
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    image = cv2.imread(image_path)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5)
    if len(faces) > 0:
        return True
    return False

# Öğrenciyi tanımlama ve yoklama kaydı ekleme
def identify_and_record(image_path):
    face_detected = detect_face(image_path)
    if not face_detected:
        return {'status': 'fail', 'message': 'No face detected in the image'}

    # Veritabanındaki öğrenci resimleriyle karşılaştırma (örnek basit bir karşılaştırma)
    for student_id, student_data in students_ref.get().items():
        if 'image_url' in student_data:
            student_image_path = f"./static/{student_data['image_url']}"
            if os.path.exists(student_image_path):  # Öğrenci resmi mevcutsa
                known_image = cv2.imread(student_image_path)
                unknown_image = cv2.imread(image_path)

                # Görüntülerin karşılaştırılması
                known_gray = cv2.cvtColor(known_image, cv2.COLOR_BGR2GRAY)
                unknown_gray = cv2.cvtColor(unknown_image, cv2.COLOR_BGR2GRAY)
                if cv2.norm(known_gray, unknown_gray) < 1000:  # Basit bir norm karşılaştırma
                    # Yoklama kaydı ekleme
                    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    attendance_ref.push({
                        'student_id': student_id,
                        'timestamp': now
                    })
                    return {'status': 'success', 'message': f'Attendance recorded for {student_data["name"]}'}

    return {'status': 'fail', 'message': 'Student not recognized'}

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']

    if file.filename == '':  # Dosya seçilmediyse
        return jsonify({'error': 'No selected file'}), 400

    # Görüntüyü kaydet
    filename = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    file.save(filename)

    # Yüz tanıma ve yoklama kaydı
    result = identify_and_record(filename)

    return jsonify(result), 200 if result['status'] == 'success' else 400

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
