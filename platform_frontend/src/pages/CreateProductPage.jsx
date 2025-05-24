import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { productService } from '../services/apiService'; // Assuming productService is in apiService.js

const CreateProductPage = () => {
  const [formData, setFormData] = useState({
    name: '', // Not in backend model directly, used for user convenience, might map to description or be omitted
    quantity_kg: '',
    price_per_kg: '',
    location_region: '',
    production_method: 'Electrolysis (Solar)', // Default value
    purity_percentage: '',
    delivery_terms: '',
    ghg_intensity_kgco2e_per_kgh2: '',
    feedstock: '',
    energy_source: '', // Added based on model
    available_from_date: '', // Added based on model
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState('');
  const { token } = useAuth(); // For ensuring user is authenticated, token is used by apiService
  const navigate = useNavigate();

  const productionMethods = [
    "Electrolysis (Solar)",
    "Electrolysis (Wind)",
    "Electrolysis (Grid, Renewable Mix)",
    "Electrolysis (Hydro)",
    "SMR with CCS",
    "ATR with CCS",
    "Biomass Gasification with CCS",
    "Other (Specify)",
  ];

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setSuccess('');
    setLoading(true);

    // Basic client-side validation
    if (!formData.quantity_kg || !formData.price_per_kg || !formData.location_region || !formData.production_method) {
      setError('Please fill in all required fields: Quantity, Price, Location, and Production Method.');
      setLoading(false);
      return;
    }
    if (isNaN(parseFloat(formData.quantity_kg)) || isNaN(parseFloat(formData.price_per_kg))) {
      setError('Quantity and Price must be valid numbers.');
      setLoading(false);
      return;
    }
    if (formData.ghg_intensity_kgco2e_per_kgh2 && isNaN(parseFloat(formData.ghg_intensity_kgco2e_per_kgh2))) {
        setError('GHG Intensity must be a valid number if provided.');
        setLoading(false);
        return;
    }
     if (formData.purity_percentage && (isNaN(parseFloat(formData.purity_percentage)) || parseFloat(formData.purity_percentage) > 100 || parseFloat(formData.purity_percentage) < 0) ) {
        setError('Purity must be a valid number between 0 and 100 if provided.');
        setLoading(false);
        return;
    }


    // Prepare payload for the backend (ensure field names match backend model)
    const payload = {
        quantity_kg: formData.quantity_kg,
        price_per_kg: formData.price_per_kg,
        location_region: formData.location_region,
        production_method: formData.production_method,
        purity_percentage: formData.purity_percentage || null, // Send null if empty
        delivery_terms: formData.delivery_terms,
        ghg_intensity_kgco2e_per_kgh2: formData.ghg_intensity_kgco2e_per_kgh2 || null,
        feedstock: formData.feedstock,
        energy_source: formData.energy_source,
        available_from_date: formData.available_from_date || null,
        // 'name' field from form is not directly sent if not in backend model for product creation
        // Seller ID is handled by the backend using the JWT token
    };

    try {
      const response = await productService.createProduct(payload); // Assuming createProduct exists
      setSuccess(`Product "${response.id}" created successfully!`); // Using product ID from response
      setFormData({ // Reset form
        name: '', quantity_kg: '', price_per_kg: '', location_region: '',
        production_method: 'Electrolysis (Solar)', purity_percentage: '', delivery_terms: '',
        ghg_intensity_kgco2e_per_kgh2: '', feedstock: '', energy_source: '', available_from_date: '',
      });
      // Optionally navigate away
      // setTimeout(() => navigate('/dashboard'), 2000); 
    } catch (err) {
      setError(err.msg || err.message || 'Failed to create product. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  if (!token) { // Should be handled by ProtectedRoute, but good as a safeguard
    navigate('/login');
    return <p>Please log in to create a product.</p>;
  }

  return (
    <div className="page-container">
      <h2>List New Hydrogen Product</h2>
      <form onSubmit={handleSubmit} className="form-container create-product-form">
        {/* Name field - for user convenience, not directly in model */}
        {/* <div className="form-group">
          <label htmlFor="name">Product Name/Title (Optional):</label>
          <input
            type="text"
            id="name"
            name="name"
            value={formData.name}
            onChange={handleChange}
          />
        </div> */}
        
        <div className="form-group">
          <label htmlFor="quantity_kg">Quantity (kg) <span className="required-star">*</span></label>
          <input
            type="number"
            id="quantity_kg"
            name="quantity_kg"
            value={formData.quantity_kg}
            onChange={handleChange}
            required
            step="any"
          />
        </div>

        <div className="form-group">
          <label htmlFor="price_per_kg">Price (USD per kg) <span className="required-star">*</span></label>
          <input
            type="number"
            id="price_per_kg"
            name="price_per_kg"
            value={formData.price_per_kg}
            onChange={handleChange}
            required
            step="any"
          />
        </div>

        <div className="form-group">
          <label htmlFor="location_region">Location (Region) <span className="required-star">*</span></label>
          <input
            type="text"
            id="location_region"
            name="location_region"
            value={formData.location_region}
            onChange={handleChange}
            required
          />
        </div>

        <div className="form-group">
          <label htmlFor="production_method">Production Method <span className="required-star">*</span></label>
          <select
            id="production_method"
            name="production_method"
            value={formData.production_method}
            onChange={handleChange}
            required
          >
            {productionMethods.map(method => (
              <option key={method} value={method}>{method}</option>
            ))}
          </select>
        </div>

        <div className="form-group">
          <label htmlFor="purity_percentage">Purity (%):</label>
          <input
            type="number"
            id="purity_percentage"
            name="purity_percentage"
            value={formData.purity_percentage}
            onChange={handleChange}
            step="any"
            min="0"
            max="100"
          />
        </div>
        
        <div className="form-group">
          <label htmlFor="available_from_date">Available From Date:</label>
          <input
            type="date"
            id="available_from_date"
            name="available_from_date"
            value={formData.available_from_date}
            onChange={handleChange}
          />
        </div>

        <div className="form-group">
          <label htmlFor="delivery_terms">Delivery Terms:</label>
          <textarea
            id="delivery_terms"
            name="delivery_terms"
            value={formData.delivery_terms}
            onChange={handleChange}
            rows="3"
          ></textarea>
        </div>

        <div className="form-group">
          <label htmlFor="ghg_intensity_kgco2e_per_kgh2">GHG Intensity (kg CO2e/kg H2) (Optional):</label>
          <input
            type="number"
            id="ghg_intensity_kgco2e_per_kgh2"
            name="ghg_intensity_kgco2e_per_kgh2"
            value={formData.ghg_intensity_kgco2e_per_kgh2}
            onChange={handleChange}
            step="any"
          />
        </div>

        <div className="form-group">
          <label htmlFor="feedstock">Feedstock (Optional):</label>
          <input
            type="text"
            id="feedstock"
            name="feedstock"
            value={formData.feedstock}
            onChange={handleChange}
          />
        </div>

        <div className="form-group">
          <label htmlFor="energy_source">Energy Source (Optional):</label>
          <input
            type="text"
            id="energy_source"
            name="energy_source"
            value={formData.energy_source}
            onChange={handleChange}
          />
        </div>

        {loading && <p className="loading-message">Creating product...</p>}
        {error && <p className="error-message">{error}</p>}
        {success && <p className="success-message">{success}</p>}
        
        <button type="submit" disabled={loading} className="cta-button">
          List Product
        </button>
      </form>
      <style jsx>{`
        .create-product-form .form-group {
          margin-bottom: 1rem;
        }
        .create-product-form label {
          display: block;
          margin-bottom: 0.3rem;
          font-weight: 600;
          color: #333;
        }
        .create-product-form input,
        .create-product-form select,
        .create-product-form textarea {
          width: 100%;
          padding: 0.6rem;
          border: 1px solid #ccc;
          border-radius: 4px;
          font-size: 1rem;
        }
        .create-product-form .required-star {
          color: red;
          margin-left: 0.2rem;
        }
        .success-message {
          color: green;
          margin-top: 1rem;
          text-align: center;
        }
        .cta-button { 
            /* Ensure this style is available or define it in index.css */
            display: inline-block;
            background-color: #00796b;
            color: #fff;
            padding: 0.8rem 1.5rem;
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
      `}</style>
    </div>
  );
};

export default CreateProductPage;
