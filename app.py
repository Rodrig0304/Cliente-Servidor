import os
from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Configuración de la base de datos SQLite
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'  # La base de datos se guardará como "users.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.path.join(os.getcwd(), 'uploads')  # Carpeta donde se almacenarán los PDFs
app.config['ALLOWED_EXTENSIONS'] = {'pdf'}  # Permitir solo archivos PDF
app.config['SECRET_KEY'] = 'mi_clave_secreta'  # Necesaria para el uso de flash
db = SQLAlchemy(app)

# Crear un modelo de Usuario para la base de datos
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)

# Crear un modelo para los PDFs
class PDF(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(150), unique=True, nullable=False)

# Crear la base de datos si no existe
with app.app_context():
    db.create_all()

# Ruta principal (inicio de sesión)
@app.route('/')
def home():
    return render_template('index.html')

# Ruta para iniciar sesión
@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    
    # Buscar el usuario en la base de datos
    user = User.query.filter_by(username=username).first()

    if user and check_password_hash(user.password, password):
        return redirect(url_for('welcome', username=username))  # Redirigir al usuario a la página de bienvenida
    else:
        flash('Credenciales incorrectas', 'danger')
        return redirect(url_for('home'))  # Redirigir de vuelta al inicio de sesión

# Ruta para registrarse
@app.route('/register', methods=['POST'])
def register():
    username = request.form['username']
    email = request.form['email']
    password = request.form['password']

    # Verificar si el usuario ya existe
    existing_user = User.query.filter_by(username=username).first()
    if existing_user:
        flash('El usuario ya existe', 'danger')
        return redirect(url_for('home'))

    # Crear un nuevo usuario y almacenar la contraseña de forma segura
    hashed_password = generate_password_hash(password, method='pbkdf2:sha256')

    new_user = User(username=username, email=email, password=hashed_password)
    db.session.add(new_user)
    db.session.commit()
    
    flash('Cuenta creada exitosamente', 'success')
    return redirect(url_for('home'))

# Ruta de bienvenida después de iniciar sesión
@app.route('/welcome/<username>', methods=['GET', 'POST'])
def welcome(username):
    pdfs = PDF.query.all()  # Obtener todos los PDFs de la base de datos
    if request.method == 'POST':
        # Verificar si el formulario tiene un archivo
        if 'file' not in request.files:
            flash('No se ha enviado un archivo', 'danger')
            return redirect(request.url)

        file = request.files['file']
        if file.filename == '':
            flash('No se ha seleccionado un archivo', 'danger')
            return redirect(request.url)

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

            # Guardar el PDF en la base de datos
            new_pdf = PDF(filename=filename)
            db.session.add(new_pdf)
            db.session.commit()
            flash('Archivo cargado exitosamente', 'success')
            return redirect(url_for('welcome', username=username))  # Redirigir después de agregar el archivo

        flash('Archivo no permitido. Solo se permiten archivos PDF.', 'danger')
        return redirect(request.url)

    return render_template('welcome.html', username=username, pdfs=pdfs)

# Ruta para eliminar un PDF
@app.route('/delete_pdf/<int:pdf_id>', methods=['GET'])
def delete_pdf(pdf_id):
    pdf_to_delete = PDF.query.get_or_404(pdf_id)
    # Eliminar el archivo PDF del servidor
    os.remove(os.path.join(app.config['UPLOAD_FOLDER'], pdf_to_delete.filename))
    db.session.delete(pdf_to_delete)
    db.session.commit()
    flash('Archivo eliminado exitosamente', 'success')
    return redirect(url_for('welcome', username=pdf_to_delete.filename))  # Redirigir después de eliminar

# Verificar si el archivo es un PDF permitido
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

# Ruta para servir archivos PDF desde la carpeta 'uploads'
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    app.run(debug=True)
