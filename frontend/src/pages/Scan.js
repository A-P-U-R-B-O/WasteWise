import React, { useState, useRef, useCallback } from 'react';
import Webcam from 'react-webcam';
import { motion, AnimatePresence } from 'framer-motion';
import Confetti from 'react-confetti';
import { toast } from 'react-hot-toast';
import {
  Camera,
  Upload,
  RotateCcw,
  Loader,
  CheckCircle,
  AlertCircle,
  X,
  Trash2,
  Leaf,
  Award,
  ArrowRight,
  Info
} from 'lucide-react';

import { scanWasteImage, scanWasteBase64 } from '../services/wasteService';
import './Scan.css';

function ScanPage({ user, setUser }) {
  // Camera states
  const [cameraActive, setCameraActive] = useState(false);
  const [facingMode, setFacingMode] = useState('environment'); // 'user' or 'environment'
  const webcamRef = useRef(null);
  
  // Image states
  const [capturedImage, setCapturedImage] = useState(null);
  const [selectedFile, setSelectedFile] = useState(null);
  
  // Processing states
  const [isProcessing, setIsProcessing] = useState(false);
  const [scanResult, setScanResult] = useState(null);
  const [error, setError] = useState(null);
  
  // UI states
  const [showConfetti, setShowConfetti] = useState(false);
  const fileInputRef = useRef(null);

  // ==================== CAMERA FUNCTIONS ====================

  const startCamera = () => {
    setCameraActive(true);
    setCapturedImage(null);
    setScanResult(null);
    setError(null);
  };

  const stopCamera = () => {
    setCameraActive(false);
  };

  const capturePhoto = useCallback(() => {
    const imageSrc = webcamRef.current. getScreenshot();
    if (imageSrc) {
      setCapturedImage(imageSrc);
      setCameraActive(false);
      toast.success('Photo captured! ');
    }
  }, [webcamRef]);

  const switchCamera = () => {
    setFacingMode(prev => prev === 'user' ? 'environment' : 'user');
  };

  const retakePhoto = () => {
    setCapturedImage(null);
    setScanResult(null);
    setError(null);
    startCamera();
  };

  // ==================== FILE UPLOAD ====================

  const handleFileSelect = (event) => {
    const file = event.target.files[0];
    if (file) {
      // Validate file type
      if (! file.type.startsWith('image/')) {
        toast.error('Please select an image file');
        return;
      }

      // Validate file size (10MB max)
      if (file.size > 10 * 1024 * 1024) {
        toast.error('Image too large. Maximum size is 10MB');
        return;
      }

      // Convert to base64
      const reader = new FileReader();
      reader. onloadend = () => {
        setCapturedImage(reader.result);
        setSelectedFile(file);
        setCameraActive(false);
        setScanResult(null);
        setError(null);
        toast.success('Image loaded! ');
      };
      reader. readAsDataURL(file);
    }
  };

  const triggerFileInput = () => {
    fileInputRef.current?. click();
  };

  // ==================== SCAN FUNCTIONS ====================

  const scanImage = async () => {
    if (!capturedImage) {
      toast. error('No image to scan');
      return;
    }

    setIsProcessing(true);
    setError(null);
    setScanResult(null);

    try {
      let result;

      if (selectedFile) {
        // Upload as file
        result = await scanWasteImage(selectedFile, user.id);
      } else {
        // Send base64
        result = await scanWasteBase64(capturedImage, user.id);
      }

      if (result.success) {
        setScanResult(result);
        
        // Update user points
        setUser(prev => ({
          ...prev,
          points: prev.points + result.points_earned,
          scans: prev.scans + 1
        }));

        // Show confetti for high confidence results
        if (result.confidence >= 0.8) {
          setShowConfetti(true);
          setTimeout(() => setShowConfetti(false), 5000);
        }

        toast.success(`Identified: ${result.item_name}! `, {
          icon: '🎉',
          duration: 4000
        });
      } else {
        throw new Error(result.message || 'Scan failed');
      }
    } catch (err) {
      console.error('Scan error:', err);
      setError(err.message || 'Failed to scan image.  Please try again.');
      toast. error('Scan failed. Please try again.');
    } finally {
      setIsProcessing(false);
    }
  };

  const resetScan = () => {
    setCapturedImage(null);
    setSelectedFile(null);
    setScanResult(null);
    setError(null);
    setCameraActive(false);
  };

  // ==================== RENDER ====================

  return (
    <div className="scan-page">
      {showConfetti && <Confetti recycle={false} numberOfPieces={500} />}
      
      <div className="container">
        <div className="scan-header">
          <h1>Scan Waste Item</h1>
          <p>Take a photo or upload an image to identify waste type</p>
        </div>

        <div className="scan-container">
          {/* ========== CAMERA / IMAGE DISPLAY ========== */}
          <div className="scan-view">
            <AnimatePresence mode="wait">
              {/* No Image - Show Options */}
              {!cameraActive && ! capturedImage && ! scanResult && (
                <motion. div
                  key="options"
                  initial={{ opacity: 0, scale: 0.9 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0, scale: 0.9 }}
                  className="scan-options"
                >
                  <div className="option-card" onClick={startCamera}>
                    <Camera size={64} />
                    <h3>Use Camera</h3>
                    <p>Take a photo of the waste item</p>
                  </div>

                  <div className="option-card" onClick={triggerFileInput}>
                    <Upload size={64} />
                    <h3>Upload Image</h3>
                    <p>Choose from your device</p>
                  </div>

                  <input
                    ref={fileInputRef}
                    type="file"
                    accept="image/*"
                    onChange={handleFileSelect}
                    style={{ display: 'none' }}
                  />
                </motion.div>
              )}

              {/* Camera Active */}
              {cameraActive && (
                <motion.div
                  key="camera"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  className="camera-view"
                >
                  <Webcam
                    ref={webcamRef}
                    audio={false}
                    screenshotFormat="image/jpeg"
                    videoConstraints={{
                      facingMode: facingMode,
                      width: 1280,
                      height: 720
                    }}
                    className="webcam"
                  />

                  <div className="camera-overlay">
                    <div className="scan-frame"></div>
                    <p className="camera-hint">
                      <Info size={16} />
                      Position the waste item in the frame
                    </p>
                  </div>

                  <div className="camera-controls">
                    <button className="btn-icon" onClick={stopCamera} title="Cancel">
                      <X size={24} />
                    </button>

                    <button className="btn-capture" onClick={capturePhoto}>
                      <div className="capture-ring">
                        <div className="capture-button"></div>
                      </div>
                    </button>

                    <button className="btn-icon" onClick={switchCamera} title="Switch Camera">
                      <RotateCcw size={24} />
                    </button>
                  </div>
                </motion.div>
              )}

              {/* Captured Image - Waiting for Scan */}
              {capturedImage && ! scanResult && ! isProcessing && (
                <motion.div
                  key="preview"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  className="image-preview"
                >
                  <img src={capturedImage} alt="Captured waste" />

                  <div className="preview-actions">
                    <button className="btn btn-outline" onClick={retakePhoto}>
                      <RotateCcw size={20} />
                      Retake
                    </button>

                    <button className="btn btn-primary" onClick={scanImage}>
                      <Camera size={20} />
                      Scan Now
                    </button>
                  </div>
                </motion.div>
              )}

              {/* Processing */}
              {isProcessing && (
                <motion.div
                  key="processing"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  className="processing-view"
                >
                  <div className="processing-animation">
                    <Loader className="spinner" size={64} />
                    <div className="processing-dots">
                      <span></span>
                      <span></span>
                      <span></span>
                    </div>
                  </div>

                  <h3>Analyzing Waste... </h3>
                  <p>Our AI is identifying your item</p>

                  {capturedImage && (
                    <img src={capturedImage} alt="Processing" className="processing-image" />
                  )}
                </motion.div>
              )}

              {/* Scan Result */}
              {scanResult && (
                <motion. div
                  key="result"
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -20 }}
                  className="scan-result"
                >
                  <ScanResult result={scanResult} image={capturedImage} />

                  <div className="result-actions">
                    <button className="btn btn-outline" onClick={resetScan}>
                      <Camera size={20} />
                      Scan Another
                    </button>
                  </div>
                </motion.div>
              )}

              {/* Error */}
              {error && (
                <motion.div
                  key="error"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  className="error-view"
                >
                  <AlertCircle size={64} className="error-icon" />
                  <h3>Scan Failed</h3>
                  <p>{error}</p>

                  <button className="btn btn-primary" onClick={retakePhoto}>
                    <RotateCcw size={20} />
                    Try Again
                  </button>
                </motion.div>
              )}
            </AnimatePresence>
          </div>

          {/* ========== TIPS SIDEBAR ========== */}
          <div className="scan-tips">
            <h3>📸 Tips for Best Results</h3>
            <ul>
              <li>
                <CheckCircle size={16} />
                Ensure good lighting
              </li>
              <li>
                <CheckCircle size={16} />
                Focus on one item at a time
              </li>
              <li>
                <CheckCircle size={16} />
                Get close to the item
              </li>
              <li>
                <CheckCircle size={16} />
                Avoid blurry images
              </li>
              <li>
                <CheckCircle size={16} />
                Remove packaging if possible
              </li>
            </ul>

            <div className="tip-card">
              <Leaf size={24} />
              <p>
                <strong>Did you know?</strong>
                <br />
                Recycling 1 plastic bottle saves enough energy to power a light bulb for 3 hours!
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

// ==================== SCAN RESULT COMPONENT ====================

function ScanResult({ result, image }) {
  const getBinColorStyle = (color) => {
    const colors = {
      'BLUE': '#3b82f6',
      'GREEN': '#10b981',
      'RED': '#ef4444',
      'BLACK': '#374151',
      'GREY': '#6b7280',
      'YELLOW': '#f59e0b'
    };
    return colors[color] || '#6b7280';
  };

  const getConfidenceColor = (confidence) => {
    if (confidence >= 0.8) return '#10b981';
    if (confidence >= 0.6) return '#f59e0b';
    return '#ef4444';
  };

  return (
    <div className="result-content">
      {/* Image Thumbnail */}
      {image && (
        <div className="result-image">
          <img src={image} alt={result.item_name} />
          <div 
            className="confidence-badge"
            style={{ background: getConfidenceColor(result.confidence) }}
          >
            {(result.confidence * 100).toFixed(0)}% Confident
          </div>
        </div>
      )}

      {/* Item Info */}
      <div className="result-header">
        <h2>{result.item_name}</h2>
        <div className="category-badge">
          {result.category}
        </div>
      </div>

      {/* Subcategory */}
      {result.subcategory && (
        <p className="subcategory">Type: {result.subcategory}</p>
      )}

      {/* Recyclable Badge */}
      <div className={`recyclable-badge ${result. recyclable ? 'recyclable' : 'non-recyclable'}`}>
        {result.recyclable ? '♻️ Recyclable' : '🚫 Non-Recyclable'}
      </div>

      {/* Points Earned */}
      <div className="points-earned">
        <Award size={24} />
        <span>+{result.points_earned} Points Earned! </span>
      </div>

      {/* Disposal Instructions */}
      <div className="disposal-section">
        <h3>
          <Trash2 size={20} />
          How to Dispose
        </h3>
        
        <div 
          className="bin-indicator"
          style={{ background: getBinColorStyle(result. bin_color) }}
        >
          <strong>{result.bin_color} BIN</strong>
        </div>

        <ol className="disposal-steps">
          {result.disposal_steps.map((step, index) => (
            <li key={index}>
              <span className="step-number">{index + 1}</span>
              {step}
            </li>
          ))}
        </ol>
      </div>

      {/* Environmental Impact */}
      {result.environmental_impact && (
        <div className="impact-section">
          <h3>
            <Leaf size={20} />
            Environmental Impact
          </h3>
          
          <div className="impact-grid">
            {result.environmental_impact.co2_saved_kg > 0 && (
              <div className="impact-item">
                <strong>CO₂ Saved</strong>
                <span>{result.environmental_impact.co2_saved_kg} kg</span>
              </div>
            )}
            
            {result.environmental_impact. decomposition_time && (
              <div className="impact-item">
                <strong>Decomposition Time</strong>
                <span>{result.environmental_impact.decomposition_time}</span>
              </div>
            )}
            
            {result.environmental_impact.recycling_potential && (
              <div className="impact-item">
                <strong>Recycling Potential</strong>
                <span>{result. environmental_impact.recycling_potential}</span>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Additional Tips */}
      {result.additional_tips && result.additional_tips.length > 0 && (
        <div className="tips-section">
          <h3>💡 Additional Tips</h3>
          <ul>
            {result.additional_tips.map((tip, index) => (
              <li key={index}>{tip}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Warnings */}
      {result.warnings && result.warnings.length > 0 && (
        <div className="warnings-section">
          <h3>⚠️ Important</h3>
          <ul>
            {result.warnings.map((warning, index) => (
              <li key={index}>{warning}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Alternatives */}
      {result.alternatives && (
        <div className="alternatives-section">
          <h3>🌱 For the Future</h3>
          <p>{result.alternatives}</p>
        </div>
      )}
    </div>
  );
}

export default ScanPage;
