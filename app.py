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
from flask_wtf.csrf import CSRFProtect


app = Flask(__name__)
app.secret_key = 'mega-secret-key-yeah'  
app.config['LOGO_SVG_PATH'] = 'jinaq_logo.svg'
firebase_creds_str = os.getenv('FIREBASE_PRIVATE_KEY')
ADMIN_IDS = os.getenv("ADMIN_IDS")
if not firebase_creds_str:
    raise ValueError("FIREBASE_PRIVATE_KEY не найден в .env файле")
# Преобразуем строку в словарь
firebase_credentials = json.loads(firebase_creds_str)
csrf = CSRFProtect(app)
NOTIFICATION_TYPES = {
    'like_comment': {
        'icon': '❤️',
        'label': 'Comment Liked'
    },
    'reply_comment': {
        'icon': '💬',
        'label': 'Comment Replied'
    },
    'profile_comment': {
        'icon': '📝',
        'label': 'Profile Comment'
    },
    'account_change': {
        'icon': '🌐',
        'label': 'System Notification'
    },
    'verification': {
        'icon': '🏆',
        'label': 'Account Verified'
    },
    'system': {
        'icon': '🌐',
        'label': 'System Notification'
    }
}
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


@app.route('/login/google')
def google_login():
    # Этот маршрут будет перенаправлять на клиентскую аутентификацию
    return redirect(url_for('login'))
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
    
    try:
        # Получаем и валидируем JSON данные
        if not request.is_json:
            return jsonify({
                'success': False, 
                'error': 'Content-Type must be application/json'
            }), 400

        data = request.get_json()
        
        # Проверяем структуру данных
        if not isinstance(data, dict):
            return jsonify({
                'success': False, 
                'error': 'Invalid data format'
            }), 400

        # Валидация требуемых полей
        required_keys = ['gpa', 'sat_score', 'toefl_score', 'ielts_score', 'languages', 'achievements']
        for key in required_keys:
            if key not in data:
                return jsonify({
                    'success': False, 
                    'error': f'Missing required key: {key}'
                }), 400

        # Создаем структуру данных для обновления
        academic_info = {
            'gpa': str(data.get('gpa', '')).strip(),
            'sat_score': str(data.get('sat_score', '')).strip(),
            'toefl_score': str(data.get('toefl_score', '')).strip(),
            'ielts_score': str(data.get('ielts_score', '')).strip(),
            'languages': data.get('languages', []),
            'achievements': data.get('achievements', [])
        }

        # Обновляем в базе данных
        db.collection('users').document(user_id).update({
            'academic_info': academic_info,
            'updated_at': datetime.datetime.now(tz=datetime.timezone.utc)
        })

        return jsonify({
            'success': True, 
            'message': 'Academic portfolio updated successfully'
        })

    except Exception as e:
        print(f"Academic Portfolio Update Error: {e}")
        return jsonify({
            'success': False, 
            'error': str(e)
        }), 500

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
    create_notification(
        user_id, 
        'account_change', 
        {
            'action': 'email_updated',
            'new_email': new_email
        }
    )

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


# Обновляем функцию generate_avatar_url
def generate_avatar_url(user_data):
    """Генерирует URL аватарки для пользователя"""
    if not user_data:
        return "https://ui-avatars.com/api/?name=U&background=random&color=fff&size=128"
    
    # Если есть своя аватарка, возвращаем её
    if user_data.get('avatar_url'):
        return user_data['avatar_url']
    
    # Генерируем аватарку на основе display_username
    display_name = user_data.get('display_username', user_data.get('username', 'U'))
    initials = ''.join(word[0].upper() for word in display_name.split()[:2])
    
    return f"https://ui-avatars.com/api/?name={initials}&background=random&color=fff&size=128"

# Обновляем часть функции register для корректной обработки username
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        display_username = request.form['username']  # Оригинальный username с сохранением регистра
        username = display_username.lower()  # Версия для поиска

        try:
            # Проверка уникальности username
            users_ref = db.collection('users')
            username_query = users_ref.where('username', '==', username).get()
            if len(list(username_query)) > 0:
                flash('Username already taken')
                return redirect(url_for('register'))

            # Create user in Firebase Auth
            user = auth.create_user(
                email=email,
                password=password,
                display_name=display_username
            )

            # Create user document in Firestore
            user_data = {
                'username': username,  # Lowercase для поиска
                'display_username': display_username,  # Оригинальный регистр
                'email': email,
                'created_at': datetime.datetime.now(tz=datetime.timezone.utc),
                'uid': user.uid,
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
@app.route('/<username>/comments/<comment_id>/reply', methods=['POST'])
@login_required
def reply_to_comment(username, comment_id):
    try:
        # Находим пользователя по username
        users_ref = db.collection('users')
        query = users_ref.where('username', '==', username.lower()).limit(1).stream()
        user_doc = next(query, None)

        if user_doc is None:
            return jsonify({'error': 'User not found'}), 404

        target_user_id = user_doc.id
        reply_text = request.form.get('reply')

        if not reply_text:
            return jsonify({'error': 'Reply text is required'}), 400

        # Получаем оригинальный комментарий
        original_comment_ref = db.collection('users').document(target_user_id).collection('comments').document(comment_id)
        original_comment_doc = original_comment_ref.get()

        # Проверяем, существует ли комментарий
        if not original_comment_doc.exists:
            return jsonify({'error': 'Original comment not found'}), 404

        original_comment_data = original_comment_doc.to_dict()

        # Создаем данные ответа
        reply_data = {
            'author_id': session['user_id'],
            'author_username': session['username'],
            'text': reply_text,
            'created_at': datetime.datetime.now(tz=datetime.timezone.utc),
            'parent_id': comment_id,
            'likes': []
        }

        # Сохраняем ответ
        reply_ref = db.collection('users').document(target_user_id).collection('comments').add(reply_data)
        
        # Получаем данные автора для ответа
        author_doc = db.collection('users').document(reply_data['author_id']).get()
        author_data = author_doc.to_dict()
        
        reply_data['id'] = reply_ref[1].id
        reply_data['author_avatar'] = author_data.get('avatar_url', url_for('static', filename='default-avatar.png'))
        
        # Создание уведомления для автора оригинального комментария
        if original_comment_data['author_id'] != session['user_id']:
            create_notification(
                original_comment_data['author_id'], 
                'reply_comment', 
                {
                    'original_comment_text': original_comment_data['text'],
                    'reply_text': reply_text,
                    'replier_username': session['username']
                },
                sender_id=session['user_id'],
                related_id=comment_id
            )

        return jsonify({'status': 'success', 'reply': reply_data}), 201

    except Exception as e:
        return jsonify({'error': str(e)}), 500
@app.route('/<username>/comments/<comment_id>/like', methods=['POST'])
@login_required
def like_comment(username, comment_id):
    try:
        users_ref = db.collection('users')
        query = users_ref.where('username', '==', username.lower()).limit(1).stream()
        user_doc = next(query, None)

        if user_doc is None:
            return jsonify({'error': 'User not found'}), 404

        target_user_id = user_doc.id
        current_user_id = session['user_id']

        # Получаем комментарий
        comment_ref = db.collection('users').document(target_user_id).collection('comments').document(comment_id)
        comment_doc = comment_ref.get()
        comment_data = comment_doc.to_dict()
        
        if comment_data['author_id'] != current_user_id:
            create_notification(
                comment_data['author_id'], 
                'like_comment', 
                {
                    'comment_text': comment_data['text'],
                    'liker_username': session['username']
                },
                sender_id=current_user_id,
                related_id=comment_id
            )
        if not comment_doc.exists:
            return jsonify({'error': 'Comment not found'}), 404

        comment_data = comment_doc.to_dict()
        likes = comment_data.get('likes', [])

        # Переключаем лайк
        if current_user_id in likes:
            likes.remove(current_user_id)
        else:
            likes.append(current_user_id)
            # Создаем уведомление для автора комментария


        # Обновляем комментарий
        comment_ref.update({'likes': likes})

        return jsonify({
            'status': 'success',
            'likes_count': len(likes),
            'is_liked': current_user_id in likes
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        identifier = request.form['identifier']  # Может быть email или username
        password = request.form['password']
        
        try:
            # Сначала проверяем, является ли identifier email-ом
            try:
                user = auth.get_user_by_email(identifier)
                email = identifier
            except:
                # Если это не email, ищем пользователя по username в Firestore
                users_ref = db.collection('users')
                query = users_ref.where('username', '==', identifier.lower()).limit(1).get()
                
                if not query:
                    flash('User not found')
                    return redirect(url_for('login'))
                
                user_data = query[0].to_dict()
                email = user_data['email']
                # Получаем пользователя Firebase по найденному email
                user = auth.get_user_by_email(email)
            
            # Проверяем существование пользователя в Firestore
            user_doc = db.collection('users').document(user.uid).get()
            user_data = user_doc.to_dict()

            if user_data:
                # Устанавливаем сессию
                session['user_id'] = user.uid
                session['username'] = user_data.get('display_username', user_data['username'])
                return redirect(url_for('profile'))
            else:
                flash('User data not found')
                return redirect(url_for('login'))

        except Exception as e:
            print(f"Login error: {str(e)}")  # Для отладки
            flash('Login failed: Invalid credentials')
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

@app.route('/<username>/comments', methods=['GET'])
def get_comments(username):
    try:
        users_ref = db.collection('users')
        query = users_ref.where('username', '==', username.lower()).limit(1).stream()
        user_doc = next(query, None)

        if user_doc is None:
            return jsonify({'error': 'User not found'}), 404

        target_user_id = user_doc.id
        comments_ref = db.collection('users').document(target_user_id).collection('comments')
        
        # Получаем все комментарии
        comments = comments_ref.order_by('created_at', direction=firestore.Query.DESCENDING).stream()
        
        comments_dict = {}
        replies_dict = {}
        
        for comment_doc in comments:
            comment = comment_doc.to_dict()
            comment['id'] = comment_doc.id
            
            # Получаем данные автора комментария
            author_doc = db.collection('users').document(comment['author_id']).get()
            author_data = author_doc.to_dict()
            
            comment['author_avatar'] = author_data.get('avatar_url', url_for('static', filename='default-avatar.png'))
            comment['likes_count'] = len(comment.get('likes', []))
            comment['is_liked'] = session.get('user_id') in comment.get('likes', [])
            
            if 'parent_id' in comment:
                if comment['parent_id'] not in replies_dict:
                    replies_dict[comment['parent_id']] = []
                replies_dict[comment['parent_id']].append(comment)
            else:
                comments_dict[comment_doc.id] = comment

        # Добавляем ответы к родительским комментариям
        for comment_id, comment in comments_dict.items():
            comment['replies'] = replies_dict.get(comment_id, [])

        return jsonify(list(comments_dict.values()))

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
    
# Обновляем функцию generate_avatar_url
def generate_avatar_url(user_data):
    """Генерирует URL аватарки для пользователя"""
    if not user_data:
        return "https://ui-avatars.com/api/?name=U&background=random&color=fff&size=128"
    
    # Если есть своя аватарка, возвращаем её
    if user_data.get('avatar_url'):
        return user_data['avatar_url']
    
    # Генерируем аватарку на основе display_username
    display_name = user_data.get('display_username', user_data.get('username', 'U'))
    initials = ''.join(word[0].upper() for word in display_name.split()[:2])
    
    return f"https://ui-avatars.com/api/?name={initials}&background=random&color=fff&size=128"

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
    try:
        # Поиск пользователя без учета регистра
        users_ref = db.collection('users')
        query = users_ref.where('username', '==', username.lower()).limit(1).stream()
        user_doc = next(query, None)

        if user_doc is None:
            flash('User not found')
            return redirect(url_for('index'))

        viewed_user_data = user_doc.to_dict()
        viewed_user_avatar = generate_avatar_url(viewed_user_data)
        
        # Получаем данные текущего пользователя для корректного отображения current_user_avatar
        current_user_avatar = None
        if 'user_id' in session:
            current_user = db.collection('users').document(session['user_id']).get()
            if current_user.exists:
                current_user_data = current_user.to_dict()
                current_user_avatar = generate_avatar_url(current_user_data)
        
        certificates = list(db.collection('users').document(user_doc.id).collection('certificates').stream())
        certificates_count = len(certificates)

        return render_template('public_profile.html',
                             user_data=viewed_user_data,
                             avatar_url=viewed_user_avatar,
                             current_user_avatar=current_user_avatar,
                             current_username=session.get('username'),
                             certificates=certificates,
                             certificates_count=certificates_count)
    except Exception as e:
        print(f"Error in public_profile: {str(e)}")  # Для отладки
        flash(f'Error: {str(e)}')
        return redirect(url_for('index'))   

from firebase_admin import auth

@app.route('/update-links', methods=['POST'])
@login_required
def update_links():
    try:
        # Получаем данные из запроса
        data = request.get_json()
        links = data.get('links', [])
        
        # Получаем ID пользователя из сессии
        user_id = session['user_id']
        
        # Валидация данных
        if not isinstance(links, list):
            return jsonify(success=False, error="Invalid data format"), 400
            
        # Проверяем структуру каждой ссылки
        for link in links:
            if not isinstance(link, dict) or 'title' not in link or 'url' not in link:
                return jsonify(success=False, error="Invalid link format"), 400
        
        # Обновляем документ пользователя в Firestore
        db.collection('users').document(user_id).update({
            'links': links,
            'updated_at': datetime.datetime.now(tz=datetime.timezone.utc)
        })
        
        return jsonify(success=True)
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

@app.route('/update-profile', methods=['POST'])
@login_required
def update_profile():
    user_id = session['user_id']
    data = request.json
    
    try:
        profile_data = {}
        
        if 'full_name' in data:
            profile_data['full_name'] = data['full_name']
            # Добавляем нижний регистр для поиска
            profile_data['full_name_lower'] = data['full_name'].lower()
        
        if 'bio' in data:
            profile_data['bio'] = data['bio']
            
        if 'education' in data:
            profile_data['education'] = data['education']
            
        profile_data['updated_at'] = datetime.datetime.now(tz=datetime.timezone.utc)
        
        db.collection('users').document(user_id).update(profile_data)
        
        return jsonify({'success': True, 'message': 'Profile updated successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    

@app.route('/update-password', methods=['POST'])
@login_required
def update_password():
    user_id = session['user_id']
    current_password = request.json.get('current_password')
    new_password = request.json.get('new_password')
    create_notification(
        user_id, 
        'account_change', 
        {
            'action': 'password_changed'
        }
    )
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
    try:
        email = request.json.get('email')
        if not email:
            return jsonify({
                'success': False,
                'error': 'Email is required'
            }), 400

        # Создаем настройки для ссылки сброса пароля
        action_code_settings = auth.ActionCodeSettings(
            url=f"{request.host_url}login",  # URL для возврата после сброса
            handle_code_in_app=False
        )
        
        # Генерируем и отправляем ссылку для сброса пароля
        reset_link = auth.generate_password_reset_link(
            email,
            action_code_settings
        )
        
        # Логируем для отладки
        print(f"Generated reset link for {email}")
        
        return jsonify({
            'success': True,
            'message': 'If an account exists with this email, password reset instructions have been sent.'
        })
        
    except Exception as e:
        print(f"Error in reset_password: {str(e)}")  # Для отладки
        return jsonify({
            'success': False,
            'error': 'An error occurred. Please try again later.'
        }), 500

@app.route('/search_users')
def search_users():
    query = request.args.get('query', '').lower()
    
    try:
        users_ref = db.collection('users')
        results = {}  # Используем словарь для уникальности результатов
        
        # Получаем все документы, которые могут соответствовать запросу
        all_users = users_ref.stream()
        
        for user_doc in all_users:
            user_data = user_doc.to_dict()
            
            if not user_data or 'username' not in user_data:
                continue
                
            # Получаем все поля для поиска
            username = user_data.get('username', '').lower()
            display_username = user_data.get('display_username', '').lower()
            full_name = user_data.get('full_name', '').lower()
            
            # Проверяем совпадения во всех полях
            if (query in username or 
                query in display_username or 
                query in full_name or 
                any(query in word.lower() for word in full_name.split())):
                
                # Если нашли совпадение, добавляем пользователя в результаты
                results[user_doc.id] = {
                    'username': user_data.get('display_username', user_data['username']),
                    'full_name': user_data.get('full_name', ''),
                    'avatar': generate_avatar_url(user_data),
                    'verified': user_data.get('verified', False),
                    'verification_type': user_data.get('verification_type', None)
                }
        
        # Ограничиваем количество результатов
        results_list = list(results.values())[:10]
        
        # Сортируем результаты: сначала точные совпадения, потом частичные
        results_list.sort(key=lambda x: (
            not x['username'].lower().startswith(query),  # Сначала по началу username
            not (x['full_name'] and x['full_name'].lower().startswith(query)),  # Потом по началу full_name
            x['username'].lower(),  # Потом по алфавиту
        ))
        
        return jsonify(results_list)
    except Exception as e:
        print(f"Search error: {e}")
        return jsonify([]), 500


@app.route('/admin/migrate_fullnames', methods=['GET'])
@login_required
def migrate_fullnames():
    if session.get('user_id') != 'vVbXL4LKGidXtrKnvqa21gWRY3V2':  # Замените на ваш admin ID
        return "Unauthorized", 403
        
    try:
        users_ref = db.collection('users')
        users = users_ref.stream()
        
        for user_doc in users:
            user_data = user_doc.to_dict()
            
            if 'full_name' in user_data and 'full_name_lower' not in user_data:
                users_ref.document(user_doc.id).update({
                    'full_name_lower': user_data['full_name'].lower()
                })
        
        return "Migration completed successfully"
    except Exception as e:
        return f"Error during migration: {str(e)}", 500
# Маршрут для верификации пользователей

@app.route('/admin/verify_user', methods=['POST'])
@login_required
def verify_user():
    create_notification(
        user_id, 
        'verification', 
        {
            'verification_type': verification_type
        }
    )

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
def create_notification(user_id, type, content, sender_id=None, related_id=None):
    """
    Create a new notification
    
    Args:
        user_id (str): ID of the user receiving the notification
        type (str): Type of notification
        content (dict): Notification details
        sender_id (str, optional): ID of the user who triggered the notification
        related_id (str, optional): Related document/resource ID
    """
    try:
        notification_ref = db.collection('users').document(user_id).collection('notifications').document()
        
        notification_data = {
            'type': type,
            'content': content,
            'sender_id': sender_id,
            'related_id': related_id,
            'is_read': False,
            'created_at': firestore.SERVER_TIMESTAMP
        }
        
        notification_ref.set(notification_data)
        return notification_ref.id
    except Exception as e:
        print(f"Error creating notification: {e}")
        return None

@app.route('/notifications', methods=['GET'])
@login_required
def get_notifications():
    """Retrieve user notifications"""
    user_id = session['user_id']
    
    try:
        notifications_ref = db.collection('users').document(user_id).collection('notifications')
        notifications = notifications_ref.order_by('created_at', direction=firestore.Query.DESCENDING).limit(20).stream()
        
        notification_list = []
        for notification_doc in notifications:
            notification = notification_doc.to_dict()
            notification['id'] = notification_doc.id
            
            # Получаем данные отправителя, если есть
            if notification.get('sender_id'):
                sender_doc = db.collection('users').document(notification['sender_id']).get()
                sender_data = sender_doc.to_dict() if sender_doc.exists else {}
                notification['sender_avatar'] = generate_avatar_url(sender_data)
                notification['sender_username'] = sender_data.get('display_username', '')
            
            # Добавляем иконку и метку из NOTIFICATION_TYPES
            notification_type_info = NOTIFICATION_TYPES.get(notification['type'], {})
            notification['icon'] = notification_type_info.get('icon', '🔔')
            notification['type_label'] = notification_type_info.get('label', 'Notification')
            
            notification_list.append(notification)
        
        return jsonify(notification_list)
    except Exception as e:
        print(f"Error retrieving notifications: {e}")
        return jsonify({'error': 'Failed to retrieve notifications'}), 500
@app.route('/notifications/<notification_id>', methods=['DELETE'])
@login_required
def delete_notification(notification_id):
    """Delete a specific notification"""
    user_id = session['user_id']
    
    try:
        notification_ref = db.collection('users').document(user_id).collection('notifications').document(notification_id)
        notification_ref.delete()
        return jsonify({'success': True})
    except Exception as e:
        print(f"Error deleting notification: {e}")
        return jsonify({'error': 'Failed to delete notification'}), 500

@app.route('/notifications/mark_read/<notification_id>', methods=['POST'])
@login_required
def mark_notification_read(notification_id):
    """Mark a specific notification as read"""
    user_id = session['user_id']
    
    try:
        notification_ref = db.collection('users').document(user_id).collection('notifications').document(notification_id)
        notification_ref.update({'is_read': True})
        return jsonify({'success': True})
    except Exception as e:
        print(f"Error marking notification as read: {e}")
        return jsonify({'error': 'Failed to mark notification as read'}), 500

@app.route('/admin/send_system_notification', methods=['POST'])
@login_required
def send_system_notification():
    # Список администраторов - замените на реальные ID
    ADMIN_IDS = ['vVbXL4LKGidXtrKnvqa21gWRY3V2']  # Например, ['vVbXL4LKGidXtrKnvqa21gWRY3V2']
    
    # Проверка, что текущий пользователь - администратор
    if session.get('user_id') not in ADMIN_IDS:
        return jsonify({'error': 'Unauthorized access'}), 403
    
    # Получаем JSON-данные
    data = request.json
    
    recipient_type = data.get('recipient_type', 'all')
    message_type = data.get('message_type', 'system')
    message_text = data.get('message_text', '')
    selected_users = data.get('selected_users', [])
    
    if not message_text:
        return jsonify({'error': 'Message cannot be empty'}), 400
    
    try:
        # Запрос пользователей в зависимости от типа получателей
        users_ref = db.collection('users')
        
        if recipient_type == 'verified':
            query = users_ref.where('verified', '==', True)
        elif recipient_type == 'unverified':
            query = users_ref.where('verified', '==', False)
        elif recipient_type == 'selected':
            # Выбираем только указанных пользователей
            if not selected_users:
                return jsonify({'error': 'No users selected'}), 400
            
            notification_count = 0
            for user_id in selected_users:
                create_notification(
                    user_id, 
                    message_type, 
                    {
                        'message': message_text,
                        'sender': 'Admin'
                    }
                )
                notification_count += 1
            
            return jsonify({
                'success': True, 
                'notifications_sent': notification_count
            })
        else:
            # Все пользователи
            query = users_ref
        
        # Для всех и верифицированных/неверифицированных
        users = query.stream()
        
        notification_count = 0
        for user_doc in users:
            create_notification(
                user_doc.id, 
                message_type, 
                {
                    'message': message_text,
                    'sender': 'Admin'
                }
            )
            notification_count += 1
        
        return jsonify({
            'success': True, 
            'notifications_sent': notification_count
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500
if __name__ == '__main__':
    app.run(debug=True)