import React from 'react';
import { Link } from 'react-router-dom';
import { Camera, TrendingUp, Leaf, Award, Recycle, ArrowRight } from 'lucide-react';
import './Home.css';

function HomePage({ user }) {
  return (
    <div className="home-page">
      <div className="container">
        {/* Hero Section */}
        <section className="hero">
          <div className="hero-content">
            <h1 className="hero-title">
              Hi, {user.name}! 👋
              <br />
              <span className="gradient-text">Let's Sort Smarter</span>
            </h1>
            <p className="hero-subtitle">
              Scan waste, earn points, and save the planet one item at a time
            </p>
            
            <Link to="/scan" className="btn btn-primary btn-lg">
              <Camera size={24} />
              Scan Waste Now
              <ArrowRight size={20} />
            </Link>
          </div>
          
          <div className="hero-illustration">
            <div className="floating-card">
              <Recycle size={80} className="recycle-icon" />
            </div>
          </div>
        </section>

        {/* Stats Section */}
        <section className="stats-section">
          <div className="stats-grid">
            <div className="stat-card">
              <div className="stat-icon" style={{ background: 'linear-gradient(135deg, #10b981, #059669)' }}>
                <Award size={32} />
              </div>
              <div className="stat-info">
                <h3>{user.points. toLocaleString()}</h3>
                <p>Points Earned</p>
              </div>
            </div>
            
            <div className="stat-card">
              <div className="stat-icon" style={{ background: 'linear-gradient(135deg, #3b82f6, #2563eb)' }}>
                <TrendingUp size={32} />
              </div>
              <div className="stat-info">
                <h3>Level {user.level}</h3>
                <p>Eco Warrior</p>
              </div>
            </div>
            
            <div className="stat-card">
              <div className="stat-icon" style={{ background: 'linear-gradient(135deg, #f59e0b, #d97706)' }}>
                <Camera size={32} />
              </div>
              <div className="stat-info">
                <h3>{user.scans}</h3>
                <p>Items Scanned</p>
              </div>
            </div>
            
            <div className="stat-card">
              <div className="stat-icon" style={{ background: 'linear-gradient(135deg, #8b5cf6, #7c3aed)' }}>
                <Leaf size={32} />
              </div>
              <div className="stat-info">
                <h3>23. 4 kg</h3>
                <p>CO₂ Saved</p>
              </div>
            </div>
          </div>
        </section>

        {/* Features Section */}
        <section className="features-section">
          <h2 className="section-title">How It Works</h2>
          
          <div className="features-grid">
            <div className="feature-card">
              <div className="feature-number">1</div>
              <Camera size={40} className="feature-icon" />
              <h3>Scan Item</h3>
              <p>Take a photo of your waste item using your camera</p>
            </div>
            
            <div className="feature-card">
              <div className="feature-number">2</div>
              <Recycle size={40} className="feature-icon" />
              <h3>AI Identifies</h3>
              <p>Our AI analyzes and identifies the waste category</p>
            </div>
            
            <div className="feature-card">
              <div className="feature-number">3</div>
              <Leaf size={40} className="feature-icon" />
              <h3>Get Instructions</h3>
              <p>Receive step-by-step disposal guidance</p>
            </div>
            
            <div className="feature-card">
              <div className="feature-number">4</div>
              <Award size={40} className="feature-icon" />
              <h3>Earn Rewards</h3>
              <p>Collect points and climb the leaderboard</p>
            </div>
          </div>
        </section>

        {/* CTA Section */}
        <section className="cta-section">
          <div className="cta-card">
            <h2>Ready to Make an Impact?</h2>
            <p>Join thousands of users making a difference, one scan at a time</p>
            <Link to="/scan" className="btn btn-primary btn-lg">
              Start Scanning
            </Link>
          </div>
        </section>
      </div>
    </div>
  );
}

export default HomePage;
