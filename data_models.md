# Green Hydrogen Exchange and Credit Platform - Data Models

This document outlines the core data models for the Green Hydrogen Exchange and Credit Platform.

## 1. User

Represents an individual or organization interacting with the platform.

*   **Attributes:**
    *   `user_id`: STRING (Primary Key, Unique) - Unique identifier for the user.
    *   `username`: STRING (Unique) - User-chosen name for login.
    *   `email`: STRING (Unique) - User's email address.
    *   `password_hash`: STRING - Hashed password for security.
    *   `organization_name`: STRING (Optional) - Name of the organization the user belongs to.
    *   `created_at`: TIMESTAMP - Timestamp of account creation.
    *   `updated_at`: TIMESTAMP - Timestamp of last profile update.

*   **Roles:** (This can be implemented as a separate table `UserRole` for many-to-many relationship if a user can have multiple roles, or an ENUM/array if roles are limited and a user has one primary role). For simplicity here, we'll initially consider it as an attribute that can hold multiple values or link to a roles table.
    *   `roles`: ARRAY of STRING (e.g., "buyer", "seller", "admin", "verifier") - Defines the user's permissions and access levels.

## 2. HydrogenProduct (or Listing)

Represents a specific batch or offer of hydrogen available for sale on the exchange.

*   **Attributes:**
    *   `product_id`: STRING (Primary Key, Unique) - Unique identifier for the hydrogen product listing.
    *   `seller_id`: STRING (Foreign Key to `User.user_id`) - Identifier of the user selling the hydrogen.
    *   `quantity_kg`: DECIMAL - Amount of hydrogen available in kilograms.
    *   `price_per_kg`: DECIMAL - Price per kilogram of hydrogen.
    *   `location_region`: STRING - Geographical region of the hydrogen production/availability.
    *   `location_plant_id`: STRING (Optional) - Specific plant identifier if applicable.
    *   `production_method`: ENUM (e.g., "electrolysis_renewables", "smr_ccs", "atr_ccs", "biomass_gasification") - Method used to produce the hydrogen.
    *   `purity_percentage`: DECIMAL (e.g., 99.999) - Purity level of the hydrogen.
    *   `delivery_terms`: TEXT - Description of delivery terms, incoterms, etc.
    *   `ghg_intensity_kgco2e_per_kgh2`: DECIMAL (Optional) - Greenhouse gas emissions intensity associated with the production of this hydrogen (kg CO2 equivalent per kg H2).
    *   `feedstock`: STRING (Optional) - The primary feedstock used for hydrogen production (e.g., "solar_power", "wind_power", "natural_gas", "biomethane").
    *   `energy_source`: STRING (Optional) - The energy source used in production (e.g., "grid_electricity", "ppa_solar", "ppa_wind").
    *   `pipeline_injection_ready`: BOOLEAN (Optional) - Indicates if the hydrogen is suitable for direct pipeline injection.
    *   `compression_pressure_bar`: INTEGER (Optional) - Compression pressure if applicable.
    *   `available_from_date`: DATE - Date when the hydrogen product becomes available.
    *   `listing_timestamp`: TIMESTAMP - Timestamp when the product was listed.
    *   `updated_timestamp`: TIMESTAMP - Timestamp of the last update to the listing.
    *   `status`: ENUM ("active", "inactive", "sold", "expired") - Current status of the listing.
    *   `certification_ids`: ARRAY of STRING (Optional, Foreign Keys to a potential `Certification` table) - IDs of any certifications associated with this product.

## 3. Order

Represents a buy or sell intention placed by a user on the exchange.

*   **Attributes:**
    *   `order_id`: STRING (Primary Key, Unique) - Unique identifier for the order.
    *   `user_id`: STRING (Foreign Key to `User.user_id`) - Identifier of the user placing the order.
    *   `order_type`: ENUM ("buy", "sell") - Specifies whether it's a buy or sell order.
    *   `hydrogen_product_id`: STRING (Foreign Key to `HydrogenProduct.product_id`, Optional) - For sell orders, this links directly to a specific product listing. For buy orders, this might be null if buying based on criteria rather than a specific listing.
    *   `quantity_kg`: DECIMAL - Amount of hydrogen the user wants to buy or sell.
    *   `price_per_kg`: DECIMAL - Desired price for buy orders (bid price) or asking price for sell orders (ask price).
    *   `production_method_criteria`: ARRAY of ENUM (Optional, for buy orders) - Buyer's preferred production methods.
    *   `location_criteria`: STRING (Optional, for buy orders) - Buyer's preferred location.
    *   `purity_criteria`: DECIMAL (Optional, for buy orders) - Minimum acceptable purity.
    *   `max_ghg_intensity_criteria`: DECIMAL (Optional, for buy orders) - Maximum acceptable GHG intensity.
    *   `status`: ENUM ("pending", "partially_filled", "filled", "cancelled", "expired") - Current status of the order.
    *   `created_timestamp`: TIMESTAMP - Timestamp when the order was created.
    *   `updated_timestamp`: TIMESTAMP - Timestamp of the last update to the order.
    *   `expiration_timestamp`: TIMESTAMP (Optional) - Time when the order automatically expires if not filled.

## 4. Trade

Represents a consummated transaction between a buyer and a seller.

*   **Attributes:**
    *   `trade_id`: STRING (Primary Key, Unique) - Unique identifier for the trade.
    *   `buy_order_id`: STRING (Foreign Key to `Order.order_id`) - Identifier of the buy order involved in the trade.
    *   `sell_order_id`: STRING (Foreign Key to `Order.order_id`) - Identifier of the sell order involved in the trade.
    *   `hydrogen_product_id`: STRING (Foreign Key to `HydrogenProduct.product_id`) - Identifier of the hydrogen product traded.
    *   `quantity_traded_kg`: DECIMAL - Amount of hydrogen traded in this transaction.
    *   `price_per_kg_agreed`: DECIMAL - The price at which the hydrogen was traded.
    *   `trade_timestamp`: TIMESTAMP - Timestamp when the trade occurred.
    *   `settlement_status`: ENUM ("pending", "completed", "failed") - Status of the settlement process (for POC, this might be simulated).
    *   `buyer_id`: STRING (Foreign Key to `User.user_id`) - Identifier of the buyer.
    *   `seller_id`: STRING (Foreign Key to `User.user_id`) - Identifier of the seller.

## 5. EnvironmentalCredit

Represents an environmental credit associated with the production of green hydrogen, which can be traded or retired.

*   **Attributes:**
    *   `credit_id`: STRING (Primary Key, Unique) - Unique identifier for the environmental credit.
    *   `issuing_organization_id`: STRING (Optional, Foreign Key to `User.user_id` or a separate `Organization` table if issuers are distinct entities) - The organization that issued the credit.
    *   `hydrogen_production_batch_id`: STRING (Optional, could be `HydrogenProduct.product_id` or a more granular batch ID if products are split) - Links the credit to a specific hydrogen production event or product.
    *   `credit_type`: ENUM ("REC", "GO", "CarbonCredit_Avoidance", "CarbonCredit_Removal", "LowCarbonFuelStandard_Credit") - Type of environmental credit.
    *   `quantity`: DECIMAL - Number of credits (e.g., 1 REC = 1 MWh of renewable energy). Units depend on `credit_type`.
    *   `unit_of_measure`: STRING (e.g., "MWh", "tCO2e") - The unit for the quantity of the credit.
    *   `owner_id`: STRING (Foreign Key to `User.user_id`) - Current owner of the credit.
    *   `beneficiary_id`: STRING (Foreign Key to `User.user_id`, Optional) - If retired for a specific beneficiary.
    *   `status`: ENUM ("active", "retired", "transferred", "pending_issuance", "expired") - Current status of the credit.
    *   `issuance_date`: DATE - Date when the credit was issued.
    *   `expiry_date`: DATE (Optional) - Date when the credit expires.
    *   `retirement_date`: DATE (Optional) - Date when the credit was retired.
    *   `region`: STRING (Optional) - Applicable region for the credit (e.g., country, state).
    *   `project_id_reference`: STRING (Optional) - Reference to the specific project that generated the credits.
    *   `transaction_history`: ARRAY of OBJECT (Optional) - A log of transfers, splits, or retirements. Each object could contain `timestamp`, `from_user_id`, `to_user_id`, `action_type`, `quantity_transferred`.

## Relationships between Entities:

*   **User and HydrogenProduct:**
    *   One-to-Many: A `User` (seller) can have multiple `HydrogenProduct` listings. A `HydrogenProduct` belongs to one `User` (seller).
    *   Relationship: `HydrogenProduct.seller_id` -> `User.user_id`

*   **User and Order:**
    *   One-to-Many: A `User` can place multiple `Order`s. An `Order` belongs to one `User`.
    *   Relationship: `Order.user_id` -> `User.user_id`

*   **User and EnvironmentalCredit:**
    *   One-to-Many: A `User` can own multiple `EnvironmentalCredit`s. An `EnvironmentalCredit` is owned by one `User` (at a time).
    *   Relationship: `EnvironmentalCredit.owner_id` -> `User.user_id`
    *   (Also potentially `EnvironmentalCredit.issuing_organization_id` -> `User.user_id` if users can be issuers)

*   **HydrogenProduct and Order:**
    *   One-to-Many (for specific sell orders): A `HydrogenProduct` can be associated with one specific `Order` (if it's a sell order directly tied to a listing).
    *   Relationship: `Order.hydrogen_product_id` -> `HydrogenProduct.product_id` (This applies mostly to sell orders that are created directly from a listing).
    *   Buy orders might not directly link to a *specific* product initially, but rather to criteria that match products.

*   **Order and Trade:**
    *   Many-to-Many (conceptually, but implemented via Trade): Multiple buy orders could potentially match with multiple sell orders. The `Trade` table resolves this.
    *   One-to-Many: An `Order` (buy) can be involved in multiple `Trade`s (if partially filled). A `Trade` involves one buy `Order`.
    *   One-to-Many: An `Order` (sell) can be involved in multiple `Trade`s (if partially filled). A `Trade` involves one sell `Order`.
    *   Relationships:
        *   `Trade.buy_order_id` -> `Order.order_id`
        *   `Trade.sell_order_id` -> `Order.order_id`

*   **HydrogenProduct and Trade:**
    *   One-to-Many: A `HydrogenProduct` can be involved in multiple `Trade`s (if the quantity is split across multiple trades). A `Trade` is associated with one `HydrogenProduct`.
    *   Relationship: `Trade.hydrogen_product_id` -> `HydrogenProduct.product_id`

*   **HydrogenProduct and EnvironmentalCredit:**
    *   One-to-Many or One-to-One (depending on granularity): A `HydrogenProduct` (or a production batch it represents) can be associated with one or more `EnvironmentalCredit`s. An `EnvironmentalCredit` is typically linked to one specific `HydrogenProduct` or production batch.
    *   Relationship: `EnvironmentalCredit.hydrogen_production_batch_id` -> `HydrogenProduct.product_id` (or a more granular batch ID).

*   **User and Role (if `UserRole` is a separate table):**
    *   `UserRole` Table:
        *   `user_id`: STRING (Foreign Key to `User.user_id`)
        *   `role_name`: STRING (e.g., "buyer", "seller")
        *   Primary Key: (`user_id`, `role_name`)
    *   This creates a Many-to-Many relationship: A `User` can have multiple roles, and a role can be assigned to multiple `User`s.

This structure provides a foundation for the Green Hydrogen Exchange and Credit Platform. Further details like specific data types, constraints, and indexes would be refined during the database schema design phase.
