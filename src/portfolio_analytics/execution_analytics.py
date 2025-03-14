import datetime
import pandas as pd
import schedule

class ExecutionSummary:
    """
    Handles periodic summary updates of execution performance.
    """

    def __init__(self, trade_log="trade_log.csv", summary_file="execution_summary.csv"):
        self.trade_log = trade_log
        self.summary_file = summary_file

    def update_summary(self):
        """
        Reads the trade log, aggregates execution statistics,
        and updates a summary file every hour.
        """
        try:
            df = pd.read_csv(self.trade_log)

            # Convert timestamps to datetime format
            df["Timestamp"] = pd.to_datetime(df["Timestamp"])

            # Filter last 1 hour of trades
            one_hour_ago = datetime.now() - pd.Timedelta(hours=1)
            df = df[df["Timestamp"] > one_hour_ago]

            if df.empty:
                print("[INFO] No new trades in the last hour.")
                return

            # Calculate average slippage, execution price, and spreads
            summary = {
                "Timestamp": datetime.now(),
                "Total Trades": len(df),
                "Avg Estimated Slippage (%)": df["Estimated Slippage (%)"].mean(),
                "Avg Actual Slippage (%)": df["Actual Slippage (%)"].mean(),
                "Avg Execution Price": df["Execution Price"].mean(),
            }

            # Append to summary file
            summary_df = pd.DataFrame([summary])
            summary_df.to_csv(self.summary_file, mode="a", header=not pd.io.common.file_exists(self.summary_file), index=False)

            print(f"[SUMMARY] Execution summary updated at {datetime.now()}")

        except Exception as e:
            print(f"[ERROR] Failed to update summary: {e}")

# Example Usage
# Schedule hourly updates
# execution_summary = ExecutionSummary()
# schedule.every().hour.do(execution_summary.update_summary)
