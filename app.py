from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

# Configuración de la base de datos SQLite
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'  # La base de datos se guardará como "users.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Crear un modelo de Usuario para la base de datos
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)

# Crear la base de datos si no existe
with app.app_context():
    db.create_all()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    
    # Buscar el usuario en la base de datos
    user = User.query.filter_by(username=username).first()

    if user and check_password_hash(user.password, password):
        return redirect(url_for('welcome', username=username))  # Redirigir al usuario a una página de bienvenida
    else:
        return "Credenciales incorrectas"

@app.route('/register', methods=['POST'])
def register():
    username = request.form['username']
    email = request.form['email']
    password = request.form['password']

    # Verificar si el usuario ya existe
    existing_user = User.query.filter_by(username=username).first()
    if existing_user:
        return "El usuario ya existe"

    # Crear un nuevo usuario y almacenar la contraseña de forma segura
    hashed_password = generate_password_hash(password, method='pbkdf2:sha256')

    new_user = User(username=username, email=email, password=hashed_password)
    db.session.add(new_user)
    db.session.commit()
    
    return "Cuenta creada exitosamente"

@app.route('/welcome/<username>')
def welcome(username):
    return f"¡Bienvenido, {username}!"

if __name__ == '__main__':
    app.run(debug=True)
