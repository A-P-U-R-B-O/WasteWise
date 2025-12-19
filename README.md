# 🌱 WasteWise - AI-Powered Waste Management App

[![License:  MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![React](https://img.shields.io/badge/React-18.x-61DAFB? logo=react)](https://reactjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-009688? logo=fastapi)](https://fastapi.tiangolo.com/)
[![Google Gemini](https://img.shields.io/badge/Google-Gemini%20AI-4285F4?logo=google)](https://ai.google. dev/)
[![Firebase](https://img.shields.io/badge/Firebase-Firestore-FFCA28?logo=firebase)](https://firebase.google.com/)

> **Empowering users to make informed waste disposal decisions through AI-powered image recognition and gamification.**

WasteWise is a modern web application that uses Google's Gemini AI to identify waste items from photos, provides proper disposal instructions, tracks environmental impact, and gamifies recycling through points and leaderboards.

---

## 🌟 Features

### 🤖 **AI-Powered Waste Identification**
- Upload images or use your camera to identify waste items
- Powered by Google Gemini Vision AI
- High-accuracy classification across multiple waste categories
- Confidence scoring for predictions

### ♻️ **Smart Disposal Guidance**
- Step-by-step disposal instructions
- Bin color coding (Blue, Green, Red, Black, etc.)
- Recyclability status and subcategory classification
- Safety warnings for hazardous materials

### 🌍 **Environmental Impact Tracking**
- CO₂ savings calculation
- Decomposition time information
- Recycling potential data
- Personal environmental impact dashboard

### 🎮 **Gamification & Engagement**
- Points system for every scan
- User levels and achievements
- Global leaderboard
- Scan history and statistics

### 📚 **Educational Content**
- Category-specific waste management tips
- Fun facts and "Did You Know?" sections
- Eco-friendly alternatives suggestions
- Best practices for waste reduction

---

## 🏗️ Architecture

```
┌─────────────────┐      ┌──────────────────┐      ┌─────────────────┐
│                 │      │                  │      │                 │
│  React Frontend │─────▶│  FastAPI Backend │─────▶│  Google Gemini  │
│   (Render)      │      │    (Render)      │      │      AI         │
│                 │      │                  │      │                 │
└─────────────────┘      └──────────────────┘      └─────────────────┘
                                  │
                                  │
                                  ▼
                         ┌─────────────────┐
                         │                 │
                         │  Firebase       │
                         │  Firestore      │
                         │                 │
                         └─────────────────┘
```

### **Tech Stack**

#### Frontend
- **React 18** - UI framework
- **React Router** - Navigation
- **Axios** - HTTP client
- **Framer Motion** - Animations
- **React Webcam** - Camera integration
- **React Hot Toast** - Notifications
- **Lucide React** - Icons

#### Backend
- **FastAPI** - Web framework
- **Python 3.11+** - Programming language
- **Google Generative AI (Gemini)** - Image recognition
- **Firebase Admin SDK** - Database
- **Pillow** - Image processing
- **SlowAPI** - Rate limiting
- **Uvicorn** - ASGI server

#### Database
- **Firebase Firestore** - NoSQL cloud database

#### Deployment
- **Render** - Cloud hosting for frontend and backend

---

## 🚀 Getting Started

### Prerequisites

- **Node.js** 16+ and npm
- **Python** 3.11+
- **Google Gemini API Key** ([Get one here](https://ai.google.dev/))
- **Firebase Project** ([Create one here](https://console.firebase.google.com/))

---

## 📦 Installation

### 1️⃣ Clone the Repository

```bash
git clone https://github.com/A-P-U-R-B-O/WasteWise.git
cd WasteWise
```

---

### 2️⃣ Backend Setup

#### Navigate to backend directory
```bash
cd backend
```

#### Create virtual environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

#### Install dependencies
```bash
pip install -r requirements. txt
```

#### Create `.env` file
```bash
cp .env.example .env
```

#### Configure `.env`
```env
# App Settings
APP_NAME=WasteWise API
APP_VERSION=1.0.0
ENVIRONMENT=development
DEBUG=True

# Security
SECRET_KEY=your-secret-key-here-change-in-production

# Google Gemini AI
GEMINI_API_KEY=your-gemini-api-key-here
GEMINI_MODEL=gemini-1.5-flash

# Firebase
FIREBASE_CREDENTIALS_PATH=path/to/firebase-credentials.json

# CORS (add your frontend URL)
BACKEND_CORS_ORIGINS=["http://localhost:3000","https://your-frontend-url.onrender.com"]

# Rate Limiting
RATE_LIMIT_PER_MINUTE=60
RATE_LIMIT_SCAN_PER_HOUR=50
```

#### Add Firebase Credentials
- Download your Firebase service account JSON from Firebase Console
- Place it in the `backend/` directory
- Update `FIREBASE_CREDENTIALS_PATH` in `.env`

#### Run Backend
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend will be available at:  **http://localhost:8000**  
API Docs: **http://localhost:8000/docs**

---

### 3️⃣ Frontend Setup

#### Navigate to frontend directory
```bash
cd frontend
```

#### Install dependencies
```bash
npm install
```

#### Create `.env` file
```bash
cp .env.example .env
```

#### Configure `.env`
```env
REACT_APP_API_URL=http://localhost:8000/api/v1
REACT_APP_APP_NAME=WasteWise
REACT_APP_VERSION=1.0.0
```

#### Run Frontend
```bash
npm start
```

Frontend will be available at: **http://localhost:3000**

---

## 🌐 Deployment

### Backend (Render - Web Service)

1. Create a new **Web Service** on Render
2. Connect your GitHub repository
3. Configure: 
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **Environment:** Python 3.11+
4. Add environment variables from `.env`
5. Deploy!

### Frontend (Render - Static Site)

1. Create a new **Static Site** on Render
2. Connect your GitHub repository
3. Configure:
   - **Build Command:** `cd frontend && npm install && npm run build`
   - **Publish Directory:** `frontend/build`
4. Add environment variables: 
   - `REACT_APP_API_URL` = Your backend URL
5. Deploy!

---

## 📡 API Documentation

### Base URL
```
https://your-backend-url.onrender.com/api/v1
```

### Endpoints

#### **POST** `/waste/scan`
Upload an image file to identify waste

**Request:**
- `file` (multipart/form-data) - Image file
- `user_id` (optional) - User ID for tracking

**Response:**
```json
{
  "success":  true,
  "scan_id": "scan_20241219_abc123",
  "item_name": "Plastic Water Bottle",
  "category":  "Recyclable Plastic",
  "confidence": 0.95,
  "recyclable":  true,
  "disposal_steps": ["Remove cap", "Rinse clean", "Place in blue bin"],
  "bin_color": "BLUE",
  "environmental_impact": {
    "co2_saved_kg": 1.5,
    "decomposition_time": "450 years"
  },
  "points_earned": 50
}
```

#### **POST** `/waste/scan/base64`
Scan waste from base64 encoded image

#### **GET** `/waste/categories`
Get all supported waste categories

#### **GET** `/waste/education/{category}`
Get educational content for a category

#### **GET** `/waste/history/{user_id}`
Get scan history for a user

#### **GET** `/waste/stats/{user_id}`
Get user statistics

#### **GET** `/health`
Check API and service health

---

## 🎯 Usage

### 1. **Scan Waste**
- Click "Use Camera" or "Upload Image"
- Take/select a photo of your waste item
- Wait for AI analysis
- View results and disposal instructions

### 2. **Track Progress**
- Check your dashboard for stats
- View CO₂ savings and scan history
- See your level and points

### 3. **Compete**
- Check the leaderboard
- Earn points for each scan
- Level up by scanning more items

### 4. **Learn**
- Read educational content
- Discover eco-friendly alternatives
- Learn about environmental impact

---

## 🗂️ Project Structure

```
WasteWise/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── routes/
│   │   │       └── waste.py
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   └── database.py
│   │   ├── services/
│   │   │   └── gemini_service.py
│   │   ├── utils/
│   │   │   └── image_processor.py
│   │   └── main.py
│   ├── requirements.txt
│   └── . env
│
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   │   ├── Scan. js
│   │   │   ├── Dashboard.js
│   │   │   ├── Leaderboard.js
│   │   │   └── Education.js
│   │   ├── services/
│   │   │   └── wasteService.js
│   │   ├── App.js
│   │   └── index.js
│   ├── package.json
│   └── .env
│
└── README.md
```

---

## 🧪 Testing

### Backend Tests
```bash
cd backend
pytest
```

### Frontend Tests
```bash
cd frontend
npm test
```

### Manual Testing
- Use Postman/Thunder Client for API testing
- Test with various waste item images
- Verify rate limiting
- Check error handling

---

## 🔒 Security Features

- **Rate Limiting** - Prevents API abuse
- **CORS Protection** - Restricts cross-origin requests
- **Input Validation** - Validates all user inputs
- **File Type Validation** - Only accepts image files
- **File Size Limits** - Max 10MB uploads
- **Security Headers** - XSS, CSRF protection
- **Environment Variables** - Sensitive data protected

---

## 🐛 Troubleshooting

### Common Issues

#### **"Scan Failed - 404 Not Found"**
- Check backend is running
- Verify `REACT_APP_API_URL` is correct
- Ensure `/api/v1/waste/scan` endpoint exists

#### **"Method Not Allowed"**
- Ensure POST request (not GET)
- Check endpoint path is correct

#### **"Gemini AI unhealthy"**
- Verify `GEMINI_API_KEY` is set
- Check API key is valid
- Ensure sufficient quota

#### **"Firebase unavailable"**
- Check Firebase credentials path
- Verify service account has correct permissions
- Ensure Firestore is enabled

#### **CORS Errors**
- Add frontend URL to `BACKEND_CORS_ORIGINS`
- Redeploy backend after changes

---

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 👨‍💻 Author

**A-P-U-R-B-O**
- GitHub:  [@A-P-U-R-B-O](https://github.com/A-P-U-R-B-O)
- Repository: [WasteWise](https://github.com/A-P-U-R-B-O/WasteWise)

---

## 🙏 Acknowledgments

- [Google Gemini AI](https://ai.google.dev/) - AI-powered image recognition
- [FastAPI](https://fastapi.tiangolo.com/) - Modern Python web framework
- [React](https://reactjs.org/) - Frontend framework
- [Firebase](https://firebase.google.com/) - Backend services
- [Render](https://render.com/) - Deployment platform

---

## 📞 Support

If you have questions or need help:
- Open an issue on GitHub
- Check the [API Documentation](https://your-backend-url.onrender. com/docs)
- Review troubleshooting section above

---

## 🌟 Show Your Support

If you found this project helpful, please give it a ⭐️! 

---

## 📈 Roadmap

- [ ] Mobile app (React Native)
- [ ] Offline mode support
- [ ] Community challenges
- [ ] Waste collection scheduling
- [ ] Integration with local recycling centers
- [ ] Multi-language support
- [ ] Barcode scanning
- [ ] Social sharing features

---

**Made with 💚 for a cleaner planet 🌍**
