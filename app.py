# app.py
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from firebase_admin import credentials, initialize_app, auth, firestore, storage
import firebase_admin
from functools import wraps
from werkzeug.utils import secure_filename
import uuid
import datetime
from flask import jsonify, request, abort
import json
import os
from dotenv import load_dotenv

app = Flask(__name__)
app.secret_key = 'mega-secret-key-yeah'  
app.config['LOGO_SVG_PATH'] = 'jinaq_logo.svg'
firebase_creds_str = os.getenv('FIREBASE_PRIVATE_KEY')
if not firebase_creds_str:
    raise ValueError("FIREBASE_PRIVATE_KEY не найден в .env файле")
# Преобразуем строку в словарь
firebase_credentials = json.loads(firebase_creds_str)

# Инициализация Firebase Admin SDK
cred = credentials.Certificate(firebase_credentials)
firebase_admin.initialize_app(cred, {
    'storageBucket': 'jinaq-1b755.firebasestorage.app'
})


db = firestore.client()
bucket = storage.bucket()

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function
@app.route('/update_academic_portfolio', methods=['POST'])
@login_required
def update_academic_portfolio():
    user_id = session['user_id']
    data = request.json

    try:
        # Обновляем академическую информацию
        db.collection('users').document(user_id).update({
            'academic_info': data
        })
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})
@app.route('/settings')
@login_required
def settings():
    user_id = session['user_id']
    user_doc = db.collection('users').document(user_id).get()
    
    return render_template('settings.html', user_data=user_doc.to_dict())

@app.route('/')
def index():
    if 'user_id' in session:
        user_id = session['user_id']
        user_doc = db.collection('users').document(user_id).get()
        user_data = user_doc.to_dict() if user_doc.exists else None
        return render_template('index.html', user_data=user_data)
    return render_template('index.html', user_data=None)


@app.route('/register', methods=['GET', 'POST'])
def register():
    # Redirect if user is already logged in
    if 'user_id' in session:
        flash('You are already registered and logged in')
        return redirect(url_for('profile'))

    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        username = request.form['username']

        try:
            # Check if username already exists
            users_ref = db.collection('users')
            username_query = users_ref.where('username', '==', username).get()
            if len(list(username_query)) > 0:
                flash('Username already taken')
                return redirect(url_for('register'))

            # Create user in Firebase Auth
            user = auth.create_user(
                email=email,
                password=password,
                display_name=username
            )

            # Create user document in Firestore с добавлением academic_info
            user_data = {
                'username': username,
                'email': email,
                'created_at': datetime.datetime.now(tz=datetime.timezone.utc),
                'uid': user.uid,
                'academic_info': {  # Добавляем эту секцию
                    'gpa': '',
                    'sat_score': '',
                    'toefl_score': '',
                    'ielts_score': '',
                    'languages': [],
                    'achievements': []
                }
            }
            db.collection('users').document(user.uid).set(user_data)

            flash('Registration successful! Please log in.')
            return redirect(url_for('login'))
        except Exception as e:
            flash(f'Error: {str(e)}')
            return redirect(url_for('register'))

    return render_template('register.html')
@app.route('/login', methods=['GET', 'POST'])
def login():
    # Redirect if user is already logged in
    if 'user_id' in session:
        flash('You are already logged in')
        return redirect(url_for('profile'))

    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        try:
            # Get user by email through Admin SDK
            user = auth.get_user_by_email(email)
            
            # Get user data from Firestore
            user_doc = db.collection('users').document(user.uid).get()
            user_data = user_doc.to_dict()

            if user_data:
                # Set session data
                session['user_id'] = user.uid
                session['username'] = user_data.get('username')
                return redirect(url_for('profile'))
            else:
                flash('User data not found')
                return redirect(url_for('login'))

        except Exception as e:
            flash('Login failed: Invalid email or password')
            return redirect(url_for('login'))

    return render_template('login.html')
@app.route('/delete-certificate/<cert_id>', methods=['DELETE'])
@login_required
def delete_certificate(cert_id):
    try:
        user_id = session['user_id']
        
        # Получаем данные сертификата
        cert_ref = db.collection('users').document(user_id).collection('certificates').document(cert_id)
        cert_doc = cert_ref.get()
        
        if not cert_doc.exists:
            return jsonify({'error': 'Certificate not found'}), 404
            
        cert_data = cert_doc.to_dict()
        
        # Удаляем файл из Storage
        if 'file_url' in cert_data:
            try:
                # Извлекаем путь к файлу из URL
                file_path = cert_data['file_url'].split('/')[-1]
                blob = bucket.blob(f'certificates/{user_id}/{file_path}')
                blob.delete()
            except Exception as e:
                print(f"Error deleting file from storage: {e}")
        
        # Удаляем документ из Firestore
        cert_ref.delete()
        
        return jsonify({'status': 'success'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/<username>/comments', methods=['GET', 'POST'])
def profile_comments(username):
    try:
        # Находим пользователя по username
        users_ref = db.collection('users')
        query = users_ref.where('username', '==', username).limit(1).stream()
        user_doc = next(query, None)

        if user_doc is None:
            return jsonify({'error': 'User not found'}), 404

        target_user_id = user_doc.id

        if request.method == 'POST':
            # Проверяем, авторизован ли текущий пользователь
            if 'user_id' not in session:
                return jsonify({'error': 'Unauthorized'}), 401

            # Получаем данные комментария
            comment_text = request.form.get('comment')
            if not comment_text:
                return jsonify({'error': 'Comment text is required'}), 400

            # Сохраняем комментарий
            comment_data = {
                'author_id': session['user_id'],
                'author_username': session['username'],
                'text': comment_text,
                'created_at': datetime.datetime.now(tz=datetime.timezone.utc)
            }

            db.collection('users').document(target_user_id).collection('comments').add(comment_data)
            
            return jsonify({'status': 'success', 'comment': comment_data}), 201

        # Получение комментариев
        comments_ref = db.collection('users').document(target_user_id).collection('comments')
        comments = comments_ref.order_by('created_at', direction=firestore.Query.DESCENDING).stream()
        
        comments_list = []
        for comment_doc in comments:
            comment = comment_doc.to_dict()
            
            # Получаем данные автора комментария
            author_doc = db.collection('users').document(comment['author_id']).get()
            author_data = author_doc.to_dict()
            
            comment['id'] = comment_doc.id
            comment['author_avatar'] = author_data.get('avatar_url', url_for('static', filename='default-avatar.png'))
            comment['author_username'] = author_data.get('username', 'Unknown User')
            comments_list.append(comment)

        return jsonify(comments_list), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/<username>/comments/<comment_id>', methods=['DELETE'])
@login_required
def delete_comment(username, comment_id):
    try:
        # Находим пользователя по username
        users_ref = db.collection('users')
        query = users_ref.where('username', '==', username).limit(1).stream()
        user_doc = next(query, None)

        if user_doc is None:
            return jsonify({'error': 'User not found'}), 404

        target_user_id = user_doc.id
        
        # Проверяем, является ли текущий пользователь автором или владельцем профиля
        comment_ref = db.collection('users').document(target_user_id).collection('comments').document(comment_id)
        comment_doc = comment_ref.get()
        
        if not comment_doc.exists:
            return jsonify({'error': 'Comment not found'}), 404
        
        comment_data = comment_doc.to_dict()
        
        if comment_data['author_id'] != session['user_id'] and session['user_id'] != target_user_id:
            return jsonify({'error': 'Unauthorized to delete this comment'}), 403
        
        comment_ref.delete()
        return jsonify({'status': 'success'}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
def generate_avatar_url(user_data):
    if user_data and user_data.get('avatar_url'):
        return user_data['avatar_url']
    
    if user_data and user_data.get('full_name'):
        # Используем первые две буквы имени и фамилии
        initials = ''.join(word[0].upper() for word in user_data['full_name'].split()[:2])
        return f"https://ui-avatars.com/api/?name={initials}&background=random&color=fff&size=128"
    
    return "https://ui-avatars.com/api/?name=U&background=random&color=fff&size=128"

# В маршрутах profile и public_profile
@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    user_id = session['user_id']
    
    user_doc = db.collection('users').document(user_id).get()
    user_data = user_doc.to_dict() or {}
    avatar_url = generate_avatar_url(user_data)

    # Добавляем значение по умолчанию, если academic_info отсутствует
    if 'academic_info' not in user_data:
        user_data['academic_info'] = {
            'gpa': '',
            'sat_score': '',
            'toefl_score': '',
            'ielts_score': '',
            'languages': [],
            'achievements': []
        }

    certificates = list(db.collection('users').document(user_id).collection('certificates').stream())
    
    if request.method == 'POST':
        try:
            # Обработка JSON запроса для обновления ссылок
            if request.headers.get('Content-Type') == 'application/json':
                data = request.get_json()
                if data.get('action') == 'update_links':
                    links = data.get('links', [])
                    # Валидация и обработка URL
                    processed_links = []
                    for link in links:
                        if link.get('title') and link.get('url'):
                            url = link['url']
                            if not url.startswith(('http://', 'https://')):
                                url = 'https://' + url
                            processed_links.append({
                                'title': link['title'],
                                'url': url
                            })
                    
                    # Обновляем ссылки в документе пользователя
                    db.collection('users').document(user_id).update({
                        'links': processed_links,
                        'updated_at': datetime.datetime.now(tz=datetime.timezone.utc)
                    })
                    return jsonify({'success': True})

            # Обработка загрузки сертификата
# Inside the certificate upload handling section of your profile route
# Inside your profile route where certificate upload is handled
            if 'certificate' in request.files:
                file = request.files['certificate']
                title = request.form.get('title', file.filename)
                
                if file and file.filename:
                    try:
                        file_extension = file.filename.rsplit('.', 1)[1].lower()
                        filename = f"certificates/{user_id}/{str(uuid.uuid4())}.{file_extension}"
                        
                        # Upload to Firebase Storage
                        blob = bucket.blob(filename)
                        blob.upload_from_string(
                            file.read(),
                            content_type=file.content_type
                        )
                        
                        blob.make_public()

                        # Save to Firestore
                        cert_data = {
                            'title': title,
                            'file_url': blob.public_url,
                            'uploaded_at': datetime.datetime.now(tz=datetime.timezone.utc)
                        }
                        
                        # Add document and get its ID
                        cert_ref = db.collection('users').document(user_id).collection('certificates').add(cert_data)
                        
                        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                            # Return both the ID and the certificate data
                            return jsonify({
                                'success': True,
                                'certificate': {
                                    'id': cert_ref[1].id,  # Get the ID from the DocumentReference
                                    **cert_data
                                }
                            })
                    except Exception as e:
                        return jsonify({'success': False, 'error': str(e)})
            # Обработка аватара
            if 'avatar' in request.files:
                avatar_file = request.files['avatar']
                if avatar_file and avatar_file.filename:
                    # Генерируем уникальное имя файла
                    file_extension = avatar_file.filename.rsplit('.', 1)[1].lower()
                    filename = f"avatars/{user_id}/{str(uuid.uuid4())}.{file_extension}"
                    
                    # Загружаем в Firebase Storage
                    blob = bucket.blob(filename)
                    blob.upload_from_string(
                        avatar_file.read(),
                        content_type=avatar_file.content_type
                    )
                    
                    # Делаем файл публичным
                    blob.make_public()
                    
                    # Обновляем URL аватара в профиле пользователя
                    profile_data = {
                        'avatar_url': blob.public_url,
                        'updated_at': datetime.datetime.now(tz=datetime.timezone.utc)
                    }
                    db.collection('users').document(user_id).update(profile_data)

                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return jsonify({
                            'success': True,
                            'avatar_url': blob.public_url
                        })
                pass
            if 'certificates' in request.files:
                files = request.files.getlist('certificates')
                uploaded_files = []
                
                for file in files:
                    if file and file.filename:
                        # Generate unique filename
                        file_extension = file.filename.rsplit('.', 1)[1].lower()
                        filename = f"certificates/{user_id}/{str(uuid.uuid4())}.{file_extension}"
                        
                        # Upload to Firebase Storage
                        blob = bucket.blob(filename)
                        blob.upload_from_string(
                            file.read(),
                            content_type=file.content_type
                        )
                        
                        # Make the file publicly accessible
                        blob.make_public()

                        # Save certificate info in Firestore
                        cert_data = {
                            'title': file.filename,
                            'file_url': blob.public_url,
                            'uploaded_at': datetime.datetime.now(tz=datetime.timezone.utc)
                        }
                        db.collection('users').document(user_id).collection('certificates').add(cert_data)
                        uploaded_files.append(cert_data)

                # Если это AJAX запрос, возвращаем JSON
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return jsonify({
                        'success': True,
                        'files': uploaded_files
                    })
                
                flash('Files uploaded successfully!')
                return redirect(url_for('profile'))

            # Обработка других POST данных...
            # Обновление основных данных профиля
            if request.form:
                profile_data = {
                    'full_name': request.form.get('full_name', ''),
                    'bio': request.form.get('bio', ''),
                    'education': request.form.get('education', ''),
                    'updated_at': datetime.datetime.now(tz=datetime.timezone.utc)
                }
                
                db.collection('users').document(user_id).update(profile_data)
                
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return jsonify({'success': True})
                
                flash('Profile updated successfully!')
                return redirect(url_for('profile'))

        except Exception as e:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'success': False, 'error': str(e)})
            flash(f'Error updating profile: {str(e)}')
            return redirect(url_for('profile'))
        
    # GET запрос
    user_doc = db.collection('users').document(user_id).get()
    certificates = list(db.collection('users').document(user_id).collection('certificates').stream())
    
    return render_template('profile.html',
                         user_data=user_data,
                         avatar_url=avatar_url,
                         certificates=certificates)
@app.route('/<username>')
def public_profile(username):
    try:
        users_ref = db.collection('users')
        query = users_ref.where('username', '==', username).limit(1).stream()
        user_doc = next(query, None)

        if user_doc is None:
            flash('User not found')
            return redirect(url_for('index'))

        user_data = user_doc.to_dict()
        avatar_url = generate_avatar_url(user_data)
        user_data = user_doc.to_dict()
        # Получаем список сертификатов и считаем их количество
        certificates = list(db.collection('users').document(user_doc.id).collection('certificates').stream())
        certificates_count = len(certificates)

        return render_template('public_profile.html',
                             user_data=user_data,
                             avatar_url=avatar_url,
                             certificates=certificates,
                             certificates_count=certificates_count)
    except Exception as e:
        flash(f'Error: {str(e)}')
        return redirect(url_for('index'))
from firebase_admin import auth

@app.route('/update_links', methods=['POST'])
def update_links():
    try:
        # Получаем токен из заголовка
        id_token = request.headers.get('Authorization')
        if not id_token:
            return jsonify(success=False, error="No token provided"), 401
            
        # Убираем 'Bearer ' из токена если он есть
        if id_token.startswith('Bearer '):
            id_token = id_token.split('Bearer ')[1]
            
        # Верифицируем токен и получаем информацию о пользователе
        decoded_token = auth.verify_id_token(id_token)
        user_id = decoded_token['uid']
        
        # Получаем данные из JSON
        data = request.get_json()
        links = data.get('links', [])
        
        # Валидация данных
        if not isinstance(links, list):
            return jsonify(success=False, error="Invalid data format"), 400
            
        # Проверяем структуру каждой ссылки
        for link in links:
            if not isinstance(link, dict) or 'title' not in link or 'url' not in link:
                return jsonify(success=False, error="Invalid link format"), 400
        
        # Обновляем документ пользователя в Firestore
        db.collection('users').document(user_id).update({
            'links': links
        })
        
        return jsonify(success=True)
    except auth.InvalidIdTokenError:
        return jsonify(success=False, error="Invalid token"), 401
    except Exception as e:
        print(f"Error updating links: {str(e)}")
        return jsonify(success=False, error=str(e)), 500
    
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)