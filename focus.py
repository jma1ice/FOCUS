import os, json, sqlite3
from datetime import datetime, timedelta
from flask import Flask, render_template, request, jsonify, redirect, url_for, g

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key-change-in-production')

DATABASE = os.environ.get('DATABASE_PATH', 'focus.db')

def format_date(date_string, format_string='%m/%d/%Y'):
    if not date_string:
        return None
    try:
        if 'T' in date_string:
            dt = datetime.fromisoformat(date_string.replace('Z', ''))
        else:
            try:
                dt = datetime.strptime(date_string, '%Y-%m-%d %H:%M:%S')
            except:
                dt = datetime.strptime(date_string, '%Y-%m-%d')
        return dt.strftime(format_string)
    except:
        return date_string

def format_datetime(date_string, format_string='%m/%d %H:%M'):
    return format_date(date_string, format_string)

app.jinja_env.filters['strftime'] = format_date
app.jinja_env.filters['format_datetime'] = format_datetime

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
    return g.db

def close_db(error):
    db = g.pop('db', None)
    if db is not None:
        db.close()

@app.teardown_appcontext
def close_db_on_teardown(error):
    close_db(error)

def init_db():
    db = sqlite3.connect(DATABASE)
    db.executescript('''
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            color TEXT DEFAULT '#6366f1',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_active BOOLEAN DEFAULT 1
        );
        
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            priority TEXT DEFAULT 'medium',
            energy_level TEXT DEFAULT 'medium',
            estimated_time INTEGER,
            is_completed BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP,
            due_date TIMESTAMP,
            project_id INTEGER,
            FOREIGN KEY (project_id) REFERENCES projects (id) ON DELETE SET NULL
        );
        
        CREATE TABLE IF NOT EXISTS ideas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            tags TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            project_id INTEGER,
            FOREIGN KEY (project_id) REFERENCES projects (id) ON DELETE SET NULL
        );
        
        CREATE TABLE IF NOT EXISTS backburner_links (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT NOT NULL,
            title TEXT,
            description TEXT,
            tags TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            project_id INTEGER,
            FOREIGN KEY (project_id) REFERENCES projects (id) ON DELETE SET NULL
        );
        
        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            content TEXT NOT NULL,
            tags TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            project_id INTEGER,
            FOREIGN KEY (project_id) REFERENCES projects (id) ON DELETE SET NULL
        );
        
        CREATE INDEX IF NOT EXISTS idx_tasks_project ON tasks(project_id);
        CREATE INDEX IF NOT EXISTS idx_tasks_completed ON tasks(is_completed);
        CREATE INDEX IF NOT EXISTS idx_tasks_priority ON tasks(priority);
        CREATE INDEX IF NOT EXISTS idx_ideas_project ON ideas(project_id);
        CREATE INDEX IF NOT EXISTS idx_links_project ON backburner_links(project_id);
        CREATE INDEX IF NOT EXISTS idx_notes_project ON notes(project_id);
    ''')
    
    cursor = db.execute('SELECT COUNT(*) FROM projects')
    if cursor.fetchone()[0] == 0:
        db.execute('''
            INSERT INTO projects (name, description) 
            VALUES (?, ?)
        ''', ('Personal', 'General personal tasks and ideas'))
    
    db.commit()
    db.close()

def dict_from_row(row):
    return dict(row) if row else None

def get_project_with_counts(project_id):
    db = get_db()
    
    project = db.execute(
        'SELECT * FROM projects WHERE id = ? AND is_active = 1',
        (project_id,)
    ).fetchone()
    
    if not project:
        return None
    
    project = dict(project)
    
    task_count = db.execute(
        'SELECT COUNT(*) FROM tasks WHERE project_id = ? AND is_completed = 0',
        (project_id,)
    ).fetchone()[0]
    
    completed_count = db.execute(
        'SELECT COUNT(*) FROM tasks WHERE project_id = ? AND is_completed = 1',
        (project_id,)
    ).fetchone()[0]
    
    idea_count = db.execute(
        'SELECT COUNT(*) FROM ideas WHERE project_id = ?',
        (project_id,)
    ).fetchone()[0]
    
    note_count = db.execute(
        'SELECT COUNT(*) FROM notes WHERE project_id = ?',
        (project_id,)
    ).fetchone()[0]
    
    project['task_count'] = task_count
    project['completed_count'] = completed_count
    project['idea_count'] = idea_count
    project['note_count'] = note_count
    
    return project

@app.route('/')
def index():
    db = get_db()
    
    projects = []
    project_rows = db.execute(
        'SELECT * FROM projects WHERE is_active = 1 ORDER BY created_at DESC'
    ).fetchall()
    
    for row in project_rows:
        project = dict(row)
        
        task_count = db.execute(
            'SELECT COUNT(*) FROM tasks WHERE project_id = ? AND is_completed = 0',
            (project['id'],)
        ).fetchone()[0]
        
        idea_count = db.execute(
            'SELECT COUNT(*) FROM ideas WHERE project_id = ?',
            (project['id'],)
        ).fetchone()[0]
        
        note_count = db.execute(
            'SELECT COUNT(*) FROM notes WHERE project_id = ?',
            (project['id'],)
        ).fetchone()[0]
        
        project['task_count'] = task_count
        project['idea_count'] = idea_count
        project['note_count'] = note_count
        projects.append(project)
    
    today = datetime.now().strftime('%Y-%m-%d')
    focus_tasks = db.execute('''
        SELECT t.*, p.name as project_name
        FROM tasks t
        LEFT JOIN projects p ON t.project_id = p.id
        WHERE t.is_completed = 0
        AND (t.priority IN ('high', 'urgent') OR DATE(t.due_date) = ?)
        ORDER BY 
            CASE t.priority 
                WHEN 'urgent' THEN 4 
                WHEN 'high' THEN 3 
                WHEN 'medium' THEN 2 
                ELSE 1 
            END DESC, 
            t.due_date ASC
        LIMIT 5
    ''', (today,)).fetchall()
    
    focus_tasks = [dict(row) for row in focus_tasks]
    
    recent_ideas = db.execute('''
        SELECT i.*, p.name as project_name
        FROM ideas i
        LEFT JOIN projects p ON i.project_id = p.id
        ORDER BY i.created_at DESC
        LIMIT 3
    ''').fetchall()
    
    recent_ideas = [dict(row) for row in recent_ideas]

    recent_notes = db.execute('''
        SELECT n.*, p.name as project_name
        FROM notes n
        LEFT JOIN projects p ON n.project_id = p.id
        ORDER BY n.updated_at DESC
        LIMIT 3
    ''').fetchall()

    recent_notes = [dict(row) for row in recent_notes]
    
    return render_template('index.html', 
                         projects=projects, 
                         focus_tasks=focus_tasks,
                         recent_ideas=recent_ideas,
                         recent_notes=recent_notes)

@app.route('/api/tasks/quick-add', methods=['POST'])
def quick_add_task():
    db = get_db()
    data = request.get_json()
    
    db.execute('''
        INSERT INTO tasks (title, description, priority, energy_level, estimated_time, due_date, project_id)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (
        data['title'],
        data.get('description', ''),
        data.get('priority', 'medium'),
        data.get('energy_level', 'medium'),
        data.get('estimated_time', ''),
        data.get('due_date', ''),
        data.get('project_id') if data.get('project_id') else None
    ))
    db.commit()
    
    return jsonify({'success': True})

@app.route('/api/tasks/<int:task_id>/complete', methods=['POST'])
def complete_task(task_id):
    db = get_db()
    
    task = db.execute('SELECT id FROM tasks WHERE id = ?', (task_id,)).fetchone()
    if not task:
        return jsonify({'success': False, 'error': 'Task not found'}), 404
    
    db.execute('''
        UPDATE tasks 
        SET is_completed = 1, completed_at = CURRENT_TIMESTAMP
        WHERE id = ?
    ''', (task_id,))
    db.commit()
    
    return jsonify({'success': True})

@app.route('/api/tasks/<int:task_id>/uncomplete', methods=['POST'])
def uncomplete_task(task_id):
    db = get_db()
    
    task = db.execute('SELECT id FROM tasks WHERE id = ?', (task_id,)).fetchone()
    if not task:
        return jsonify({'success': False, 'error': 'Task not found'}), 404
    
    db.execute('''
        UPDATE tasks 
        SET is_completed = 0, completed_at = NULL
        WHERE id = ?
    ''', (task_id,))
    db.commit()
    
    return jsonify({'success': True})

@app.route('/api/ideas/quick-add', methods=['POST'])
def quick_add_idea():
    db = get_db()
    data = request.get_json()
    
    db.execute('''
        INSERT INTO ideas (title, description, project_id)
        VALUES (?, ?, ?)
    ''', (
        data['title'],
        data.get('description', ''),
        data.get('project_id') if data.get('project_id') else None
    ))
    db.commit()
    
    return jsonify({'success': True})

@app.route('/api/links/quick-add', methods=['POST'])
def quick_add_link():
    db = get_db()
    data = request.get_json()
    
    db.execute('''
        INSERT INTO backburner_links (url, title, description, project_id)
        VALUES (?, ?, ?, ?)
    ''', (
        data['url'],
        data.get('title', ''),
        data.get('description', ''),
        data.get('project_id') if data.get('project_id') else None
    ))
    db.commit()
    
    return jsonify({'success': True})

@app.route('/api/notes/quick-add', methods=['POST'])
def quick_add_note():
    db = get_db()
    data = request.get_json()
    
    db.execute('''
        INSERT INTO notes (title, content, project_id)
        VALUES (?, ?, ?)
    ''', (
        data.get('title', ''),
        data['content'],
        data.get('project_id') if data.get('project_id') else None
    ))
    db.commit()
    
    return jsonify({'success': True})

@app.route('/api/tasks/<int:task_id>/update', methods=['PUT'])
def update_task(task_id):
    db = get_db()
    data = request.get_json()
    
    task = db.execute('SELECT id FROM tasks WHERE id = ?', (task_id,)).fetchone()
    if not task:
        return jsonify({'success': False, 'error': 'Task not found'}), 404
    
    db.execute('''
        UPDATE tasks 
        SET title = ?, description = ?, priority = ?, energy_level = ?, 
            estimated_time = ?, due_date = ?
        WHERE id = ?
    ''', (
        data['title'],
        data.get('description', ''),
        data.get('priority', 'medium'),
        data.get('energy_level', 'medium'),
        data.get('estimated_time'),
        data.get('due_date'),
        task_id
    ))
    db.commit()
    
    return jsonify({'success': True})

@app.route('/api/ideas/<int:idea_id>/update', methods=['PUT'])
def update_idea(idea_id):
    db = get_db()
    data = request.get_json()
    
    idea = db.execute('SELECT id FROM ideas WHERE id = ?', (idea_id,)).fetchone()
    if not idea:
        return jsonify({'success': False, 'error': 'Idea not found'}), 404
    
    db.execute('''
        UPDATE ideas 
        SET title = ?, description = ?
        WHERE id = ?
    ''', (
        data['title'],
        data.get('description', ''),
        idea_id
    ))
    db.commit()
    
    return jsonify({'success': True})

@app.route('/api/notes/<int:note_id>/update', methods=['PUT'])
def update_note(note_id):
    db = get_db()
    data = request.get_json()
    
    note = db.execute('SELECT id FROM notes WHERE id = ?', (note_id,)).fetchone()
    if not note:
        return jsonify({'success': False, 'error': 'Note not found'}), 404
    
    db.execute('''
        UPDATE notes 
        SET title = ?, content = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    ''', (
        data.get('title', ''),
        data['content'],
        note_id
    ))
    db.commit()
    
    return jsonify({'success': True})

@app.route('/api/links/<int:link_id>/update', methods=['PUT'])
def update_link(link_id):
    db = get_db()
    data = request.get_json()
    
    link = db.execute('SELECT id FROM backburner_links WHERE id = ?', (link_id,)).fetchone()
    if not link:
        return jsonify({'success': False, 'error': 'Link not found'}), 404
    
    db.execute('''
        UPDATE backburner_links 
        SET url = ?, title = ?, description = ?
        WHERE id = ?
    ''', (
        data['url'],
        data.get('title', ''),
        data.get('description', ''),
        link_id
    ))
    db.commit()
    
    return jsonify({'success': True})

@app.route('/api/tasks/<int:task_id>/delete', methods=['DELETE'])
def delete_task(task_id):
    db = get_db()
    
    task = db.execute('SELECT id FROM tasks WHERE id = ?', (task_id,)).fetchone()
    if not task:
        return jsonify({'success': False, 'error': 'Task not found'}), 404
    
    db.execute('DELETE FROM tasks WHERE id = ?', (task_id,))
    db.commit()
    
    return jsonify({'success': True, 'message': 'Task deleted successfully'})

@app.route('/api/ideas/<int:idea_id>/delete', methods=['DELETE'])
def delete_idea(idea_id):
    db = get_db()
    
    idea = db.execute('SELECT id FROM ideas WHERE id = ?', (idea_id,)).fetchone()
    if not idea:
        return jsonify({'success': False, 'error': 'Idea not found'}), 404
    
    db.execute('DELETE FROM ideas WHERE id = ?', (idea_id,))
    db.commit()
    
    return jsonify({'success': True, 'message': 'Idea deleted successfully'})

@app.route('/api/notes/<int:note_id>/delete', methods=['DELETE'])
def delete_note(note_id):
    db = get_db()
    
    note = db.execute('SELECT id FROM notes WHERE id = ?', (note_id,)).fetchone()
    if not note:
        return jsonify({'success': False, 'error': 'Note not found'}), 404
    
    db.execute('DELETE FROM notes WHERE id = ?', (note_id,))
    db.commit()
    
    return jsonify({'success': True, 'message': 'Note deleted successfully'})

@app.route('/api/links/<int:link_id>/delete', methods=['DELETE'])
def delete_link(link_id):
    db = get_db()
    
    link = db.execute('SELECT id FROM backburner_links WHERE id = ?', (link_id,)).fetchone()
    if not link:
        return jsonify({'success': False, 'error': 'Link not found'}), 404
    
    db.execute('DELETE FROM backburner_links WHERE id = ?', (link_id,))
    db.commit()
    
    return jsonify({'success': True, 'message': 'Link deleted successfully'})

@app.route('/api/projects', methods=['POST'])
def create_project():
    db = get_db()
    data = request.get_json()
    
    db.execute('''
        INSERT INTO projects (name, description, color)
        VALUES (?, ?, ?)
    ''', (
        data['name'],
        data.get('description', ''),
        data.get('color', '#6366f1')
    ))
    db.commit()
    
    return jsonify({'success': True})

@app.route('/api/projects/<int:project_id>/update', methods=['PUT'])
def update_project(project_id):
    db = get_db()
    data = request.get_json()
    
    project = db.execute(
        'SELECT * FROM projects WHERE id = ? AND is_active = 1',
        (project_id,)
    ).fetchone()
    
    if not project:
        return jsonify({'success': False, 'error': 'Project not found'}), 404
    
    db.execute('''
        UPDATE projects 
        SET name = ?, description = ?, color = ?
        WHERE id = ?
    ''', (
        data['name'],
        data.get('description', ''),
        data.get('color', '#3b82f6'),
        project_id
    ))
    db.commit()
    
    return jsonify({'success': True, 'message': 'Project updated successfully'})

@app.route('/project/<int:project_id>')
def project_detail(project_id):
    db = get_db()
    
    project = db.execute(
        'SELECT * FROM projects WHERE id = ? AND is_active = 1',
        (project_id,)
    ).fetchone()
    
    if not project:
        return "Project not found", 404
    
    project = dict(project)
    
    tasks = db.execute('''
        SELECT * FROM tasks 
        WHERE project_id = ? AND is_completed = 0
        ORDER BY 
            CASE priority 
                WHEN 'urgent' THEN 4 
                WHEN 'high' THEN 3 
                WHEN 'medium' THEN 2 
                ELSE 1 
            END DESC, 
            created_at ASC
    ''', (project_id,)).fetchall()
    tasks = [dict(row) for row in tasks]
    
    completed_tasks = db.execute('''
        SELECT * FROM tasks 
        WHERE project_id = ? AND is_completed = 1
        ORDER BY completed_at DESC
        LIMIT 10
    ''', (project_id,)).fetchall()
    completed_tasks = [dict(row) for row in completed_tasks]
    
    ideas = db.execute('''
        SELECT * FROM ideas 
        WHERE project_id = ?
        ORDER BY created_at DESC
    ''', (project_id,)).fetchall()
    ideas = [dict(row) for row in ideas]
    
    links = db.execute('''
        SELECT * FROM backburner_links 
        WHERE project_id = ?
        ORDER BY created_at DESC
    ''', (project_id,)).fetchall()
    links = [dict(row) for row in links]
    
    notes = db.execute('''
        SELECT * FROM notes 
        WHERE project_id = ?
        ORDER BY updated_at DESC
    ''', (project_id,)).fetchall()
    notes = [dict(row) for row in notes]
    
    return render_template('project.html',
                         project=project,
                         tasks=tasks,
                         completed_tasks=completed_tasks,
                         ideas=ideas,
                         links=links,
                         notes=notes)

@app.route('/quick-capture')
def quick_capture():
    db = get_db()
    projects = db.execute(
        'SELECT * FROM projects WHERE is_active = 1 ORDER BY name'
    ).fetchall()
    projects = [dict(row) for row in projects]
    return render_template('quick_capture.html', projects=projects)

@app.route('/api/projects', methods=['GET'])
def get_projects():
    db = get_db()
    projects = db.execute(
        'SELECT * FROM projects WHERE is_active = 1 ORDER BY name'
    ).fetchall()
    
    return jsonify([{
        'id': project['id'],
        'name': project['name'],
        'description': project['description'],
        'color': project['color']
    } for project in projects])

@app.route('/api/projects/<int:project_id>/delete', methods=['DELETE'])
def delete_project(project_id):
    db = get_db()
    
    project = db.execute(
        'SELECT * FROM projects WHERE id = ? AND is_active = 1',
        (project_id,)
    ).fetchone()
    
    if not project:
        return jsonify({'success': False, 'error': 'Project not found'}), 404
    
    db.execute('''
        UPDATE projects 
        SET is_active = 0 
        WHERE id = ?
    ''', (project_id,))
    
    db.execute('UPDATE tasks SET project_id = NULL WHERE project_id = ?', (project_id,))
    db.execute('UPDATE ideas SET project_id = NULL WHERE project_id = ?', (project_id,))
    db.execute('UPDATE notes SET project_id = NULL WHERE project_id = ?', (project_id,))
    db.execute('UPDATE backburner_links SET project_id = NULL WHERE project_id = ?', (project_id,))
    
    db.commit()
    
    return jsonify({'success': True, 'message': 'Project deleted successfully'})

@app.route('/api/smart-suggestions')
def smart_suggestions():
    db = get_db()
    
    now = datetime.now()
    hour = now.hour
    
    if 6 <= hour < 12:
        energy_filter = ('high', 'medium')
    elif 12 <= hour < 17:
        energy_filter = ('medium', 'high', 'low')
    else:
        energy_filter = ('low', 'medium')
    
    placeholders = ','.join('?' * len(energy_filter))
    
    suggestions = db.execute(f'''
        SELECT t.*, p.name as project_name
        FROM tasks t
        LEFT JOIN projects p ON t.project_id = p.id
        WHERE t.is_completed = 0
        AND t.energy_level IN ({placeholders})
        ORDER BY 
            CASE t.priority 
                WHEN 'urgent' THEN 4 
                WHEN 'high' THEN 3 
                WHEN 'medium' THEN 2 
                ELSE 1 
            END DESC
        LIMIT 3
    ''', energy_filter).fetchall()
    
    return jsonify([{
        'id': task['id'],
        'title': task['title'],
        'priority': task['priority'],
        'energy_level': task['energy_level'],
        'project_name': task['project_name']
    } for task in suggestions])

if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=36287)