# Crypto Trading Pipeline: Algorithmic Trading on Robinhood

## Overview
This project is a full end-to-end system for algorithmic trading using the official [Robinhood Crypto Trading API](https://newsroom.aboutrobinhood.com/robinhood-crypto-trading-api/). It enables users to retrieve real-time and historical market data, execute trades, and develop automated trading strategies. 

To ensure data efficiency and reliability, I have set up a small server using a single-board computer that continuously (24/7 at 1-second intervals) collects and saves cryptocurrency market data in an optimized manner. The plan is to accumulate multiple months of data and open-source the dataset.

Additionally, I aim to build a platform that allows users to:
- Develop and backtest trading strategies.
- Automatically execute strategies.
- Access a structured dataset for research.

## Current Features

### Data Collection Pipeline
- **Real-time data collection** at 1-second intervals.
- **Optimized data storage** using Parquet format for efficiency.
- **Multi-currency support** for tracking different crypto assets.
- **Automated processing** to run continuously without intervention.

### Robinhood API Integration
- **Account Management:** Retrieve balance, buying power, and holdings.
- **Market Data Retrieval:** Fetch best bid/ask prices and historical data.
- **Order Execution:** Place, cancel, and track trades (market, limit, stop-loss).

### Web Dashboard (Dash-based UI)
- View account information and holdings.
- Track real-time market prices.
- Error handling and robustness improvements.

### Testing & Validation
- **Comprehensive testing suite** (`test.py.ipynb`) covering:
  - API authentication
  - Market data retrieval
  - Order execution and tracking
  - Error handling and input validation

## Roadmap
### **Phase 1: Core Enhancements** *(Current Focus)*
- **Improve Order Management:**
  - Robust tracking of order status (pending, filled, canceled, etc.).
  - Enhanced error handling for API failures and invalid parameters.
  - Implement order modifications.
- **Expand Data Retrieval:**
  - Support for historical OHLC (candlestick) and volume data.
  - Data filtering by timeframes and symbols.
- **Authentication & Security:**
  - Secure user management system.
  - Better handling of API credentials.

### **Phase 2: Real-Time Trading & Execution**
- **Websockets for Real-Time Updates:**
  - Investigate Robinhood WebSocket API (if available).
  - Implement real-time data streaming.
- **Strategy Execution Engine:**
  - Develop a modular system for algorithmic strategies.
  - Implement logging and monitoring for live trading.

### **Phase 3: Backtesting & Open-Source Dataset**
- **Backtesting Framework:**
  - Create a historical data replay system.
  - Simulate order execution and performance metrics.
- **Open-Source Crypto Dataset:**
  - Publish cleaned historical crypto data for research and development.
  - Allow users to contribute additional datasets.

### **Phase 4: Advanced Features** *(Future Work)*
- **Paper Trading Mode**: Test strategies without real capital.
- **Technical Indicators**: Integrate common TA indicators.
- **Machine Learning & AI**: Allow integration of ML-based trading models.
- **Cloud Deployment**: Enable users to deploy strategies on the cloud.

## Project Structure
```
CryptoTrading/
│── data/                     # Collected crypto market data
│── src/
│   ├── robinhood_api/
│   │   ├── api_access.py      # High-level API interactions
│   │   ├── api_client.py      # Low-level API requests
│   │   ├── orders.py          # Order execution functions
│   │   ├── market_data.py     # Market data retrieval functions
│   │   ├── account.py         # Account management functions
│   ├── data_processing/
│   │   ├── collect_ticker_data.py  # Real-time data collection script
│── app.py                     # Web dashboard for trading
│── README.md                  # Project documentation
```

## Getting Started
### Prerequisites
- Python 3.9+
- Pip and virtualenv
- Robinhood API credentials

### Installation
```bash
# Clone the repository
git clone https://github.com/your-repo/CryptoTrading.git
cd CryptoTrading

# Create and activate a virtual environment
python3.9 -m venv .venv
source .venv/bin/activate  # On Mac/Linux
.venv\Scripts\activate    # On Windows

# Install dependencies
pip install -r requirements.txt
```

### Running the Data Collector
```bash
python src/data_processing/collect_ticker_data.py --ticker BTC-USD --interval 1s --batch_size 250
```

### Running the Web Dashboard
```bash
python app.py
```

## Contributing
Contributions are welcome! If you have ideas or improvements, feel free to open an issue or submit a pull request.

## License
[MIT License] – Feel free to use, modify, and distribute this project.