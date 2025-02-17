# Jinaq - Academic Social Platform

![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![Flask](https://img.shields.io/badge/flask-2.0+-green.svg)
![Firebase](https://img.shields.io/badge/firebase-10.0+-orange.svg)
![TailwindCSS](https://img.shields.io/badge/tailwindcss-%2338B2AC.svg?style=flat&logo=tailwind-css&logoColor=white)

## About The Project

Jinaq is a comprehensive educational social platform that bridges the gap between academic achievements and social networking. The platform enables students to create detailed academic portfolios, connect with peers, and build their professional academic presence online.

### Website
[🌐website](https://jinaq.onrender.com)

### Key Features

#### 1. Academic Portfolio System
- GPA and test scores tracking (SAT, TOEFL, IELTS)
- Skills and achievements showcase
- Certificate upload and verification
- Custom profile headers and avatars
- Academic timeline display

#### 2. User Authentication System
- Email-based registration
- Firebase authentication integration
- Password reset functionality
- Session management
- Role-based access control

#### 3. Verification System
- Multiple verification types:
  - Official accounts
- Custom verification badges
- Admin verification panel
- Verification request system

#### 4. Social Interaction Features
- Comment system with nested replies
- Like functionality
- User mentions (@username)
- Profile viewing
- Follow/unfollow system

#### 5. Notification System
- Real-time notifications
- Multiple notification types:
  - Like notifications
  - Comment notifications
  - Reply notifications
  - System notifications
  - Verification notifications
- Notification management panel

#### 6. Location Features
- Geolocation services
- Location-based user discovery
- Geographic data visualization
- Location privacy settings

#### 7. File Management
- Secure file upload system
- Support for multiple file types
- Firebase Storage integration
- File verification system

## Technical Implementation

### Backend Architecture

#### Core Framework
- Flask web framework
- Blueprint organization
- Custom decorators
- Error handling middleware

#### Database Structure (Firebase Firestore)
- Collections:
  - users
  - comments
  - notifications
  - certificates
- Real-time updates
- Data validation

#### Authentication System
- Firebase Authentication
- Custom middleware
- Session management
- Token verification

#### File Storage
- Firebase Storage integration
- File type validation
- Secure URL generation
- Image processing

### Frontend Implementation

#### User Interface
- Responsive design
- TailwindCSS framework
- Custom components
- Mobile-first approach

#### JavaScript Features
- Real-time updates
- Form validation
- Dynamic content loading
- Interactive elements

#### Security Features
- CSRF protection
- XSS prevention
- Input sanitization
- File upload validation

## Project Structure
```
jinaq/
├── app/
│   ├── __init__.py
│   ├── models/
│   ├── routes/
│   ├── static/
│   └── templates/
├── config/
│   ├── __init__.py
│   └── settings.py
├── tests/
├── requirements.txt
└── README.md
```

## Setup and Installation

### Prerequisites
- Python 3.8+
- Firebase account
- Git
- Code editor (VS Code recommended)

### Development Setup

1. **Fork and Clone**
```bash
git clone https://github.com/adlenxk/jinaq.git
cd jinaq
```

2. **Environment Setup**
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Unix/macOS
source venv/bin/activate
```

3. **Install Dependencies**
```bash
pip install -r requirements.txt
```

4. **Firebase Configuration**
- Create new Firebase project
- Enable Authentication, Firestore, and Storage
- Download service account key
- Configure `.env`:
```env
FIREBASE_PRIVATE_KEY=your_firebase_credentials_json
ADMIN_IDS=admin_id_list
ADMIN_PASSWORD=admin_password
```

5. **Run Development Server**
```bash
python app.py
```

### Firebase Setup Details

1. **Create Firebase Project**
- Go to Firebase Console
- Create new project
- Note down Project ID

2. **Enable Services**
- Authentication
  - Enable Email/Password
  - Set up authentication rules
- Firestore
  - Create database
  - Set up security rules
- Storage
  - Initialize storage
  - Configure cors settings

3. **Security Rules**
Firestore rules:
```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    match /{document=**} {
      allow read: if request.auth != null;
      allow write: if request.auth != null;
    }
  }
}
```

## API Documentation

### User Endpoints
```
POST /register - User registration
POST /login - User authentication
GET /profile - Get user profile
PUT /profile - Update profile
POST /update-avatar - Update profile picture
```

### Social Endpoints
```
POST /comments - Create comment
GET /comments - Get comments
POST /like - Like content
DELETE /comment - Delete comment
```

### File Endpoints
```
POST /upload - File upload
GET /files - Get user files
DELETE /files - Delete file
```

## Contributing

1. Fork the Project
2. Create your Feature Branch
```bash
git checkout -b feature/AmazingFeature
```
3. Commit your Changes
```bash
git commit -m 'Add some AmazingFeature'
```
4. Push to the Branch
```bash
git push origin feature/AmazingFeature
```
5. Open a Pull Request

### Contribution Guidelines
- Follow PEP 8 style guide
- Write meaningful commit messages
- Add tests for new features
- Update documentation
- Ensure all tests pass

## Testing

```bash
# Run all tests
python -m pytest

# Run specific test file
python -m pytest tests/test_users.py

# Run with coverage
python -m pytest --cov=app
```

## Deployment

### Production Requirements
- Gunicorn server
- Nginx configuration
- SSL certificate
- Environment variables

### Example Nginx Configuration
```nginx
server {
    listen 80;
    server_name jinaq.com;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contact

Email: alazimvak@gmail.com
GitHub: [Repository](https://github.com/adlenxk/jinaq)
