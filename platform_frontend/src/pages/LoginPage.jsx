import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

const LoginPage = () => {
  const [identifier, setIdentifier] = useState(''); // Can be username or email
  const [password, setPassword] = useState('');
  const { login, loading, error, setError } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null); // Clear previous errors
    if (!identifier || !password) {
      setError("Username/Email and Password are required.");
      return;
    }
    const success = await login({ identifier, password });
    if (success) {
      navigate('/dashboard');
    }
  };

  return (
    <div className="page-container">
      <h2>Login</h2>
      <form onSubmit={handleSubmit} className="form-container">
        <div>
          <label htmlFor="identifier">Username or Email:</label>
          <input
            type="text"
            id="identifier"
            value={identifier}
            onChange={(e) => setIdentifier(e.target.value)}
            required
          />
        </div>
        <div>
          <label htmlFor="password">Password:</label>
          <input
            type="password"
            id="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
        </div>
        {loading && <p className="loading-message">Logging in...</p>}
        {error && <p className="error-message">{error}</p>}
        <button type="submit" disabled={loading}>
          Login
        </button>
      </form>
      {/* Placeholder for registration link if needed later
      <p className="text-center mt-1">
        Don't have an account? <Link to="/register">Register here</Link>
      </p>
      */}
    </div>
  );
};

export default LoginPage;
