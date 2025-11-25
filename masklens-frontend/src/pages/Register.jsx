import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";

function Register() {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    fullname: "",
    email: "",
    password: ""
  });
  const [loading, setLoading] = useState(false);
  const [passwordError, setPasswordError] = useState("");

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
    
    // Clear password error when user types
    if (e.target.name === "password") {
      setPasswordError("");
    }
  };

  const validatePassword = (password) => {
    if (password.length < 8) {
      return "Password must be at least 8 characters long";
    }
    if (password.length > 16) {
      return "Password must not exceed 16 characters";
    }
    if (!/[A-Z]/.test(password)) {
      return "Password must contain at least one uppercase letter";
    }
    if (!/[a-z]/.test(password)) {
      return "Password must contain at least one lowercase letter";
    }
    if (!/\d/.test(password)) {
      return "Password must contain at least one number";
    }
    if (!/[!@#$%^&*(),.?":{}|<>]/.test(password)) {
      return "Password must contain at least one special character";
    }
    return "";
  };

  const handleRegister = async (e) => {
    e.preventDefault();
    
    // Validate password before submitting
    const error = validatePassword(formData.password);
    if (error) {
      setPasswordError(error);
      return;
    }
    
    setLoading(true);

    try {
      const response = await fetch("http://localhost:5000/register", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(formData),
      });

      const data = await response.json();

      if (response.ok) {
        alert("Registered successfully!");
        navigate("/login");
      } else {
        alert(`Error: ${data.error}`);
      }
    } catch (error) {
      alert("Failed to connect to server");
      console.error("Registration error:", error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={styles.container}>
      {/* Navbar */}
      <nav style={styles.navbar}>
        <Link to="/" style={styles.backButton}>← Home</Link>
        <h2 style={styles.navTitle}>Register</h2>
      </nav>

      {/* Register Form */}
      <div style={styles.formContainer}>
        <form onSubmit={handleRegister} style={styles.form}>
          <h2 style={styles.formTitle}>Create Your Account</h2>
          <input 
            type="text" 
            name="fullname"
            placeholder="Full Name" 
            required 
            style={styles.input}
            value={formData.fullname}
            onChange={handleChange}
          />
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
          {passwordError && (
            <div style={styles.errorMessage}>{passwordError}</div>
          )}
          <div style={styles.passwordRequirements}>
            <small style={styles.requirementsTitle}>Password Requirements:</small>
            <small style={styles.requirementItem}>• 8-16 characters</small>
            <small style={styles.requirementItem}>• At least one uppercase letter</small>
            <small style={styles.requirementItem}>• At least one lowercase letter</small>
            <small style={styles.requirementItem}>• At least one number</small>
            <small style={styles.requirementItem}>• At least one special character (!@#$%^&*...)</small>
          </div>
          <button type="submit" style={styles.submitButton} disabled={loading}>
            {loading ? "Registering..." : "Register"}
          </button>
          <p style={styles.loginText}>
            Already have an account?{" "}
            <Link to="/login" style={styles.loginLink}>Login here</Link>
          </p>
        </form>
      </div>
    </div>
  );
}

const styles = {
  container: {
    minHeight: "100vh",
    background: "linear-gradient(to right, #FFDEE9, #B5FFFC)",
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
    backgroundColor: "#74C69D",
    color: "#fff",
    border: "none",
    padding: "12px 20px",
    borderRadius: "10px",
    cursor: "pointer",
    fontSize: "1rem",
    transition: "0.3s",
    boxShadow: "0 3px 6px rgba(0,0,0,0.1)",
  },
  loginText: {
    marginTop: "15px",
    fontSize: "0.9rem",
    color: "#333",
  },
  loginLink: {
    color: "#6C63FF",
    textDecoration: "none",
    fontWeight: "500",
  },
  passwordRequirements: {
    textAlign: "left",
    backgroundColor: "#f0f0f0",
    padding: "10px",
    borderRadius: "8px",
    marginBottom: "15px",
    display: "flex",
    flexDirection: "column",
    gap: "3px",
  },
  requirementsTitle: {
    fontWeight: "600",
    color: "#333",
    marginBottom: "5px",
  },
  requirementItem: {
    color: "#666",
    fontSize: "0.8rem",
  },
  errorMessage: {
    backgroundColor: "#ffebee",
    color: "#c62828",
    padding: "8px",
    borderRadius: "6px",
    marginBottom: "10px",
    fontSize: "0.85rem",
    textAlign: "left",
  },
};

export default Register;
