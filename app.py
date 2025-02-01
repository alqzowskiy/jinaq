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
from flask import jsonify, url_for
from firebase_admin import firestore
from dotenv import load_dotenv
import gunicorn
app = Flask(__name__)
app.secret_key = 'mega-secret-key-yeah'  
app.config['LOGO_SVG_PATH'] = 'jinaq_logo.svg'
firebase_creds_str = os.getenv('FIREBASE_PRIVATE_KEY')
ADMIN_IDS = os.getenv("ADMIN_IDS")
if not firebase_creds_str:
    raise ValueError("FIREBASE_PRIVATE_KEY не найден в .env файле")
# Преобразуем строку в словарь
firebase_credentials = json.loads(firebase_creds_str)
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
# Расширенная конфигурация типов уведомлений
ENHANCED_NOTIFICATION_TYPES = {
    **NOTIFICATION_TYPES,  # Сначала базовые типы
    'system': {  # Затем переопределяем системные
        'icon': '🌐',
        'label': 'System Notification',
        'priority': 'high',
        'sender': {
            'username': 'Jinaq',
            'verified': True,
            'verification_type': 'system'
        }
    },
    'admin_message': {
        'icon': '🏛️', 
        'label': 'Administrative Message', 
        'priority': 'critical',
        'sender': {
            'username': 'Jinaq Admin',
            'verified': True,
            'verification_type': 'official'
        }
    },
    'important': {
        'icon': '❗', 
        'label': 'Important Notification', 
        'priority': 'high',
        'sender': {
            'username': 'Jinaq Alert',
            'verified': True,
            'verification_type': 'system'
        }
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
    
    # Detailed logging
    print("Full Request Data:", request.get_data(as_text=True))
    print("Request Headers:", dict(request.headers))
    print("Content Type:", request.content_type)
    
    # Force JSON parsing with error handling
    try:
        data = request.get_json(force=True)
        
        # Validate data structure
        if not isinstance(data, dict):
            print("Invalid data type:", type(data))
            return jsonify({
                'success': False, 
                'error': 'Invalid data format'
            }), 400

        # Comprehensive data validation
        required_keys = ['gpa', 'sat_score', 'toefl_score', 'ielts_score', 'languages', 'achievements']
        for key in required_keys:
            if key not in data:
                print(f"Missing key: {key}")
                return jsonify({
                    'success': False, 
                    'error': f'Missing required key: {key}'
                }), 400

        # Sanitize and validate each field
        academic_info = {
            'gpa': str(data.get('gpa', '')).strip(),
            'sat_score': str(data.get('sat_score', '')).strip(),
            'toefl_score': str(data.get('toefl_score', '')).strip(),
            'ielts_score': str(data.get('ielts_score', '')).strip(),
            'languages': data.get('languages', []),
            'achievements': data.get('achievements', [])
        }

        # Update Firestore
        db.collection('users').document(user_id).update({
            'academic_info': academic_info
        })

        return jsonify({'success': True, 'message': 'Academic portfolio updated'})

    except Exception as e:
        print(f"Academic Portfolio Update Error: {e}")
        return jsonify({
            'success': False, 
            'error': str(e)
        }), 400


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

        create_notification(
            user_id, 
            'account_change', 
            {
                'action': 'email_updated',
                'new_email': new_email,
                'message': f'Your email has been updated to {new_email}'
            }
        )

        return jsonify({'success': True, 'message': 'Email updated successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
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
        users_ref = db.collection('users')
        query = users_ref.where('username', '==', username.lower()).limit(1).stream()
        user_doc = next(query, None)

        if user_doc is None:
            return jsonify({'error': 'User not found'}), 404

        target_user_id = user_doc.id
        reply_text = request.form.get('reply')
        original_comment_id = request.form.get('original_comment_id', comment_id)

        if not reply_text or len(reply_text.strip()) == 0:
            return jsonify({'error': 'Reply text is required'}), 400

        # Получаем оригинальный комментарий
        comment_ref = db.collection('users').document(target_user_id).collection('comments').document(original_comment_id)
        comment_doc = comment_ref.get()
        
        if not comment_doc.exists:
            return jsonify({'error': 'Comment not found'}), 404
            
        comment_data = comment_doc.to_dict()
        
        # Проверяем, что автор ответа не является автором комментария
        if session['user_id'] != comment_data['author_id']:
            create_notification(
                comment_data['author_id'],
                'reply_comment',
                {
                    'original_comment_text': comment_data['text'],
                    'reply_text': reply_text.strip(),
                    'reply_chain': comment_data.get('reply_chain', [])
                },
                sender_id=session['user_id'],
                related_id=original_comment_id
            )

        # Определяем уровень вложенности и цепочку ответов
        reply_chain = comment_data.get('reply_chain', [])
        if 'parent_id' in comment_data:
            reply_chain = comment_data.get('reply_chain', [])
        reply_chain.append(original_comment_id)

        # Создаём данные ответа
        reply_data = {
            'author_id': session['user_id'],
            'author_username': session['username'],
            'text': reply_text.strip(),
            'created_at': datetime.datetime.now(tz=datetime.timezone.utc),
            'parent_id': comment_id,  # ID комментария, к которому делается ответ
            'reply_chain': reply_chain,
            'reply_to_username': comment_data['author_username'],
            'reply_level': len(reply_chain),
            'likes': []
        }

        # Сохраняем ответ
        reply_ref = db.collection('users').document(target_user_id).collection('comments').add(reply_data)

        # Получаем данные автора для ответа
        author_doc = db.collection('users').document(session['user_id']).get()
        author_data = author_doc.to_dict()

        # Подготавливаем ответ
        response_data = {
            'status': 'success',
            'reply': {
                'id': reply_ref[1].id,
                **reply_data,
                'author_avatar': generate_avatar_url(author_data),
                'author_verified': author_data.get('verified', False),
                'author_verification_type': author_data.get('verification_type'),
                'likes_count': 0,
                'is_liked': False
            }
        }

        return jsonify(response_data), 201

    except Exception as e:
        print(f"Error in reply_to_comment: {str(e)}")
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
                    'comment_text': comment_data['text']
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

            # Проверка блокировки
            if user_data.get('blocked', False):
                flash('This account has been blocked. Please contact support.')
                return redirect(url_for('login'))

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
@app.route('/<username>/comments', methods=['GET', 'POST'])
def comments(username):
    if request.method == 'POST':
        # Логика для создания комментария
        if 'user_id' not in session:
            return jsonify({'error': 'Authentication required'}), 401

        comment_text = request.form.get('comment')
        if not comment_text or len(comment_text.strip()) == 0:
            return jsonify({'error': 'Comment text is required'}), 400
        
        if len(comment_text) > 500:
            return jsonify({'error': 'Comment is too long'}), 400

        try:
            # Находим пользователя, на чей профиль оставляют комментарий
            users_ref = db.collection('users')
            query = users_ref.where('username', '==', username.lower()).limit(1).stream()
            user_doc = next(query, None)

            if user_doc is None:
                return jsonify({'error': 'User not found'}), 404

            target_user_id = user_doc.id

            # Создаем данные комментария
            comment_data = {
                'author_id': session['user_id'],
                'author_username': session['username'],
                'text': comment_text.strip(),
                'created_at': datetime.datetime.now(tz=datetime.timezone.utc),
                'likes': []
            }

            # Сохраняем комментарий
            comment_ref = db.collection('users').document(target_user_id).collection('comments').add(comment_data)
            
            # Получаем данные автора для ответа
            author_doc = db.collection('users').document(session['user_id']).get()
            author_data = author_doc.to_dict()
            
            # Создаем уведомление, если комментарий не от владельца профиля
            if session['user_id'] != target_user_id:
                create_notification(
                    target_user_id,
                    'profile_comment',
                    {
                        'commenter_username': session['username'],
                        'comment_text': comment_text.strip()
                    },
                    sender_id=session['user_id'],
                    related_id=comment_ref[1].id
                )

            # Подготавливаем ответ
            response_data = {
                'status': 'success',
                'comment': {
                    'id': comment_ref[1].id,
                    **comment_data,
                    'author_avatar': generate_avatar_url(author_data),
                    'likes_count': 0,
                    'is_liked': False
                }
            }

            return jsonify(response_data), 201

        except Exception as e:
            print(f"Error creating comment: {str(e)}")
            return jsonify({'error': str(e)}), 500

    # GET-запрос (существующая логика)
    try:
        # Find user by username (case-insensitive)
        users_ref = db.collection('users')
        query = users_ref.where('username', '==', username.lower()).limit(1).stream()
        user_doc = next(query, None)

        if user_doc is None:
            return jsonify({'error': 'User not found'}), 404

        target_user_id = user_doc.id

        # Получаем все комментарии с их ответами
        comments_ref = db.collection('users').document(target_user_id).collection('comments')
        comments_query = comments_ref.order_by('created_at', direction=firestore.Query.DESCENDING)
        
        # Получаем все комментарии
        all_comments = comments_query.stream()
        
        # Создаем словари для main comments и replies
        main_comments = {}
        replies = {}

        # Первый проход: собираем все комментарии и replies
        for comment_doc in all_comments:
            comment = comment_doc.to_dict()
            comment['id'] = comment_doc.id
            
            # Получаем аватар автора
            author_doc = db.collection('users').document(comment['author_id']).get()
            author_data = author_doc.to_dict()
            
            comment['author_avatar'] = generate_avatar_url(author_data)
            comment['likes_count'] = len(comment.get('likes', []))
            comment['is_liked'] = session.get('user_id') in comment.get('likes', [])
            
            # Если это ответ (есть parent_id)
            if 'parent_id' in comment:
                if comment['parent_id'] not in replies:
                    replies[comment['parent_id']] = []
                replies[comment['parent_id']].append(comment)
            else:
                # Это основной комментарий
                main_comments[comment_doc.id] = comment

        # Второй проход: добавляем replies к основным комментариям
        for comment_id, comment in main_comments.items():
            if comment_id in replies:
                # Сортируем ответы по дате создания
                sorted_replies = sorted(replies[comment_id], key=lambda x: x['created_at'])
                
                # Рекурсивно обрабатываем вложенные ответы
                def process_nested_replies(reply_list):
                    for reply in reply_list:
                        nested_replies = [r for r in replies.get(reply['id'], []) if r.get('parent_id') == reply['id']]
                        if nested_replies:
                            reply['replies'] = sorted(nested_replies, key=lambda x: x['created_at'])
                            process_nested_replies(reply['replies'])
                    return reply_list
                
                comment['replies'] = process_nested_replies(sorted_replies)

        return jsonify(list(main_comments.values()))

    except Exception as e:
        print(f"Error in comments route: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/<username>/comments/<comment_id>/replies', methods=['GET'])
def get_comment_replies(username, comment_id):
    try:
        users_ref = db.collection('users')
        query = users_ref.where('username', '==', username.lower()).limit(1).stream()
        user_doc = next(query, None)

        if user_doc is None:
            return jsonify({'error': 'User not found'}), 404

        target_user_id = user_doc.id
        replies = db.collection('users').document(target_user_id).collection('comments').where('parent_id', '==', comment_id).order_by('created_at').stream()
        
        replies_list = []
        for reply_doc in replies:
            reply = reply_doc.to_dict()
            reply['id'] = reply_doc.id
            
            author_doc = db.collection('users').document(reply['author_id']).get()
            author_data = author_doc.to_dict()
            
            reply['author_avatar'] = author_data.get('avatar_url', url_for('static', filename='default-avatar.png'))
            reply['likes_count'] = len(reply.get('likes', []))
            reply['is_liked'] = session.get('user_id') in reply.get('likes', [])
            
            replies_list.append(reply)
            
        return jsonify(replies_list)
        
    except Exception as e:
        print(f"Error in get_comment_replies: {str(e)}")
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
    if user_data.get('blocked', False):
        # Redirect to 404 for blocked users
        abort(404)
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
        # Additional logging for debugging
        print(f"Attempting to access profile for username: {username}")
        
        # Find user without case sensitivity
        users_ref = db.collection('users')
        query = users_ref.where('username', '==', username.lower()).limit(1).stream()
        user_doc = next(query, None)

        # Log query results
        if user_doc is None:
            print(f"No user found with username: {username}")
            abort(404, description=f"User '{username}' not found")

        viewed_user_data = user_doc.to_dict()
        
        # Log user data
        print(f"User data: {viewed_user_data}")
        
        # Check if the viewed profile is blocked
        if viewed_user_data.get('blocked', False):
            print(f"Profile for {username} is blocked")
            abort(404, description="User profile not available")
        
        viewed_user_avatar = generate_avatar_url(viewed_user_data)
        
        # Get current user's avatar if logged in
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
        # Log the full error details
        print(f"Comprehensive error in public_profile: {e}")
        import traceback
        traceback.print_exc()
        
        # Re-raise to let Flask's error handler catch it
        raise
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
@app.route('/admin/add_admin', methods=['POST'])
@login_required
def add_admin():
    # Список суперадминов
    SUPER_ADMIN_IDS = ['vVbXL4LKGidXtrKnvqa21gWRY3V2']

    if session['user_id'] not in SUPER_ADMIN_IDS:
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.json
    user_id = data.get('user_id')
    
    try:
        # Обновляем документ пользователя, добавляя ему права администратора
        db.collection('users').document(user_id).update({
            'is_admin': True,
            'admin_added_by': session['user_id'],
            'admin_added_at': firestore.SERVER_TIMESTAMP
        })

        # Создаем уведомление пользователю
        create_notification(
            user_id, 
            'account_change', 
            {
                'message': 'You have been granted admin access.'
            },
            sender_id=session['user_id']
        )

        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
@app.route('/admin/verify_user', methods=['POST'])
@login_required
def verify_user():
    # List of administrators who can verify
    ADMIN_IDS = ['vVbXL4LKGidXtrKnvqa21gWRY3V2']  # Replace with actual admin user ID

    # Debug logging
    print(f"Verification attempt by user: {session.get('user_id')}")

    if session['user_id'] not in ADMIN_IDS:
        print("Unauthorized verification attempt")
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
    
    try:
        # Get JSON data from request
        data = request.get_json()
        
        # Validate input
        user_id = data.get('user_id')
        verification_type = data.get('type', 'official')
        
        if not user_id:
            print("No user ID provided")
            return jsonify({'success': False, 'error': 'User ID is required'}), 400

        # Validate verification type
        valid_types = ['official', 'creator', 'business', 'remove']
        if verification_type not in valid_types:
            print(f"Invalid verification type: {verification_type}")
            return jsonify({'success': False, 'error': 'Invalid verification type'}), 400

        # Get user document
        user_ref = db.collection('users').document(user_id)
        user_doc = user_ref.get()
        
        if not user_doc.exists:
            print(f"User not found: {user_id}")
            return jsonify({'success': False, 'error': 'User not found'}), 404
        
        user_data = user_doc.to_dict()
        
        # Determine verification update
        update_data = {
            'verified': verification_type != 'remove',
            'verification_type': None if verification_type == 'remove' else verification_type,
            'verified_by': session['user_id'] if verification_type != 'remove' else None,
            'verified_at': firestore.SERVER_TIMESTAMP if verification_type != 'remove' else None
        }
        
        # Perform update
        try:
            user_ref.update(update_data)
        except Exception as update_error:
            print(f"Database update error: {update_error}")
            return jsonify({'success': False, 'error': 'Failed to update user verification'}), 500

        # Create notification based on verification action
        if verification_type == 'remove':
            create_notification(
                user_id, 
                'account_change', 
                {
                    'message': 'Your account verification has been revoked.',
                    'action': 'verification_revoked'
                },
                sender_id=session['user_id']
            )
        else:
            create_notification(
                user_id, 
                'verification', 
                {
                    'message': f'Your account has been verified as a {verification_type} account.',
                    'verification_type': verification_type
                },
                sender_id=session['user_id']
            )

        # Log the verification action
        print(f"User {user_id} verified as {verification_type}")
        
        return jsonify({
            'success': True, 
            'message': f'User verified as {verification_type}',
            'verification_type': verification_type
        })
    
    except Exception as e:
        # Catch-all for any unexpected errors
        print(f"Unexpected error in user verification: {e}")
        return jsonify({
            'success': False, 
            'error': 'An error occurred while verifying the user.',
            'details': str(e)
        }), 500
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
    try:
        # Определение отправителя
        if sender_id:
            try:
                sender_doc = db.collection('users').document(sender_id).get()
                sender_data = sender_doc.to_dict()
                sender_info = {
                    'username': sender_data.get('display_username', sender_data.get('username', 'Jinaq')),
                    'avatar_url': generate_avatar_url(sender_data),
                    'verified': sender_data.get('verified', False),
                    'verification_type': sender_data.get('verification_type')
                }
            except Exception as e:
                print(f"Error fetching sender info: {e}")
                sender_info = None
        else:
            # Использование дефолтных данных из конфигурации типов
            type_config = ENHANCED_NOTIFICATION_TYPES.get(type, {})
            sender_info = type_config.get('sender', {
                'username': 'Jinaq',
                'avatar_url': generate_avatar_url({'username': 'Jinaq'}),
                'verified': True,
                'verification_type': 'system'
            })

        # Обогащение контента уведомления
        notification_config = ENHANCED_NOTIFICATION_TYPES.get(type, {})
        enriched_content = {
            'type_label': notification_config.get('label', 'Notification'),
            'icon': notification_config.get('icon', '🔔'),
            'priority': notification_config.get('priority', 'normal'),
            **content  # Сохраняем original content
        }

        # Специальная обработка для уведомлений об изменении аккаунта
        if type == 'account_change':
            action = content.get('action')
            if action == 'email_updated':
                enriched_content['message'] = f"Email updated to {content.get('new_email')}"
            elif action == 'password_changed':
                enriched_content['message'] = "Password has been changed"
            elif not enriched_content.get('message'):
                enriched_content['message'] = "Account settings have been updated"

        # Формирование полных данных уведомления
        notification_data = {
            'type': type,
            'content': enriched_content,
            'sender_info': sender_info,
            'sender_id': sender_id,
            'related_id': related_id,
            'is_read': False,
            'created_at': firestore.SERVER_TIMESTAMP,
            'recipient_id': user_id,
            'metadata': {
                'timestamp': datetime.datetime.now(tz=datetime.timezone.utc),
                'source': 'server',
                'version': '1.1'
            }
        }

        # Добавление расширенной маршрутизации и фильтрации
        if notification_config.get('priority') == 'critical':
            notification_data['is_pinned'] = True

        # Сохранение уведомления
        notification_ref = db.collection('users').document(user_id).collection('notifications').document()
        notification_ref.set(notification_data)

        return notification_ref.id

    except Exception as e:
        print(f"Comprehensive Notification Creation Error: {e}")
        return None

@app.route('/notifications/<notification_id>/details', methods=['GET'])
@login_required
def get_notification_details(notification_id):
    """Get full details for a notification including all related data"""
    user_id = session['user_id']
    
    try:
        notification_ref = db.collection('users').document(user_id).collection('notifications').document(notification_id)
        notification = notification_ref.get()
        
        if not notification.exists:
            return jsonify({'error': 'Notification not found'}), 404
            
        notification_data = notification.to_dict()
        
        # Дополняем данные в зависимости от типа уведомления
        if notification_data['type'] == 'reply_comment' and notification_data.get('related_id'):
            comment_id = notification_data['related_id']
            comment_ref = db.collection('users').document(user_id).collection('comments').document(comment_id)
            comment_data = comment_ref.get().to_dict()
            
            if comment_data:
                notification_data['comment_details'] = {
                    'text': comment_data['text'],
                    'created_at': comment_data['created_at'],
                    'author_username': comment_data['author_username']
                }

        return jsonify(notification_data)
    except Exception as e:
        print(f"Error getting notification details: {e}")
        return jsonify({'error': 'Failed to get notification details'}), 500
@app.route('/notifications', methods=['GET'])
@login_required
def get_notifications():
    user_id = session['user_id']
    
    try:
        notifications_ref = db.collection('users').document(user_id).collection('notifications')
        notifications = notifications_ref.order_by('created_at', direction=firestore.Query.DESCENDING).limit(20).stream()
        
        notification_list = []
        for notification_doc in notifications:
            notification = notification_doc.to_dict()
            notification['id'] = notification_doc.id
            
            # Получаем конфигурацию типа уведомления из расширенного списка
            notification_type = notification['type']
            notification_type_info = ENHANCED_NOTIFICATION_TYPES.get(notification_type, {})
            
            # Добавляем иконку и метку из конфигурации
            notification['icon'] = notification_type_info.get('icon', '🔔')
            notification['type_label'] = notification_type_info.get('label', 'Notification')
            
            # Для системных уведомлений используем информацию об отправителе из конфигурации
            if notification_type in ['system', 'admin_message', 'important']:
                sender_config = notification_type_info.get('sender', {})
                notification['sender_info'] = {
                    'username': sender_config.get('username', 'Jinaq'),
                    'verified': sender_config.get('verified', True),
                    'verification_type': sender_config.get('verification_type', 'system'),
                    'avatar_url': url_for('static', filename='jinaq_logo.svg')  # Используем url_for для корректного пути
                }
            
            # Для обычных уведомлений обрабатываем sender_info как раньше
            elif notification.get('sender_info'):
                sender_info = notification['sender_info']
                notification['sender_info']['avatar_url'] = sender_info.get('avatar_url') or generate_avatar_url({
                    'username': sender_info['username']
                })
                notification['sender_verified'] = sender_info.get('verified', False)
                notification['sender_verification_type'] = sender_info.get('verification_type')
            
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
        # Получаем данные администратора
        admin_doc = db.collection('users').document(session['user_id']).get()
        admin_data = admin_doc.to_dict()
        
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
                        'sender': admin_data.get('display_username', 'Admin')
                    },
                    sender_id=session['user_id']
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
                    'sender': admin_data.get('display_username', 'Admin')
                },
                sender_id=session['user_id']
            )
            notification_count += 1
        
        return jsonify({
            'success': True, 
            'notifications_sent': notification_count
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500
@app.route('/admin/toggle_user_block', methods=['POST'])
@login_required
def toggle_user_block():
    # List of super admins who can block users
    SUPER_ADMIN_IDS = ['vVbXL4LKGidXtrKnvqa21gWRY3V2']

    if session['user_id'] not in SUPER_ADMIN_IDS:
        return jsonify({'success': False, 'error': 'Unauthorized access'}), 403
    
    data = request.json
    user_id = data.get('user_id')
    
    try:
        # Get the current user document
        user_ref = db.collection('users').document(user_id)
        user_doc = user_ref.get()
        
        if not user_doc.exists:
            return jsonify({'success': False, 'error': 'User not found'}), 404
        
        user_data = user_doc.to_dict()
        
        # Toggle block status
        current_blocked_status = user_data.get('blocked', False)
        new_blocked_status = not current_blocked_status
        
        # Update user document
        user_ref.update({
            'blocked': new_blocked_status,
            'blocked_at': firestore.SERVER_TIMESTAMP if new_blocked_status else None,
            'blocked_by': session['user_id'] if new_blocked_status else None
        })
        
        # Create a notification for the user
        create_notification(
            user_id, 
            'account_change', 
            {
                'message': f'Your account has been {"blocked" if new_blocked_status else "unblocked"} by an admin.',
                'action': 'account_blocked' if new_blocked_status else 'account_unblocked'
            },
            sender_id=session['user_id']
        )
        
        return jsonify({
            'success': True, 
            'blocked': new_blocked_status,
            'message': f'User has been {"blocked" if new_blocked_status else "unblocked"} successfully.'
        })
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
# Add error handlers
# Add error handlers
@app.errorhandler(404)
def page_not_found(e):
    # Additional logging for debugging
    print(f"404 Error: {e}")
    
    # Optional: Log the request details for more context
    print(f"Request URL: {request.url}")
    print(f"Request Method: {request.method}")
    
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    # Additional logging for debugging
    print(f"500 Error: {e}")
    print(f"Request URL: {request.url}")
    print(f"Request Method: {request.method}")
    
    return render_template('500.html'), 500

# Explicitly enable debug mode to get more detailed error information
app.config['DEBUG'] = True

# Optional: Add a route to test error handling
@app.route('/test_404')
def test_404():
    abort(404)

@app.route('/test_500')
def test_500():
    abort(500)
if __name__ == '__main__':
    app.run(debug=True)