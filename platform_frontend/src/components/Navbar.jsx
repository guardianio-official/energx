import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

const Navbar = () => {
  const { token, user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <nav>
      <h1>Green H2 Exchange</h1>
      <ul>
        {token ? (
          <>
            <li><span>Welcome, {user?.username || 'User'}!</span></li>
            <li><Link to="/dashboard">Dashboard</Link></li>
            <li><Link to="/products">Browse Products</Link></li> {/* Added link */}
            <li><Link to="/products/new">List New Product</Link></li>
            {/* Add other links like My Products, My Orders etc. later */}
            <li>
              <button onClick={handleLogout}>Logout</button>
            </li>
          </>
        ) : (
          <li>
            <Link to="/login">Login</Link>
          </li>
          // Optionally, add a Register link here if a separate register page exists
          // <li><Link to="/register">Register</Link></li> 
        )}
      </ul>
    </nav>
  );
};

export default Navbar;
