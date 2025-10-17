from flask import Flask, render_template, request, jsonify
from datetime import datetime
import sqlite3
import os

app = Flask(__name__)

DATABASE = 'journal.db'

def get_db():
    db = sqlite3.connect(DATABASE)
    db.row_factory = sqlite3.Row
    return db

def init_db():
    if not os.path.exists(DATABASE):
        db = get_db()
        db.execute('''
            CREATE TABLE entries (
                id TEXT PRIMARY KEY,
                timestamp TEXT,
                author TEXT,
                title TEXT,
                entry TEXT,
                hearts INTEGER DEFAULT 0,
                likes INTEGER DEFAULT 0
            )
        ''')
        db.execute('''
            CREATE TABLE comments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entry_id TEXT,
                author TEXT,
                comment TEXT,
                timestamp TEXT
            )
        ''')
        db.commit()
        db.close()

init_db()

@app.route('/')
def index():
    db = get_db()
    entries = db.execute('SELECT * FROM entries ORDER BY timestamp DESC').fetchall()
    db.close()
    return render_template('index.html', entries=entries)

@app.route('/add_entry', methods=['POST'])
def add_entry():
    data = request.json
    entry_id = f"ENTRY-{int(datetime.now().timestamp() * 1000)}"
    timestamp = datetime.now().isoformat()
    
    db = get_db()
    db.execute(
        'INSERT INTO entries (id, timestamp, author, title, entry, hearts, likes) VALUES (?, ?, ?, ?, ?, 0, 0)',
        (entry_id, timestamp, data['author'], data['title'], data['entry'])
    )
    db.commit()
    db.close()
    
    return jsonify({'success': True, 'id': entry_id})

@app.route('/get_entries')
def get_entries():
    db = get_db()
    entries = db.execute('SELECT * FROM entries ORDER BY timestamp DESC').fetchall()
    db.close()
    return jsonify([dict(e) for e in entries])

@app.route('/react/<entry_id>/<reaction_type>', methods=['POST'])
def react(entry_id, reaction_type):
    db = get_db()
    if reaction_type == 'hearts':
        db.execute('UPDATE entries SET hearts = hearts + 1 WHERE id = ?', (entry_id,))
    elif reaction_type == 'likes':
        db.execute('UPDATE entries SET likes = likes + 1 WHERE id = ?', (entry_id,))
    db.commit()
    entry = db.execute('SELECT hearts, likes FROM entries WHERE id = ?', (entry_id,)).fetchone()
    db.close()
    return jsonify({'success': True, 'reactions': dict(entry)})

@app.route('/add_comment', methods=['POST'])
def add_comment():
    data = request.json
    timestamp = datetime.now().isoformat()
    
    db = get_db()
    db.execute(
        'INSERT INTO comments (entry_id, author, comment, timestamp) VALUES (?, ?, ?, ?)',
        (data['entry_id'], data['author'], data['comment'], timestamp)
    )
    db.commit()
    db.close()
    
    return jsonify({'success': True})

@app.route('/get_comments/<entry_id>')
def get_comments(entry_id):
    db = get_db()
    comments = db.execute(
        'SELECT * FROM comments WHERE entry_id = ? ORDER BY timestamp ASC',
        (entry_id,)
    ).fetchall()
    db.close()
    return jsonify([dict(c) for c in comments])

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
