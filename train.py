from flask import Flask, request, jsonify
import os
import firebase_admin
from firebase_admin import credentials, db
import base64
from datetime import datetime
import cv2

app = Flask(__name__)

# Firebase bağlantısı
cred = credentials.Certificate('serviceAccountKey.json')
firebase_admin.initialize_app(cred, {'databaseURL': "https://studentattandence-fd186-default-rtdb.firebaseio.com/"})

# Firebase Realtime Database bağlantısı
ref = db.reference('students')

UPLOAD_FOLDER = './uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


# Fotoğraf yükleme ve yüz tanıma işlemleri
def detect_face(image_path):
    # OpenCV ile yüz tanıma işlemi yapılacak
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    image = cv2.imread(image_path)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5)
    if len(faces) > 0:
        return True  # Yüz tanındı
    return False


@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    # Dosya kaydetme
    filename = os.path.join(app.config['UPLOAD_FOLDER'], 'uploaded_image.jpg')
    file.save(filename)

    # Yüz tanıma işlemi
    if detect_face(filename):
        # Fotoğraf yüklendikten sonra veritabanında öğrenci bilgilerini kontrol etme
        student_number = filename.split("_")[0]  # Öğrenci noyu dosya isminden alıyoruz, örneğin: 1234_ismi.jpg
        student_ref = ref.child(student_number)
        student_data = student_ref.get()  # Veritabanında öğrenci arama

        if student_data:
            # Öğrenci bulundu
            return jsonify({
                'status': 'success',
                'message': 'Student recognized',
                'student_number': student_number,
                'student_data': student_data
            })
        else:
            # Öğrenci bulunamadı
            return jsonify({
                'status': 'error',
                'message': 'Student not found'
            }), 404
    else:
        return jsonify({'status': 'error', 'message': 'Face not detected'}), 400


if __name__ == "__main__":
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    app.run(host="0.0.0.0", port=5000)
