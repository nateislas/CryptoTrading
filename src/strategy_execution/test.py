import asyncio
import random
import logging
from trade import TrackedTrade, TradeStatus
from trade_manager import TradeManager
from src.robinhood_api.api_access import CryptoAPITrading

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

async def place_order(api_trading_client, symbol, quantity, side):
    """
    Submit a market order (buy/sell) to the brokerage.
    Returns the order_id and best bid/ask at submission.
    Does NOT wait for the order to fill.
    """
    try:
        # Step 1: Get the adjusted estimated price
        adj_est_price = api_trading_client.market_data.get_adj_est_price(
            symbol=symbol,
            side=('ask' if side == 'buy' else 'bid'),
            quantity=quantity
        )
        # Step 2: Get best bid/ask
        best_bid_ask = api_trading_client.market_data.get_best_bid_ask(symbol)
        best_bid = float(best_bid_ask['results'][0]['bid_inclusive_of_sell_spread'])
        best_ask = float(best_bid_ask['results'][0]['ask_inclusive_of_buy_spread'])
        logging.info(
            f"Submitting Market {side.capitalize()} Order for {symbol} with adj_est_price={adj_est_price:.6f}"
        )
        # Step 3: Place market order
        order_result = api_trading_client.orders.place_market_order(
            symbol=symbol,
            side=side,
            quantity=quantity
        )
        order_id = order_result[0]['id']
        return order_id, best_bid, best_ask, adj_est_price
    except Exception as e:
        logging.error(f"Error placing {side} order: {e}")
        return None, None, None, None

async def monitor_pending_trades(api_trading_client, trade_manager: TradeManager):
    while True:
        pending_trades, open_trades = trade_manager.load_trades()
        updated = False
        for trade in pending_trades[:]:
            if trade.status == TradeStatus.PENDING:
                order_details = api_trading_client.orders.get_order(trade.buy_order_id)
                if order_details and order_details.get('executions'):
                    execution_price = float(order_details['executions'][0]['effective_price'])
                    trade.buy_price = execution_price  # record actual fill price
                    trade.status = TradeStatus.OPEN
                    logging.info(
                        f"[PendingMonitor] Buy order filled for {trade.symbol} at price={execution_price:.6f}, transitioning to OPEN."
                    )
                    pending_trades.remove(trade)
                    open_trades.append(trade)
                    updated = True
                    # Once one trade is processed, break to re‑load updated state
                    break
        if updated:
            trade_manager.save_trades(pending_trades, open_trades)
        await asyncio.sleep(1)

async def monitor_open_trades(api_trading_client, trade_manager: TradeManager):
    """
    Continuously monitors open trades (from CSV) for exit conditions.
    When conditions are met, submits a sell order and polls for fill.
    """
    while True:
        pending_trades, open_trades = trade_manager.load_trades()
        for trade in open_trades[:]:
            if trade.status == TradeStatus.OPEN and not trade.is_closed():
                adj_est_price = api_trading_client.market_data.get_adj_est_price(
                    symbol=trade.symbol,
                    side='bid',
                    quantity=trade.quantity
                )
                if adj_est_price < trade.buy_price:
                    logging.info(
                        f"[OpenMonitor] Sell condition met for {trade.symbol}: adj_est_price={adj_est_price:.6f} < buy_price={trade.buy_price:.6f}"
                    )
                    sell_id, best_bid_sell, best_ask_sell, sell_adj_est_price = await place_order(
                        api_trading_client, trade.symbol, trade.quantity, 'sell'
                    )
                    if sell_id:
                        trade.sell_order_id = sell_id
                        trade.best_bid_sell = best_bid_sell  # Store best bid at sell order placement
                        trade.best_ask_sell = best_ask_sell  # Store best ask at sell order placement
                        trade.estimated_price_sell = sell_adj_est_price  # Store estimated price at sell order placement

                        # Save trade state after placing the sell order
                        trade_manager.save_trades(pending_trades, open_trades)

                        await poll_for_sell_fill(api_trading_client, trade, trade_manager)
                        open_trades.remove(trade)
                        trade_manager.save_trades(pending_trades, open_trades)
                else:
                    logging.info(
                        f"[OpenMonitor] Sell condition NOT met for {trade.symbol}: adj_est_price={adj_est_price:.6f}, buy_price={trade.buy_price:.6f}"
                    )
                    await asyncio.sleep(2)
        await asyncio.sleep(1)

async def poll_for_sell_fill(api_trading_client, trade, trade_manager: TradeManager):
    """
    Polls until the sell order is filled, then closes the trade and logs it.
    """
    while True:
        sell_details = api_trading_client.orders.get_order(trade.sell_order_id)
        if sell_details and sell_details.get('executions'):
            sell_price = float(sell_details['executions'][0]['effective_price'])
            trade.close_trade(
                sell_order_id=trade.sell_order_id,
                sell_price=sell_price,
                best_bid=trade.best_bid_sell,  # Use the stored sell order best bid
                best_ask=trade.best_ask_sell,  # Use the stored sell order best ask
                estimated_price=trade.estimated_price_sell  # Use the stored estimated price at sell order
            )
            trade.status = TradeStatus.CLOSED
            logging.info(
                f"[SellFillMonitor] Sell order filled for {trade.symbol} at price={sell_price:.6f}. Trade closed."
            )
            trade_manager.log_trade(trade)
            pending_trades, open_trades = trade_manager.load_trades()
            trade_manager.save_trades(pending_trades, open_trades)
            return
        await asyncio.sleep(1)

async def buy_trades_loop(api_trading_client, trade_manager: TradeManager, symbol='DOGE-USD', quantity=1.0, interval_seconds=10):
    """
    Places buy orders based on a schedule.
    Each new buy order is added to the CSV as a PENDING trade.
    """
    while True:
        buy_id, best_bid, best_ask, adj_est_price = await place_order(
            api_trading_client, symbol, quantity, 'buy'
        )
        if buy_id:
            new_trade = TrackedTrade(
                symbol=symbol,
                quantity=quantity,
                buy_order_id=buy_id,
                buy_price=0.0,  # Unknown until order fills
                best_bid=best_bid,
                best_ask=best_ask,
                estimated_price=adj_est_price,
                status=TradeStatus.PENDING
            )
            pending_trades, open_trades = trade_manager.load_trades()
            pending_trades.append(new_trade)
            trade_manager.save_trades(pending_trades, open_trades)
        sleepy_time = interval_seconds + random.uniform(120, 600)
        logging.info(f"[BuyLoop] Sleeping for {sleepy_time:.2f} seconds before next buy...")
        await asyncio.sleep(sleepy_time)

async def main_trading(api_trading_client):
    """
    Main execution loop.
    Loads the persistent trade state from CSV and launches the buy, pending, and open monitors concurrently.
    """
    trade_manager = TradeManager()
    # Ensure the CSV exists and load the initial state.
    trade_manager.load_trades()
    buy_task = asyncio.create_task(buy_trades_loop(api_trading_client, trade_manager))
    pending_monitor_task = asyncio.create_task(monitor_pending_trades(api_trading_client, trade_manager))
    open_monitor_task = asyncio.create_task(monitor_open_trades(api_trading_client, trade_manager))
    await asyncio.gather(buy_task, pending_monitor_task, open_monitor_task)

if __name__ == '__main__':
    api_trading_client = CryptoAPITrading()
    try:
        asyncio.run(main_trading(api_trading_client))
    except KeyboardInterrupt:
        logging.info("Trading stopped by user.")