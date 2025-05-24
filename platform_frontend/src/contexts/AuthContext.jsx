import React, { createContext, useState, useContext, useEffect } from 'react';
import { authService } from '../services/apiService'; // Assuming login/register functions are here

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [token, setToken] = useState(localStorage.getItem('authToken'));
  const [user, setUser] = useState(JSON.parse(localStorage.getItem('authUser'))); // Store user details
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (token) {
      localStorage.setItem('authToken', token);
      // Potentially fetch user profile here if not storing user object or to validate token
    } else {
      localStorage.removeItem('authToken');
      localStorage.removeItem('authUser');
    }
  }, [token]);

  const login = async (credentials) => {
    setLoading(true);
    setError(null);
    try {
      const data = await authService.login(credentials); // { access_token, user }
      setToken(data.access_token);
      setUser(data.user); // Set user data from login response
      localStorage.setItem('authToken', data.access_token);
      localStorage.setItem('authUser', JSON.stringify(data.user));
      setLoading(false);
      return true; // Indicate success
    } catch (err) {
      setError(err.msg || 'Login failed. Please check your credentials.');
      setLoading(false);
      return false; // Indicate failure
    }
  };

  const register = async (userData) => {
    setLoading(true);
    setError(null);
    try {
      const data = await authService.register(userData); // { access_token, user }
      setToken(data.access_token);
      setUser(data.user);
      localStorage.setItem('authToken', data.access_token);
      localStorage.setItem('authUser', JSON.stringify(data.user));
      setLoading(false);
      return true;
    } catch (err) {
      setError(err.msg || 'Registration failed.');
      setLoading(false);
      return false;
    }
  };

  const logout = () => {
    setToken(null);
    setUser(null);
    localStorage.removeItem('authToken');
    localStorage.removeItem('authUser');
    // apiClient.defaults.headers.common['Authorization'] = ''; // Clear from axios instance if needed
  };

  return (
    <AuthContext.Provider value={{ token, user, login, logout, register, loading, error, setError, setUser }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);
