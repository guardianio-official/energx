import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { productService } from '../services/apiService';
import { useAuth } from '../contexts/AuthContext'; // To ensure user is logged in if required

const ProductListPage = () => {
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const { token } = useAuth(); // For authenticated access

  useEffect(() => {
    if (!token) { // For POC, ensuring authenticated access
        setError("Please log in to view products.");
        setLoading(false);
        return;
    }
    setLoading(true);
    productService.getAllProducts()
      .then(data => {
        setProducts(data);
        setLoading(false);
      })
      .catch(err => {
        setError(err.msg || err.message || 'Failed to fetch products.');
        setLoading(false);
      });
  }, [token]);

  if (loading) return <p className="loading-message">Loading available products...</p>;
  if (error) return <p className="error-message">{error}</p>;
  if (!products.length) return <p className="text-center">No hydrogen products currently available.</p>;

  return (
    <div className="page-container product-list-container">
      <h2>Available Green Hydrogen Products</h2>
      <div className="products-grid">
        {products.map(product => (
          <div key={product.id} className="product-card">
            <h3>Product ID: {product.id}</h3> {/* Using ID as name if no name field */}
            <p><strong>Seller:</strong> {product.seller_username || 'N/A'}</p>
            <p><strong>Price:</strong> ${product.price_per_kg} / kg</p>
            <p><strong>Available Quantity:</strong> {product.quantity_kg} kg</p>
            <p><strong>Location:</strong> {product.location_region}</p>
            <p><strong>Production Method:</strong> {product.production_method}</p>
            <Link to={`/products/${product.id}`} className="cta-button product-card-button">
              View Details & Bid
            </Link>
          </div>
        ))}
      </div>
      <style jsx>{`
        .product-list-container h2 {
          text-align: center;
          margin-bottom: 2rem;
        }
        .products-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
          gap: 1.5rem;
        }
        .product-card {
          background-color: #fff;
          border: 1px solid #e0e0e0;
          border-radius: 8px;
          padding: 1.5rem;
          box-shadow: 0 2px 5px rgba(0,0,0,0.05);
          display: flex;
          flex-direction: column;
        }
        .product-card h3 {
          font-size: 1.2rem;
          color: #004d40; /* Dark Green */
          margin-bottom: 0.75rem;
        }
        .product-card p {
          font-size: 0.95rem;
          margin-bottom: 0.5rem;
          color: #333;
        }
        .product-card strong {
          color: #555;
        }
        .product-card-button {
          margin-top: auto; /* Pushes button to the bottom of the card */
          background-color: #00796b; /* Medium Green */
          color: white;
          text-align: center;
          padding: 0.6rem 1rem;
          border-radius: 4px;
          text-decoration: none;
          transition: background-color 0.3s ease;
          display: block; /* Make it block to take full width if needed, or keep inline-block */
        }
        .product-card-button:hover {
          background-color: #004d40; /* Darker Green */
        }
      `}</style>
    </div>
  );
};

export default ProductListPage;
