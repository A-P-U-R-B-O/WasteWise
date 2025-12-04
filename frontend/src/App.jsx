import React, { useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Link, useNavigate } from 'react-router-dom';
import { Toaster, toast } from 'react-hot-toast';
import { 
  Camera, 
  Home, 
  TrendingUp, 
  Book, 
  User, 
  Menu, 
  X,
  Leaf,
  Recycle
} from 'lucide-react';

// Import pages (we'll create these)
import HomePage from './pages/Home';
import ScanPage from './pages/Scan';
import ProfilePage from './pages/Profile';
import LeaderboardPage from './pages/Leaderboard';
import EducationPage from './pages/Education';

import './App.css';

function App() {
  const [user, setUser] = useState({
    id: 'demo_user_' + Math.random().toString(36).substr(2, 9),
    name: 'Demo User',
    points: 1250,
    level: 3,
    scans: 47
  });
  
  const [menuOpen, setMenuOpen] = useState(false);

  return (
    <Router>
      <div className="app">
        <Toaster 
          position="top-right"
          toastOptions={{
            duration: 3000,
            style: {
              background: '#363636',
              color: '#fff',
            },
            success: {
              iconTheme: {
                primary: '#10b981',
                secondary: '#fff',
              },
            },
          }}
        />
        
        <Header 
          user={user} 
          menuOpen={menuOpen} 
          setMenuOpen={setMenuOpen} 
        />
        
        <main className="main-content">
          <Routes>
            <Route path="/" element={<HomePage user={user} />} />
            <Route path="/scan" element={<ScanPage user={user} setUser={setUser} />} />
            <Route path="/profile" element={<ProfilePage user={user} />} />
            <Route path="/leaderboard" element={<LeaderboardPage user={user} />} />
            <Route path="/education" element={<EducationPage />} />
          </Routes>
        </main>
        
        <BottomNav />
      </div>
    </Router>
  );
}

// ==================== HEADER COMPONENT ====================
function Header({ user, menuOpen, setMenuOpen }) {
  return (
    <header className="header">
      <div className="container header-content">
        <Link to="/" className="logo">
          <Recycle size={32} />
          <span>WasteWise</span>
        </Link>
        
        <nav className={`nav ${menuOpen ? 'nav-open' : ''}`}>
          <Link to="/" onClick={() => setMenuOpen(false)}>
            <Home size={20} /> Home
          </Link>
          <Link to="/scan" onClick={() => setMenuOpen(false)}>
            <Camera size={20} /> Scan
          </Link>
          <Link to="/leaderboard" onClick={() => setMenuOpen(false)}>
            <TrendingUp size={20} /> Leaderboard
          </Link>
          <Link to="/education" onClick={() => setMenuOpen(false)}>
            <Book size={20} /> Learn
          </Link>
          <Link to="/profile" onClick={() => setMenuOpen(false)}>
            <User size={20} /> Profile
          </Link>
        </nav>
        
        <div className="header-user">
          <div className="user-points">
            <Leaf size={16} />
            <span>{user.points} pts</span>
          </div>
          
          <button 
            className="menu-toggle"
            onClick={() => setMenuOpen(!menuOpen)}
            aria-label="Toggle menu"
          >
            {menuOpen ?  <X size={24} /> : <Menu size={24} />}
          </button>
        </div>
      </div>
    </header>
  );
}

// ==================== BOTTOM NAVIGATION ====================
function BottomNav() {
  return (
    <nav className="bottom-nav">
      <Link to="/" className="nav-item">
        <Home size={24} />
        <span>Home</span>
      </Link>
      <Link to="/scan" className="nav-item nav-item-primary">
        <div className="scan-button">
          <Camera size={28} />
        </div>
        <span>Scan</span>
      </Link>
      <Link to="/profile" className="nav-item">
        <User size={24} />
        <span>Profile</span>
      </Link>
    </nav>
  );
}

export default App;
