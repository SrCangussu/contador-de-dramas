
import os
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret')
# Use DATABASE_URL if present (e.g., Postgres on Render/Neon/Supabase), otherwise SQLite local
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///dramas.db')
# Render/Heroku style postgres:// to postgresql:// fix
if DATABASE_URL.startswith('postgres://'):
    DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Models
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    nickname = db.Column(db.String(80), nullable=False, unique=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    dramas = db.relationship('Drama', backref='author', lazy=True)

class Drama(db.Model):
    __tablename__ = 'dramas'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    intensity = db.Column(db.Integer, nullable=False)  # 0..10
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def emoji(self):
        return intensity_to_emoji(self.intensity)

# Jinja filter for emoji
@app.template_filter('emoji')
def emoji_filter(value):
    return intensity_to_emoji(value)

# Helpers
EMOJIS = {
    0: '😌', 1: '🙂', 2: '😊', 3: '😯', 4: '😕',
    5: '😬', 6: '😟', 7: '😫', 8: '😤', 9: '😭', 10: '💥'
}

def intensity_to_emoji(i):
    try:
        i = int(i)
    except Exception:
        i = 0
    i = max(0, min(10, i))
    return EMOJIS.get(i, '🙂')

# Routes
@app.route('/')
def index():
    total_users = db.session.query(func.count(User.id)).scalar() or 0
    total_dramas = db.session.query(func.count(Drama.id)).scalar() or 0
    avg_intensity = db.session.query(func.avg(Drama.intensity)).scalar()
    recent = Drama.query.order_by(Drama.created_at.desc()).limit(5).all()
    return render_template('index.html', total_users=total_users, total_dramas=total_dramas,
                           avg_intensity=avg_intensity, recent=recent)

# Users CRUD
@app.route('/usuarios')
def users_list():
    q = request.args.get('q', '').strip()
    users = User.query
    if q:
        users = users.filter((User.name.ilike(f'%{q}%')) | (User.nickname.ilike(f'%{q}%')))
    users = users.order_by(User.created_at.desc()).all()
    return render_template('users/list.html', users=users, q=q)

@app.route('/usuarios/novo', methods=['GET', 'POST'])
def users_create():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        nickname = request.form.get('nickname', '').strip()
        if not name or not nickname:
            flash('Nome e Apelido são obrigatórios.', 'warning')
            return redirect(url_for('users_create'))
        u = User(name=name, nickname=nickname)
        db.session.add(u)
        try:
            db.session.commit()
            flash('Usuário criado com sucesso!', 'success')
            return redirect(url_for('users_list'))
        except Exception as e:
            db.session.rollback()
            flash('Erro ao criar usuário. Verifique se o apelido é único.', 'danger')
    return render_template('users/create.html')

@app.route('/usuarios/<int:user_id>/editar', methods=['GET', 'POST'])
def users_edit(user_id):
    u = User.query.get_or_404(user_id)
    if request.method == 'POST':
        u.name = request.form.get('name', '').strip()
        u.nickname = request.form.get('nickname', '').strip()
        if not u.name or not u.nickname:
            flash('Nome e Apelido são obrigatórios.', 'warning')
            return redirect(url_for('users_edit', user_id=user_id))
        try:
            db.session.commit()
            flash('Usuário atualizado!', 'success')
            return redirect(url_for('users_list'))
        except Exception:
            db.session.rollback()
            flash('Erro ao atualizar usuário. Verifique se o apelido é único.', 'danger')
    return render_template('users/edit.html', u=u)

@app.route('/usuarios/<int:user_id>/excluir', methods=['POST'])
def users_delete(user_id):
    u = User.query.get_or_404(user_id)
    try:
        db.session.delete(u)
        db.session.commit()
        flash('Usuário excluído.', 'info')
    except Exception:
        db.session.rollback()
        flash('Erro ao excluir usuário.', 'danger')
    return redirect(url_for('users_list'))

# Dramas CRUD
@app.route('/dramas')
def dramas_list():
    q = request.args.get('q', '').strip()
    uid = request.args.get('user_id')
    dramas = Drama.query
    if q:
        dramas = dramas.filter((Drama.title.ilike(f'%{q}%')) | (Drama.description.ilike(f'%{q}%')))
    if uid:
        dramas = dramas.filter(Drama.user_id == uid)
    dramas = dramas.order_by(Drama.created_at.desc()).all()
    users = User.query.order_by(User.nickname.asc()).all()
    return render_template('dramas/list.html', dramas=dramas, users=users, q=q, uid=uid)

@app.route('/dramas/novo', methods=['GET', 'POST'])
def dramas_create():
    users = User.query.order_by(User.nickname.asc()).all()
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        intensity = request.form.get('intensity', 0)
        try:
            intensity = int(intensity)
        except Exception:
            intensity = 0
        intensity = max(0, min(10, intensity))
        user_id = request.form.get('user_id') or None
        if not title or not description:
            flash('Drama e descrição são obrigatórios.', 'warning')
            return redirect(url_for('dramas_create'))
        d = Drama(title=title, description=description, intensity=intensity, user_id=user_id)
        db.session.add(d)
        db.session.commit()
        flash('Drama registrado 👌', 'success')
        return redirect(url_for('dramas_list'))
    return render_template('dramas/create.html', users=users)

@app.route('/dramas/<int:drama_id>/editar', methods=['GET', 'POST'])
def dramas_edit(drama_id):
    d = Drama.query.get_or_404(drama_id)
    users = User.query.order_by(User.nickname.asc()).all()
    if request.method == 'POST':
        d.title = request.form.get('title', '').strip()
        d.description = request.form.get('description', '').strip()
        intensity = request.form.get('intensity', 0)
        try:
            d.intensity = max(0, min(10, int(intensity)))
        except Exception:
            d.intensity = 0
        user_id = request.form.get('user_id') or None
        d.user_id = int(user_id) if user_id else None
        if not d.title or not d.description:
            flash('Drama e descrição são obrigatórios.', 'warning')
            return redirect(url_for('dramas_edit', drama_id=drama_id))
        db.session.commit()
        flash('Drama atualizado!', 'success')
        return redirect(url_for('dramas_list'))
    return render_template('dramas/edit.html', d=d, users=users)

@app.route('/dramas/<int:drama_id>/excluir', methods=['POST'])
def dramas_delete(drama_id):
    d = Drama.query.get_or_404(drama_id)
    try:
        db.session.delete(d)
        db.session.commit()
        flash('Drama excluído.', 'info')
    except Exception:
        db.session.rollback()
        flash('Erro ao excluir drama.', 'danger')
    return redirect(url_for('dramas_list'))

# Init DB on first run
@app.before_first_request
def init_db():
    db.create_all()

if __name__ == '__main__':
    port = int(os.getenv('PORT', '5000'))
    app.run(host='0.0.0.0', port=port, debug=True)
