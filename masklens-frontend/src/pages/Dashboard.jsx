import React, { useRef, useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

const Dashboard = () => {
  const navigate = useNavigate();
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const [cameraOn, setCameraOn] = useState(false);
  const [capturedImage, setCapturedImage] = useState(null);
  const [predictedEmotion, setPredictedEmotion] = useState(null);
  const [maskStatus, setMaskStatus] = useState(null);
  const [facesDetected, setFacesDetected] = useState(1);
  const [annotatedImage, setAnnotatedImage] = useState(null);
  const [showProfile, setShowProfile] = useState(false);
  const [showWeeklySummary, setShowWeeklySummary] = useState(false);
  const [emotionHistory, setEmotionHistory] = useState([]);
  const [weeklySummaryData, setWeeklySummaryData] = useState(null);
  const [isAdmin, setIsAdmin] = useState(false);
  const [userFullname, setUserFullname] = useState("");

  // Check if user is logged in and check admin status
  useEffect(() => {
    const token = localStorage.getItem("access_token");
    if (!token) {
      alert("Please login first");
      navigate("/login");
    } else {
      // Get user's fullname from localStorage
      const fullname = localStorage.getItem("user_fullname") || "User";
      setUserFullname(fullname);
      
      // Fetch user's emotion history
      fetchEmotionHistory();
      // Check if user is admin
      checkAdminStatus();
    }
  }, [navigate]);

  // Check if current user is admin
  const checkAdminStatus = async () => {
    const token = localStorage.getItem("access_token");
    
    try {
      const response = await fetch("http://localhost:5000/admin/dashboard", {
        method: "GET",
        headers: {
          "Authorization": `Bearer ${token}`,
        },
      });

      if (response.ok) {
        setIsAdmin(true);
      } else {
        setIsAdmin(false);
      }
    } catch (error) {
      setIsAdmin(false);
    }
  };

  // Fetch emotion history from backend
  const fetchEmotionHistory = async () => {
    const token = localStorage.getItem("access_token");
    
    try {
      const response = await fetch("http://localhost:5000/my_emotions", {
        method: "GET",
        headers: {
          "Authorization": `Bearer ${token}`,
        },
      });

      const data = await response.json();
      
      if (response.ok) {
        setEmotionHistory(data.emotions);
      } else {
        console.error("Failed to fetch emotions:", data);
      }
    } catch (error) {
      console.error("Error fetching emotions:", error);
    }
  };

  // Fetch weekly summary from backend
  const fetchWeeklySummary = async () => {
    const token = localStorage.getItem("access_token");
    console.log("Fetching weekly summary...");
    
    try {
      const response = await fetch("http://localhost:5000/weekly_summary", {
        method: "GET",
        headers: {
          "Authorization": `Bearer ${token}`,
        },
      });

      console.log("Weekly summary response status:", response.status);
      const data = await response.json();
      console.log("Weekly summary data:", data);
      
      if (response.ok) {
        setWeeklySummaryData(data);
        console.log("Weekly summary data set successfully");
      } else {
        console.error("Failed to fetch weekly summary:", data);
        // Set empty data structure if no data available
        if (data.message === "No data for weekly summary") {
          setWeeklySummaryData({
            daily_graph: {},
            most_frequent: null,
            quote: null
          });
        }
      }
    } catch (error) {
      console.error("Error fetching weekly summary:", error);
    }
  };

  // Navigation handlers
  const handleLogout = () => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("user_fullname");
    localStorage.removeItem("user_role");
    navigate("/");
  };

  const handleProfile = () => {
    setShowProfile(!showProfile);
    setShowWeeklySummary(false);
  };

  const handleWeeklySummary = () => {
    const newState = !showWeeklySummary;
    setShowWeeklySummary(newState);
    setShowProfile(false);
    if (newState) {
      fetchWeeklySummary();
    }
  };

  // Start Camera
  const startCamera = async () => {
    setCameraOn(true);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: true });

      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        videoRef.current.play();
      }
    } catch (err) {
      alert("Camera permission denied / No camera available");
      console.error(err);
    }
  };

  // Stop Camera
  const stopCamera = () => {
    if (videoRef.current && videoRef.current.srcObject) {
      videoRef.current.srcObject.getTracks().forEach(track => track.stop());
      videoRef.current.srcObject = null;
    }
    setCameraOn(false);
  };

  // Capture Photo and Send to API with JWT
  const capturePhoto = async () => {
    if (!videoRef.current) return;

    const canvas = canvasRef.current;
    const video = videoRef.current;

    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;

    const ctx = canvas.getContext("2d");
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

    const photo = canvas.toDataURL("image/png");
    setCapturedImage(photo);
    setPredictedEmotion("Analyzing...");
    setMaskStatus(null);
    setFacesDetected(1);
    setAnnotatedImage(null);

    // Get JWT token
    const token = localStorage.getItem("access_token");
    console.log("Token exists:", !!token);

    if (!token) {
      setPredictedEmotion("Error: Not logged in");
      alert("Please login first");
      navigate("/login");
      return;
    }

    // Convert base64 to blob
    const blob = await fetch(photo).then(res => res.blob());
    console.log("Blob created:", blob.size, "bytes");
    
    // Create FormData and append the image
    const formData = new FormData();
    formData.append("image", blob, "captured_image.png");

    try {
      console.log("Sending request to backend...");
      
      // Send to backend API with Authorization header
      const response = await fetch("http://localhost:5000/predict", {
        method: "POST",
        headers: {
          "Authorization": `Bearer ${token}`,
        },
        body: formData,
      });

      console.log("Response status:", response.status);
      console.log("Response ok:", response.ok);

      // Try to parse response
      let data;
      try {
        const responseText = await response.text();
        console.log("Raw response:", responseText);
        data = JSON.parse(responseText);
        console.log("Parsed response data:", data);
      } catch (parseError) {
        console.error("Failed to parse response:", parseError);
        setPredictedEmotion("Error: Invalid response from server");
        alert(`Error: Server returned invalid response. Status: ${response.status}`);
        return;
      }
      
      if (response.ok) {
        // Handle new response format with mask_status and emotion
        if (data.emotion) {
          setPredictedEmotion(data.emotion);
          setMaskStatus(data.mask_status);
          setFacesDetected(data.faces_detected || 1);
          
          // If multiple faces detected and annotated image provided
          if (data.annotated_image) {
            setAnnotatedImage(data.annotated_image);
          }
          
          console.log("Prediction set to:", data.emotion);
          console.log("Mask status:", data.mask_status);
          console.log("Faces detected:", data.faces_detected);
        } else if (data.prediction) {
          // Fallback for old format
          setPredictedEmotion(data.prediction);
          console.log("Prediction set to:", data.prediction);
        }
        // Refresh emotion history
        fetchEmotionHistory();
      } else {
        const errorMsg = data.error || data.msg || `Server error (${response.status})`;
        setPredictedEmotion(`Error: ${errorMsg}`);
        console.error("API Error:", data);
        alert(`API Error: ${errorMsg}`);
      }
    } catch (error) {
      const errorMsg = "Failed to connect to API";
      setPredictedEmotion(errorMsg);
      console.error("Network Error:", error);
      alert(`Network Error: ${error.message}`);
    }
  };

  // Calculate weekly summary from emotion history
  const calculateWeeklySummary = () => {
    const oneWeekAgo = new Date();
    oneWeekAgo.setDate(oneWeekAgo.getDate() - 7);

    const weeklyEmotions = emotionHistory.filter(emotion => {
      const emotionDate = new Date(emotion.timestamp);
      return emotionDate >= oneWeekAgo;
    });

    const happyCount = weeklyEmotions.filter(e => e.emotion === "Happy").length;
    const sadCount = weeklyEmotions.filter(e => e.emotion === "Sad").length;

    return {
      total: weeklyEmotions.length,
      happy: happyCount,
      sad: sadCount,
    };
  };

  const weeklySummary = calculateWeeklySummary();

  return (
    <div style={styles.container}>
      {/* Navigation Bar */}
      <nav style={styles.navbar}>
        <div style={styles.navLeft}>
          <h2 style={styles.navTitle}>MaskLens Dashboard</h2>
        </div>
        <div style={styles.navRight}>
          <button style={styles.navButton} onClick={handleProfile}>
            👤 Profile
          </button>
          <button style={styles.navButton} onClick={handleWeeklySummary}>
            📊 Weekly Summary
          </button>
          {isAdmin && (
            <button style={styles.navButton} onClick={() => navigate("/admin")}>
              🛡️ Admin
            </button>
          )}
          <button style={styles.logoutButton} onClick={handleLogout}>
            🚪 Logout
          </button>
        </div>
      </nav>

      {/* Main Content */}
      <div style={styles.mainContent}>
        {/* Greeting Section */}
        <div style={styles.greetingSection}>
          <h2 style={styles.greetingText}>Hi {userFullname}, how are you doing 👋</h2>
          <h5 style={styles.greetQuote}>Every emotion you record is a message from your mind trying to help you grow.</h5>
          <h6 style={styles.greetQuote}>Just Track Your Mood!</h6>
        </div>

        {/* Profile Section */}
        {showProfile && (
          <div style={styles.infoCard}>
            <h3 style={styles.cardTitle}>User Profile</h3>
            <div style={styles.userInfo}>
              <p><strong>Total Predictions:</strong> {emotionHistory.length}</p>
              <p><strong>Happy Emotions:</strong> {emotionHistory.filter(e => e.emotion === "Happy").length}</p>
              <p><strong>Sad Emotions:</strong> {emotionHistory.filter(e => e.emotion === "Sad").length}</p>
            </div>
            
            <h4 style={{ marginTop: "20px", marginBottom: "10px" }}>Recent History:</h4>
            <div style={styles.historyList}>
              {emotionHistory.slice(0, 5).map((emotion) => (
                <div key={emotion.id} style={styles.historyItem}>
                  <span style={styles.emotionBadge}>{emotion.emotion}</span>
                  <span style={styles.timestamp}>
                    {new Date(emotion.timestamp).toLocaleString()}
                  </span>
                </div>
              ))}
              {emotionHistory.length === 0 && (
                <p style={{ color: "#999", fontStyle: "italic" }}>No predictions yet</p>
              )}
            </div>
          </div>
        )}

        {/* Weekly Summary Section */}
        {showWeeklySummary && (
          <div style={styles.infoCard}>
            <h3 style={styles.cardTitle}>Weekly Summary (Last 7 Days)</h3>
            
            {weeklySummaryData ? (
              <>
                {Object.keys(weeklySummaryData.daily_graph || {}).length > 0 ? (
                  <>
                    {/* Summary Stats */}
                    <div style={styles.summaryStats}>
                      <div style={styles.statBox}>
                        <div style={styles.statNumber}>
                          {Object.values(weeklySummaryData.daily_graph || {}).reduce((sum, day) => sum + day.Happy + day.Sad, 0)}
                        </div>
                        <div style={styles.statLabel}>Total Sessions</div>
                      </div>
                      <div style={styles.statBox}>
                        <div style={{...styles.statNumber, color: "#4CAF50"}}>
                          {Object.values(weeklySummaryData.daily_graph || {}).reduce((sum, day) => sum + day.Happy, 0)}
                        </div>
                        <div style={styles.statLabel}>Happy 😊</div>
                      </div>
                      <div style={styles.statBox}>
                        <div style={{...styles.statNumber, color: "#FF6B6B"}}>
                          {Object.values(weeklySummaryData.daily_graph || {}).reduce((sum, day) => sum + day.Sad, 0)}
                        </div>
                        <div style={styles.statLabel}>Sad 😢</div>
                      </div>
                    </div>

                    {/* Graph */}
                    <div style={styles.graphContainer}>
                      <h4 style={styles.graphTitle}>Daily Emotion Trend</h4>
                      <ResponsiveContainer width="100%" height={300}>
                        <LineChart
                          data={Object.entries(weeklySummaryData.daily_graph).map(([date, emotions]) => ({
                            date: new Date(date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
                            Happy: emotions.Happy,
                            Sad: emotions.Sad,
                          }))}
                          margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
                        >
                          <CartesianGrid strokeDasharray="3 3" />
                          <XAxis dataKey="date" />
                          <YAxis />
                          <Tooltip />
                          <Legend />
                          <Line type="monotone" dataKey="Happy" stroke="#4CAF50" strokeWidth={2} />
                          <Line type="monotone" dataKey="Sad" stroke="#FF6B6B" strokeWidth={2} />
                        </LineChart>
                      </ResponsiveContainer>
                    </div>

                    {/* Motivational Quote */}
                    {weeklySummaryData.quote && (
                      <div style={styles.quoteBox}>
                        <p style={styles.quote}>"{weeklySummaryData.quote}"</p>
                        <p style={styles.quoteAuthor}>Most Frequent: {weeklySummaryData.most_frequent}</p>
                      </div>
                    )}
                  </>
                ) : (
                  <div style={{ textAlign: "center", padding: "40px 20px" }}>
                    <div style={{ fontSize: "4rem", marginBottom: "20px" }}>📊</div>
                    <h4 style={{ color: "#333", marginBottom: "10px" }}>No Data Yet</h4>
                    <p style={{ color: "#666", marginBottom: "20px" }}>
                      Start capturing emotions to see your weekly trends!
                    </p>
                    <p style={{ color: "#999", fontSize: "0.9rem" }}>
                      Capture at least one emotion in the last 7 days to generate the graph.
                    </p>
                  </div>
                )}
              </>
            ) : (
              <div style={{ textAlign: "center", padding: "40px 20px" }}>
                <div style={{ fontSize: "3rem", marginBottom: "20px" }}>⏳</div>
                <p style={{ color: "#999", fontStyle: "italic" }}>
                  Loading weekly summary...
                </p>
              </div>
            )}
          </div>
        )}

        {/* Camera Section */}
        <div style={styles.cameraSection}>
          <h3 style={styles.sectionTitle}>Emotion Detection</h3>
          
          {/* Capture Button */}
          {!cameraOn && (
            <button onClick={startCamera} style={styles.captureButton}>
              📸 Open Camera
            </button>
          )}

          {/* Video Preview */}
          {cameraOn && (
            <div style={styles.cameraBox}>
              <video
                ref={videoRef}
                style={styles.video}
              />
              <div style={styles.cameraControls}>
                <button onClick={capturePhoto} style={styles.takePhotoButton}>
                  📷 Take Photo
                </button>
                <button onClick={stopCamera} style={styles.closeCameraButton}>
                  ❌ Close Camera
                </button>
              </div>
            </div>
          )}

          <canvas ref={canvasRef} style={{ display: "none" }} />

          {/* Show Captured Image with Prediction */}
          {capturedImage && (
            <div style={styles.imagePreview}>
              <div style={styles.predictionResult}>
                {/* Multiple Faces Warning */}
                {facesDetected > 1 && (
                  <div style={styles.multipleFacesWarning}>
                    <span style={styles.warningIcon}>👥</span>
                    <span style={styles.warningText}>
                      {facesDetected} faces detected - analyzing the largest face (shown in green box)
                    </span>
                  </div>
                )}
                
                {/* Mask Status */}
                {maskStatus && (
                  <div style={styles.maskStatusContainer}>
                    <span style={{
                      ...styles.maskBadge,
                      backgroundColor: maskStatus === "MASK" ? "#2196F3" : "#FF9800"
                    }}>
                      {maskStatus === "MASK" ? "😷 Wearing Mask" : "👤 No Mask"}
                    </span>
                  </div>
                )}
                
                {/* Emotion Prediction */}
                <h3 style={styles.predictionTitle}>Predicted Emotion:</h3>
                <div style={styles.emotionDisplay}>
                  {predictedEmotion === "Happy" && <span style={styles.emotionHappy}>😊 Happy</span>}
                  {predictedEmotion === "Sad" && <span style={styles.emotionSad}>😢 Sad</span>}
                  {predictedEmotion === "Analyzing..." && <span style={styles.emotionAnalyzing}>⏳ Analyzing...</span>}
                  {predictedEmotion && !["Happy", "Sad", "Analyzing..."].includes(predictedEmotion) && (
                    <span style={styles.emotionError}>⚠️ {predictedEmotion}</span>
                  )}
                </div>
                
                {/* Model Info */}
                {maskStatus && predictedEmotion && !["Analyzing..."].includes(predictedEmotion) && (
                  <div style={styles.modelInfo}>
                    <small style={styles.modelInfoText}>
                      Model used: {maskStatus === "MASK" ? "Masked Emotion Model" : "Regular Emotion Model"}
                    </small>
                  </div>
                )}
              </div>
              <img
                src={annotatedImage || capturedImage}
                alt="Captured"
                style={styles.capturedImage}
              />
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

// Styles
const styles = {
  container: {
    minHeight: "100vh",
    background: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
    fontFamily: "'Segoe UI', Tahoma, Geneva, Verdana, sans-serif",
  },
  navbar: {
    backgroundColor: "rgba(255, 255, 255, 0.95)",
    backdropFilter: "blur(10px)",
    padding: "15px 30px",
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    boxShadow: "0 2px 10px rgba(0,0,0,0.1)",
  },
  navLeft: {
    display: "flex",
    alignItems: "center",
  },
  navTitle: {
    margin: 0,
    color: "#333",
    fontWeight: "600",
    fontSize: "1.5rem",
  },
  navRight: {
    display: "flex",
    gap: "10px",
    alignItems: "center",
  },
  navButton: {
    backgroundColor: "#4CAF50",
    color: "white",
    border: "none",
    padding: "10px 15px",
    borderRadius: "8px",
    cursor: "pointer",
    fontSize: "0.9rem",
    fontWeight: "500",
    transition: "all 0.3s ease",
  },
  logoutButton: {
    backgroundColor: "#f44336",
    color: "white",
    border: "none",
    padding: "10px 15px",
    borderRadius: "8px",
    cursor: "pointer",
    fontSize: "0.9rem",
    fontWeight: "500",
    transition: "all 0.3s ease",
  },
  mainContent: {
    padding: "30px",
    display: "flex",
    flexDirection: "column",
    gap: "20px",
  },
  greetingSection: {
    textAlign: "center",
    marginBottom: "10px",
  },
  greetingText: {
    color: "#fff",
    fontSize: "1.8rem",
    fontWeight: "500",
    textShadow: "2px 2px 4px rgba(0,0,0,0.2)",
    margin: 0,
  },
  greetQuote: {
    color: "#fff",
    fontSize: "1.2rem",   // smaller than 1.8rem
    fontWeight: "400",    // lighter weight for subheading
    fontStyle: "italic",
    textShadow: "2px 2px 4px rgba(0,0,0,0.2)",
    margin: 0,
  },
  infoCard: {
    backgroundColor: "rgba(255, 255, 255, 0.9)",
    borderRadius: "15px",
    padding: "25px",
    boxShadow: "0 4px 15px rgba(0,0,0,0.1)",
    maxWidth: "600px",
    margin: "0 auto",
    width: "100%",
  },
  cardTitle: {
    margin: "0 0 20px 0",
    color: "#333",
    fontSize: "1.3rem",
    fontWeight: "600",
  },
  userInfo: {
    lineHeight: "2",
    color: "#555",
  },
  summaryInfo: {
    lineHeight: "2",
    color: "#555",
  },
  historyList: {
    display: "flex",
    flexDirection: "column",
    gap: "10px",
  },
  historyItem: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    padding: "10px",
    backgroundColor: "#f5f5f5",
    borderRadius: "8px",
  },
  emotionBadge: {
    padding: "5px 12px",
    borderRadius: "20px",
    backgroundColor: "#4CAF50",
    color: "white",
    fontSize: "0.85rem",
    fontWeight: "500",
  },
  timestamp: {
    fontSize: "0.85rem",
    color: "#666",
  },
  cameraSection: {
    backgroundColor: "rgba(255, 255, 255, 0.9)",
    borderRadius: "15px",
    padding: "30px",
    boxShadow: "0 4px 15px rgba(0,0,0,0.1)",
    textAlign: "center",
    maxWidth: "600px",
    margin: "0 auto",
    width: "100%",
  },
  sectionTitle: {
    margin: "0 0 25px 0",
    color: "#333",
    fontSize: "1.3rem",
    fontWeight: "600",
  },
  captureButton: {
    backgroundColor: "#2196F3",
    color: "white",
    border: "none",
    padding: "15px 25px",
    borderRadius: "10px",
    cursor: "pointer",
    fontSize: "1.1rem",
    fontWeight: "500",
    transition: "all 0.3s ease",
  },
  cameraBox: {
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    gap: "15px",
  },
  video: {
    width: "400px",
    maxWidth: "100%",
    borderRadius: "12px",
    boxShadow: "0 4px 10px rgba(0,0,0,0.2)",
  },
  cameraControls: {
    display: "flex",
    gap: "15px",
  },
  takePhotoButton: {
    backgroundColor: "#4CAF50",
    color: "white",
    border: "none",
    padding: "12px 20px",
    borderRadius: "8px",
    cursor: "pointer",
    fontSize: "1rem",
    fontWeight: "500",
  },
  closeCameraButton: {
    backgroundColor: "#f44336",
    color: "white",
    border: "none",
    padding: "12px 20px",
    borderRadius: "8px",
    cursor: "pointer",
    fontSize: "1rem",
    fontWeight: "500",
  },
  imagePreview: {
    marginTop: "25px",
  },
  predictionResult: {
    marginBottom: "20px",
    padding: "20px",
    backgroundColor: "#f8f9fa",
    borderRadius: "12px",
    boxShadow: "0 2px 8px rgba(0,0,0,0.1)",
  },
  predictionTitle: {
    margin: "0 0 15px 0",
    color: "#333",
    fontSize: "1.2rem",
    fontWeight: "600",
  },
  emotionDisplay: {
    fontSize: "2rem",
    fontWeight: "bold",
    textAlign: "center",
  },
  emotionHappy: {
    color: "#4CAF50",
    display: "inline-block",
    animation: "fadeIn 0.5s ease-in",
  },
  emotionSad: {
    color: "#FF6B6B",
    display: "inline-block",
    animation: "fadeIn 0.5s ease-in",
  },
  emotionAnalyzing: {
    color: "#2196F3",
    display: "inline-block",
  },
  emotionError: {
    color: "#FF9800",
    display: "inline-block",
    fontSize: "1.2rem",
  },
  capturedImage: {
    width: "400px",
    maxWidth: "100%",
    borderRadius: "12px",
    boxShadow: "0 4px 10px rgba(0,0,0,0.2)",
  },
  maskStatusContainer: {
    marginBottom: "15px",
    textAlign: "center",
  },
  maskBadge: {
    display: "inline-block",
    padding: "8px 16px",
    borderRadius: "20px",
    color: "white",
    fontSize: "1rem",
    fontWeight: "600",
    boxShadow: "0 2px 5px rgba(0,0,0,0.2)",
  },
  multipleFacesWarning: {
    backgroundColor: "#fff3cd",
    border: "1px solid #ffc107",
    borderRadius: "8px",
    padding: "12px 16px",
    marginBottom: "15px",
    display: "flex",
    alignItems: "center",
    gap: "10px",
  },
  warningIcon: {
    fontSize: "1.5rem",
  },
  warningText: {
    color: "#856404",
    fontSize: "0.95rem",
    fontWeight: "500",
  },
  modelInfo: {
    marginTop: "15px",
    textAlign: "center",
  },
  modelInfoText: {
    color: "#666",
    fontSize: "0.85rem",
    fontStyle: "italic",
  },
  summaryStats: {
    display: "flex",
    justifyContent: "space-around",
    marginBottom: "30px",
    gap: "15px",
  },
  statBox: {
    flex: 1,
    textAlign: "center",
    padding: "20px",
    backgroundColor: "#f8f9fa",
    borderRadius: "12px",
    boxShadow: "0 2px 5px rgba(0,0,0,0.1)",
  },
  statNumber: {
    fontSize: "2.5rem",
    fontWeight: "bold",
    color: "#333",
    marginBottom: "5px",
  },
  statLabel: {
    fontSize: "0.9rem",
    color: "#666",
    fontWeight: "500",
  },
  graphContainer: {
    marginTop: "20px",
    padding: "20px",
    backgroundColor: "#fff",
    borderRadius: "12px",
    boxShadow: "0 2px 5px rgba(0,0,0,0.1)",
  },
  graphTitle: {
    margin: "0 0 20px 0",
    color: "#333",
    fontSize: "1.1rem",
    fontWeight: "600",
    textAlign: "center",
  },
  quoteBox: {
    marginTop: "25px",
    padding: "20px",
    backgroundColor: "#f0f7ff",
    borderLeft: "4px solid #2196F3",
    borderRadius: "8px",
  },
  quote: {
    fontSize: "1.1rem",
    fontStyle: "italic",
    color: "#333",
    margin: "0 0 10px 0",
  },
  quoteAuthor: {
    fontSize: "0.9rem",
    color: "#666",
    textAlign: "right",
    margin: 0,
  },
};

export default Dashboard;
