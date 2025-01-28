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
import gunicorn
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
# В самом начале файла после импортов добавьте константу для типов верификации
VERIFICATION_TYPES = {
    'official': {
        'icon': '🏛️',
        'color': 'blue',
        'label': 'Официальный аккаунт'
    },
    'creator': {
        'icon': '🎨',
        'color': 'purple',
        'label': 'Создатель контента'
    },
    'business': {
        'icon': '💼',
        'color': 'green',
        'label': 'Бизнес-аккаунт'
    }
}


db = firestore.client()
bucket = storage.bucket()
def get_current_user_avatar():
    """Helper function to get current user's avatar"""
    if 'user_id' not in session:
        return None
    
    try:
        current_user_id = session['user_id']
        current_user_doc = db.collection('users').document(current_user_id).get()
        current_user_data = current_user_doc.to_dict()
        
        return generate_avatar_url(current_user_data)
    except Exception as e:
        print(f"Error getting current user avatar: {e}")
        return None

def get_current_username():
    """Helper function to get current user's username"""
    if 'username' in session:
        return session['username']
    return None
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
    user_data = user_doc.to_dict() if user_doc.exists else {}
    
    # Получаем аватар текущего пользователя
    current_user_avatar = get_current_user_avatar()
    current_username = get_current_username()
    
    return render_template(
        'settings.html',
        user_data=user_data,
        current_user_avatar=current_user_avatar,
        current_username=current_username,
        avatar_url=generate_avatar_url(user_data)
    )
@app.route('/update-email', methods=['POST'])
@login_required
def update_email():
    user_id = session['user_id']
    current_password = request.json.get('currentPassword')
    new_email = request.json.get('newEmail')
    
    try:
        # Get user's current email from Firestore
        user_doc = db.collection('users').document(user_id).get()
        user_data = user_doc.to_dict()
        current_email = user_data['email']
        
        # Update email in Firebase Auth
        user = auth.update_user(
            user_id,
            email=new_email
        )
        
        # Update email in Firestore
        db.collection('users').document(user_id).update({
            'email': new_email,
            'updated_at': datetime.datetime.now(tz=datetime.timezone.utc)
        })
        
        return jsonify({'success': True, 'message': 'Email updated successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
@app.route('/')
def index():
    current_username = get_current_username()
    current_user_avatar = get_current_user_avatar()
    
    if 'user_id' in session:
        user_id = session['user_id']
        user_doc = db.collection('users').document(user_id).get()
        user_data = user_doc.to_dict() if user_doc.exists else None
        
        avatar_url = generate_avatar_url(user_data) if user_data else None
        
        return render_template('index.html', 
                               user_data=user_data, 
                               avatar_url=avatar_url,
                               current_user_avatar=current_user_avatar,
                               current_username=current_username)
    
    return render_template('index.html', 
                           user_data=None, 
                           avatar_url=None,
                           current_user_avatar=current_user_avatar,
                           current_username=current_username)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        username = request.form['username'].lower()  # Преобразуем к нижнему регистру

        try:
            # Проверка уникальности username (теперь в нижнем регистре)
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
                'display_username': request.form['username'],
                'email': email,
                'created_at': datetime.datetime.now(tz=datetime.timezone.utc),
                'uid': user.uid,
                # Новые поля для верификации
                'verified': False,
                'verification_type': None,
                'verified_by': None,
                'verified_at': None,
                'academic_info': {
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
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        try:
            user = auth.get_user_by_email(email)
            
            # Получаем пользователя по email, используя lowercase username для поиска
            user_doc = db.collection('users').document(user.uid).get()
            user_data = user_doc.to_dict()

            if user_data:
                # Устанавливаем сессию с оригинальным регистром
                session['user_id'] = user.uid
                session['username'] = user_data.get('display_username', user_data['username'])
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
    
    # Сначала определите avatar_url
    avatar_url = generate_avatar_url(user_data)
    
    # Затем используйте его для current_user_avatar
    current_user_avatar = avatar_url
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
                    try:
                        # Удаление старого аватара из Firebase Storage
                        if user_data.get('avatar_url'):
                            old_avatar_path = user_data['avatar_url'].split('/')[-1]
                            old_blob = bucket.blob(f'avatars/{user_id}/{old_avatar_path}')
                            old_blob.delete()
                    except Exception as e:
                        print(f"Error deleting old avatar: {e}")

                    # Генерируем уникальное имя файла
                    file_extension = avatar_file.filename.rsplit('.', 1)[1].lower()
                    filename = f"{str(uuid.uuid4())}.{file_extension}"
                    full_path = f"avatars/{user_id}/{filename}"
                    
                    # Загружаем в Firebase Storage
                    blob = bucket.blob(full_path)
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
                         current_user_avatar=current_user_avatar,
                         certificates=certificates)
@app.route('/<username>')
def public_profile(username):
    current_username = get_current_username()
    current_user_avatar = get_current_user_avatar()
    
    try:
        users_ref = db.collection('users')
        # Ищем пользователя без учета регистра
        query = users_ref.where('username', '==', username.lower()).limit(1).stream()
        user_doc = next(query, None)

        if user_doc is None:
            flash('User not found')
            return redirect(url_for('index'))

        viewed_user_data = user_doc.to_dict()
        users_ref = db.collection('users')
        query = users_ref.where('username', '==', username).limit(1).stream()
        user_doc = next(query, None)

        if user_doc is None:
            flash('User not found')
            return redirect(url_for('index'))

        viewed_user_data = user_doc.to_dict()
        viewed_user_avatar = generate_avatar_url(viewed_user_data)
        
        certificates = list(db.collection('users').document(user_doc.id).collection('certificates').stream())
        certificates_count = len(certificates)

        return render_template('public_profile.html',
                             user_data=viewed_user_data,
                             avatar_url=viewed_user_avatar,
                             current_user_avatar=current_user_avatar,
                             current_username=current_username,
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
@app.route('/admin/migrate_usernames', methods=['GET'])
@login_required  # Добавьте декоратор для защиты
def migrate_usernames():
    # Проверка, что это администратор
    if session.get('user_id') != 'admin_user_id':  # Замените на ваш реальный admin ID
        return "Unauthorized", 403
    
    users_ref = db.collection('users')
    users = users_ref.stream()
    
    for user_doc in users:
        user_data = user_doc.to_dict()
        
        # Добавляем display_username, если его нет
        if 'display_username' not in user_data:
            users_ref.document(user_doc.id).update({
                'username': user_data['username'].lower(),
                'display_username': user_data['username']
            })
    
    return "Migration completed successfully"    

# В app.py добавьте:
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'default_secret_password')

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        password = request.form.get('password')
        if password == ADMIN_PASSWORD:
            session['admin_logged_in'] = True
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Incorrect admin password', 'error')
    return render_template('admin_login.html')


@app.route('/update-username', methods=['POST'])
@login_required
def update_username():
    user_id = session['user_id']
    new_username = request.json.get('username').lower()
    display_username = request.json.get('username')  # Original case for display
    
    try:
        # Check if username is taken
        users_ref = db.collection('users')
        username_query = users_ref.where('username', '==', new_username).get()
        if len(list(username_query)) > 0:
            return jsonify({'error': 'Username already taken'}), 400
            
        # Update username in Firestore
        user_ref = db.collection('users').document(user_id)
        user_ref.update({
            'username': new_username,
            'display_username': display_username,
            'updated_at': datetime.datetime.now(tz=datetime.timezone.utc)
        })
        
        # Update session
        session['username'] = display_username
        
        return jsonify({'success': True, 'message': 'Username updated successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/update-password', methods=['POST'])
@login_required
def update_password():
    user_id = session['user_id']
    current_password = request.json.get('current_password')
    new_password = request.json.get('new_password')
    
    try:
        # Get user's email from Firestore
        user_doc = db.collection('users').document(user_id).get()
        user_data = user_doc.to_dict()
        
        # Verify current password through Firebase Auth
        user = auth.get_user_by_email(user_data['email'])
        
        # Update password in Firebase Auth
        auth.update_user(
            user_id,
            password=new_password
        )
        
        return jsonify({'success': True, 'message': 'Password updated successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/delete-account', methods=['POST'])
@login_required
def delete_account():
    user_id = session['user_id']
    password = request.json.get('password')
    
    try:
        # Get user's email from Firestore
        user_doc = db.collection('users').document(user_id).get()
        user_data = user_doc.to_dict()
        
        # Verify password through Firebase Auth
        user = auth.get_user_by_email(user_data['email'])
        
        # Delete user's data from Firestore
        # First, delete subcollections
        certificates_ref = db.collection('users').document(user_id).collection('certificates')
        comments_ref = db.collection('users').document(user_id).collection('comments')
        
        # Delete certificates
        certs = certificates_ref.stream()
        for cert in certs:
            cert.reference.delete()
            
        # Delete comments
        comments = comments_ref.stream()
        for comment in comments:
            comment.reference.delete()
            
        # Delete main user document
        db.collection('users').document(user_id).delete()
        
        # Delete user from Firebase Auth
        auth.delete_user(user_id)
        
        # Clear session
        session.clear()
        
        return jsonify({'success': True, 'message': 'Account deleted successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/reset-password', methods=['POST'])
def reset_password():
    email = request.json.get('email')
    
    try:
        # Проверяем существует ли пользователь с таким email
        user = auth.get_user_by_email(email)
        
        # Генерируем ссылку для сброса пароля
        action_code_settings = auth.ActionCodeSettings(
            url=f"{request.host_url}login",  # URL куда пользователь вернется после сброса пароля
            handle_code_in_app=False
        )
        
        # Отправляем email для сброса пароля
        reset_link = auth.generate_password_reset_link(
            email, 
            action_code_settings
        )
        
        return jsonify({
            'success': True,
            'message': 'Password reset instructions have been sent to your email'
        })
        
    except auth.UserNotFoundError:
        # Не сообщаем пользователю что email не найден (безопасность)
        return jsonify({
            'success': True,
            'message': 'If an account exists with this email, you will receive password reset instructions'
        })
        
    except Exception as e:
        print(f"Error in reset_password: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'An error occurred. Please try again later.'
        }), 500

@app.route('/search_users')
def search_users():
    query = request.args.get('query', '').lower()
    
    try:
        users_ref = db.collection('users')
        query_result = users_ref.where('username', '>=', query).where('username', '<', query + '\uf8ff').limit(10).stream()
        
        users = []
        for user_doc in query_result:
            user_data = user_doc.to_dict()
            # Проверяем, что данные есть
            if user_data and 'display_username' in user_data:
                users.append({
                    'username': user_data['display_username'],
                    'avatar': generate_avatar_url(user_data),
                    'verified': user_data.get('verified', False),
                    'verification_type': user_data.get('verification_type', None)
                })
        
        return jsonify(users)
    except Exception as e:
        print(f"Search error: {e}")
        return jsonify([]), 500

# Маршрут для верификации пользователей
# Маршрут для верификации пользователей
@app.route('/admin/verify_user', methods=['POST'])
@login_required
def verify_user():
    # Список администраторов, кто может верифицировать
    ADMIN_IDS = ['vVbXL4LKGidXtrKnvqa21gWRY3V2']  # Замените на реальный ID администратора

    if session['user_id'] not in ADMIN_IDS:
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.json
    user_id = data.get('user_id')
    verification_type = data.get('type', 'official')
    
    try:
        db.collection('users').document(user_id).update({
            'verified': True,
            'verification_type': verification_type,
            'verified_by': session['user_id'],
            'verified_at': firestore.SERVER_TIMESTAMP
        })
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/admin/dashboard')
def admin_dashboard():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    # Получаем список всех пользователей
    users_ref = db.collection('users')
    users = users_ref.stream()
    
    user_list = []
    for user_doc in users:
        user_data = user_doc.to_dict()
        user_data['id'] = user_doc.id
        user_list.append(user_data)
    
    return render_template('admin_dashboard.html', users=user_list)

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('admin_login'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)