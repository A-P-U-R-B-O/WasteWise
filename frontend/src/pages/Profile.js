import React from 'react';
import './Profile.css';

function ProfilePage({ user }) {
  return (
    <div className="profile-page">
      <div className="container">
        <h1>Profile Page</h1>
        <div className="card">
          <h2>{user.name}</h2>
          <p>Points: {user.points}</p>
          <p>Level: {user.level}</p>
          <p>Scans: {user.scans}</p>
        </div>
      </div>
    </div>
  );
}

export default ProfilePage;
