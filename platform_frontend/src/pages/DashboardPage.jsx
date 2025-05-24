import React, { useEffect, useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { userService, orderService } from '../services/apiService';

// UserProfile Component
const UserProfile = () => {
  const { user: authUser, token, setUser: setAuthUser } = useAuth(); // Get user from AuthContext
  const [profile, setProfile] = useState(authUser); // Initialize with AuthContext user
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    // Fetch profile only if not already populated from login, or to refresh
    if (token && !authUser?.fetched_at_dashboard) { // Add a flag to avoid re-fetching if already done
      setLoading(true);
      setError(null);
      userService.getProfile()
        .then(data => {
          setProfile({ ...data.user, fetched_at_dashboard: true });
          setAuthUser({ ...data.user, fetched_at_dashboard: true }); // Update context user as well
          localStorage.setItem('authUser', JSON.stringify({ ...data.user, fetched_at_dashboard: true }));
          setLoading(false);
        })
        .catch(err => {
          setError(err.msg || 'Failed to fetch profile.');
          setLoading(false);
        });
    } else if (authUser) {
        setProfile(authUser); // Use user data from context if already fetched
    }
  }, [token, authUser, setAuthUser]);

  if (loading) return <p className="loading-message">Loading profile...</p>;
  if (error) return <p className="error-message">{error}</p>;
  if (!profile) return <p>No profile data available.</p>;

  return (
    <div className="dashboard-section">
      <h2>User Profile</h2>
      <p><strong>Username:</strong> {profile.username}</p>
      <p><strong>Email:</strong> {profile.email}</p>
      <p><strong>Organization:</strong> {profile.organization_name || 'N/A'}</p>
      <p><strong>Roles:</strong> {profile.roles?.join(', ') || 'user'}</p>
      {/* <p><strong>Joined:</strong> {new Date(profile.created_at).toLocaleDateString()}</p> */}
    </div>
  );
};

// UserOrders Component
const UserOrders = () => {
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const { token } = useAuth();

  useEffect(() => {
    if (token) {
      setLoading(true);
      setError(null);
      orderService.getUserOrders()
        .then(data => {
          setOrders(data);
          setLoading(false);
        })
        .catch(err => {
          setError(err.msg || 'Failed to fetch orders.');
          setLoading(false);
        });
    }
  }, [token]);

  if (loading) return <p className="loading-message">Loading orders...</p>;
  if (error) return <p className="error-message">{error}</p>;
  if (!orders || orders.length === 0) return <p>You have no orders.</p>;

  return (
    <div className="dashboard-section">
      <h2>Your Orders</h2>
      <table className="orders-table">
        <thead>
          <tr>
            <th>ID</th>
            <th>Type</th>
            <th>Product ID</th>
            <th>Quantity (kg)</th>
            <th>Price/kg</th>
            <th>Status</th>
            <th>Created</th>
          </tr>
        </thead>
        <tbody>
          {orders.map(order => (
            <tr key={order.id}>
              <td>{order.id}</td>
              <td>{order.order_type}</td>
              <td>{order.hydrogen_product_id || 'N/A (Criteria Buy)'}</td>
              <td>{order.quantity_kg}</td>
              <td>${order.price_per_kg}</td>
              <td>{order.status}</td>
              <td>{new Date(order.created_timestamp).toLocaleDateString()}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};


// Main DashboardPage Component
const DashboardPage = () => {
  return (
    <div className="page-container">
      <h1>User Dashboard</h1>
      <UserProfile />
      <UserOrders />
      {/* Future sections like "Available Products" or "Create Order" could go here */}
    </div>
  );
};

export default DashboardPage;
