import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { productService, orderService } from '../services/apiService';
import { useAuth } from '../contexts/AuthContext';

const ProductDetailPage = () => {
  const { productId } = useParams();
  const [product, setProduct] = useState(null);
  const [loadingProduct, setLoadingProduct] = useState(true);
  const [productError, setProductError] = useState(null);

  const [bidQuantity, setBidQuantity] = useState('');
  const [bidPrice, setBidPrice] = useState('');
  const [loadingBid, setLoadingBid] = useState(false);
  const [bidError, setBidError] = useState(null);
  const [bidSuccess, setBidSuccess] = useState('');

  const { token, user } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    if (!token) {
      setProductError("Please log in to view product details and bid.");
      setLoadingProduct(false);
      return;
    }
    setLoadingProduct(true);
    productService.getProductById(productId)
      .then(data => {
        setProduct(data);
        setLoadingProduct(false);
      })
      .catch(err => {
        setProductError(err.msg || err.message || 'Failed to fetch product details.');
        setLoadingProduct(false);
      });
  }, [productId, token]);

  const handleBidSubmit = async (e) => {
    e.preventDefault();
    setBidError(null);
    setBidSuccess('');

    if (!bidQuantity || !bidPrice) {
      setBidError('Please enter both quantity and your bid price.');
      return;
    }
    if (isNaN(parseFloat(bidQuantity)) || parseFloat(bidQuantity) <= 0) {
      setBidError('Quantity must be a positive number.');
      return;
    }
    if (isNaN(parseFloat(bidPrice)) || parseFloat(bidPrice) <= 0) {
      setBidError('Bid price must be a positive number.');
      return;
    }
    if (product && parseFloat(bidQuantity) > parseFloat(product.quantity_kg)) {
        setBidError(`Your bid quantity cannot exceed the available quantity of ${product.quantity_kg} kg.`);
        return;
    }
    // Check if the user is trying to bid on their own product
    if (product && product.seller_id === user?.id) {
        setBidError("You cannot bid on your own product listing.");
        return;
    }


    setLoadingBid(true);
    const bidData = {
      order_type: 'buy',
      hydrogen_product_id: parseInt(productId),
      quantity_kg: bidQuantity,
      price_per_kg: bidPrice,
      // Add other criteria fields if necessary for your backend logic, e.g., status: 'pending'
    };

    try {
      const response = await orderService.createOrder(bidData);
      setBidSuccess(`Bid placed successfully! Order ID: ${response.order.id}. ${response.trades_made?.length > 0 ? response.trades_made.length + ' trade(s) made immediately!' : 'Your order is pending.'}`);
      setBidQuantity('');
      setBidPrice('');
      // Optionally, refresh product data if quantity changed due to immediate match
      // productService.getProductById(productId).then(setProduct);
    } catch (err) {
      setBidError(err.msg || err.message || 'Failed to place bid.');
    } finally {
      setLoadingBid(false);
    }
  };

  if (loadingProduct) return <p className="loading-message">Loading product details...</p>;
  if (productError) return <p className="error-message">{productError}</p>;
  if (!product) return <p className="text-center">Product not found.</p>;

  return (
    <div className="page-container product-detail-container">
      <h2>{product.name || `Product ID: ${product.id}`}</h2>
      <div className="product-info">
        <p><strong>Seller:</strong> {product.seller_username || 'N/A'}</p>
        <p><strong>Price:</strong> ${product.price_per_kg} / kg (Asking Price)</p>
        <p><strong>Available Quantity:</strong> {product.quantity_kg} kg</p>
        <p><strong>Location:</strong> {product.location_region}</p>
        <p><strong>Production Method:</strong> {product.production_method}</p>
        {product.purity_percentage && <p><strong>Purity:</strong> {product.purity_percentage}%</p>}
        {product.ghg_intensity_kgco2e_per_kgh2 && <p><strong>GHG Intensity:</strong> {product.ghg_intensity_kgco2e_per_kgh2} kgCO2e/kgH2</p>}
        {product.feedstock && <p><strong>Feedstock:</strong> {product.feedstock}</p>}
        {product.energy_source && <p><strong>Energy Source:</strong> {product.energy_source}</p>}
        {product.available_from_date && <p><strong>Available From:</strong> {new Date(product.available_from_date).toLocaleDateString()}</p>}
        {product.delivery_terms && <p><strong>Delivery Terms:</strong> {product.delivery_terms}</p>}
        <p><em>Listed on: {new Date(product.listing_timestamp).toLocaleString()}</em></p>
      </div>

      {product.seller_id !== user?.id && product.status === 'active' && parseFloat(product.quantity_kg) > 0 && (
        <div className="bidding-form-container">
          <h3>Place Your Bid</h3>
          <form onSubmit={handleBidSubmit} className="form-container">
            <div className="form-group">
              <label htmlFor="bidQuantity">Quantity (kg):</label>
              <input
                type="number"
                id="bidQuantity"
                value={bidQuantity}
                onChange={(e) => setBidQuantity(e.target.value)}
                required
                step="any"
                min="0.01" // Example: minimum bid quantity
                max={product.quantity_kg} // Cannot bid for more than available
              />
            </div>
            <div className="form-group">
              <label htmlFor="bidPrice">Your Bid Price (USD per kg):</label>
              <input
                type="number"
                id="bidPrice"
                value={bidPrice}
                onChange={(e) => setBidPrice(e.target.value)}
                required
                step="any"
                min="0.01" // Example: minimum bid price
              />
            </div>
            {loadingBid && <p className="loading-message">Placing bid...</p>}
            {bidError && <p className="error-message">{bidError}</p>}
            {bidSuccess && <p className="success-message">{bidSuccess}</p>}
            <button type="submit" disabled={loadingBid} className="cta-button">
              Submit Bid
            </button>
          </form>
        </div>
      )}
      {product.seller_id === user?.id && (
        <p className="info-message">This is your product listing. You cannot bid on it.</p>
      )}
      {product.status !== 'active' && (
         <p className="info-message">This product is no longer active ({product.status}). Bidding is closed.</p>
      )}
       {parseFloat(product.quantity_kg) <= 0 && product.status === 'active' && (
         <p className="info-message">This product is currently out of stock. Bidding is closed.</p>
      )}


      <style jsx>{`
        .product-detail-container h2 {
          text-align: center;
          margin-bottom: 1rem;
          color: #004d40;
        }
        .product-info {
          background-color: #f9f9f9;
          padding: 1.5rem;
          border-radius: 8px;
          margin-bottom: 2rem;
          border: 1px solid #e0e0e0;
        }
        .product-info p {
          margin-bottom: 0.6rem;
          font-size: 1.05rem;
        }
        .product-info strong {
          color: #333;
        }
        .product-info em {
          font-size: 0.9rem;
          color: #777;
        }
        .bidding-form-container {
          background-color: #fff;
          padding: 1.5rem;
          border-radius: 8px;
          box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        .bidding-form-container h3 {
          text-align: center;
          color: #00695c; /* Medium Green */
          margin-bottom: 1.5rem;
        }
        .form-group { /* Copied from CreateProductPage for consistency, can be global */
          margin-bottom: 1rem;
        }
        .form-group label {
          display: block;
          margin-bottom: 0.3rem;
          font-weight: 600;
        }
        .form-group input {
          width: 100%;
          padding: 0.6rem;
          border: 1px solid #ccc;
          border-radius: 4px;
          font-size: 1rem;
        }
        .cta-button {
            display: block;
            width: 100%;
            background-color: #00796b;
            color: #fff;
            padding: 0.8rem;
            text-decoration: none;
            font-size: 1.1em;
            border-radius: 5px;
            transition: background-color 0.3s ease;
            border: none;
            cursor: pointer;
            margin-top: 1rem;
        }
        .cta-button:hover {
            background-color: #004d40;
        }
        .success-message { color: green; text-align: center; margin-top: 1rem; }
        .error-message { color: red; text-align: center; margin-top: 1rem; }
        .loading-message { color: #00796b; text-align: center; margin-top: 1rem; }
        .info-message { color: #555; text-align: center; margin-top: 1rem; font-style: italic; }
      `}</style>
    </div>
  );
};

export default ProductDetailPage;
