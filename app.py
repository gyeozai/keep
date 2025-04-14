from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import pytz

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///diary.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# 设置时区为 GTC+8
tz = pytz.timezone('Asia/Shanghai')

class DiaryEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    date = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(tz))
    position = db.Column(db.Integer, nullable=False, default=0)

with app.app_context():
    db.create_all()

@app.route('/')
def index():
    entries = DiaryEntry.query.order_by(DiaryEntry.position.desc()).all()
    return render_template('index.html', entries=entries)

@app.route('/add', methods=['POST'])
def add_entry():
    content = request.form['content']
    lines = content.split('\n')
    title = lines[0]
    content = '\n'.join(lines[1:])
    # 获取当前最大position值
    max_position = db.session.query(db.func.max(DiaryEntry.position)).scalar() or 0
    entry = DiaryEntry(title=title, content=content, date=datetime.now(tz), position=max_position + 1)
    db.session.add(entry)
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/edit/<int:id>', methods=['POST'])
def edit_entry(id):
    entry = DiaryEntry.query.get_or_404(id)
    content = request.form['content']
    lines = content.split('\n')
    entry.title = lines[0]
    entry.content = '\n'.join(lines[1:])
    entry.date = datetime.now(tz)
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/delete/<int:id>')
def delete_entry(id):
    entry = DiaryEntry.query.get_or_404(id)
    db.session.delete(entry)
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/batch_delete', methods=['POST'])
def batch_delete():
    try:
        data = request.get_json()
        ids = data.get('ids', [])
        
        if not ids:
            return jsonify({'error': 'No IDs provided'}), 400
            
        entries = DiaryEntry.query.filter(DiaryEntry.id.in_(ids)).all()
        for entry in entries:
            db.session.delete(entry)
        
        db.session.commit()
        return jsonify({'success': True}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/update_positions', methods=['POST'])
def update_positions():
    try:
        data = request.get_json()
        positions = data.get('positions', [])
        
        for pos_data in positions:
            entry = DiaryEntry.query.get(pos_data['id'])
            if entry:
                entry.position = pos_data['position']
        
        db.session.commit()
        return jsonify({'success': True}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True) 