import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import LoginPage from './pages/LoginPage';
import DashboardPage from './pages/DashboardPage';
import CreateProductPage from './pages/CreateProductPage';
import ProductListPage from './pages/ProductListPage'; // Import new page
import ProductDetailPage from './pages/ProductDetailPage'; // Import new page
import { AuthProvider, useAuth } from './contexts/AuthContext';
import Navbar from './components/Navbar';

// ProtectedRoute component to guard routes
const ProtectedRoute = ({ children }) => {
  const { token } = useAuth();
  if (!token) {
    return <Navigate to="/login" replace />;
  }
  return children;
};

function App() {
  return (
    <Router>
      <AuthProvider>
        <div className="App">
          <Navbar />
          <Routes>
            <Route path="/login" element={<LoginPage />} />
            <Route 
              path="/dashboard" 
              element={
                <ProtectedRoute>
                  <DashboardPage />
                </ProtectedRoute>
              } 
            />
            <Route 
              path="/products/new" 
              element={
                <ProtectedRoute>
                  <CreateProductPage />
                </ProtectedRoute>
              } 
            />
            <Route 
              path="/products" 
              element={
                <ProtectedRoute> {/* Or make public if desired */}
                  <ProductListPage />
                </ProtectedRoute>
              } 
            />
            <Route 
              path="/products/:productId" 
              element={
                <ProtectedRoute> {/* Or make public if desired */}
                  <ProductDetailPage />
                </ProtectedRoute>
              } 
            />
            <Route path="/" element={<Navigate to={useAuth.token ? "/dashboard" : "/login"} />} />
          </Routes>
        </div>
      </AuthProvider>
    </Router>
  );
}

export default App;
