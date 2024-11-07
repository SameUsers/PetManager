from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import UserMixin, LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import pymysql

app = Flask(__name__)

app.secret_key = '152'

# Функция для подключения к базе данных через pymysql
def get_db_connection():
    return pymysql.connect(
        host='localhost',
        user='root',
        password='',
        database='pet_db',
        cursorclass=pymysql.cursors.DictCursor
    )

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Модель пользователя
class User(UserMixin):
    def __init__(self, id, username, role):
        self.id = id
        self.username = username
        self.role = role


        
@app.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_pet(id):
    conn = pymysql.connect(
        host='localhost',
        user='root',
        password='',
        database='pet_db',
        cursorclass=pymysql.cursors.DictCursor
    )
    cur = conn.cursor()
    cur.execute("SELECT * FROM pets WHERE id = %s", [id])
    pet = cur.fetchone()

    if request.method == 'POST':
        name = request.form['name']
        species = request.form['species']
        age = request.form['age']
        description = request.form['description']
        image_url = request.form['image_url']

        cur.execute("""
            UPDATE pets 
            SET name = %s, species = %s, age = %s, description = %s, image_url = %s 
            WHERE id = %s
        """, (name, species, age, description, image_url, id))
        conn.commit()
        flash('Pet updated successfully!', 'success')
        return redirect(url_for('index'))

    conn.close()
    return render_template('edit_pet.html', pet=pet)

# Загрузчик пользователя
@login_manager.user_loader
def load_user(user_id):
    conn = get_db_connection()
    with conn.cursor() as cur:
        cur.execute("SELECT * FROM users WHERE id = %s", [user_id])
        user = cur.fetchone()
    conn.close()
    return User(user['id'], user['username'], user['role']) if user else None

# Главная страница (отображение питомцев)
@app.route('/')
def index():
    conn = get_db_connection()
    with conn.cursor() as cur:
        cur.execute("SELECT * FROM pets")
        pets = cur.fetchall()
    conn.close()
    return render_template('index.html', pets=pets)

# Страница добавления питомца
@app.route('/add', methods=['GET', 'POST'])
@login_required
def add_pet():
    if request.method == 'POST':
        name = request.form['name']
        species = request.form['species']
        age = request.form['age']
        description = request.form['description']
        image_url = request.form['image_url']

        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO pets (name, species, age, description, image_url) VALUES (%s, %s, %s, %s, %s)",
                (name, species, age, description, image_url)
            )
        conn.commit()
        conn.close()
        flash('Pet added successfully!', 'success')
        return redirect(url_for('index'))

    return render_template('add_pet.html')

# Страница удаления питомца
@app.route('/delete/<int:id>')
@login_required
def delete_pet(id):
    conn = get_db_connection()
    with conn.cursor() as cur:
        cur.execute("DELETE FROM pets WHERE id = %s", [id])
    conn.commit()
    conn.close()
    flash('Pet deleted successfully!', 'danger')
    return redirect(url_for('index'))

# Регистрация пользователя
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        password_hash = generate_password_hash(password)

        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute("INSERT INTO users (username, password_hash) VALUES (%s, %s)", (username, password_hash))
        conn.commit()
        conn.close()
        flash('Account created successfully!', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

# Вход пользователя
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM users WHERE username = %s", [username])
            user = cur.fetchone()

        conn.close()

        if user and check_password_hash(user['password_hash'], password):
            login_user(User(user['id'], user['username'], user['role']))
            flash('Logged in successfully!', 'success')
            return redirect(url_for('index'))
        
        flash('Invalid credentials', 'danger')
    return render_template('login.html')

# Выход из системы
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully!', 'info')
    return redirect(url_for('index'))

# Запуск приложения
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
