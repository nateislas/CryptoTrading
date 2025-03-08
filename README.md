# Crypto Trading Pipeline: Building Algorithmic Strategies on Robinhood

## Overview

This project, **Crypto Trading Pipeline**, is designed to provide a robust and user-friendly platform for developing and deploying algorithmic trading strategies on the Robinhood cryptocurrency API. It allows users to interact with their Robinhood accounts, retrieve real-time and historical market data, execute trades, and build automated trading algorithms.

## Core Goals

*   **Ease of Use:** Make it easy for users to develop and test algorithmic trading strategies.
*   **Reliability:** Ensure the platform is stable, handles errors gracefully, and interacts with the Robinhood API correctly.
*   **Flexibility:** Provide a flexible framework that allows users to create a wide variety of trading strategies.
*   **Real-Time Capabilities:** Enable strategies to react to real-time market changes.
*   **Security:** Create a system that ensures the user data is safe.

## Current State

The project currently includes:

*   **`api_access.py`:** A class (`CryptoAPITrading`) to interact with the Robinhood API. It now uses the following new files:
    *   **`api_client.py`**: Handles the low-level API requests.
    *   **`orders.py`**: Handles all the order related functions.
    * **`market_data.py`**: Handles all the market data functions.
    * **`account.py`**: Handles all the user account functions.
    * It allows to:
        *   Retrieve account information (account number, buying power).
        *   Retrieve holdings.
        *   Get real-time best bid/ask and estimated prices.
        *   Place orders (market, limit, and stop loss).
        *   Cancel orders.
        *   Get an order.
        *   Get all orders.
*   **`app.py`:** A Dash application that displays basic account information and holdings. It now has:
    * Error handling.
    * It handles the minimum quantity requirement for certain assets.
    * It is much more robust.
*   **`test.py.ipynb`:** A Jupyter notebook with comprehensive testing of API functions. It now has:
    *   Tests for account functions.
    *   Tests for market data functions.
    *   Tests for orders functions.
    * Input validation tests.
    * Type error tests.
    * Error tests.
*   **`test_dashboard.ipynb`:** A Jupyter notebook that is not being used.

## Development Roadmap

This roadmap outlines the key steps needed to transform this project into a powerful algorithmic trading platform. The tasks are broken down into priority order.

### Priority 1: Core Functionality & Codebase Foundation (Essential)

These are the *absolute must-haves* to make the project functional and reliable.

1.  **Robust Order Management (Testing & Error Handling)**
    *   **Goal:** Ensure all order-related functions are thoroughly tested and handle errors correctly.
    *   **Tasks:**
        *   [x] **Thorough Testing (`test.py.ipynb`):**
            *   [x] Test `place_order` with different order types (market, limit, stop-loss, stop-limit).
            *   [x] Test `cancel_order` with orders in various states.
            *   [x] Test `get_order` (by order ID).
            *   [x] Test `get_orders` (retrieving all orders).
        *   [ ] **Order Status Tracking (`api_access.py`, `orders.py`):**
            *   Add logic to track order status (pending, filled, partially filled, canceled, rejected).
        *   [x] **Order Error Handling (`api_access.py`, `orders.py`):**
            *   [x] Handle API request errors.
            *   [x] Handle order rejection errors.
            *   [x] Handle invalid order parameters.
            *   [ ] Add a function to modify orders.
            * [x] Validate all inputs.
            * [x] Add comments to better explain the code.
    *   **Files:** `robinhood_api/api_access.py`, `robinhood_api/orders.py`, `test.py.ipynb`
2.  **Enhance Error Handling (API Requests & Inputs)**
    *   **Goal:** Make the system stable and predictable by handling errors gracefully.
    *   **Tasks:**
        *   [x] **API Request Errors (`api_access.py`, `api_client.py`):**
            *   [x] Handle network errors (`requests.exceptions.ConnectionError`).
            *   [x] Handle rate limiting errors (status code 429).
            *   [x] Handle authentication failures (status code 401).
            *   [x] Handle server errors (status code 500).
            *   [x] Log errors to a file or the console.
        *   [x] **Input Validation (`api_access.py`, `orders.py`, `market_data.py`):**
            *   [x] Check if symbols are valid.
            *   [x] Check if quantities are positive.
            *   [x] Check if order types are valid.
        *   [x] **Catch Exceptions:** Use `try-except` blocks throughout the codebase.
    *   **Files:** `robinhood_api/api_access.py`, `robinhood_api/api_client.py`, `robinhood_api/orders.py`, `robinhood_api/market_data.py`, `test.py.ipynb`, `app.py`
3.  **Authentication**
    *   **Goal:** Allow users to use the app in a secure way.
    *   **Tasks:**
        *   [ ] **Create a user management system:** Create a way for new users to create an account.
        *   [ ] **Better key management:** Don't store the user keys in plain text.
    *   **Files:** All files are going to need to be changed.
4.  **Refactor `api_access.py` (Code Organization)**
    *   **Goal:** Improve code organization by splitting `api_access.py` into multiple files.
    *   **Tasks:**
        *   [x] **`api_client.py`:** Create this new file. Move the core API request logic (`make_api_request`, `get_authorization_header`) here.
        *   [x] **`orders.py`:** Create this new file. Move order-related functions (`place_order`, `cancel_order`, `get_order`, `get_orders`) here.
        *   [x] **`market_data.py`:** Create this new file. Move market data functions (`get_best_bid_ask`, `get_estimated_price`, etc.) here.
        *   [x] **`account.py`:** Create this new file to house the account information functions.
        *   [x] **Update Imports:** Update all files to import from the new locations.
    *   **Files:** `robinhood_api/api_access.py`, `robinhood_api/api_client.py`, `robinhood_api/orders.py`, `robinhood_api/market_data.py`, `robinhood_api/account.py`, `test.py.ipynb`, `app.py`

### Priority 2: Data Retrieval & Real-Time Updates (Next Steps)

These are essential for building actual trading algorithms.

1.  **Advanced Data Retrieval (Historical & Granular)**
    *   **Goal:** Provide access to rich historical and granular market data.
    *   **Tasks:**
        *   [ ] **Historical Price Data (`market_data.py`):**
            *   Create a new function to get historical price data.
            *   Accept a symbol, timeframe (e.g., '1d', '1h', '5m'), and date range.
            *   Return data in a clear format (e.g., Pandas DataFrame with timestamps, OHLC data, volume).
        *   [ ] **Candlestick Data:** Ensure historical data function includes OHLC data.
        *   [ ] **Volume Data:** Make sure historical data includes volume.
        *   [ ] **Data Filtering:** Allow users to specify date ranges, symbols, etc.
        *   [ ] **`data_provider.py`:** Create this new file to house data manipulation code.
    *   **Files:** `robinhood_api/market_data.py`, `data_provider.py`, `test.py.ipynb`
2.  **Start Real-Time Data Exploration (Websockets)**
    *   **Goal:** Move beyond polling and use real-time data feeds.
    *   **Tasks:**
        *   [ ] **Research:** Investigate if Robinhood offers a websocket API.
        *   [ ] **Experiment:** Try to connect to the websocket and print data.
        *   [ ] **Implement:** If you can get a connection with the websocket, implement the connection.
    *   **Files:** `robinhood_api/market_data.py`, `test.py.ipynb`

### Priority 3: `app.py` Enhancements (Dashboard)

1.  **Improve Dashboard Data**
    *   **Goal:** Display more data and add charts.
    *   **Tasks:**
        *   [ ] **More data:** Display more data, such as best bid and ask.
        *   [ ] **Charts:** Add the ability to add charts to the dashboard.
        * [ ] **Error message:** Display an error message when something goes wrong.
    *   **Files:** `app.py`

### Priority 4: Code Cleanup & Structure (Ongoing)

These should be done as you go along, not as separate steps.

1.  **Remove Redundant Code**
    *   **Tasks:**
        *   [x] Remove unused imports.
        *   [x] Remove commented-out code.
    *   **Files:** All files
2.  **Jupyter Notebooks**
    *   **Tasks:**
        *   [ ] Move code from notebooks into `.py` files.
        *   [x] Use notebooks for testing and experimentation only.
    *   **Files:** `test.py.ipynb`, `test_dashboard.ipynb`
3.  **Documentation**
    *   **Tasks:**
        *   [ ] Add docstrings to all functions.
        *   [x] Add comments to complex code.
        *   [x] Update `README.md`.
    *   **Files:** All files
4.  **Testing:**
    *   **Tasks:**
        *   [ ] **Create a `test` folder:** Move the `test.py.ipynb` file to a folder called `test`.
        *   [ ] **Create more tests:** Create more testing files.
    *   **Files:** `test` folder.

### Future Enhancements

These are advanced features that can be considered after the core functionality is stable:

*   **Strategy Development Tools:**
    *   Strategy base class.
    *   Backtesting engine.
    *   Paper trading.
    *   Examples.
*   **Deployment Capabilities:**
    *   Live trading.
    *   Deployment options (local, cloud).
    *   Scheduling.
*   **Technical Indicators:**
    *   Integrate common technical indicators.
*   **Machine Learning Integration:**
    *   Allow users to integrate their own ML models.
    *   Create examples that use ML.
*   **Community:**
    *   Create a good documentation.
    *   Create tutorials.
*   **Security:**
    *   Better user and key management.

## Getting Started

1.  Clone the repository.
2.  Set up your Robinhood API credentials.
3.  Follow the development roadmap above.

## Contributing

Contributions are welcome! Please open an issue or submit a pull request.

## License

[Add your license here]