from flask import Flask, request, jsonify, render_template, send_file, redirect, url_for, session
from werkzeug.utils import secure_filename
import os
from cryptography.fernet import Fernet
import logging

# Initialize Flask app
app = Flask(__name__)
app.secret_key = "securexchange-secret-key"  # Replace with a strong secret key
app.config['UPLOAD_FOLDER'] = './uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Logger setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("SecureXchange")

# Encryption key setup
encryption_key = Fernet.generate_key()
cipher = Fernet(encryption_key)

# In-memory user data (for simplicity; replace with a database in production)
users = {"admin": "password"}  # Example user
roles = {"admin": "admin"}
sessions = {}

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        if 'file' not in request.files:
            return jsonify({"error": "No file uploaded"}), 400
        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "No selected file"}), 400

        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        encrypted_data = cipher.encrypt(file.read())
        with open(file_path, 'wb') as f:
            f.write(encrypted_data)

        logger.info(f"Uploaded file: {filename}")
        return jsonify({"message": "File uploaded successfully", "filename": filename})
    return render_template('upload.html')

@app.route('/files', methods=['GET'])
def list_files():
    files = os.listdir(app.config['UPLOAD_FOLDER'])
    return render_template('download.html', files=files)

@app.route('/download/<filename>', methods=['GET'])
def download(filename):
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if not os.path.exists(file_path):
        return jsonify({"error": "File not found"}), 404
    with open(file_path, 'rb') as f:
        encrypted_data = f.read()
    decrypted_data = cipher.decrypt(encrypted_data)
    return send_file(
        io.BytesIO(decrypted_data),
        as_attachment=True,
        download_name=filename
    )

@app.route('/message', methods=['GET', 'POST'])
def message():
    if request.method == 'POST':
        user = request.form['user']
        message = request.form['message']
        encrypted_message = cipher.encrypt(message.encode())
        logger.info(f"Message from {user}: {encrypted_message}")
        return jsonify({"message": "Message sent", "encrypted": encrypted_message.decode()})
    return render_template('message.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username in users and users[username] == password:
            session['user'] = username
            return redirect(url_for('index'))
        return jsonify({"error": "Invalid credentials"}), 401
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username in users:
            return jsonify({"error": "User already exists"}), 400
        users[username] = password
        roles[username] = "user"
        return redirect(url_for('login'))
    return render_template('signup.html')

if __name__ == '__main__':
    app.run(debug=True)
