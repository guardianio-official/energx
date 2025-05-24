import axios from 'axios';

// Define the base URL for the backend API
// In development, this might be 'http://localhost:5000/api' (or whatever port your Flask backend runs on)
// In production, this would be your actual API URL.
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api'; // Vite uses import.meta.env

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Interceptor to add the JWT token to requests
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('authToken');
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Authentication Service
export const authService = {
  login: async (credentials) => {
    try {
      const response = await apiClient.post('/auth/login', credentials);
      return response.data; // Should contain { access_token, user }
    } catch (error) {
      console.error('Login error:', error.response?.data || error.message);
      throw error.response?.data || error;
    }
  },
  register: async (userData) => {
    try {
      const response = await apiClient.post('/auth/register', userData);
      return response.data; // Should contain { access_token, user }
    } catch (error) {
      console.error('Registration error:', error.response?.data || error.message);
      throw error.response?.data || error;
    }
  },
  // refreshToken: async () => { ... } // If refresh tokens are implemented
};

// User Service
export const userService = {
  getProfile: async () => {
    try {
      const response = await apiClient.get('/user/profile');
      return response.data; // Should contain { user }
    } catch (error) {
      console.error('Get profile error:', error.response?.data || error.message);
      throw error.response?.data || error;
    }
  },
};

// Order Service
export const orderService = {
  getUserOrders: async () => {
    try {
      const response = await apiClient.get('/orders'); // Backend route is /api/orders
      return response.data; // Should be an array of orders
    } catch (error) {
      console.error('Get user orders error:', error.response?.data || error.message);
      throw error.response?.data || error;
    }
  },
  createOrder: async (orderData) => {
    try {
      const response = await apiClient.post('/orders', orderData);
      return response.data; // Should contain { order, trades_made }
    } catch (error) {
      console.error('Create order error:', error.response?.data || error.message);
      throw error.response?.data || error;
    }
  },
  // getOrderDetails: async (orderId) => { ... }
};

// Product Service (Example - can be expanded)
export const productService = {
  getAllProducts: async () => {
    try {
      const response = await apiClient.get('/products'); // Backend route is /api/products
      return response.data; // Should be an array of products
    } catch (error) {
      console.error('Get all products error:', error.response?.data || error.message);
      throw error.response?.data || error;
    }
  },
  getProductById: async (productId) => {
    try {
      const response = await apiClient.get(`/products/${productId}`);
      return response.data;
    } catch (error) {
      console.error(`Get product by ID ${productId} error:`, error.response?.data || error.message);
      throw error.response?.data || error;
    }
  },
  createProduct: async (productData) => {
    try {
      const response = await apiClient.post('/products', productData);
      return response.data; // Should contain the created product
    } catch (error) {
      console.error('Create product error:', error.response?.data || error.message);
      throw error.response?.data || error;
    }
  },
  // updateProduct: async (productId, productData) => { ... }
  // deleteProduct: async (productId) => { ... }
};


export default apiClient;
