import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, LineChart, Line, PieChart, Pie, Cell } from 'recharts';

const AdminDashboard = () => {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState("overview");
  const [dashboardData, setDashboardData] = useState(null);
  const [users, setUsers] = useState([]);
  const [emotions, setEmotions] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(false);
  const [showAddUserForm, setShowAddUserForm] = useState(false);
  const [newUser, setNewUser] = useState({
    fullname: "",
    email: "",
    password: "",
    role: "user"
  });

  // Check if user is admin
  useEffect(() => {
    const token = localStorage.getItem("access_token");
    if (!token) {
      alert("Please login first");
      navigate("/login");
      return;
    }
    
    // Load initial dashboard data and verify admin access
    fetchDashboardData();
  }, [navigate]);

  const fetchDashboardData = async () => {
    const token = localStorage.getItem("access_token");
    setLoading(true);
    
    try {
      const response = await fetch("http://localhost:5000/admin/dashboard", {
        method: "GET",
        headers: {
          "Authorization": `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setDashboardData(data);
      } else if (response.status === 403) {
        alert("Access denied: Admin privileges required");
        navigate("/dashboard");
      } else if (response.status === 401) {
        alert("Session expired. Please login again");
        localStorage.removeItem("access_token");
        navigate("/login");
      } else {
        console.error("Failed to fetch dashboard data");
        alert("Failed to load admin dashboard");
        navigate("/dashboard");
      }
    } catch (error) {
      console.error("Error fetching dashboard data:", error);
    } finally {
      setLoading(false);
    }
  };

  const fetchUsers = async () => {
    const token = localStorage.getItem("access_token");
    
    try {
      const response = await fetch("http://localhost:5000/admin/users", {
        method: "GET",
        headers: {
          "Authorization": `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setUsers(data.users);
      }
    } catch (error) {
      console.error("Error fetching users:", error);
    }
  };

  const fetchEmotions = async () => {
    const token = localStorage.getItem("access_token");
    
    try {
      const response = await fetch("http://localhost:5000/admin/emotions", {
        method: "GET",
        headers: {
          "Authorization": `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setEmotions(data.emotions);
      }
    } catch (error) {
      console.error("Error fetching emotions:", error);
    }
  };

  const fetchStats = async () => {
    const token = localStorage.getItem("access_token");
    
    try {
      const response = await fetch("http://localhost:5000/admin/stats", {
        method: "GET",
        headers: {
          "Authorization": `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setStats(data);
      }
    } catch (error) {
      console.error("Error fetching stats:", error);
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

  const createUser = async (e) => {
    e.preventDefault();
    
    if (!newUser.fullname || !newUser.email || !newUser.password) {
      alert("Please fill in all fields");
      return;
    }

    // Validate password
    const passwordError = validatePassword(newUser.password);
    if (passwordError) {
      alert(passwordError);
      return;
    }

    const token = localStorage.getItem("access_token");
    
    try {
      const response = await fetch("http://localhost:5000/admin/users/create", {
        method: "POST",
        headers: {
          "Authorization": `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify(newUser),
      });

      if (response.ok) {
        alert("User created successfully");
        setShowAddUserForm(false);
        setNewUser({ fullname: "", email: "", password: "", role: "user" });
        fetchUsers();
        fetchDashboardData(); // Refresh stats
      } else {
        const data = await response.json();
        alert(data.error || "Failed to create user");
      }
    } catch (error) {
      console.error("Error creating user:", error);
      alert("Error creating user");
    }
  };

  const toggleMaskLogic = async () => {
    const token = localStorage.getItem("access_token");
    
    try {
      const response = await fetch("http://localhost:5000/admin/toggle_mask_logic", {
        method: "POST",
        headers: {
          "Authorization": `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        alert(`Mask detection logic toggled!\n\nNew logic: ${data.current_logic}\n\nTry taking a photo with a mask to test.`);
      } else {
        alert("Failed to toggle mask logic");
      }
    } catch (error) {
      console.error("Error toggling mask logic:", error);
      alert("Error toggling mask logic");
    }
  };

  const deleteUser = async (userId) => {
    if (!window.confirm("Are you sure you want to delete this user? This will also delete all their emotion records.")) {
      return;
    }

    const token = localStorage.getItem("access_token");
    
    try {
      const response = await fetch(`http://localhost:5000/admin/users/${userId}`, {
        method: "DELETE",
        headers: {
          "Authorization": `Bearer ${token}`,
        },
      });

      if (response.ok) {
        alert("User deleted successfully");
        fetchUsers();
        fetchDashboardData(); // Refresh stats
      } else {
        alert("Failed to delete user");
      }
    } catch (error) {
      console.error("Error deleting user:", error);
      alert("Error deleting user");
    }
  };

  const deleteEmotion = async (emotionId) => {
    if (!window.confirm("Are you sure you want to delete this emotion record?")) {
      return;
    }

    const token = localStorage.getItem("access_token");
    
    try {
      const response = await fetch(`http://localhost:5000/admin/emotions/${emotionId}`, {
        method: "DELETE",
        headers: {
          "Authorization": `Bearer ${token}`,
        },
      });

      if (response.ok) {
        alert("Emotion record deleted successfully");
        fetchEmotions();
        fetchDashboardData(); // Refresh stats
      } else {
        alert("Failed to delete emotion record");
      }
    } catch (error) {
      console.error("Error deleting emotion:", error);
      alert("Error deleting emotion record");
    }
  };

  const handleTabChange = (tab) => {
    setActiveTab(tab);
    if (tab === "users" && users.length === 0) {
      fetchUsers();
    } else if (tab === "emotions" && emotions.length === 0) {
      fetchEmotions();
    } else if (tab === "analytics" && !stats) {
      fetchStats();
    }
  };

  const handleLogout = () => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("user_fullname");
    localStorage.removeItem("user_role");
    navigate("/");
  };

  // Colors for charts
  const COLORS = ['#4CAF50', '#FF6B6B', '#2196F3', '#FF9800'];

  if (loading) {
    return (
      <div style={styles.loadingContainer}>
        <div style={styles.loading}>Loading Admin Dashboard...</div>
      </div>
    );
  }

  return (
    <div style={styles.container}>
      {/* Header */}
      <header style={styles.header}>
        <div style={styles.headerLeft}>
          <h1 style={styles.title}>🛡️ Admin Dashboard</h1>
          <p style={styles.subtitle}>
            Hi {localStorage.getItem("user_fullname") || "Admin"}, how are you doing? 👋
          </p>
        </div>
        <div style={styles.headerRight}>
          <button style={styles.userDashboardBtn} onClick={() => navigate("/dashboard")}>
            👤 User Dashboard
          </button>
          <button style={styles.logoutBtn} onClick={handleLogout}>
            🚪 Logout
          </button>
        </div>
      </header>

      {/* Navigation Tabs */}
      <nav style={styles.tabNav}>
        {["overview", "users", "emotions", "analytics"].map((tab) => (
          <button
            key={tab}
            style={{
              ...styles.tabButton,
              ...(activeTab === tab ? styles.activeTab : {})
            }}
            onClick={() => handleTabChange(tab)}
          >
            {tab === "overview" && "📊 Overview"}
            {tab === "users" && "👥 Users"}
            {tab === "emotions" && "😊 Emotions"}
            {tab === "analytics" && "📈 Analytics"}
          </button>
        ))}
      </nav>

      {/* Content */}
      <main style={styles.content}>
        {/* Overview Tab */}
        {activeTab === "overview" && dashboardData && (
          <div style={styles.overviewGrid}>
            {/* Stats Cards */}
            <div style={styles.statsGrid}>
              <div style={styles.statCard}>
                <div style={styles.statIcon}>👥</div>
                <div style={styles.statContent}>
                  <div style={styles.statNumber}>{dashboardData.total_users}</div>
                  <div style={styles.statLabel}>Total Users</div>
                </div>
              </div>
              
              <div style={styles.statCard}>
                <div style={styles.statIcon}>😊</div>
                <div style={styles.statContent}>
                  <div style={styles.statNumber}>{dashboardData.total_emotions}</div>
                  <div style={styles.statLabel}>Total Emotions</div>
                </div>
              </div>
              
              <div style={styles.statCard}>
                <div style={styles.statIcon}>📈</div>
                <div style={styles.statContent}>
                  <div style={styles.statNumber}>
                    {dashboardData.emotion_stats.find(e => e.emotion === "Happy")?.count || 0}
                  </div>
                  <div style={styles.statLabel}>Happy Emotions</div>
                </div>
              </div>
              
              <div style={styles.statCard}>
                <div style={styles.statIcon}>📉</div>
                <div style={styles.statContent}>
                  <div style={styles.statNumber}>
                    {dashboardData.emotion_stats.find(e => e.emotion === "Sad")?.count || 0}
                  </div>
                  <div style={styles.statLabel}>Sad Emotions</div>
                </div>
              </div>
            </div>

            {/* Charts */}
            <div style={styles.chartsGrid}>
              {/* Emotion Distribution */}
              <div style={styles.chartCard}>
                <h3 style={styles.chartTitle}>Emotion Distribution</h3>
                <ResponsiveContainer width="100%" height={250}>
                  <PieChart>
                    <Pie
                      data={dashboardData.emotion_stats}
                      cx="50%"
                      cy="50%"
                      outerRadius={80}
                      fill="#8884d8"
                      dataKey="count"
                      label={({emotion, count}) => `${emotion}: ${count}`}
                    >
                      {dashboardData.emotion_stats.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              </div>

              {/* Recent Users */}
              <div style={styles.chartCard}>
                <h3 style={styles.chartTitle}>Recent Users</h3>
                <div style={styles.usersList}>
                  {dashboardData.recent_users.slice(0, 5).map((user) => (
                    <div key={user.id} style={styles.userItem}>
                      <div style={styles.userInfo}>
                        <div style={styles.userName}>{user.fullname}</div>
                        <div style={styles.userEmail}>{user.email}</div>
                      </div>
                      <div style={styles.userDate}>
                        {new Date(user.created_at).toLocaleDateString()}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Users Tab */}
        {activeTab === "users" && (
          <div style={styles.tableContainer}>
            <div style={styles.tableHeader}>
              <h2>User Management</h2>
              <div style={styles.headerButtons}>
                <button 
                  style={styles.addUserBtn} 
                  onClick={() => setShowAddUserForm(!showAddUserForm)}
                >
                  ➕ Add User
                </button>
                <button style={styles.refreshBtn} onClick={fetchUsers}>
                  🔄 Refresh
                </button>
                <button 
                  style={styles.debugBtn} 
                  onClick={toggleMaskLogic}
                >
                  🔧 Toggle Mask Logic
                </button>
              </div>
            </div>

            {/* Add User Form */}
            {showAddUserForm && (
              <div style={styles.addUserForm}>
                <h3 style={styles.formTitle}>Create New User</h3>
                <form onSubmit={createUser}>
                  <div style={styles.formGroup}>
                    <label style={styles.formLabel}>Full Name:</label>
                    <input
                      type="text"
                      style={styles.formInput}
                      value={newUser.fullname}
                      onChange={(e) => setNewUser({...newUser, fullname: e.target.value})}
                      placeholder="Enter full name"
                      required
                    />
                  </div>
                  <div style={styles.formGroup}>
                    <label style={styles.formLabel}>Email:</label>
                    <input
                      type="email"
                      style={styles.formInput}
                      value={newUser.email}
                      onChange={(e) => setNewUser({...newUser, email: e.target.value})}
                      placeholder="Enter email address"
                      required
                    />
                  </div>
                  <div style={styles.formGroup}>
                    <label style={styles.formLabel}>Password:</label>
                    <input
                      type="password"
                      style={styles.formInput}
                      value={newUser.password}
                      onChange={(e) => setNewUser({...newUser, password: e.target.value})}
                      placeholder="Enter password"
                      required
                    />
                    <div style={styles.passwordHint}>
                      <small>8-16 chars, uppercase, lowercase, number, special char</small>
                    </div>
                  </div>
                  <div style={styles.formGroup}>
                    <label style={styles.formLabel}>Role:</label>
                    <select
                      style={styles.formSelect}
                      value={newUser.role}
                      onChange={(e) => setNewUser({...newUser, role: e.target.value})}
                    >
                      <option value="user">User</option>
                      <option value="admin">Admin</option>
                    </select>
                  </div>
                  <div style={styles.formButtons}>
                    <button type="submit" style={styles.createBtn}>
                      Create User
                    </button>
                    <button 
                      type="button" 
                      style={styles.cancelBtn}
                      onClick={() => {
                        setShowAddUserForm(false);
                        setNewUser({ fullname: "", email: "", password: "", role: "user" });
                      }}
                    >
                      Cancel
                    </button>
                  </div>
                </form>
              </div>
            )}
            <div style={styles.table}>
              <div style={styles.tableHeaderRow}>
                <div style={styles.tableCell}>ID</div>
                <div style={styles.tableCell}>Name</div>
                <div style={styles.tableCell}>Email</div>
                <div style={styles.tableCell}>Role</div>
                <div style={styles.tableCell}>Created</div>
                <div style={styles.tableCell}>Actions</div>
              </div>
              {users.map((user) => (
                <div key={user.id} style={styles.tableRow}>
                  <div style={styles.tableCell}>{user.id}</div>
                  <div style={styles.tableCell}>{user.fullname}</div>
                  <div style={styles.tableCell}>{user.email}</div>
                  <div style={styles.tableCell}>
                    <span style={{
                      ...styles.roleBadge,
                      backgroundColor: user.role === 'admin' ? '#FF9800' : '#4CAF50'
                    }}>
                      {user.role}
                    </span>
                  </div>
                  <div style={styles.tableCell}>
                    {new Date(user.created_at).toLocaleDateString()}
                  </div>
                  <div style={styles.tableCell}>
                    {user.role !== 'admin' && (
                      <button
                        style={styles.deleteBtn}
                        onClick={() => deleteUser(user.id)}
                      >
                        🗑️ Delete
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Emotions Tab */}
        {activeTab === "emotions" && (
          <div style={styles.tableContainer}>
            <div style={styles.tableHeader}>
              <h2>Emotion Records</h2>
              <button style={styles.refreshBtn} onClick={fetchEmotions}>
                🔄 Refresh
              </button>
            </div>
            <div style={styles.table}>
              <div style={styles.tableHeaderRow}>
                <div style={styles.tableCell}>ID</div>
                <div style={styles.tableCell}>User</div>
                <div style={styles.tableCell}>Email</div>
                <div style={styles.tableCell}>Emotion</div>
                <div style={styles.tableCell}>Timestamp</div>
                <div style={styles.tableCell}>Actions</div>
              </div>
              {emotions.map((emotion) => (
                <div key={emotion.id} style={styles.tableRow}>
                  <div style={styles.tableCell}>{emotion.id}</div>
                  <div style={styles.tableCell}>{emotion.fullname}</div>
                  <div style={styles.tableCell}>{emotion.email}</div>
                  <div style={styles.tableCell}>
                    <span style={{
                      ...styles.emotionBadge,
                      backgroundColor: emotion.emotion === 'Happy' ? '#4CAF50' : '#FF6B6B'
                    }}>
                      {emotion.emotion === 'Happy' ? '😊' : '😢'} {emotion.emotion}
                    </span>
                  </div>
                  <div style={styles.tableCell}>
                    {new Date(emotion.timestamp).toLocaleString()}
                  </div>
                  <div style={styles.tableCell}>
                    <button
                      style={styles.deleteBtn}
                      onClick={() => deleteEmotion(emotion.id)}
                    >
                      🗑️ Delete
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Analytics Tab */}
        {activeTab === "analytics" && stats && (
          <div style={styles.analyticsGrid}>
            {/* Monthly Users Chart */}
            <div style={styles.chartCard}>
              <h3 style={styles.chartTitle}>Monthly User Registrations</h3>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={stats.monthly_users.reverse()}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="month" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Bar dataKey="count" fill="#4CAF50" />
                </BarChart>
              </ResponsiveContainer>
            </div>

            {/* Daily Activity Chart */}
            <div style={styles.chartCard}>
              <h3 style={styles.chartTitle}>Daily Activity (Last 30 Days)</h3>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={stats.daily_activity.reverse()}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Line type="monotone" dataKey="count" stroke="#2196F3" strokeWidth={2} />
                </LineChart>
              </ResponsiveContainer>
            </div>

            {/* Top Users */}
            <div style={styles.chartCard}>
              <h3 style={styles.chartTitle}>Most Active Users</h3>
              <div style={styles.topUsersList}>
                {stats.top_users.slice(0, 10).map((user, index) => (
                  <div key={index} style={styles.topUserItem}>
                    <div style={styles.topUserRank}>#{index + 1}</div>
                    <div style={styles.topUserInfo}>
                      <div style={styles.topUserName}>{user.fullname}</div>
                      <div style={styles.topUserEmail}>{user.email}</div>
                    </div>
                    <div style={styles.topUserCount}>{user.emotion_count} emotions</div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
};

// Styles
const styles = {
  container: {
    minHeight: "100vh",
    backgroundColor: "#f5f7fa",
    fontFamily: "'Segoe UI', Tahoma, Geneva, Verdana, sans-serif",
  },
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
  header: {
    backgroundColor: "#fff",
    padding: "20px 30px",
    boxShadow: "0 2px 4px rgba(0,0,0,0.1)",
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
  },
  headerLeft: {
    display: "flex",
    flexDirection: "column",
  },
  title: {
    margin: 0,
    color: "#333",
    fontSize: "1.8rem",
    fontWeight: "600",
  },
  subtitle: {
    margin: "5px 0 0 0",
    color: "#666",
    fontSize: "0.9rem",
  },
  headerRight: {
    display: "flex",
    gap: "10px",
  },
  userDashboardBtn: {
    backgroundColor: "#2196F3",
    color: "white",
    border: "none",
    padding: "10px 15px",
    borderRadius: "8px",
    cursor: "pointer",
    fontSize: "0.9rem",
    fontWeight: "500",
  },
  logoutBtn: {
    backgroundColor: "#f44336",
    color: "white",
    border: "none",
    padding: "10px 15px",
    borderRadius: "8px",
    cursor: "pointer",
    fontSize: "0.9rem",
    fontWeight: "500",
  },
  tabNav: {
    backgroundColor: "#fff",
    padding: "0 30px",
    display: "flex",
    borderBottom: "1px solid #e0e0e0",
  },
  tabButton: {
    backgroundColor: "transparent",
    border: "none",
    padding: "15px 20px",
    cursor: "pointer",
    fontSize: "0.95rem",
    fontWeight: "500",
    color: "#666",
    borderBottom: "3px solid transparent",
    transition: "all 0.3s ease",
  },
  activeTab: {
    color: "#2196F3",
    borderBottomColor: "#2196F3",
  },
  content: {
    padding: "30px",
  },
  overviewGrid: {
    display: "flex",
    flexDirection: "column",
    gap: "30px",
  },
  statsGrid: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fit, minmax(250px, 1fr))",
    gap: "20px",
  },
  statCard: {
    backgroundColor: "#fff",
    padding: "25px",
    borderRadius: "12px",
    boxShadow: "0 2px 8px rgba(0,0,0,0.1)",
    display: "flex",
    alignItems: "center",
    gap: "20px",
  },
  statIcon: {
    fontSize: "2.5rem",
  },
  statContent: {
    display: "flex",
    flexDirection: "column",
  },
  statNumber: {
    fontSize: "2rem",
    fontWeight: "bold",
    color: "#333",
  },
  statLabel: {
    fontSize: "0.9rem",
    color: "#666",
    marginTop: "5px",
  },
  chartsGrid: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fit, minmax(400px, 1fr))",
    gap: "20px",
  },
  chartCard: {
    backgroundColor: "#fff",
    padding: "25px",
    borderRadius: "12px",
    boxShadow: "0 2px 8px rgba(0,0,0,0.1)",
  },
  chartTitle: {
    margin: "0 0 20px 0",
    color: "#333",
    fontSize: "1.2rem",
    fontWeight: "600",
  },
  usersList: {
    display: "flex",
    flexDirection: "column",
    gap: "10px",
  },
  userItem: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    padding: "10px",
    backgroundColor: "#f8f9fa",
    borderRadius: "8px",
  },
  userInfo: {
    display: "flex",
    flexDirection: "column",
  },
  userName: {
    fontWeight: "500",
    color: "#333",
  },
  userEmail: {
    fontSize: "0.85rem",
    color: "#666",
  },
  userDate: {
    fontSize: "0.85rem",
    color: "#999",
  },
  tableContainer: {
    backgroundColor: "#fff",
    borderRadius: "12px",
    boxShadow: "0 2px 8px rgba(0,0,0,0.1)",
    overflow: "hidden",
  },
  tableHeader: {
    padding: "20px 25px",
    borderBottom: "1px solid #e0e0e0",
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
  },
  headerButtons: {
    display: "flex",
    gap: "10px",
  },
  addUserBtn: {
    backgroundColor: "#2196F3",
    color: "white",
    border: "none",
    padding: "8px 15px",
    borderRadius: "6px",
    cursor: "pointer",
    fontSize: "0.9rem",
    fontWeight: "500",
  },
  refreshBtn: {
    backgroundColor: "#4CAF50",
    color: "white",
    border: "none",
    padding: "8px 15px",
    borderRadius: "6px",
    cursor: "pointer",
    fontSize: "0.9rem",
  },
  debugBtn: {
    backgroundColor: "#FF9800",
    color: "white",
    border: "none",
    padding: "8px 15px",
    borderRadius: "6px",
    cursor: "pointer",
    fontSize: "0.9rem",
    fontWeight: "500",
  },
  addUserForm: {
    padding: "25px",
    backgroundColor: "#f8f9fa",
    borderBottom: "1px solid #e0e0e0",
  },
  formTitle: {
    margin: "0 0 20px 0",
    color: "#333",
    fontSize: "1.1rem",
    fontWeight: "600",
  },
  formGroup: {
    marginBottom: "15px",
  },
  formLabel: {
    display: "block",
    marginBottom: "5px",
    color: "#333",
    fontSize: "0.9rem",
    fontWeight: "500",
  },
  formInput: {
    width: "100%",
    padding: "10px",
    border: "1px solid #ddd",
    borderRadius: "6px",
    fontSize: "0.9rem",
    boxSizing: "border-box",
  },
  formSelect: {
    width: "100%",
    padding: "10px",
    border: "1px solid #ddd",
    borderRadius: "6px",
    fontSize: "0.9rem",
    boxSizing: "border-box",
    backgroundColor: "white",
  },
  formButtons: {
    display: "flex",
    gap: "10px",
    marginTop: "20px",
  },
  createBtn: {
    backgroundColor: "#4CAF50",
    color: "white",
    border: "none",
    padding: "10px 20px",
    borderRadius: "6px",
    cursor: "pointer",
    fontSize: "0.9rem",
    fontWeight: "500",
  },
  cancelBtn: {
    backgroundColor: "#999",
    color: "white",
    border: "none",
    padding: "10px 20px",
    borderRadius: "6px",
    cursor: "pointer",
    fontSize: "0.9rem",
    fontWeight: "500",
  },
  table: {
    display: "flex",
    flexDirection: "column",
  },
  tableHeaderRow: {
    display: "grid",
    gridTemplateColumns: "80px 1fr 1fr 100px 120px 100px",
    gap: "15px",
    padding: "15px 25px",
    backgroundColor: "#f8f9fa",
    fontWeight: "600",
    color: "#333",
    borderBottom: "1px solid #e0e0e0",
  },
  tableRow: {
    display: "grid",
    gridTemplateColumns: "80px 1fr 1fr 100px 120px 100px",
    gap: "15px",
    padding: "15px 25px",
    borderBottom: "1px solid #f0f0f0",
    alignItems: "center",
  },
  tableCell: {
    fontSize: "0.9rem",
    color: "#333",
  },
  roleBadge: {
    padding: "4px 8px",
    borderRadius: "12px",
    color: "white",
    fontSize: "0.8rem",
    fontWeight: "500",
  },
  emotionBadge: {
    padding: "4px 8px",
    borderRadius: "12px",
    color: "white",
    fontSize: "0.8rem",
    fontWeight: "500",
  },
  deleteBtn: {
    backgroundColor: "#f44336",
    color: "white",
    border: "none",
    padding: "6px 10px",
    borderRadius: "6px",
    cursor: "pointer",
    fontSize: "0.8rem",
  },
  analyticsGrid: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fit, minmax(400px, 1fr))",
    gap: "20px",
  },
  topUsersList: {
    display: "flex",
    flexDirection: "column",
    gap: "10px",
  },
  topUserItem: {
    display: "flex",
    alignItems: "center",
    gap: "15px",
    padding: "10px",
    backgroundColor: "#f8f9fa",
    borderRadius: "8px",
  },
  topUserRank: {
    fontSize: "1.2rem",
    fontWeight: "bold",
    color: "#2196F3",
    minWidth: "30px",
  },
  topUserInfo: {
    flex: 1,
    display: "flex",
    flexDirection: "column",
  },
  topUserName: {
    fontWeight: "500",
    color: "#333",
  },
  topUserEmail: {
    fontSize: "0.85rem",
    color: "#666",
  },
  topUserCount: {
    fontSize: "0.9rem",
    color: "#4CAF50",
    fontWeight: "500",
  },
  passwordHint: {
    marginTop: "5px",
    color: "#666",
    fontSize: "0.75rem",
    fontStyle: "italic",
  },
};

export default AdminDashboard;
