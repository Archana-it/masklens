import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";

const AdminRoute = ({ children }) => {
  const navigate = useNavigate();
  const [isAdmin, setIsAdmin] = useState(null); // null = checking, true = admin, false = not admin
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    checkAdminAccess();
  }, []);

  const checkAdminAccess = async () => {
    const token = localStorage.getItem("access_token");
    
    if (!token) {
      navigate("/login");
      return;
    }

    try {
      const response = await fetch("http://localhost:5000/admin/dashboard", {
        method: "GET",
        headers: {
          "Authorization": `Bearer ${token}`,
        },
      });

      if (response.ok) {
        setIsAdmin(true);
      } else if (response.status === 403) {
        setIsAdmin(false);
        alert("Access denied: Admin privileges required");
        navigate("/dashboard");
      } else if (response.status === 401) {
        setIsAdmin(false);
        alert("Session expired. Please login again");
        localStorage.removeItem("access_token");
        navigate("/login");
      } else {
        setIsAdmin(false);
        navigate("/dashboard");
      }
    } catch (error) {
      setIsAdmin(false);
      console.error("Admin check failed:", error);
      navigate("/dashboard");
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div style={styles.loadingContainer}>
        <div style={styles.loading}>Verifying admin access...</div>
      </div>
    );
  }

  if (isAdmin) {
    return children;
  }

  return null; // This shouldn't render as navigation should have occurred
};

const styles = {
  loadingContainer: {
    minHeight: "100vh",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: "#f5f7fa",
  },
  loading: {
    fontSize: "1.2rem",
    color: "#666",
  },
};

export default AdminRoute;