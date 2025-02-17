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
import geocoder
import requests
from flask import jsonify
from geopy.geocoders import Nominatim


app = Flask(__name__)
app.secret_key = 'mega-secret-key-yeah'  
app.config['LOGO_SVG_PATH'] = 'jinaq_logo.svg'
firebase_creds_str = os.getenv('FIREBASE_PRIVATE_KEY')
ADMIN_IDS = os.getenv("ADMIN_IDS")
if not firebase_creds_str:
    raise ValueError("FIREBASE_PRIVATE_KEY не найден в .env файле")
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

ENHANCED_NOTIFICATION_TYPES = {
    **NOTIFICATION_TYPES,
    'system': { 
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

cred = credentials.Certificate(firebase_credentials)
firebase_admin.initialize_app(cred, {
    'storageBucket': 'jinaq-1b755.firebasestorage.app'
})

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

app.config['INTERNSHIP_IMAGES'] = 'static/internship_images'
if not os.path.exists(app.config['INTERNSHIP_IMAGES']):
    os.makedirs(app.config['INTERNSHIP_IMAGES'])

# Add this schema to your database
internships_schema = """
CREATE TABLE IF NOT EXISTS internships (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    company TEXT NOT NULL,
    description TEXT NOT NULL,
    requirements TEXT,
    location TEXT NOT NULL,
    start_date TIMESTAMP,
    end_date TIMESTAMP,
    image_url TEXT,
    created_at TIMESTAMP,
    created_by TEXT,
    status TEXT DEFAULT 'active',
    area TEXT,
    format TEXT,
    address TEXT,
    positions INTEGER DEFAULT 1
)
"""


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
# Add this route to handle skills updates
@app.route('/update-skills', methods=['POST'])
@login_required
def update_skills():
    user_id = session['user_id']
    data = request.json
    
    try:
        # Clean and validate skills
        skills = [skill.strip() for skill in data.get('skills', []) if skill.strip()]
        
        # Update user document
        db.collection('users').document(user_id).update({
            'skills': skills,
            'updated_at': datetime.datetime.now(tz=datetime.timezone.utc)
        })
        
        return jsonify({'success': True, 'message': 'Skills updated successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
@app.route('/update_academic_portfolio', methods=['POST'])
@login_required
def update_academic_portfolio():
    user_id = session['user_id']
    
    # Detailed logging
    print("Full Request Data:", request.get_data(as_text=True))
    print("Request Headers:", dict(request.headers))
    print("Content Type:", request.content_type)
    

    try:
        data = request.get_json(force=True)
        

        if not isinstance(data, dict):
            print("Invalid data type:", type(data))
            return jsonify({
                'success': False, 
                'error': 'Invalid data format'
            }), 400


        required_keys = ['gpa', 'sat_score', 'toefl_score', 'ielts_score', 'languages', 'achievements']
        for key in required_keys:
            if key not in data:
                print(f"Missing key: {key}")
                return jsonify({
                    'success': False, 
                    'error': f'Missing required key: {key}'
                }), 400


        academic_info = {
            'gpa': str(data.get('gpa', '')).strip(),
            'sat_score': str(data.get('sat_score', '')).strip(),
            'toefl_score': str(data.get('toefl_score', '')).strip(),
            'ielts_score': str(data.get('ielts_score', '')).strip(),
            'languages': data.get('languages', []),
            'achievements': data.get('achievements', [])
        }

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

        user_doc = db.collection('users').document(user_id).get()
        user_data = user_doc.to_dict()
        current_email = user_data['email']
        
        
        user = auth.update_user(
            user_id,
            email=new_email
        )
        
        
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



@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        display_username = request.form['username'] 
        username = display_username.lower()

        try:
            # Проверка уникальности username
            users_ref = db.collection('users')
            username_query = users_ref.where('username', '==', username).get()
            if len(list(username_query)) > 0:
                flash('Username already taken')
                return redirect(url_for('register'))

            user = auth.create_user(
                email=email,
                password=password,
                display_name=display_username
            )

            user_data = {
                'username': username,
                'display_username': display_username, 
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


        comment_ref = db.collection('users').document(target_user_id).collection('comments').document(original_comment_id)
        comment_doc = comment_ref.get()
        
        if not comment_doc.exists:
            return jsonify({'error': 'Comment not found'}), 404
            
        comment_data = comment_doc.to_dict()
        

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


        reply_chain = comment_data.get('reply_chain', [])
        if 'parent_id' in comment_data:
            reply_chain = comment_data.get('reply_chain', [])
        reply_chain.append(original_comment_id)


        reply_data = {
            'author_id': session['user_id'],
            'author_username': session['username'],
            'text': reply_text.strip(),
            'created_at': datetime.datetime.now(tz=datetime.timezone.utc),
            'parent_id': comment_id, 
            'reply_chain': reply_chain,
            'reply_to_username': comment_data['author_username'],
            'reply_level': len(reply_chain),
            'likes': []
        }

        reply_ref = db.collection('users').document(target_user_id).collection('comments').add(reply_data)


        author_doc = db.collection('users').document(session['user_id']).get()
        author_data = author_doc.to_dict()


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

        if current_user_id in likes:
            likes.remove(current_user_id)
        else:
            likes.append(current_user_id)




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
        identifier = request.form['identifier']  
        password = request.form['password']
        
        try:

            try:
                user = auth.get_user_by_email(identifier)
                email = identifier
            except:

                users_ref = db.collection('users')
                query = users_ref.where('username', '==', identifier.lower()).limit(1).get()
                
                if not query:
                    flash('User not found')
                    return redirect(url_for('login'))
                
                user_data = query[0].to_dict()
                email = user_data['email']

                user = auth.get_user_by_email(email)
            

            user_doc = db.collection('users').document(user.uid).get()
            user_data = user_doc.to_dict()


            if user_data.get('blocked', False):
                flash('This account has been blocked. Please contact support.')
                return redirect(url_for('login'))

            if user_data:

                session['user_id'] = user.uid
                session['username'] = user_data.get('display_username', user_data['username'])
                return redirect(url_for('profile'))
            else:
                flash('User data not found')
                return redirect(url_for('login'))

        except Exception as e:
            print(f"Login error: {str(e)}")
            flash('Login failed: Invalid credentials')
            return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/delete-certificate/<cert_id>', methods=['DELETE'])
@login_required
def delete_certificate(cert_id):
    try:
        user_id = session['user_id']
        

        cert_ref = db.collection('users').document(user_id).collection('certificates').document(cert_id)
        cert_doc = cert_ref.get()
        
        if not cert_doc.exists:
            return jsonify({'error': 'Certificate not found'}), 404
            
        cert_data = cert_doc.to_dict()
        

        if 'file_url' in cert_data:
            try:

                file_path = cert_data['file_url'].split('/')[-1]
                blob = bucket.blob(f'certificates/{user_id}/{file_path}')
                blob.delete()
            except Exception as e:
                print(f"Error deleting file from storage: {e}")
        

        cert_ref.delete()
        
        return jsonify({'status': 'success'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
@app.route('/<username>/comments', methods=['GET', 'POST'])
def comments(username):
    if request.method == 'POST':

        if 'user_id' not in session:
            return jsonify({'error': 'Authentication required'}), 401

        comment_text = request.form.get('comment')
        if not comment_text or len(comment_text.strip()) == 0:
            return jsonify({'error': 'Comment text is required'}), 400
        
        if len(comment_text) > 500:
            return jsonify({'error': 'Comment is too long'}), 400

        try:

            users_ref = db.collection('users')
            query = users_ref.where('username', '==', username.lower()).limit(1).stream()
            user_doc = next(query, None)

            if user_doc is None:
                return jsonify({'error': 'User not found'}), 404

            target_user_id = user_doc.id

            comment_data = {
                'author_id': session['user_id'],
                'author_username': session['username'],
                'text': comment_text.strip(),
                'created_at': datetime.datetime.now(tz=datetime.timezone.utc),
                'likes': []
            }


            comment_ref = db.collection('users').document(target_user_id).collection('comments').add(comment_data)
            

            author_doc = db.collection('users').document(session['user_id']).get()
            author_data = author_doc.to_dict()
            

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


    try:

        users_ref = db.collection('users')
        query = users_ref.where('username', '==', username.lower()).limit(1).stream()
        user_doc = next(query, None)

        if user_doc is None:
            return jsonify({'error': 'User not found'}), 404

        target_user_id = user_doc.id


        comments_ref = db.collection('users').document(target_user_id).collection('comments')
        comments_query = comments_ref.order_by('created_at', direction=firestore.Query.DESCENDING)

        all_comments = comments_query.stream()
        

        main_comments = {}
        replies = {}


        for comment_doc in all_comments:
            comment = comment_doc.to_dict()
            comment['id'] = comment_doc.id

            author_doc = db.collection('users').document(comment['author_id']).get()
            author_data = author_doc.to_dict()
            
            comment['author_avatar'] = generate_avatar_url(author_data)
            comment['likes_count'] = len(comment.get('likes', []))
            comment['is_liked'] = session.get('user_id') in comment.get('likes', [])

            if 'parent_id' in comment:
                if comment['parent_id'] not in replies:
                    replies[comment['parent_id']] = []
                replies[comment['parent_id']].append(comment)
            else:

                main_comments[comment_doc.id] = comment


        for comment_id, comment in main_comments.items():
            if comment_id in replies:

                sorted_replies = sorted(replies[comment_id], key=lambda x: x['created_at'])
                
                
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
     
        users_ref = db.collection('users')
        query = users_ref.where('username', '==', username).limit(1).stream()
        user_doc = next(query, None)

        if user_doc is None:
            return jsonify({'error': 'User not found'}), 404

        target_user_id = user_doc.id
        
      
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
    """Генерирует URL аватарки для пользователя"""
    if not user_data:
        return "https://ui-avatars.com/api/?name=U&background=random&color=fff&size=128"
    
  
    if user_data.get('avatar_url'):
        return user_data['avatar_url']
    
  
    display_name = user_data.get('display_username', user_data.get('username', 'U'))
    initials = ''.join(word[0].upper() for word in display_name.split()[:2])
    
    return f"https://ui-avatars.com/api/?name={initials}&background=random&color=fff&size=128"
def get_user_location():
    try:
        # Try to get IP address
        if request.headers.get('X-Forwarded-For'):
            ip = request.headers.get('X-Forwarded-For').split(',')[0]
        else:
            ip = request.remote_addr
            
        # Get location data from IP
        g = geocoder.ip(ip)
        if g.ok:
            return {
                'city': g.city,
                'country': g.country,
                'coordinates': {
                    'lat': g.lat,
                    'lng': g.lng
                }
            }
    except Exception as e:
        print(f"Error getting location: {e}")
    return None

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    user_id = session['user_id']
    
    try:
        user_doc = db.collection('users').document(user_id).get()
        user_data = user_doc.to_dict() or {}
        
        avatar_url = generate_avatar_url(user_data)
        
        # Check if user is blocked
        if user_data.get('blocked', False):
            abort(404)

        current_user_avatar = avatar_url
        if not user_data.get('location'):
            location = get_user_location()
            if location:
                user_data['location'] = location
                db.collection('users').document(user_id).update({
                    'location': location
                })
        
        # Initialize academic info if not present
        if 'academic_info' not in user_data:
            user_data['academic_info'] = {
                'gpa': '',
                'sat_score': '',
                'toefl_score': '',
                'ielts_score': '',
                'languages': [],
                'achievements': []
            }

        # POST request handling
        if request.method == 'POST':
            try:
                # Handle JSON updates (AJAX requests)
                if request.headers.get('Content-Type') == 'application/json':
                    data = request.get_json()
                    
                    # Handle links update
                    if data.get('action') == 'update_links':
                        links = data.get('links', [])
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
                        
                        db.collection('users').document(user_id).update({
                            'links': processed_links,
                            'updated_at': datetime.datetime.now(tz=datetime.timezone.utc)
                        })
                        return jsonify({'success': True})

                # Handle certificate upload
                if 'certificate' in request.files:
                    file = request.files['certificate']
                    title = request.form.get('title', file.filename)
                    
                    if file and file.filename:
                        file_extension = file.filename.rsplit('.', 1)[1].lower()
                        filename = f"certificates/{user_id}/{str(uuid.uuid4())}.{file_extension}"
                        
                        blob = bucket.blob(filename)
                        blob.upload_from_string(
                            file.read(),
                            content_type=file.content_type
                        )
                        
                        blob.make_public()
                        
                        cert_data = {
                            'title': title,
                            'file_url': blob.public_url,
                            'uploaded_at': datetime.datetime.now(tz=datetime.timezone.utc)
                        }
                        
                        cert_ref = db.collection('users').document(user_id).collection('certificates').add(cert_data)
                        
                        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                            return jsonify({
                                'success': True,
                                'certificate': {
                                    'id': cert_ref[1].id,
                                    **cert_data
                                }
                            })

                # Handle avatar upload
                if 'avatar' in request.files:
                    avatar_file = request.files['avatar']
                    if avatar_file and avatar_file.filename:
                        # Delete old avatar if exists
                        try:
                            if user_data.get('avatar_url'):
                                old_avatar_path = user_data['avatar_url'].split('/')[-1]
                                old_blob = bucket.blob(f'avatars/{user_id}/{old_avatar_path}')
                                old_blob.delete()
                        except Exception as e:
                            print(f"Error deleting old avatar: {e}")

                        # Upload new avatar
                        file_extension = avatar_file.filename.rsplit('.', 1)[1].lower()
                        filename = f"{str(uuid.uuid4())}.{file_extension}"
                        full_path = f"avatars/{user_id}/{filename}"
                        
                        blob = bucket.blob(full_path)
                        blob.upload_from_string(
                            avatar_file.read(),
                            content_type=avatar_file.content_type
                        )
                        
                        blob.make_public()
                        
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

                # Handle regular form submission
                if request.form:
                    profile_data = {
                        'full_name': request.form.get('full_name', ''),
                        'age': request.form.get('age', ''),
                        'specialty': request.form.get('specialty', ''),
                        'goals': request.form.get('goals', ''),
                        'bio': request.form.get('bio', ''),
                        'education': request.form.get('education', ''),
                        'updated_at': datetime.datetime.now(tz=datetime.timezone.utc)
                    }

                    # Convert age to integer if provided
                    if profile_data['age']:
                        try:
                            profile_data['age'] = int(profile_data['age'])
                        except ValueError:
                            del profile_data['age']

                    # Add social media and contact links
                    social_media = {
                        'linkedin': request.form.get('linkedin', ''),
                        'github': request.form.get('github', ''),
                        'twitter': request.form.get('twitter', ''),
                        'website': request.form.get('website', '')
                    }
                    profile_data['social_media'] = {k: v for k, v in social_media.items() if v}

                    # Update academic information
                    academic_info = {
                        'current_institution': request.form.get('current_institution', ''),
                        'field_of_study': request.form.get('field_of_study', ''),
                        'graduation_year': request.form.get('graduation_year', ''),
                        'research_interests': request.form.get('research_interests', '').split(','),
                        'achievements': request.form.getlist('achievements[]')
                    }
                    profile_data['academic_info'] = academic_info

                    # Update all profile data
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

        # Get certificates for display
        certificates = list(db.collection('users').document(user_id).collection('certificates').stream())
        
        # Get notifications count
        notifications_ref = db.collection('users').document(user_id).collection('notifications')
        unread_notifications = notifications_ref.where('is_read', '==', False).get()
        notifications_count = len(list(unread_notifications))

        # Render template with all necessary data
        return render_template('profile.html',
                            user_data=user_data,
                            avatar_url=avatar_url,
                            current_user_avatar=current_user_avatar,
                            certificates=certificates,
                            notifications_count=notifications_count,
                            social_media=user_data.get('social_media', {}),
                            academic_info=user_data.get('academic_info', {}))

    except Exception as e:
        print(f"Error in profile route: {e}")
        flash('An error occurred while loading your profile.')
        return redirect(url_for('index'))

@app.route('/<username>')
def public_profile(username):
    try:
        print(f"Attempting to access profile for username: {username}")
        
        users_ref = db.collection('users')
        query = users_ref.where('username', '==', username.lower()).limit(1).stream()
        user_doc = next(query, None)


        if user_doc is None:
            print(f"No user found with username: {username}")
            abort(404, description=f"User '{username}' not found")

        viewed_user_data = user_doc.to_dict()
        

        print(f"User data: {viewed_user_data}")
        

        if viewed_user_data.get('blocked', False):
            print(f"Profile for {username} is blocked")
            abort(404, description="User profile not available")
        
        viewed_user_avatar = generate_avatar_url(viewed_user_data)
        

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

        print(f"Comprehensive error in public_profile: {e}")
        import traceback
        traceback.print_exc()
        

        raise
from firebase_admin import auth

@app.route('/update_links', methods=['POST'])
def update_links():
    try:

        id_token = request.headers.get('Authorization')
        if not id_token:
            return jsonify(success=False, error="No token provided"), 401
            

        if id_token.startswith('Bearer '):
            id_token = id_token.split('Bearer ')[1]
            

        decoded_token = auth.verify_id_token(id_token)
        user_id = decoded_token['uid']
        

        data = request.get_json()
        links = data.get('links', [])
        

        if not isinstance(links, list):
            return jsonify(success=False, error="Invalid data format"), 400
            

        for link in links:
            if not isinstance(link, dict) or 'title' not in link or 'url' not in link:
                return jsonify(success=False, error="Invalid link format"), 400
        

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
@login_required  
def migrate_usernames():

    if session.get('user_id') != 'admin_user_id':  
        return "Unauthorized", 403
    
    users_ref = db.collection('users')
    users = users_ref.stream()
    
    for user_doc in users:
        user_data = user_doc.to_dict()
        

        if 'display_username' not in user_data:
            users_ref.document(user_doc.id).update({
                'username': user_data['username'].lower(),
                'display_username': user_data['username']
            })
    
    return "Migration completed successfully"    


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
    display_username = request.json.get('username') 
    
    try:

        users_ref = db.collection('users')
        username_query = users_ref.where('username', '==', new_username).get()
        if len(list(username_query)) > 0:
            return jsonify({'error': 'Username already taken'}), 400
            

        user_ref = db.collection('users').document(user_id)
        user_ref.update({
            'username': new_username,
            'display_username': display_username,
            'updated_at': datetime.datetime.now(tz=datetime.timezone.utc)
        })
        

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

        user_doc = db.collection('users').document(user_id).get()
        user_data = user_doc.to_dict()
        

        user = auth.get_user_by_email(user_data['email'])
        

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
    try:
        user_id = session['user_id']
        password = request.json.get('password')
        
        if not password:
            return jsonify({'error': 'Password is required'}), 400

        # Get user data from Firestore
        user_doc = db.collection('users').document(user_id).get()
        if not user_doc.exists:
            return jsonify({'error': 'User not found'}), 404
            
        user_data = user_doc.to_dict()
        
        try:
            # Get Firebase Auth user
            user = auth.get_user(user_id)
            
            # Clean up user data
            # 1. Delete user's certificates
            certificates_ref = db.collection('users').document(user_id).collection('certificates')
            certs = certificates_ref.stream()
            for cert in certs:
                # Delete certificate file from storage if exists
                cert_data = cert.to_dict()
                if cert_data.get('file_url'):
                    try:
                        file_path = cert_data['file_url'].split('/')[-1]
                        blob = bucket.blob(f'certificates/{user_id}/{file_path}')
                        blob.delete()
                    except Exception as e:
                        print(f"Error deleting certificate file: {e}")
                cert.reference.delete()

            # 2. Delete user's comments
            comments_ref = db.collection('users').document(user_id).collection('comments')
            comments = comments_ref.stream()
            for comment in comments:
                comment.reference.delete()

            # 3. Delete user's notifications
            notifications_ref = db.collection('users').document(user_id).collection('notifications')
            notifications = notifications_ref.stream()
            for notification in notifications:
                notification.reference.delete()

            # 4. Delete user's avatar if exists
            if user_data.get('avatar_url'):
                try:
                    avatar_path = user_data['avatar_url'].split('/')[-1]
                    avatar_blob = bucket.blob(f'avatars/{user_id}/{avatar_path}')
                    avatar_blob.delete()
                except Exception as e:
                    print(f"Error deleting avatar: {e}")

            # 5. Delete user's header image if exists
            if user_data.get('header_image', {}).get('url'):
                try:
                    header_path = user_data['header_image']['url'].split('/')[-1]
                    header_blob = bucket.blob(f'headers/{user_id}/{header_path}')
                    header_blob.delete()
                except Exception as e:
                    print(f"Error deleting header image: {e}")

            # 6. Delete user document from Firestore
            db.collection('users').document(user_id).delete()

            # 7. Delete user from Firebase Auth
            auth.delete_user(user_id)

            # 8. Clear session
            session.clear()
            
            return jsonify({
                'success': True, 
                'message': 'Account deleted successfully'
            })

        except auth.AuthError as auth_error:
            print(f"Auth error during account deletion: {auth_error}")
            return jsonify({
                'error': 'Authentication failed. Please check your password.'
            }), 401

    except Exception as e:
        print(f"Error during account deletion: {e}")
        return jsonify({
            'error': 'An error occurred while deleting your account. Please try again.'
        }), 500
@app.route('/reset-password', methods=['POST'])
def reset_password():
    try:
        email = request.json.get('email')
        if not email:
            return jsonify({
                'success': False,
                'error': 'Email is required'
            }), 400


        action_code_settings = auth.ActionCodeSettings(
            url=f"{request.host_url}login",
            handle_code_in_app=False
        )
        

        reset_link = auth.generate_password_reset_link(
            email,
            action_code_settings
        )
        

        print(f"Generated reset link for {email}")
        
        return jsonify({
            'success': True,
            'message': 'If an account exists with this email, password reset instructions have been sent.'
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
        results = {} 
        

        all_users = users_ref.stream()
        
        for user_doc in all_users:
            user_data = user_doc.to_dict()
            
            if not user_data or 'username' not in user_data:
                continue
                

            username = user_data.get('username', '').lower()
            display_username = user_data.get('display_username', '').lower()
            full_name = user_data.get('full_name', '').lower()
            

            if (query in username or 
                query in display_username or 
                query in full_name or 
                any(query in word.lower() for word in full_name.split())):
                

                results[user_doc.id] = {
                    'username': user_data.get('display_username', user_data['username']),
                    'full_name': user_data.get('full_name', ''),
                    'avatar': generate_avatar_url(user_data),
                    'verified': user_data.get('verified', False),
                    'verification_type': user_data.get('verification_type', None)
                }
        

        results_list = list(results.values())[:10]
        

        results_list.sort(key=lambda x: (
            not x['username'].lower().startswith(query), 
            not (x['full_name'] and x['full_name'].lower().startswith(query)),  
            x['username'].lower(), 
        ))
        
        return jsonify(results_list)
    except Exception as e:
        print(f"Search error: {e}")
        return jsonify([]), 500


@app.route('/admin/migrate_fullnames', methods=['GET'])
@login_required
def migrate_fullnames():
    if session.get('user_id') != 'vVbXL4LKGidXtrKnvqa21gWRY3V2': 
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

    SUPER_ADMIN_IDS = ['vVbXL4LKGidXtrKnvqa21gWRY3V2']

    if session['user_id'] not in SUPER_ADMIN_IDS:
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.json
    user_id = data.get('user_id')
    
    try:

        db.collection('users').document(user_id).update({
            'is_admin': True,
            'admin_added_by': session['user_id'],
            'admin_added_at': firestore.SERVER_TIMESTAMP
        })


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

    ADMIN_IDS = ['vVbXL4LKGidXtrKnvqa21gWRY3V2']

    # Debug logging
    print(f"Verification attempt by user: {session.get('user_id')}")

    if session['user_id'] not in ADMIN_IDS:
        print("Unauthorized verification attempt")
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
    
    try:

        data = request.get_json()
        

        user_id = data.get('user_id')
        verification_type = data.get('type', 'official')
        
        if not user_id:
            print("No user ID provided")
            return jsonify({'success': False, 'error': 'User ID is required'}), 400

        valid_types = ['official', 'creator', 'business', 'remove']
        if verification_type not in valid_types:
            print(f"Invalid verification type: {verification_type}")
            return jsonify({'success': False, 'error': 'Invalid verification type'}), 400


        user_ref = db.collection('users').document(user_id)
        user_doc = user_ref.get()
        
        if not user_doc.exists:
            print(f"User not found: {user_id}")
            return jsonify({'success': False, 'error': 'User not found'}), 404
        
        user_data = user_doc.to_dict()
        

        update_data = {
            'verified': verification_type != 'remove',
            'verification_type': None if verification_type == 'remove' else verification_type,
            'verified_by': session['user_id'] if verification_type != 'remove' else None,
            'verified_at': firestore.SERVER_TIMESTAMP if verification_type != 'remove' else None
        }
        

        try:
            user_ref.update(update_data)
        except Exception as update_error:
            print(f"Database update error: {update_error}")
            return jsonify({'success': False, 'error': 'Failed to update user verification'}), 500


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


        print(f"User {user_id} verified as {verification_type}")
        
        return jsonify({
            'success': True, 
            'message': f'User verified as {verification_type}',
            'verification_type': verification_type
        })
    
    except Exception as e:

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

            type_config = ENHANCED_NOTIFICATION_TYPES.get(type, {})
            sender_info = type_config.get('sender', {
                'username': 'Jinaq',
                'avatar_url': generate_avatar_url({'username': 'Jinaq'}),
                'verified': True,
                'verification_type': 'system'
            })


        notification_config = ENHANCED_NOTIFICATION_TYPES.get(type, {})
        enriched_content = {
            'type_label': notification_config.get('label', 'Notification'),
            'icon': notification_config.get('icon', '🔔'),
            'priority': notification_config.get('priority', 'normal'),
            **content
        }

        if type == 'account_change':
            action = content.get('action')
            if action == 'email_updated':
                enriched_content['message'] = f"Email updated to {content.get('new_email')}"
            elif action == 'password_changed':
                enriched_content['message'] = "Password has been changed"
            elif not enriched_content.get('message'):
                enriched_content['message'] = "Account settings have been updated"

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


        if notification_config.get('priority') == 'critical':
            notification_data['is_pinned'] = True


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
            

            notification_type = notification['type']
            notification_type_info = ENHANCED_NOTIFICATION_TYPES.get(notification_type, {})
            

            notification['icon'] = notification_type_info.get('icon', '🔔')
            notification['type_label'] = notification_type_info.get('label', 'Notification')
            

            if notification_type in ['system', 'admin_message', 'important']:
                sender_config = notification_type_info.get('sender', {})
                notification['sender_info'] = {
                    'username': sender_config.get('username', 'Jinaq'),
                    'verified': sender_config.get('verified', True),
                    'verification_type': sender_config.get('verification_type', 'system'),
                    'avatar_url': url_for('static', filename='jinaq_logo.svg')
                }
            

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

    ADMIN_IDS = ['vVbXL4LKGidXtrKnvqa21gWRY3V2'] 
    

    if session.get('user_id') not in ADMIN_IDS:
        return jsonify({'error': 'Unauthorized access'}), 403
    

    data = request.json
    
    recipient_type = data.get('recipient_type', 'all')
    message_type = data.get('message_type', 'system')
    message_text = data.get('message_text', '')
    selected_users = data.get('selected_users', [])
    
    if not message_text:
        return jsonify({'error': 'Message cannot be empty'}), 400
    
    try:

        admin_doc = db.collection('users').document(session['user_id']).get()
        admin_data = admin_doc.to_dict()
        

        users_ref = db.collection('users')
        
        if recipient_type == 'verified':
            query = users_ref.where('verified', '==', True)
        elif recipient_type == 'unverified':
            query = users_ref.where('verified', '==', False)
        elif recipient_type == 'selected':

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

            query = users_ref
        

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

    SUPER_ADMIN_IDS = ['vVbXL4LKGidXtrKnvqa21gWRY3V2']

    if session['user_id'] not in SUPER_ADMIN_IDS:
        return jsonify({'success': False, 'error': 'Unauthorized access'}), 403
    
    data = request.json
    user_id = data.get('user_id')
    
    try:

        user_ref = db.collection('users').document(user_id)
        user_doc = user_ref.get()
        
        if not user_doc.exists:
            return jsonify({'success': False, 'error': 'User not found'}), 404
        
        user_data = user_doc.to_dict()
        

        current_blocked_status = user_data.get('blocked', False)
        new_blocked_status = not current_blocked_status
        

        user_ref.update({
            'blocked': new_blocked_status,
            'blocked_at': firestore.SERVER_TIMESTAMP if new_blocked_status else None,
            'blocked_by': session['user_id'] if new_blocked_status else None
        })
        

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
# Add these routes to your Flask app
@app.route('/update-location', methods=['POST'])
@login_required
def update_location():
    try:
        data = request.get_json()
        coordinates = data.get('coordinates')
        
        if not coordinates:
            return jsonify({'success': False, 'error': 'No coordinates provided'}), 400

        geolocator = Nominatim(user_agent="your_app_name")
        location = geolocator.reverse(f"{coordinates['lat']}, {coordinates['lng']}")

        if location:
            location_data = {
                'city': location.raw.get('address', {}).get('city') or 
                       location.raw.get('address', {}).get('town') or 
                       location.raw.get('address', {}).get('municipality'),
                'country': location.raw.get('address', {}).get('country'),
                'coordinates': coordinates
            }

            # Update user's location in database
            db.collection('users').document(session['user_id']).update({
                'location': location_data
            })

            return jsonify({
                'success': True,
                'location': location_data
            })

        return jsonify({'success': False, 'error': 'Location not found'}), 404

    except Exception as e:
        print(f"Error updating location: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/get-ip-location')
@login_required
def get_ip_location():
    try:
        # Get IP address
        ip = request.headers.get('X-Forwarded-For', request.remote_addr)
        
        # Use ip-api.com for IP geolocation (free tier)
        response = requests.get(f'http://ip-api.com/json/{ip}')
        data = response.json()
        
        if data['status'] == 'success':
            location_data = {
                'city': data.get('city'),
                'country': data.get('country'),
                'coordinates': {
                    'lat': data.get('lat'),
                    'lng': data.get('lon')
                }
            }

            # Update user's location in database
            db.collection('users').document(session['user_id']).update({
                'location': location_data
            })

            return jsonify({
                'success': True,
                'location': location_data
            })

        return jsonify({'success': False, 'error': 'Location not found'}), 404

    except Exception as e:
        print(f"Error getting IP location: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/update_header', methods=['POST'])
@login_required
def update_header():
    try:
        user_id = session['user_id']

        if 'header_image' not in request.files:
            return jsonify({'success': False, 'error': 'No file provided'}), 400

        file = request.files['header_image']
        position = request.form.get('position', '50% 50%')
        focal_point = request.form.get('focal_point', 'center') # New parameter for focal point

        if not file or not file.filename:
            return jsonify({'success': False, 'error': 'No file selected'}), 400

        # Validate file type
        allowed_extensions = {'png', 'jpg', 'jpeg', 'webp'}
        if '.' not in file.filename or \
           file.filename.rsplit('.', 1)[1].lower() not in allowed_extensions:
            return jsonify({'success': False, 'error': 'Invalid file type'}), 400

        # Validate file size (max 5MB)
        if len(file.read()) > 5 * 1024 * 1024:  # 5MB in bytes
            return jsonify({'success': False, 'error': 'File too large (max 5MB)'}), 400
        file.seek(0)  # Reset file pointer after reading

        # Get user doc to check for existing header
        user_doc = db.collection('users').document(user_id).get()
        user_data = user_doc.to_dict()

        # Delete old header if exists
        if user_data.get('header_image', {}).get('url'):
            try:
                old_path = user_data['header_image']['url'].split('/')[-1]
                old_blob = bucket.blob(f'headers/{user_id}/{old_path}')
                old_blob.delete()
            except Exception as e:
                print(f"Error deleting old header: {e}")

        # Upload new header to Firebase Storage
        file_extension = file.filename.rsplit('.', 1)[1].lower()
        filename = f"{str(uuid.uuid4())}.{file_extension}"
        full_path = f"headers/{user_id}/{filename}"

        blob = bucket.blob(full_path)
        
        # Set content type and cache control
        content_type = f'image/{file_extension}'
        if file_extension == 'jpg':
            content_type = 'image/jpeg'
            
        blob.content_type = content_type
        blob.cache_control = 'public, max-age=31536000'  # Cache for 1 year

        # Upload with metadata
        blob.metadata = {
            'uploaded_by': user_id,
            'original_filename': file.filename,
            'focal_point': focal_point
        }

        blob.upload_from_string(
            file.read(),
            content_type=content_type
        )

        blob.make_public()

        # Update user document with new header info
        header_data = {
            'header_image': {
                'url': blob.public_url,
                'position': position,
                'focal_point': focal_point,
                'original_filename': file.filename,
                'updated_at': datetime.datetime.now(tz=datetime.timezone.utc)
            }
        }

        db.collection('users').document(user_id).update(header_data)

        return jsonify({
            'success': True,
            'header': header_data['header_image']
        })

    except Exception as e:
        print(f"Error updating header: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
@app.route('/internships/create', methods=['GET', 'POST'])
@login_required
def create_internship():
    if request.method == 'POST':
        try:
            user_id = session['user_id']
            
            # Get form data
            title = request.form.get('title')
            company = request.form.get('company')
            description = request.form.get('description')
            requirements = request.form.get('requirements')
            location = request.form.get('location')
            start_date = request.form.get('start_date')
            end_date = request.form.get('end_date')
            area = request.form.get('area')
            format_type = request.form.get('format')
            address = request.form.get('address')
            positions = int(request.form.get('positions', 1))

            # Handle image upload
            image_url = None
            if 'image' in request.files:
                image = request.files['image']
                if image and image.filename:
                    # Create a unique filename
                    ext = image.filename.split('.')[-1]
                    filename = f"internships/{user_id}/{str(uuid.uuid4())}.{ext}"
                    
                    # Upload to Firebase Storage
                    blob = bucket.blob(filename)
                    blob.upload_from_string(
                        image.read(),
                        content_type=image.content_type
                    )
                    
                    # Make the image public and get URL
                    blob.make_public()
                    image_url = blob.public_url

            # Create internship document
            internship_data = {
                'title': title,
                'company': company,
                'description': description,
                'requirements': requirements,
                'location': location,
                'start_date': start_date,
                'end_date': end_date,
                'image_url': image_url,
                'created_at': datetime.datetime.now(tz=datetime.timezone.utc),
                'created_by': user_id,
                'status': 'active',
                'area': area,
                'format': format_type,
                'address': address,
                'positions': positions,
                'applications': []
            }

            # Save to Firestore
            internship_ref = db.collection('internships').document()
            internship_ref.set(internship_data)

            # Create notification for followers
            user_doc = db.collection('users').document(user_id).get()
            user_data = user_doc.to_dict()
            
            if user_data.get('followers'):
                for follower_id in user_data['followers']:
                    create_notification(
                        follower_id,
                        'new_internship',
                        {
                            'internship_id': internship_ref.id,
                            'company': company,
                            'title': title
                        },
                        sender_id=user_id
                    )

            flash('Internship posted successfully!')
            return redirect(url_for('view_internship', internship_id=internship_ref.id))

        except Exception as e:
            print(f"Error creating internship: {e}")
            flash('Error creating internship. Please try again.')
            return redirect(url_for('create_internship'))

    return render_template('create_internship.html')

@app.route('/internships')
def list_internships():
    try:
        # Get all active internships
        internships_ref = db.collection('internships')\
            .where('status', '==', 'active')\
            .order_by('created_at', direction=firestore.Query.DESCENDING)\
            .stream()

        internships = []
        for doc in internships_ref:
            internship = doc.to_dict()
            internship['id'] = doc.id
            
            # Get creator information
            creator_doc = db.collection('users').document(internship['created_by']).get()
            if creator_doc.exists:
                creator_data = creator_doc.to_dict()
                internship['creator'] = {
                    'username': creator_data.get('display_username', creator_data.get('username')),
                    'avatar_url': generate_avatar_url(creator_data),
                    'verified': creator_data.get('verified', False),
                    'verification_type': creator_data.get('verification_type')
                }

            internships.append(internship)

        return render_template('internships.html', 
                             internships=internships,
                             current_user_id=session.get('user_id'))

    except Exception as e:
        print(f"Error listing internships: {e}")
        flash('Error loading internships. Please try again.')
        return redirect(url_for('index'))

@app.route('/internships/<internship_id>')
def view_internship(internship_id):
    try:
        internship_doc = db.collection('internships').document(internship_id).get()
        if not internship_doc.exists:
            flash('Internship not found')
            return redirect(url_for('list_internships'))

        internship = internship_doc.to_dict()
        internship['id'] = internship_doc.id
        
        # Get creator information
        creator_doc = db.collection('users').document(internship['created_by']).get()
        if creator_doc.exists:
            creator_data = creator_doc.to_dict()
            internship['creator'] = {
                'username': creator_data.get('display_username', creator_data.get('username')),
                'avatar_url': generate_avatar_url(creator_data),
                'verified': creator_data.get('verified', False),
                'verification_type': creator_data.get('verification_type')
            }

        return render_template('view_internship.html', 
                             internship=internship,
                             current_user_id=session.get('user_id'))

    except Exception as e:
        print(f"Error viewing internship: {e}")
        flash('Error loading internship. Please try again.')
        return redirect(url_for('list_internships'))

@app.route('/internships/<internship_id>/apply', methods=['POST'])
@login_required
def apply_internship(internship_id):
    try:
        user_id = session['user_id']
        
        # Get user data for application
        user_doc = db.collection('users').document(user_id).get()
        user_data = user_doc.to_dict()
        
        # Get the internship
        internship_ref = db.collection('internships').document(internship_id)
        internship_doc = internship_ref.get()
        
        if not internship_doc.exists:
            return jsonify({'error': 'Internship not found'}), 404
            
        internship_data = internship_doc.to_dict()
        
        # Ensure applications is a list
        applications = internship_data.get('applications', [])
        if not isinstance(applications, list):
            print(f"Invalid applications type: {type(applications)}")
            applications = []
        
        # Clean existing applications to remove invalid entries
        cleaned_applications = [
            app for app in applications 
            if isinstance(app, dict) and app.get('user_id')
        ]
        
        # Check if user already applied
        if any(app.get('user_id') == user_id for app in cleaned_applications):
            return jsonify({'error': 'Already applied'}), 400
            
        # Create application object
        application = {
            'user_id': user_id,
            'username': user_data.get('display_username', user_data.get('username')),
            'avatar_url': generate_avatar_url(user_data),
            'status': 'pending',
            'applied_at': datetime.datetime.now(tz=datetime.timezone.utc),
            'skills': user_data.get('skills', []),
            'academic_info': user_data.get('academic_info', {})
        }
        
        # Add application to internship
        cleaned_applications.append(application)
        internship_ref.update({
            'applications': cleaned_applications
        })
        
        # Create notification for internship creator
        create_notification(
            internship_data['created_by'],
            'new_application',
            {
                'internship_id': internship_id,
                'internship_title': internship_data['title']
            },
            sender_id=user_id
        )
        
        return jsonify({'success': True, 'message': 'Application submitted successfully'})
        
    except Exception as e:
        print(f"Error applying to internship: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Error submitting application'}), 500
@app.route('/admin/clean_internship_applications', methods=['GET'])
@login_required
def clean_internship_applications():
    # Only allow super admin to run this
    if session.get('user_id') != 'vVbXL4LKGidXtrKnvqa21gWRY3V2':
        return "Unauthorized", 403
    
    try:
        # Get all internships
        internships_ref = db.collection('internships')
        internships = internships_ref.stream()
        
        cleaned_count = 0
        for internship_doc in internships:
            internship_data = internship_doc.to_dict()
            
            # Ensure applications is a list of dictionaries
            applications = internship_data.get('applications', [])
            
            # Clean applications
            cleaned_applications = [
                app for app in applications 
                if isinstance(app, dict) and 
                   isinstance(app.get('user_id'), str) and 
                   app.get('user_id')
            ]
            
            # Update if cleaned applications differ
            if len(cleaned_applications) != len(applications):
                internships_ref.document(internship_doc.id).update({
                    'applications': cleaned_applications
                })
                cleaned_count += 1
        
        return f"Cleaned applications in {cleaned_count} internships"
    
    except Exception as e:
        print(f"Error cleaning internship applications: {e}")
        return f"Error: {str(e)}", 500
@app.route('/internships/<internship_id>/delete', methods=['POST'])
@login_required
def delete_internship(internship_id):
    try:
        user_id = session['user_id']
        
        # Get the internship
        internship_ref = db.collection('internships').document(internship_id)
        internship_doc = internship_ref.get()
        
        if not internship_doc.exists:
            flash('Internship not found')
            return redirect(url_for('list_internships'))
            
        internship_data = internship_doc.to_dict()
        
        # Check if user is the creator
        if internship_data.get('created_by') != user_id:
            flash('Unauthorized to delete this internship')
            return redirect(url_for('view_internship', internship_id=internship_id))
            
        # Delete image from storage if exists
        if internship_data.get('image_url'):
            try:
                image_path = internship_data['image_url'].split('/')[-1]
                blob = bucket.blob(f"internships/{user_id}/{image_path}")
                blob.delete()
            except Exception as e:
                print(f"Error deleting internship image: {e}")
        
        # Delete the internship document
        internship_ref.delete()
        
        flash('Internship deleted successfully')
        return redirect(url_for('list_internships'))
        
    except Exception as e:
        print(f"Error deleting internship: {e}")
        flash('Error deleting internship. Please try again.')
        return redirect(url_for('view_internship', internship_id=internship_id))


@app.route('/internships/<internship_id>/applications/<applicant_id>/respond', methods=['POST'])
@login_required
def respond_to_application(internship_id, applicant_id):
    try:
        user_id = session['user_id']
        response = request.json.get('response')  # 'accept' or 'reject'
        
        if response not in ['accept', 'reject']:
            return jsonify({'error': 'Invalid response'}), 400
        
        # Get internship data
        internship_ref = db.collection('internships').document(internship_id)
        internship_doc = internship_ref.get()
        
        if not internship_doc.exists:  # Changed from internship_doc.exists()
            return jsonify({'error': 'Internship not found'}), 404
            
        internship_data = internship_doc.to_dict()
        
        # Verify ownership
        if internship_data.get('created_by') != user_id:
            return jsonify({'error': 'Unauthorized'}), 403
        
        # Ensure applications is a list
        applications = internship_data.get('applications', [])
        if not isinstance(applications, list):
            print(f"Invalid applications type: {type(applications)}")
            applications = []
        
        # Clean and validate applications
        cleaned_applications = [
            app for app in applications 
            if isinstance(app, dict) and 
               isinstance(app.get('user_id'), str) and 
               app.get('user_id')
        ]
        
        # Find and update application
        found = False
        for app in cleaned_applications:
            if app.get('user_id') == applicant_id:
                app['status'] = 'accepted' if response == 'accept' else 'rejected'
                app['responded_at'] = datetime.datetime.now(tz=datetime.timezone.utc)
                found = True
                break
                
        if not found:
            return jsonify({'error': 'Application not found'}), 404
            
        # Update internship with modified applications
        internship_ref.update({
            'applications': cleaned_applications
        })
        
        # Check if all positions are filled after accepting
        if response == 'accept':
            accepted_count = sum(1 for app in cleaned_applications if app.get('status') == 'accepted')
            if accepted_count >= internship_data.get('positions', 1):
                # Mark internship as closed
                internship_ref.update({
                    'status': 'closed',
                    'closed_at': datetime.datetime.now(tz=datetime.timezone.utc)
                })
                
                # Notify remaining pending applicants
                for app in cleaned_applications:
                    if app.get('status') == 'pending':
                        create_notification(
                            app.get('user_id'),
                            'application_update',
                            {
                                'internship_id': internship_id,
                                'internship_title': internship_data['title'],
                                'message': 'This position has been filled'
                            }
                        )
        
        # Create notification for applicant
        create_notification(
            applicant_id,
            'application_update',
            {
                'internship_id': internship_id,
                'internship_title': internship_data['title'],
                'status': 'accepted' if response == 'accept' else 'rejected',
                'message': f'Your application has been {"accepted" if response == "accept" else "rejected"}'
            }
        )
        
        return jsonify({
            'success': True,
            'message': f'Application {response}ed successfully'
        })
        
    except Exception as e:
        print(f"Error responding to application: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500
@app.route('/internships/<internship_id>/applications')
@login_required
def view_applications(internship_id):
    try:
        user_id = session['user_id']
        
        # Get internship data
        internship_ref = db.collection('internships').document(internship_id)
        internship_doc = internship_ref.get()
        
        if not internship_doc.exists:
            flash('Internship not found')
            return redirect(url_for('list_internships'))
            
        internship_data = internship_doc.to_dict()
        
        # Ensure internship_data is a dictionary
        if not isinstance(internship_data, dict):
            print(f"Unexpected internship data type: {type(internship_data)}")
            flash('Invalid internship data')
            return redirect(url_for('list_internships'))
        
        internship_data['id'] = internship_id
        
        # Verify ownership
        if internship_data.get('created_by') != user_id:
            flash('Unauthorized')
            return redirect(url_for('list_internships'))
            
        # Sort applications by status and date
        applications = internship_data.get('applications', [])
        
        # Ensure applications is a list and each item is a dictionary
        if not isinstance(applications, list):
            print(f"Unexpected applications type: {type(applications)}")
            applications = []
        
        # Clean and validate applications
        cleaned_applications = []
        for app in applications:
            # If app is a string, skip it
            if isinstance(app, str):
                print(f"Skipping invalid string application: {app}")
                continue
            
            # Ensure app is a dictionary
            if not isinstance(app, dict):
                print(f"Skipping invalid application type: {type(app)}")
                continue
            
            # Normalize applied_at to datetime
            applied_at = app.get('applied_at')
            if isinstance(applied_at, str):
                try:
                    applied_at = datetime.datetime.fromisoformat(applied_at.replace('Z', '+00:00'))
                except:
                    applied_at = datetime.datetime.min
            elif not isinstance(applied_at, datetime.datetime):
                applied_at = datetime.datetime.min
            
            # Prepare clean application dictionary
            app_copy = {
                'user_id': app.get('user_id', ''),
                'username': app.get('username', ''),
                'avatar_url': app.get('avatar_url', ''),
                'status': app.get('status', 'pending'),
                'applied_at': applied_at,
                'skills': app.get('skills', []),
                'academic_info': app.get('academic_info', {})
            }
            cleaned_applications.append(app_copy)
        
        # Sort applications 
        sorted_applications = sorted(
            cleaned_applications,
            key=lambda x: (
                {'pending': 0, 'accepted': 1, 'rejected': 2}.get(x.get('status', 'pending'), 0),
                x.get('applied_at', datetime.datetime.min)
            )
        )
        
        return render_template(
            'view_applications.html',
            internship=internship_data,
            applications=sorted_applications
        )
        
    except Exception as e:
        print(f"Comprehensive error viewing applications: {e}")
        print(f"Internship ID: {internship_id}")
        print(f"User ID: {user_id}")
        
        import traceback
        traceback.print_exc()
        
        flash('Error loading applications')
        return redirect(url_for('list_internships'))





def format_datetime(value, format='%b %d, %Y'):
    """Custom datetime filter for Jinja2"""
    if value is None:
        return ""
    if not isinstance(value, datetime.datetime):
        return str(value)
    return value.strftime(format)

# Register the filter with Jinja2
app.jinja_env.filters['datetime'] = format_datetime





@app.errorhandler(404)
def page_not_found(e):

    print(f"404 Error: {e}")
    

    print(f"Request URL: {request.url}")
    print(f"Request Method: {request.method}")
    
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):

    print(f"500 Error: {e}")
    print(f"Request URL: {request.url}")
    print(f"Request Method: {request.method}")
    
    return render_template('500.html'), 500


app.config['DEBUG'] = True


@app.route('/test_404')
def test_404():
    abort(404)

@app.route('/test_500')
def test_500():
    abort(500)
if __name__ == '__main__':
    app.run(debug=True)
