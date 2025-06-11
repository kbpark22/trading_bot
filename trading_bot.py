import ccxt
import platform
import logging
import time  # Add for measuring execution time
import random  # Add for randomizing delays
import csv  # Add for reading CSV files
import argparse  # Add for argument parsing
from datetime import datetime  # Add for date handling
from apikeys import UPBIT_ACCESS_KEY, UPBIT_SECRET_KEY  # Import API keys from apikeys.py
from logger_config import configure_logger  # Import logger configuration

def read_symbols_from_csv(file_path):
    """Read symbols and their respective parameters from a CSV file."""
    symbols = []
    with open(file_path, mode='r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            symbol = row['symbol']
            avg_days = int(row['avg_days'])
            target_ratio = float(row['target_ratio'])
            buy_ratio = float(row['buy_ratio'])  # Read the buy ratio
            symbols.append({'symbol': symbol, 'avg_days': avg_days, 'target_ratio': target_ratio, 'buy_ratio': buy_ratio})
    return symbols

def sell_all_assets(exchange, logger, trade_file_handler):
    """
    Sell all assets (except KRW) at market price.
    """
    balance = exchange.fetch_balance()
    for asset, asset_balance in balance.items():
        if asset in ['free', 'used', 'total', 'KRW']:
            continue
        if isinstance(asset_balance, dict) and asset_balance.get('free', 0) > 0:
            symbol = f"{asset}/KRW"
            if symbol in exchange.markets:
                if 'BTC' in symbol:
                    continue  # Skip BTC
                amount_to_sell = asset_balance['free']
                try:
                    logger.info(f"[SELL-ALL] Market sell order: {amount_to_sell} {symbol} (ALL holdings)")
                    exchange.create_order(symbol, 'market', 'sell', amount_to_sell)
                    logger.info(f"[SELL-ALL] SUCCESS: Sold {amount_to_sell} {symbol} at market price", extra={'handler': trade_file_handler})
                except Exception as e:
                    logger.error(f"[SELL-ALL] ERROR: Could not sell {symbol} - {e}", extra={'handler': trade_file_handler})
                time.sleep(random.uniform(0.1, 0.2))  # Avoid rate-limiting

def save_valuation_to_csv(date_str, krw_total, file_path='portfolio_valuation.csv'):
    """Append the date and total KRW valuation to a CSV file."""
    file_exists = False
    try:
        file_exists = open(file_path, 'r')
        file_exists.close()
    except FileNotFoundError:
        pass

    with open(file_path, mode='a', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        if not file_exists:
            writer.writerow(['date', 'krw_total'])
        writer.writerow([date_str, int(krw_total)])

def main():
    """Main function to execute the bot."""
    parser = argparse.ArgumentParser()
    parser.add_argument('--sell-all', action='store_true', help='Sell all coins and exit')
    args = parser.parse_args()

    logger, trade_file_handler = configure_logger()  # Use the logger and trade-specific handler
    logger.info("*" * 100)
    logger.info("[START] Trading bot is starting up.")
    
    exchange = ccxt.upbit({
        'apiKey': UPBIT_ACCESS_KEY,  # Use imported API key
        'secret': UPBIT_SECRET_KEY,  # Use imported secret key
    })

    if args.sell_all:
        logger.info("[MODE] Sell-all mode activated. Selling all assets except KRW and BTC.")
        sell_all_assets(exchange, logger, trade_file_handler)
        logger.info("[EXIT] All assets have been sold. Bot is exiting.")
        return

    # Read symbols and their parameters from a CSV file
    csv_file_path = 'symbols.csv'  # Update with the actual path to your CSV file
    logger.info(f"[LOAD] Loading trading symbols and parameters from CSV: {csv_file_path}")
    symbols_data = read_symbols_from_csv(csv_file_path)

    try:
        # Fetch balance once
        balance = exchange.fetch_balance()
        krw_free = balance['KRW']['free']
        krw_used = balance['KRW']['used']
        krw_total = krw_free + krw_used

        # Include the KRW-equivalent value of all other assets
        for asset, asset_balance in balance.items():
            # Skip non-asset keys like 'free', 'used', and 'total'
            if asset in ['free', 'used', 'total']:
                continue

            if asset != 'KRW' and isinstance(asset_balance, dict):
                market_symbol = f"{asset}/KRW"
                if market_symbol in exchange.markets:  # Check if the market exists
                    try:
                        ticker = exchange.fetch_ticker(market_symbol)  # Fetch the current price of the asset in KRW
                        asset_price_in_krw = ticker['last'] if 'last' in ticker else 0
                        krw_total += asset_balance.get('total', 0) * asset_price_in_krw
                        time.sleep(random.uniform(0.1, 0.1))  # Add a small delay to avoid rate-limiting
                    except ccxt.RateLimitExceeded as e:
                        logger.warning(f"[RATE-LIMIT] Rate limit exceeded for {market_symbol}. Waiting before retry...")
                        time.sleep(1)  # Wait before retrying
                        continue
                else:
                    logger.warning(f"[SKIP] Market {market_symbol} does not exist on Upbit. Skipping asset.")

        logger.info("*" * 100)
        logger.info(f"[BALANCE] Total portfolio value: {krw_total:,.0f} KRW (KRW + all coins)")

        # Save valuation to CSV with current date
        date_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        save_valuation_to_csv(date_str, krw_total)

        for symbol_data in symbols_data:
            logger.info("*" * 100)
            symbol = symbol_data['symbol']
            avg_days = symbol_data['avg_days']
            target_ratio = symbol_data['target_ratio']
            buy_ratio = symbol_data['buy_ratio']  # Use the buy ratio

            try:
                # Fetch OHLCV, ticker, and order book data sequentially
                ohlcv = exchange.fetch_ohlcv(symbol, timeframe='1d', limit=avg_days)
                time.sleep(random.uniform(0.1, 0.1))  # Add a small delay to avoid rate-limiting
                ticker = exchange.fetch_ticker(symbol)
                time.sleep(random.uniform(0.1, 0.1))  # Add a small delay to avoid rate-limiting
                order_book = exchange.fetch_order_book(symbol)
                time.sleep(random.uniform(0.1, 0.1))  # Add a small delay to avoid rate-limiting

                # Ensure all data is available before proceeding
                if not ohlcv or not ticker or not order_book:
                    logger.warning(f"[SKIP] {symbol}: Missing OHLCV/ticker/orderbook data. Skipping.")
                    continue

                # Calculate the average open price based on the specified number of days
                open_prices = [candle[1] for candle in ohlcv]
                avg_open_price = sum(open_prices) / len(open_prices)
                logger.info(f"[{symbol}] {avg_days}-day average open price: {avg_open_price:,.0f} KRW")

                # Execute trade logic
                current_price = ticker['last']
                target_price = avg_open_price * target_ratio  # 매수 타겟 조건 금액
                logger.info(f"[{symbol}] Current price: {current_price} KRW | Buy target: {target_price:.2f} KRW")

                # Extract best ask and bid prices from the order book
                best_ask = order_book['asks'][-1][0] if order_book['asks'] else None
                best_bid = order_book['bids'][-1][0] if order_book['bids'] else None

                # Fetch current holdings from the pre-fetched balance
                base_currency = symbol.split('/')[0]
                current_holdings = balance[base_currency]['total'] if base_currency in balance else 0
                current_valuation = current_holdings * current_price

                if current_price > target_price and best_ask:
                    # Calculate the shortfall between target valuation and current valuation
                    target_valuation = krw_total * buy_ratio  # Use the buy ratio for target valuation
                    shortfall = target_valuation - current_valuation

                    if shortfall >= 5000:  # Only proceed if the shortfall is at least 5,000 KRW
                        amount_to_buy = shortfall / best_ask
                        buy_price = best_ask

                        # Fetch the latest balance to update krw_free
                        balance = exchange.fetch_balance()
                        krw_free = balance['KRW']['free']
                        
                        # Recalculate amount_to_buy and buy_price based on available KRW
                        max_buy_amount = krw_free / buy_price
                        amount_to_buy = min(amount_to_buy, max_buy_amount*0.99)
                        
                        if krw_free < 5000:  # Skip buying if free KRW is less than 5,000
                            logger.info(f"[{symbol}] SKIP BUY: Not enough KRW (Available: {krw_free:,.2f} KRW, Needed: 5,000 KRW)")
                        else:
                            logger.info(f"[{symbol}] BUY: Placing limit buy order for {amount_to_buy:.6f} at {buy_price} KRW")
                            try:
                                exchange.create_order(symbol, 'limit', 'buy', amount_to_buy, buy_price)
                                logger.info(f"[{symbol}] BUY SUCCESS: Limit buy order placed for {amount_to_buy:.6f} at {buy_price} KRW", extra={'handler': trade_file_handler})
                            except Exception as e:
                                logger.error(f"[{symbol}] BUY ERROR: Failed to place buy order - {e}", extra={'handler': trade_file_handler})
                    else:
                        logger.info(f"[{symbol}] SKIP BUY: Shortfall ({shortfall:,.2f} KRW) is less than 5,000 KRW.")
                elif best_bid:
                    # Sell logic
                    if base_currency in balance and balance[base_currency]['free'] > 0:
                        amount_to_sell = balance[base_currency]['free']
                        sell_price = best_bid
                        logger.info(f"[{symbol}] SELL: Placing limit sell order for {amount_to_sell:.6f} at {sell_price} KRW")
                        try:
                            exchange.create_order(symbol, 'limit', 'sell', amount_to_sell, sell_price)
                            logger.info(f"[{symbol}] SELL SUCCESS: Limit sell order placed for {amount_to_sell:.6f} at {sell_price} KRW", extra={'handler': trade_file_handler})
                        except Exception as e:
                            logger.error(f"[{symbol}] SELL ERROR: Failed to place sell order - {e}", extra={'handler': trade_file_handler})
            except ccxt.RateLimitExceeded as e:
                logger.warning(f"[RATE-LIMIT] Rate limit exceeded while processing {symbol}. Waiting before retry...")
                time.sleep(1)  # Wait before retrying
                continue
            except Exception as e:
                logger.error(f"[{symbol}] ERROR: {e}")

    finally:
        logger.info("[END] Trading bot finished execution.")

if __name__ == "__main__":
    main()
