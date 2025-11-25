import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";

function Login() {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    email: "",
    password: ""
  });
  const [loading, setLoading] = useState(false);

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      const response = await fetch("http://localhost:5000/login", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(formData),
      });

      const data = await response.json();

      if (response.ok) {
        // Store JWT token and user info in localStorage
        localStorage.setItem("access_token", data.access_token);
        
        // Store user fullname and role if provided by backend
        if (data.fullname) {
          localStorage.setItem("user_fullname", data.fullname);
        }
        if (data.role) {
          localStorage.setItem("user_role", data.role);
        }
        
        // Check if user is admin
        if (data.role === "admin") {
          console.log("User is admin, redirecting to /admin");
          alert(`Welcome ${data.fullname || "Admin"}!`);
          navigate("/admin");
        } else {
          console.log("User is regular user, redirecting to /dashboard");
          alert(`Welcome ${data.fullname || "User"}!`);
          navigate("/dashboard");
        }
      } else {
        alert(`Error: ${data.error}`);
      }
    } catch (error) {
      alert("Failed to connect to server");
      console.error("Login error:", error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={styles.container}>
      {/* Navbar */}
      <nav style={styles.navbar}>
        <Link to="/" style={styles.backButton}>← Home</Link>
        <h2 style={styles.navTitle}>Login</h2>
      </nav>

      {/* Login Form */}
      <div style={styles.formContainer}>
        <form onSubmit={handleLogin} style={styles.form}>
          <h2 style={styles.formTitle}>Welcome Back!</h2>
          <input 
            type="email" 
            name="email"
            placeholder="Email" 
            required 
            style={styles.input}
            value={formData.email}
            onChange={handleChange}
          />
          <input 
            type="password" 
            name="password"
            placeholder="Password" 
            required 
            style={styles.input}
            value={formData.password}
            onChange={handleChange}
          />
          <button type="submit" style={styles.submitButton} disabled={loading}>
            {loading ? "Logging in..." : "Login"}
          </button>
          <p style={styles.registerText}>
            Don't have an account?{" "}
            <Link to="/register" style={styles.registerLink}>Register</Link>
          </p>
        </form>
      </div>
    </div>
  );
}

const styles = {
  container: {
    minHeight: "100vh",
    background: "linear-gradient(to right, #C9FFBF, #FFAFBD)",
    display: "flex",
    flexDirection: "column",
    fontFamily: "'Poppins', sans-serif",
  },
  navbar: {
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    padding: "15px 40px",
    backgroundColor: "rgba(255, 255, 255, 0.4)",
    backdropFilter: "blur(10px)",
    boxShadow: "0 2px 5px rgba(0,0,0,0.1)",
  },
  backButton: {
    color: "#333",
    textDecoration: "none",
    fontWeight: "500",
    fontSize: "1rem",
  },
  navTitle: {
    margin: 0,
    color: "#333",
    fontWeight: "600",
  },
  formContainer: {
    flex: 1,
    display: "flex",
    justifyContent: "center",
    alignItems: "center",
  },
  form: {
    backgroundColor: "rgba(255,255,255,0.8)",
    padding: "40px",
    borderRadius: "20px",
    boxShadow: "0 4px 10px rgba(0,0,0,0.1)",
    textAlign: "center",
    width: "350px",
  },
  formTitle: {
    marginBottom: "20px",
    color: "#333",
  },
  input: {
    width: "100%",
    padding: "10px 15px",
    marginBottom: "15px",
    borderRadius: "10px",
    border: "1px solid #ccc",
    outline: "none",
    fontSize: "1rem",
    transition: "0.2s",
  },
  submitButton: {
    backgroundColor: "#6C63FF",
    color: "#fff",
    border: "none",
    padding: "12px 20px",
    borderRadius: "10px",
    cursor: "pointer",
    fontSize: "1rem",
    transition: "0.3s",
  },
  registerText: {
    marginTop: "15px",
    fontSize: "0.9rem",
    color: "#333",
  },
  registerLink: {
    color: "#6C63FF",
    textDecoration: "none",
    fontWeight: "500",
  },
};

export default Login;
