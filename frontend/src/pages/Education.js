import React from 'react';
import './Education.css';

function EducationPage() {
  return (
    <div className="education-page">
      <div className="container">
        <h1>Learn About Waste</h1>
        <div className="card">
          <h2>Waste Categories</h2>
          <ul>
            <li>♻️ Recyclable Plastic</li>
            <li>📄 Paper & Cardboard</li>
            <li>🍃 Organic/Compost</li>
            <li>🔋 Hazardous Waste</li>
            <li>🗑️ Non-Recyclable</li>
            <li>🥫 Metal & Glass</li>
          </ul>
        </div>
      </div>
    </div>
  );
}

export default EducationPage;
