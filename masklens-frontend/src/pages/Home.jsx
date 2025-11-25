import React from "react";
import { Link } from "react-router-dom";

function Home() {
  return (
    <div style={styles.container}>
      {/* Navbar */}
      <nav style={styles.navbar}>
        <div style={styles.logoText}>MaskLens</div>
        <div>
          <Link to="/register" style={{ ...styles.button, marginRight: "10px" }}>
            Register
          </Link>
          <Link to="/login" style={styles.button}>
            Login
          </Link>
        </div>
      </nav>

      {/* Main Section */}
      <div style={styles.main}>
        {/* Logo / Title */}
        <div style={styles.logoCircle}>😷</div>
        <h1 style={styles.title}>Welcome to MaskLens</h1>
        <p style={styles.description}>
          Detect emotions with or without masks — track your mood every day and view your
          weekly emotional summary. Your well-being, visualized beautifully.
        </p>
      </div>
    </div>
  );
}

// 🎨 Style objects
const styles = {
  container: {
    minHeight: "100vh",
    background: "linear-gradient(to bottom right, #6C63FF, #74ebd5)",
    color: "#fff",
    fontFamily: "'Poppins', sans-serif",
    display: "flex",
    flexDirection: "column",
  },
  navbar: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    padding: "15px 50px",
    backgroundColor: "rgba(255, 255, 255, 0.1)",
    backdropFilter: "blur(10px)",
  },
  logoText: {
    fontSize: "1.8rem",
    fontWeight: "bold",
    letterSpacing: "1px",
  },
  button: {
    backgroundColor: "#fff",
    color: "#6C63FF",
    padding: "10px 20px",
    borderRadius: "25px",
    textDecoration: "none",
    fontWeight: "500",
    transition: "0.3s",
  },
  main: {
    flex: 1,
    textAlign: "center",
    marginTop: "80px",
    padding: "0 20px",
  },
  title: {
    fontSize: "3rem",
    marginBottom: "10px",
  },
  description: {
    fontSize: "1.2rem",
    maxWidth: "600px",
    margin: "0 auto",
    color: "rgba(255,255,255,0.9)",
  },
  logoCircle: {
    width: "100px",
    height: "100px",
    backgroundColor: "rgba(255,255,255,0.2)",
    borderRadius: "50%",
    margin: "0 auto 20px",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    fontSize: "2.5rem",
  },
};

// Add hover effects using inline pseudo-class (optional JS approach)
styles.button = {
  ...styles.button,
  cursor: "pointer",
};
export default Home;
