import os
import sqlite3
from flask import Flask, render_template, request, jsonify

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_DIR = os.path.join(BASE_DIR, 'templates')

app = Flask(__name__, template_folder=TEMPLATE_DIR)
DB_FILE = os.path.join(BASE_DIR, "silentink.db")

def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS stories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            emotion TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            react_hurt INTEGER DEFAULT 0,
            react_felt INTEGER DEFAULT 0,
            react_intense INTEGER DEFAULT 0,
            react_stayed INTEGER DEFAULT 0
        )
    ''')
    conn.commit()
    conn.close()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/stories', methods=['GET'])
def get_stories():
    try:
        conn = get_db_connection()
        rows = conn.execute('SELECT * FROM stories ORDER BY created_at DESC').fetchall()
        conn.close()
        
        stories = []
        for row in rows:
            stories.append({
                "id": row['id'],
                "title": row['title'],
                "content": row['content'],
                "emotion": row['emotion'],
                "created_at": row['created_at'],
                "reactions": {
                    "hurt": row['react_hurt'],
                    "felt": row['react_felt'],
                    "intense": row['react_intense'],
                    "stayed": row['react_stayed']
                }
            })
        return jsonify(stories), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/stories', methods=['POST'])
def create_story():
    data = request.get_json(silent=True) or {}
    title = data.get('title', '').strip() or 'Untitled'
    content = data.get('content', '').strip()
    emotion = data.get('emotion', 'This Hurt').strip()
    
    if not content:
        return jsonify({"error": "Content cannot be empty"}), 400
        
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO stories (title, content, emotion) VALUES (?, ?, ?)', 
            (title, content, emotion)
        )
        conn.commit()
        new_id = cursor.lastrowid
        conn.close()
        
        return jsonify({
            "message": "Published successfully!", 
            "story": {
                "id": new_id, "title": title, "content": content, "emotion": emotion,
                "reactions": {"hurt": 0, "felt": 0, "intense": 0, "stayed": 0}
            }
        }), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/stories/<int:story_id>/react', methods=['POST'])
def react_story(story_id):
    data = request.get_json(silent=True) or {}
    reaction_type = data.get('reaction')
    
    valid_columns = {
        'hurt': 'react_hurt',
        'felt': 'react_felt',
        'intense': 'react_intense',
        'stayed': 'react_stayed'
    }
    
    if reaction_type not in valid_columns:
        return jsonify({"error": "Invalid reaction"}), 400
        
    column = valid_columns[reaction_type]
    
    try:
        conn = get_db_connection()
        conn.execute(f"UPDATE stories SET {column} = {column} + 1 WHERE id = ?", (story_id,))
        conn.commit()
        
        row = conn.execute(f"SELECT react_hurt, react_felt, react_intense, react_stayed FROM stories WHERE id = ?", (story_id,)).fetchone()
        conn.close()
        
        if row:
            return jsonify({
                "hurt": row['react_hurt'],
                "felt": row['react_felt'],
                "intense": row['react_intense'],
                "stayed": row['react_stayed']
            }), 200
        return jsonify({"error": "Story not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    init_db()
    os.makedirs(TEMPLATE_DIR, exist_ok=True)
    app.run(debug=True, port=5000)
