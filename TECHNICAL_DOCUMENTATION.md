# 🛠️ TECHNICAL DOCUMENTATION - Loopync

## Table of Contents
1. [Getting Started](#getting-started)
2. [Architecture Overview](#architecture-overview)
3. [Backend Documentation](#backend-documentation)
4. [Frontend Documentation](#frontend-documentation)
5. [API Reference](#api-reference)
6. [Database Schema](#database-schema)
7. [Authentication Flow](#authentication-flow)
8. [Real-time Features](#real-time-features)
9. [Media Management](#media-management)
10. [Deployment](#deployment)

---

## Getting Started

### Prerequisites
```bash
# Required
- Python 3.11+
- Node.js 18+
- MongoDB 6.0+
- Yarn package manager

# Optional
- Docker (for containerized deployment)
```

### Local Development Setup

#### 1. Clone and Install
```bash
# Backend
cd /app/backend
pip install -r requirements.txt

# Frontend
cd /app/frontend
yarn install
```

#### 2. Configure Environment
```bash
# Backend .env
MONGO_URL=mongodb://localhost:27017
DB_NAME=loopync_dev
JWT_SECRET=your-dev-secret-key
EMERGENT_LLM_KEY=your-emergent-key
AGORA_APP_ID=your-agora-app-id

# Frontend .env
REACT_APP_BACKEND_URL=http://localhost:8001
REACT_APP_AGORA_APP_ID=your-agora-app-id
```

#### 3. Start Services
```bash
# Using supervisor (production)
sudo supervisorctl restart all

# Or manually (development)
# Terminal 1: Backend
cd /app/backend && uvicorn server:app --reload --port 8001

# Terminal 2: Frontend
cd /app/frontend && yarn start
```

#### 4. Access Application
- Frontend: http://localhost:3000
- Backend API: http://localhost:8001
- API Docs: http://localhost:8001/docs (FastAPI Swagger UI)

---

## Architecture Overview

### System Design Principles
1. **Separation of Concerns** - Clear backend/frontend separation
2. **RESTful API** - Standard HTTP methods and status codes
3. **Real-time First** - WebSocket for live features
4. **Persistent Storage** - MongoDB for all data and media
5. **Stateless Authentication** - JWT tokens for scalability
6. **Environment-based Config** - No hardcoded values

### Request Flow
```
User → Browser → Frontend (React)
  ↓
  → Kubernetes Ingress → Backend (FastAPI)
    ↓
    → MongoDB (Data + Media)
    ↓
  ← Response (JSON)
  ↓
← UI Update
```

### WebSocket Flow
```
User → Socket.IO Client → Backend Socket.IO Server
  ↓                              ↓
  Emit event                  Handle event
  ↓                              ↓
  Wait for response           Broadcast to users
  ↓                              ↓
← Receive event              ← Store in DB
  ↓
← Update UI
```

---

## Backend Documentation

### Project Structure
```
/app/backend/
├── server.py              # Main FastAPI application
├── auth_service.py        # Authentication logic
├── messenger_service.py   # Messaging logic
├── requirements.txt       # Python dependencies
├── .env                  # Environment variables
└── uploads/              # Temporary file storage (deprecated)
```

### Key Components

#### 1. FastAPI Application (server.py)
```python
from fastapi import FastAPI, APIRouter

app = FastAPI()
api_router = APIRouter(prefix="/api")

# All routes must have /api prefix for Kubernetes ingress
@api_router.get("/posts")
async def get_posts():
    # Implementation
    pass

app.include_router(api_router)
```

#### 2. MongoDB Connection
```python
from motor.motor_asyncio import AsyncIOMotorClient
import os

mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Usage
posts = await db.posts.find({}).to_list(100)
```

#### 3. Socket.IO Server
```python
import socketio

sio = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins='*'
)

@sio.event
async def connect(sid, environ, auth):
    # Handle client connection
    pass

@sio.event
async def disconnect(sid):
    # Handle client disconnection
    pass
```

### Authentication Service

#### Password Hashing
```python
import bcrypt

class AuthService:
    def hash_password(self, password: str) -> str:
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode(), salt)
        return hashed.decode()
    
    def verify_password(self, password: str, hashed: str) -> bool:
        return bcrypt.checkpw(
            password.encode(),
            hashed.encode()
        )
```

#### JWT Token Generation
```python
import jwt
from datetime import datetime, timedelta, timezone

def create_access_token(user_id: str) -> str:
    expiration = datetime.now(timezone.utc) + timedelta(hours=24)
    payload = {
        'sub': user_id,
        'exp': expiration,
        'iat': datetime.now(timezone.utc)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm='HS256')

def verify_token(token: str) -> Optional[str]:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
        return payload.get('sub')  # Returns user_id
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None
```

### Pydantic Models

#### User Model
```python
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
import uuid

class User(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    handle: str
    name: str
    email: str
    avatar: str = "https://api.dicebear.com/7.x/avataaars/svg?seed=default"
    friends: List[str] = Field(default_factory=list)
    # ... other fields
```

#### Post Model
```python
class Post(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    authorId: str
    text: str
    media: Optional[str] = None  # Relative URL: /api/media/{id}
    hashtags: List[str] = Field(default_factory=list)
    stats: dict = Field(default_factory=lambda: {
        "likes": 0,
        "quotes": 0,
        "reposts": 0,
        "replies": 0
    })
    likedBy: List[str] = Field(default_factory=list)
    createdAt: str = Field(default_factory=lambda: 
        datetime.now(timezone.utc).isoformat()
    )
```

### API Route Examples

#### Create Post
```python
@api_router.post("/posts")
async def create_post(post: PostCreate, authorId: str):
    post_obj = Post(authorId=authorId, **post.model_dump())
    doc = post_obj.model_dump()
    
    # MongoDB insertion
    await db.posts.insert_one(doc)
    
    # Exclude MongoDB _id from response
    doc.pop('_id', None)
    
    # Enrich with author data
    author = await db.users.find_one({"id": authorId}, {"_id": 0})
    doc["author"] = author
    
    return doc
```

#### Like Post
```python
@api_router.post("/posts/{postId}/like")
async def toggle_like_post(postId: str, userId: str):
    post = await db.posts.find_one({"id": postId}, {"_id": 0})
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    liked_by = post.get("likedBy", [])
    
    if userId in liked_by:
        # Unlike
        await db.posts.update_one(
            {"id": postId},
            {
                "$pull": {"likedBy": userId},
                "$inc": {"stats.likes": -1}
            }
        )
        action = "unliked"
    else:
        # Like
        await db.posts.update_one(
            {"id": postId},
            {
                "$addToSet": {"likedBy": userId},
                "$inc": {"stats.likes": 1}
            }
        )
        action = "liked"
        
        # Create notification
        notification = Notification(
            userId=post["authorId"],
            type="post_like",
            message=f"Someone liked your post",
            fromUserId=userId
        )
        await db.notifications.insert_one(notification.model_dump())
    
    return {"success": True, "action": action}
```

---

## Frontend Documentation

### Project Structure
```
/app/frontend/
├── src/
│   ├── App.js                 # Main app component
│   ├── index.js              # React entry point
│   ├── components/           # Reusable components
│   │   ├── PostCard.js
│   │   ├── ComposerModal.js
│   │   ├── ReelViewer.js
│   │   └── ...
│   ├── pages/                # Page components
│   │   ├── Home.js
│   │   ├── Profile.js
│   │   ├── Messenger.js
│   │   └── ...
│   ├── context/              # React context
│   │   ├── AuthContext.js
│   │   └── WebSocketContext.js
│   ├── hooks/                # Custom hooks
│   │   ├── useSpeechRecognition.js
│   │   └── useTextToSpeech.js
│   └── utils/                # Utilities
│       └── mediaUtils.js
├── public/
├── package.json
└── .env
```

### Key Components

#### 1. Authentication Context
```javascript
import React, { createContext, useState, useContext, useEffect } from 'react';
import axios from 'axios';

const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
  const [currentUser, setCurrentUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [token, setToken] = useState(localStorage.getItem('token'));

  useEffect(() => {
    if (token) {
      fetchCurrentUser();
    } else {
      setLoading(false);
    }
  }, [token]);

  const fetchCurrentUser = async () => {
    try {
      const response = await axios.get(
        `${process.env.REACT_APP_BACKEND_URL}/api/auth/me`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setCurrentUser(response.data);
    } catch (error) {
      console.error('Failed to fetch user:', error);
      logout();
    } finally {
      setLoading(false);
    }
  };

  const login = (newToken, user) => {
    localStorage.setItem('token', newToken);
    setToken(newToken);
    setCurrentUser(user);
  };

  const logout = () => {
    localStorage.removeItem('token');
    setToken(null);
    setCurrentUser(null);
  };

  return (
    <AuthContext.Provider value={{ currentUser, token, login, logout, loading }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);
```

#### 2. WebSocket Context
```javascript
import { createContext, useContext, useEffect, useState } from 'react';
import io from 'socket.io-client';
import { useAuth } from './AuthContext';

const WebSocketContext = createContext();

export const WebSocketProvider = ({ children }) => {
  const [socket, setSocket] = useState(null);
  const { token } = useAuth();

  useEffect(() => {
    if (token) {
      const newSocket = io(process.env.REACT_APP_BACKEND_URL, {
        auth: { token },
        transports: ['websocket', 'polling']
      });

      newSocket.on('connect', () => {
        console.log('✅ Connected to WebSocket');
      });

      newSocket.on('disconnect', () => {
        console.log('❌ Disconnected from WebSocket');
      });

      setSocket(newSocket);

      return () => newSocket.disconnect();
    }
  }, [token]);

  return (
    <WebSocketContext.Provider value={{ socket }}>
      {children}
    </WebSocketContext.Provider>
  );
};

export const useWebSocket = () => useContext(WebSocketContext);
```

#### 3. Media URL Utility
```javascript
// utils/mediaUtils.js
export const getMediaUrl = (mediaUrl) => {
  if (!mediaUrl) return null;
  
  // If already absolute URL, return as-is
  if (mediaUrl.startsWith('http://') || mediaUrl.startsWith('https://')) {
    return mediaUrl;
  }
  
  // Convert relative URL to absolute
  const backendUrl = process.env.REACT_APP_BACKEND_URL;
  return `${backendUrl}${mediaUrl}`;
};
```

#### 4. Post Card Component
```javascript
import React from 'react';
import { getMediaUrl } from '../utils/mediaUtils';
import axios from 'axios';

const PostCard = ({ post }) => {
  const handleLike = async () => {
    try {
      await axios.post(
        `${process.env.REACT_APP_BACKEND_URL}/api/posts/${post.id}/like`,
        { userId: currentUser.id },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      // Update UI
    } catch (error) {
      console.error('Failed to like post:', error);
    }
  };

  return (
    <div className="post-card">
      <div className="post-header">
        <img src={post.author.avatar} alt={post.author.name} />
        <span>{post.author.name}</span>
      </div>
      
      <p>{post.text}</p>
      
      {post.media && (
        <img src={getMediaUrl(post.media)} alt="Post media" />
      )}
      
      <div className="post-actions">
        <button onClick={handleLike}>
          ❤️ {post.stats.likes}
        </button>
      </div>
    </div>
  );
};

export default PostCard;
```

### Custom Hooks

#### Speech Recognition Hook
```javascript
import { useState, useEffect, useCallback } from 'react';

export const useSpeechRecognition = () => {
  const [isListening, setIsListening] = useState(false);
  const [transcript, setTranscript] = useState('');
  const [recognition, setRecognition] = useState(null);

  useEffect(() => {
    if ('webkitSpeechRecognition' in window) {
      const recognitionInstance = new window.webkitSpeechRecognition();
      recognitionInstance.continuous = false;
      recognitionInstance.interimResults = true;
      recognitionInstance.lang = 'en-US';

      recognitionInstance.onresult = (event) => {
        const current = event.resultIndex;
        const transcript = event.results[current][0].transcript;
        setTranscript(transcript);
      };

      recognitionInstance.onend = () => {
        setIsListening(false);
      };

      setRecognition(recognitionInstance);
    }
  }, []);

  const startListening = useCallback(() => {
    if (recognition) {
      recognition.start();
      setIsListening(true);
      setTranscript('');
    }
  }, [recognition]);

  const stopListening = useCallback(() => {
    if (recognition) {
      recognition.stop();
      setIsListening(false);
    }
  }, [recognition]);

  return {
    isListening,
    transcript,
    startListening,
    stopListening,
    supported: !!recognition
  };
};
```

---

## API Reference

See **PROJECT_REPORT.md** for complete API endpoint documentation.

### Standard Response Format

#### Success Response
```json
{
  "success": true,
  "data": { ... },
  "message": "Operation successful"
}
```

#### Error Response
```json
{
  "detail": "Error message",
  "status_code": 400
}
```

### Common HTTP Status Codes
- `200 OK` - Successful GET/PUT/DELETE
- `201 Created` - Successful POST
- `400 Bad Request` - Invalid input
- `401 Unauthorized` - Missing/invalid token
- `403 Forbidden` - Insufficient permissions
- `404 Not Found` - Resource doesn't exist
- `500 Internal Server Error` - Server error

---

## Database Schema

### MongoDB Collections

See **PROJECT_REPORT.md** for complete collection list and schema details.

### Common Patterns

#### UUID vs MongoDB ObjectId
```python
# ✅ DO: Use UUID strings
import uuid
id = str(uuid.uuid4())

# ❌ DON'T: Use MongoDB ObjectId
from bson import ObjectId
id = ObjectId()  # Not JSON serializable!
```

#### Excluding _id from Responses
```python
# Always exclude MongoDB's _id field
user = await db.users.find_one({"id": user_id}, {"_id": 0})

# Or remove after fetching
user = await db.users.find_one({"id": user_id})
user.pop('_id', None)
```

#### DateTime Handling
```python
from datetime import datetime, timezone

# ✅ DO: Use timezone-aware UTC
date = datetime.now(timezone.utc).isoformat()

# ❌ DON'T: Use naive datetime
date = datetime.now()  # No timezone info
```

---

## Authentication Flow

### 1. User Signup
```mermaid
User → Frontend: Enter email, password
Frontend → Backend: POST /api/auth/signup
Backend → MongoDB: Create user with bcrypt hash
Backend → Frontend: Return JWT token + user data
Frontend: Store token in localStorage
Frontend: Set AuthContext
```

### 2. User Login
```mermaid
User → Frontend: Enter email, password
Frontend → Backend: POST /api/auth/login
Backend → MongoDB: Find user by email
Backend: Verify password with bcrypt
Backend → Frontend: Return JWT token + user data
Frontend: Store token in localStorage
Frontend: Set AuthContext
```

### 3. Protected Route Access
```mermaid
Frontend → Backend: GET /api/posts (with Bearer token)
Backend: Extract token from Authorization header
Backend: Verify JWT signature and expiration
Backend → MongoDB: Get user by ID from token
Backend → Frontend: Return protected resource
```

---

## Real-time Features

### WebSocket Events

#### Client Events (Emit)
```javascript
socket.emit('typing', {
  threadId: 'thread-uuid',
  isTyping: true
});

socket.emit('message_read', {
  messageId: 'message-uuid',
  threadId: 'thread-uuid'
});
```

#### Server Events (Listen)
```javascript
socket.on('new_message', (data) => {
  console.log('New message:', data);
  // Update UI
});

socket.on('typing', (data) => {
  console.log('User typing:', data);
  // Show typing indicator
});

socket.on('call_incoming', (data) => {
  console.log('Incoming call:', data);
  // Show call UI
});
```

### Connection Management
```javascript
const socket = io(BACKEND_URL, {
  auth: { token: localStorage.getItem('token') },
  transports: ['websocket', 'polling'],
  reconnection: true,
  reconnectionAttempts: 5,
  reconnectionDelay: 1000
});

socket.on('connect', () => {
  console.log('Connected:', socket.id);
});

socket.on('disconnect', (reason) => {
  console.log('Disconnected:', reason);
  if (reason === 'io server disconnect') {
    // Reconnect manually
    socket.connect();
  }
});
```

---

## Media Management

### File Upload Flow

#### Frontend
```javascript
const handleFileUpload = async (file) => {
  const formData = new FormData();
  formData.append('file', file);

  try {
    const response = await axios.post(
      `${BACKEND_URL}/api/upload`,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
          'Authorization': `Bearer ${token}`
        }
      }
    );

    // Returns: { url: "/api/media/{file_id}", ... }
    return response.data.url;
  } catch (error) {
    console.error('Upload failed:', error);
  }
};
```

#### Backend
```python
@api_router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    # Read file content
    content = await file.read()
    
    # Convert to base64
    import base64
    file_data = base64.b64encode(content).decode('utf-8')
    
    # Store in MongoDB
    file_id = str(uuid.uuid4())
    file_doc = {
        "id": file_id,
        "filename": file.filename,
        "content_type": file.content_type,
        "file_data": file_data,
        "uploaded_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.media_files.insert_one(file_doc)
    
    # Return relative URL
    return {"url": f"/api/media/{file_id}"}
```

### Serving Media Files
```python
@api_router.get("/media/{file_id}")
async def serve_media_file(file_id: str):
    # Fetch from MongoDB
    file_doc = await db.media_files.find_one(
        {"id": file_id},
        {"_id": 0}
    )
    
    if not file_doc:
        raise HTTPException(status_code=404, detail="File not found")
    
    # Decode base64
    import base64
    file_content = base64.b64decode(file_doc["file_data"])
    
    # Return with proper headers
    return Response(
        content=file_content,
        media_type=file_doc["content_type"],
        headers={
            "Cache-Control": "public, max-age=31536000",  # 1 year
            "Content-Disposition": f"inline; filename={file_doc['filename']}"
        }
    )
```

---

## Deployment

### Environment Setup

#### Production Environment Variables
```bash
# Backend
MONGO_URL=mongodb://production-host:27017
DB_NAME=loopync_production
JWT_SECRET=generate-secure-random-string-here
FRONTEND_URL=https://your-domain.com
EMERGENT_LLM_KEY=sk-emergent-xxxxx
AGORA_APP_ID=your-production-agora-id
AGORA_APP_CERTIFICATE=your-agora-certificate

# Frontend
REACT_APP_BACKEND_URL=https://your-domain.com
REACT_APP_AGORA_APP_ID=your-production-agora-id
```

### Kubernetes Deployment

The application is configured for Kubernetes deployment with:
- Backend runs on port 8001 (managed by supervisor)
- Frontend runs on port 3000 (managed by supervisor)
- Ingress routes `/api/*` to backend, `/*` to frontend

### Health Checks

#### Backend Health
```bash
curl https://your-domain.com/api/posts
# Should return 200 OK with posts array
```

#### Frontend Health
```bash
curl https://your-domain.com/
# Should return 200 OK with HTML
```

#### WebSocket Health
```javascript
const socket = io('https://your-domain.com');
socket.on('connect', () => {
  console.log('✅ WebSocket healthy');
});
```

### Monitoring

#### Backend Logs
```bash
# Supervisor logs
tail -f /var/log/supervisor/backend.err.log
tail -f /var/log/supervisor/backend.out.log

# Frontend logs
tail -f /var/log/supervisor/frontend.err.log
tail -f /var/log/supervisor/frontend.out.log
```

#### Service Status
```bash
sudo supervisorctl status
```

### Common Issues

#### Issue: 502 Bad Gateway
**Cause:** Backend not running or not bound to 0.0.0.0:8001  
**Fix:** Check backend logs and supervisor status

#### Issue: Media Not Loading
**Cause:** REACT_APP_BACKEND_URL not set correctly  
**Fix:** Verify frontend .env file

#### Issue: WebSocket Connection Failed
**Cause:** Token expired or invalid  
**Fix:** Logout and login again

---

## Development Guidelines

### Code Style
- **Python:** Follow PEP 8
- **JavaScript:** Use ES6+ features
- **Async/Await:** Prefer over callbacks
- **Error Handling:** Always use try-catch

### Git Workflow
```bash
# Feature branch
git checkout -b feature/new-feature

# Make changes
git add .
git commit -m "feat: add new feature"

# Push to remote
git push origin feature/new-feature
```

### Testing Best Practices
1. Test authentication flow first
2. Test CRUD operations for each feature
3. Test real-time features with multiple clients
4. Test error handling and edge cases
5. Test media upload and serving

---

## Support

For issues and questions:
1. Check this documentation
2. Review PROJECT_REPORT.md
3. Check DEPLOYMENT_GUIDE.md
4. Review test_result.md for known issues

---

**Documentation Version:** 1.0.0  
**Last Updated:** November 2025  
**Status:** Production Ready ✅
