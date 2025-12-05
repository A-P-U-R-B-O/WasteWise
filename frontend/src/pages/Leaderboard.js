import React from 'react';
import './Leaderboard.css';

function LeaderboardPage({ user }) {
  return (
    <div className="leaderboard-page">
      <div className="container">
        <h1>Leaderboard</h1>
        <div className="card">
          <p>Leaderboard feature coming soon! </p>
          <p>Your current rank: #145</p>
          <p>Your points: {user.points}</p>
        </div>
      </div>
    </div>
  );
}

export default LeaderboardPage;
