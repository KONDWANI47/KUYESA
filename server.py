from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
import os
import sqlite3
import uuid
from datetime import datetime

# Initialize Flask app
app = Flask(__name__, static_folder='public')
CORS(app)  # Enable CORS for all routes

# Create uploads directory if it doesn't exist
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Database setup
def get_db_connection():
    conn = sqlite3.connect('musicvibe.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create users table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id TEXT PRIMARY KEY,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Create audio table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS audio (
        id TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        artist TEXT NOT NULL,
        genre TEXT NOT NULL,
        file_path TEXT NOT NULL,
        user_id TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    ''')
    
    conn.commit()
    conn.close()

# Initialize database
init_db()

# Serve static files
@app.route('/', defaults={'path': 'index.html'})
@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('public', path)

# API Routes
@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    
    if not username or not email or not password:
        return jsonify({'error': 'All fields are required'}), 400
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if email already exists
    cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
    if cursor.fetchone():
        conn.close()
        return jsonify({'error': 'Email already exists'}), 409
    
    # Check if username already exists
    cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
    if cursor.fetchone():
        conn.close()
        return jsonify({'error': 'Username already exists'}), 409
    
    # Hash password and create user
    hashed_password = generate_password_hash(password)
    user_id = str(uuid.uuid4())
    
    cursor.execute(
        'INSERT INTO users (id, username, email, password) VALUES (?, ?, ?, ?)',
        (user_id, username, email, hashed_password)
    )
    
    conn.commit()
    conn.close()
    
    return jsonify({'message': 'User created successfully', 'user_id': user_id}), 201

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email')
    password = data.get('password')
    
    if not email or not password:
        return jsonify({'error': 'Email and password are required'}), 400
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
    user = cursor.fetchone()
    
    if not user or not check_password_hash(user['password'], password):
        conn.close()
        return jsonify({'error': 'Invalid email or password'}), 401
    
    conn.close()
    
    # Return user info (excluding password)
    return jsonify({
        'message': 'Login successful',
        'user': {
            'id': user['id'],
            'username': user['username'],
            'email': user['email']
        }
    })

@app.route('/api/upload', methods=['POST'])
def upload_audio():
    # Check if user is authenticated (in a real app, you'd use sessions or tokens)
    user_id = request.form.get('user_id')
    if not user_id:
        return jsonify({'error': 'Unauthorized'}), 401
    
    # Check if user exists
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()
    
    if not user:
        conn.close()
        return jsonify({'error': 'User not found'}), 404
    
    # Get form data
    title = request.form.get('title')
    artist = request.form.get('artist')
    genre = request.form.get('genre')
    
    if not title or not artist or not genre:
        return jsonify({'error': 'All fields are required'}), 400
    
    # Check if file was uploaded
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    # Check file type
    if not file.filename.endswith(('.mp3', '.wav')):
        return jsonify({'error': 'Only MP3 or WAV files are allowed'}), 400
    
    # Save file
    file_id = str(uuid.uuid4())
    filename = f"{file_id}_{file.filename}"
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    file.save(file_path)
    
    # Save to database
    audio_id = str(uuid.uuid4())
    cursor.execute(
        'INSERT INTO audio (id, title, artist, genre, file_path, user_id) VALUES (?, ?, ?, ?, ?, ?)',
        (audio_id, title, artist, genre, file_path, user_id)
    )
    
    conn.commit()
    conn.close()
    
    return jsonify({
        'message': 'Audio uploaded successfully',
        'audio': {
            'id': audio_id,
            'title': title,
            'artist': artist,
            'genre': genre
        }
    }), 201

@app.route('/api/search', methods=['GET'])
def search():
    query = request.args.get('q', '')
    
    if not query:
        return jsonify({'error': 'Query parameter is required'}), 400
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Search in title, artist, and genre
    cursor.execute('''
    SELECT id, title, artist, genre, file_path, created_at
    FROM audio
    WHERE title LIKE ? OR artist LIKE ? OR genre LIKE ?
    ''', (f'%{query}%', f'%{query}%', f'%{query}%'))
    
    results = []
    for row in cursor.fetchall():
        results.append({
            'id': row['id'],
            'title': row['title'],
            'artist': row['artist'],
            'genre': row['genre'],
            'fileUrl': f'/api/audio/{row["id"]}',
            'createdAt': row['created_at']
        })
    
    conn.close()
    
    return jsonify({'results': results})

@app.route('/api/audio/<audio_id>', methods=['GET'])
def get_audio(audio_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT file_path FROM audio WHERE id = ?', (audio_id,))
    audio = cursor.fetchone()
    
    conn.close()
    
    if not audio:
        return jsonify({'error': 'Audio not found'}), 404
    
    return send_from_directory(os.path.dirname(audio['file_path']), os.path.basename(audio['file_path']))

@app.route('/api/contact', methods=['POST'])
def contact():
    data = request.json
    name = data.get('name')
    email = data.get('email')
    message = data.get('message')
    
    if not name or not email or not message:
        return jsonify({'error': 'All fields are required'}), 400
    
    # In a real app, you would send an email or store the contact message
    # For now, we'll just log it
    print(f"Contact form submission: {name} ({email}): {message}")
    
    return jsonify({'message': 'Message sent successfully'})

if __name__ == '__main__':
    app.run(debug=True, port=5000)
