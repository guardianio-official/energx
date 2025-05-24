# Green Hydrogen Exchange - Frontend Platform

This directory contains the React frontend for the Green Hydrogen Exchange platform. It's built using Vite.

## Prerequisites

*   Node.js (v18 or later recommended)
*   npm or yarn

## Environment Variables

Before running the frontend, you need to set up the API base URL. Create a file named `.env` in the `platform_frontend/` directory with the following content:

```env
VITE_API_BASE_URL=http://localhost:5000/api
```

*   Replace `http://localhost:5000/api` with the actual URL where your backend API is running if it's different. The Flask backend for this project typically runs on port 5000.

## Getting Started

1.  **Navigate to the frontend directory:**
    ```bash
    cd platform_frontend
    ```

2.  **Install dependencies:**
    ```bash
    npm install
    ```
    or
    ```bash
    yarn install
    ```

3.  **Run the development server:**
    ```bash
    npm run dev
    ```
    or
    ```bash
    yarn dev
    ```

    This will start the Vite development server, typically on `http://localhost:5173` (or `http://localhost:3000` if configured in `vite.config.js`).

## Available Scripts

*   `npm run dev` or `yarn dev`: Runs the app in development mode.
*   `npm run build` or `yarn build`: Builds the app for production.
*   `npm run lint` or `yarn lint`: Lints the codebase.
*   `npm run preview` or `yarn preview`: Serves the production build locally for preview.

## Key Features Implemented

*   User Login
*   User Dashboard (Profile & Order History)
*   Product Listing Creation (for sellers)
*   Product Discovery (listing page)
*   Product Detail View & Bidding (for buyers)

## CORS Note

Ensure the backend API has CORS (Cross-Origin Resource Sharing) enabled for the frontend development server's URL (e.g., `http://localhost:5173` or `http://localhost:3000`). The backend in this project is configured to allow these origins.
---
