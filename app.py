from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_mail import Mail, Message
from werkzeug.security import generate_password_hash, check_password_hash
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, IntegerField, TextAreaField, FloatField
from wtforms.validators import DataRequired, Email, Length, NumberRange, EqualTo
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
from functools import wraps
from sqlalchemy import func
from flask_migrate import Migrate

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key-here')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///loyalty.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Email configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')

db = SQLAlchemy(app)
migrate = Migrate(app, db)
mail = Mail(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(20))
    password = db.Column(db.String(200), nullable=False)
    points = db.Column(db.Integer, default=0)
    is_admin = db.Column(db.Boolean, default=False)
    active = db.Column(db.Boolean, default=True)
    transactions = db.relationship('Transaction', backref='user', lazy=True)
    rewards = db.relationship('Redemption', backref='user', lazy=True)

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    points_earned = db.Column(db.Integer, nullable=False)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

class Reward(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    points_required = db.Column(db.Integer, nullable=False)
    available = db.Column(db.Boolean, default=True)
    image_url = db.Column(db.String(500))
    stock = db.Column(db.Integer, default=0)
    redemptions = db.relationship('Redemption', backref='reward', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'points_required': self.points_required,
            'available': self.available,
            'image_url': self.image_url,
            'stock': self.stock
        }

class Redemption(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    reward_id = db.Column(db.Integer, db.ForeignKey('reward.id'), nullable=False)
    points_spent = db.Column(db.Integer, nullable=False)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

class SystemConfig(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    points_rate = db.Column(db.Float, default=5.0)  # 5% por defecto
    min_amount = db.Column(db.Float, default=100.0)  # $100 MXN mínimo

# Form Classes
class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Contraseña', validators=[DataRequired()])
    remember = BooleanField('Recordarme')

class RegistrationForm(FlaskForm):
    name = StringField('Nombre', validators=[DataRequired(), Length(min=2, max=80)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    phone = StringField('Teléfono', validators=[DataRequired(), Length(min=10, max=15)])
    password = PasswordField('Contraseña', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirmar Contraseña', validators=[DataRequired(), Length(min=6), EqualTo('password')])
    terms = BooleanField('Acepto los términos y condiciones', validators=[DataRequired()])

class RewardForm(FlaskForm):
    name = StringField('Nombre', validators=[DataRequired()])
    description = TextAreaField('Descripción', validators=[DataRequired()])
    points_required = IntegerField('Puntos Requeridos', validators=[DataRequired(), NumberRange(min=1)])
    available = BooleanField('Disponible')

class ConfigForm(FlaskForm):
    points_rate = FloatField('Tasa de Puntos (%)', validators=[DataRequired(), NumberRange(min=0)])
    min_amount = FloatField('Monto Mínimo', validators=[DataRequired(), NumberRange(min=0)])

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('No tienes permiso para acceder a esta página.', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

def send_notification(user_email, subject, body):
    if app.config['MAIL_USERNAME'] and app.config['MAIL_PASSWORD']:
        try:
            msg = Message(subject,
                        sender=app.config['MAIL_USERNAME'],
                        recipients=[user_email])
            msg.body = body
            mail.send(msg)
            return True
        except Exception as e:
            print(f"Error sending email: {e}")
    return False

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            return redirect(url_for('dashboard'))
        flash('Email o contraseña incorrectos')
    return render_template('login.html', form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        if User.query.filter_by(email=form.email.data).first():
            flash('El email ya está registrado')
            return redirect(url_for('register'))
        
        hashed_password = generate_password_hash(form.password.data)
        user = User(
            name=form.name.data,
            email=form.email.data,
            phone=form.phone.data,
            password=hashed_password,
            points=0
        )
        db.session.add(user)
        db.session.commit()
        
        # Send welcome email
        msg = Message('¡Bienvenido al Sistema de Puntos!',
                    sender=app.config['MAIL_USERNAME'],
                    recipients=[user.email])
        msg.body = f'Hola {user.name},\n\nBienvenido al Sistema de Puntos. ¡Comienza a acumular puntos con tus compras!'
        mail.send(msg)
        
        flash('Registro exitoso. Por favor inicia sesión.')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    transactions = Transaction.query.filter_by(user_id=current_user.id).order_by(Transaction.date.desc()).limit(10).all()
    available_rewards = Reward.query.filter_by(available=True).all()
    total_transactions = Transaction.query.filter_by(user_id=current_user.id).count()
    total_rewards = Redemption.query.filter_by(user_id=current_user.id).count()
    
    return render_template('dashboard.html',
                         transactions=transactions,
                         available_rewards=available_rewards,
                         total_transactions=total_transactions,
                         total_rewards=total_rewards)

@app.route('/rewards')
@login_required
def rewards():
    rewards = Reward.query.filter_by(available=True).all()
    return render_template('rewards.html', rewards=[{
        'id': r.id,
        'name': r.name,
        'description': r.description,
        'points_required': r.points_required,
        'available': r.available,
        'image_url': r.image_url,
        'stock': r.stock
    } for r in rewards])

@app.route('/add-points', methods=['POST'])
@login_required
def add_points():
    amount = float(request.json.get('amount', 0))
    config = SystemConfig.query.first() or SystemConfig()
    
    if amount < config.min_amount:
        return jsonify({'success': False, 'message': f'El monto mínimo es ${config.min_amount} MXN'})

    points_earned = int((amount / 100) * config.points_rate)
    
    transaction = Transaction(user_id=current_user.id,
                            amount=amount,
                            points_earned=points_earned)
    
    current_user.points += points_earned
    db.session.add(transaction)
    db.session.commit()

    send_notification(current_user.email,
                     '¡Has ganado puntos!',
                     f'Has ganado {points_earned} puntos por tu compra de ${amount} MXN')

    return jsonify({
        'success': True,
        'points_earned': points_earned,
        'total_points': current_user.points
    })

@app.route('/redeem/<int:reward_id>', methods=['POST'])
@login_required
def redeem_reward(reward_id):
    reward = Reward.query.get_or_404(reward_id)
    
    if not reward.available:
        return jsonify({'success': False, 'message': 'Esta recompensa no está disponible.'})
    
    if current_user.points < reward.points_required:
        return jsonify({'success': False, 'message': 'No tienes suficientes puntos.'})
    
    redemption = Redemption(user_id=current_user.id,
                          reward_id=reward_id,
                          points_spent=reward.points_required)
    
    current_user.points -= reward.points_required
    db.session.add(redemption)
    db.session.commit()

    send_notification(current_user.email,
                     '¡Recompensa Canjeada!',
                     f'Has canjeado {reward.name} por {reward.points_required} puntos.')

    return jsonify({'success': True})

@app.route('/admin')
@login_required
@admin_required
def admin_panel():
    reward_form = RewardForm()
    config_form = ConfigForm()
    
    # Get statistics
    total_users = User.query.count()
    total_points = db.session.query(db.func.sum(User.points)).scalar() or 0
    total_redemptions = Redemption.query.count()
    total_sales = db.session.query(db.func.sum(Transaction.amount)).scalar() or 0
    
    # Get rewards
    rewards = Reward.query.all()
    
    # Get chart data - last 7 days of points accumulation
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    daily_points = db.session.query(
        func.date(Transaction.date).label('date'),
        func.sum(Transaction.points_earned).label('points')
    ).filter(Transaction.date >= seven_days_ago)\
     .group_by(func.date(Transaction.date))\
     .order_by(func.date(Transaction.date)).all()
    
    dates = []
    points = []
    
    # Process the results
    if daily_points:
        for row in daily_points:
            if hasattr(row.date, 'strftime'):
                dates.append(row.date.strftime('%Y-%m-%d'))
            else:
                dates.append(str(row.date))
            points.append(int(row.points or 0))
    
    # If no data, provide empty arrays
    if not dates:
        current_date = datetime.utcnow()
        for i in range(7):
            day = current_date - timedelta(days=i)
            dates.insert(0, day.strftime('%Y-%m-%d'))
            points.insert(0, 0)
    
    return render_template('admin.html',
                         reward_form=reward_form,
                         config_form=config_form,
                         total_users=total_users,
                         total_points=total_points,
                         total_redemptions=total_redemptions,
                         total_sales=total_sales,
                         rewards=rewards,
                         dates=dates,
                         points=points)

@app.route('/admin/users')
@login_required
@admin_required
def admin_users():
    users = User.query.filter(User.is_admin == False).all()
    return render_template('admin_users.html', users=users)

@app.route('/admin/toggle-user/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def toggle_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.is_admin:
        return jsonify({'success': False, 'message': 'No se puede desactivar un administrador'})
    
    user.active = not user.active
    db.session.commit()
    return jsonify({'success': True, 'active': user.active})

@app.route('/admin/redeem/<int:user_id>/<int:reward_id>', methods=['POST'])
@login_required
@admin_required
def admin_redeem(user_id, reward_id):
    user = User.query.get_or_404(user_id)
    reward = Reward.query.get_or_404(reward_id)
    
    if not user.active:
        return jsonify({'success': False, 'message': 'Usuario inactivo'})
    
    if user.points < reward.points_required:
        return jsonify({'success': False, 'message': 'Puntos insuficientes'})
    
    redemption = Redemption(
        user_id=user.id,
        reward_id=reward.id,
        points_spent=reward.points_required
    )
    
    user.points -= reward.points_required
    db.session.add(redemption)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Recompensa canjeada exitosamente'})

@app.route('/admin/rewards', methods=['POST'])
@login_required
@admin_required
def create_reward():
    data = request.get_json()
    
    if not data:
        return jsonify({'success': False, 'message': 'No se recibieron datos'})
    
    try:
        # Validar datos requeridos
        if not all(key in data for key in ['name', 'description', 'points_required', 'stock']):
            return jsonify({'success': False, 'message': 'Faltan campos requeridos'})
        
        # Convertir y validar puntos requeridos
        try:
            points_required = int(data['points_required'])
            if points_required < 1:
                return jsonify({'success': False, 'message': 'Los puntos requeridos deben ser un número entero positivo'})
        except (ValueError, TypeError):
            return jsonify({'success': False, 'message': 'Los puntos requeridos deben ser un número válido'})
            
        # Convertir y validar stock
        try:
            stock = int(data['stock'])
            if stock < 0:
                return jsonify({'success': False, 'message': 'El stock debe ser un número entero no negativo'})
        except (ValueError, TypeError):
            return jsonify({'success': False, 'message': 'El stock debe ser un número válido'})
        
        reward = Reward(
            name=data['name'],
            description=data['description'],
            points_required=points_required,
            available=data.get('available', True),
            image_url=data.get('image_url', ''),
            stock=stock
        )
        db.session.add(reward)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Recompensa creada exitosamente',
            'reward': reward.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Error al crear la recompensa: {str(e)}'})

@app.route('/admin/rewards', methods=['GET'])
@login_required
@admin_required
def get_rewards():
    rewards = Reward.query.all()
    return jsonify([{
        'id': r.id,
        'name': r.name,
        'description': r.description,
        'points_required': r.points_required,
        'available': r.available,
        'image_url': r.image_url,
        'stock': r.stock
    } for r in rewards])

@app.route('/admin/rewards/<int:reward_id>', methods=['DELETE'])
@login_required
@admin_required
def delete_reward(reward_id):
    try:
        reward = Reward.query.get_or_404(reward_id)
        
        # Verificar si hay redenciones asociadas
        if Redemption.query.filter_by(reward_id=reward_id).first():
            return jsonify({
                'success': False,
                'message': 'No se puede eliminar la recompensa porque ya ha sido canjeada por usuarios'
            })
        
        db.session.delete(reward)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Error al eliminar la recompensa: {str(e)}'
        })

@app.route('/admin/rewards/<int:reward_id>', methods=['PUT'])
@login_required
@admin_required
def update_reward(reward_id):
    data = request.get_json()
    
    if not data:
        return jsonify({'success': False, 'message': 'No se recibieron datos'})
    
    try:
        reward = Reward.query.get_or_404(reward_id)
        
        # Validar datos requeridos
        if not all(key in data for key in ['name', 'description', 'points_required', 'stock']):
            return jsonify({'success': False, 'message': 'Faltan campos requeridos'})
        
        # Convertir y validar puntos requeridos
        try:
            points_required = int(data['points_required'])
            if points_required < 1:
                return jsonify({'success': False, 'message': 'Los puntos requeridos deben ser un número entero positivo'})
        except (ValueError, TypeError):
            return jsonify({'success': False, 'message': 'Los puntos requeridos deben ser un número válido'})
            
        # Convertir y validar stock
        try:
            stock = int(data['stock'])
            if stock < 0:
                return jsonify({'success': False, 'message': 'El stock debe ser un número entero no negativo'})
        except (ValueError, TypeError):
            return jsonify({'success': False, 'message': 'El stock debe ser un número válido'})
        
        # Actualizar datos
        reward.name = data['name']
        reward.description = data['description']
        reward.points_required = points_required
        reward.available = data.get('available', True)
        reward.image_url = data.get('image_url', reward.image_url)
        reward.stock = stock
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Recompensa actualizada exitosamente',
            'reward': reward.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Error al actualizar la recompensa: {str(e)}'})

@app.route('/admin/config', methods=['POST'])
@login_required
@admin_required
def update_config():
    try:
        data = request.get_json()
        if not data or 'points_rate' not in data or 'min_amount' not in data:
            return jsonify({
                'success': False,
                'message': 'Datos incompletos'
            })

        points_rate = float(data['points_rate'])
        min_amount = float(data['min_amount'])

        if points_rate < 0 or min_amount < 0:
            return jsonify({
                'success': False,
                'message': 'Los valores deben ser mayores o iguales a 0'
            })

        config = SystemConfig.query.first()
        if not config:
            config = SystemConfig()
            db.session.add(config)
        
        config.points_rate = points_rate
        config.min_amount = min_amount
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Configuración guardada exitosamente'
        })
    except ValueError:
        return jsonify({
            'success': False,
            'message': 'Los valores deben ser números válidos'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Error al guardar la configuración: {str(e)}'
        })

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        # Limpiar todas las tablas excepto el usuario admin
        db.session.query(Redemption).delete()
        db.session.query(Transaction).delete()
        db.session.query(Reward).delete()
        non_admin_users = User.query.filter_by(is_admin=False).all()
        for user in non_admin_users:
            db.session.delete(user)
        
        db.session.commit()
        
        # Asegurarse de que existe el usuario admin
        admin_user = User.query.filter_by(email='admin@example.com').first()
        if not admin_user:
            admin_user = User(
                name='Administrador',
                email='admin@example.com',
                password=generate_password_hash('admin123'),
                is_admin=True
            )
            db.session.add(admin_user)
            db.session.commit()
        
        print('Base de datos limpiada y usuario admin verificado.')
    
    port = int(os.environ.get('PORT', 5001))
    app.run(host='0.0.0.0', port=port)
