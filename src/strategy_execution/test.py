from trade import TradeLogger, Trade
from src.robinhood_api.api_access import CryptoAPITrading
import time
import logging
import random

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

open_trades = []  # Stores open trades that need to be closed


def execute_trade(api_trading_client, symbol, quantity, side):
    """
    Executes a market order (buy/sell) and returns raw execution details.
    The returned values can be post-processed to calculate slippage.

    Args:
        api_trading_client: CryptoAPITrading instance.
        symbol (str): Trading symbol (e.g., 'DOGE-USD').
        quantity (float): Trade quantity.
        side (str): 'buy' or 'sell'.
    """
    try:
        # Step 1: Get Adjusted Real-Time Execution Price (Including Robinhood Spread)
        adjusted_estimated_price = api_trading_client.market_data.get_adj_est_price(
            symbol=symbol, side=('ask' if side == 'buy' else 'bid'), quantity=quantity)

        # Step 2: Get Best Bid/Ask Prices
        best_bid_ask = api_trading_client.market_data.get_best_bid_ask(symbol)
        best_bid = float(best_bid_ask['results'][0]['bid_inclusive_of_sell_spread'])
        best_ask = float(best_bid_ask['results'][0]['ask_inclusive_of_buy_spread'])

        # (We now simply store raw data without calculating slippage.)

        # Step 3: Place Market Order
        logging.info(f"Placing Market {side.capitalize()} Order at estimated price {adjusted_estimated_price:.6f}")
        order_result = api_trading_client.orders.place_market_order(symbol=symbol, side=side, quantity=quantity)
        order_id = order_result[0]['id']

        # Step 4: Wait briefly to ensure order execution is completed
        time.sleep(5.0)

        # Step 5: Fetch the Actual Execution Price
        order_details = api_trading_client.orders.get_order(order_id)
        if not order_details['executions']:
            logging.error(f"Order {order_id} was not executed.")
            return None, None, None, None, None

        execution_price = float(order_details['executions'][0]['effective_price'])

        return order_id, execution_price, best_bid, best_ask, adjusted_estimated_price

    except Exception as e:
        logging.error(f"Error executing {side} order: {e}")
        return None, None, None, None, None


def check_and_close_trades(api_trading_client, trade_logger):
    global open_trades

    for trade in open_trades[:]:  # slice copy to safely remove within loop
        if not trade.is_closed():
            (sell_order_id,
             sell_execution_price,
             sell_best_bid,
             sell_best_ask,
             sell_adjusted_est_price) = execute_trade(api_trading_client, trade.symbol, trade.quantity, "sell")

            if sell_order_id:
                # Pass the relevant raw data to close_trade
                trade.close_trade(
                    sell_order_id=sell_order_id,
                    sell_price=sell_execution_price,
                    best_bid=sell_best_bid,
                    best_ask=sell_best_ask,
                    estimated_price=sell_adjusted_est_price
                )
                trade_logger.log_trade(trade)
                open_trades.remove(trade)


def execute_trades_continuous(api_trading_client, trade_logger, symbol='DOGE-USD', quantity=1.0):
    global open_trades

    # Execute Buy Order and retrieve raw data
    (buy_order_id,
     buy_execution_price,
     buy_best_bid,
     buy_best_ask,
     buy_adjusted_est_price) = execute_trade(api_trading_client, symbol, quantity, 'buy')

    if buy_order_id:
        # Create a new Trade object with relevant buy data
        new_trade = Trade(
            symbol=symbol,
            quantity=quantity,
            buy_order_id=buy_order_id,
            buy_price=buy_execution_price,  # Actual execution price
            best_bid=buy_best_bid,  # Best bid at time of buy
            best_ask=buy_best_ask,  # Best ask at time of buy
            estimated_price=buy_adjusted_est_price  # Adjusted estimated price
        )
        open_trades.append(new_trade)

    sleepy_time = random.uniform(30, 300)
    logging.info(f"Sleeping for {sleepy_time} seconds before selling...")

    time.sleep(sleepy_time)

    # Now check & close any open trades (execute sell orders)
    check_and_close_trades(api_trading_client, trade_logger)

def continuous_trading(api_trading_client, trade_logger, symbol='DOGE-USD', quantity=1.0, interval_seconds=10):
    while True:
        try:
            execute_trades_continuous(api_trading_client, trade_logger, symbol, quantity)
            sleepy_time = interval_seconds + random.uniform(30, 300)
            logging.info(f"Sleeping for {sleepy_time} seconds before next trade...")
            time.sleep(sleepy_time)

        except KeyboardInterrupt:
            logging.info("Trading stopped by user.")
            break
        except Exception as e:
            logging.error(f"Error in continuous trading: {e}")
            time.sleep(10)


if __name__ == '__main__':
    api_trading_client = CryptoAPITrading()
    trade_logger = TradeLogger()
    continuous_trading(api_trading_client, trade_logger)