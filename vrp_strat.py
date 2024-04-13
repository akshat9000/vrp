import numpy as np
import pandas as pd
import datetime
import traceback

from tqdm import tqdm

from helpers import *
from params import netVal, cash_percentage


optChain = pd.read_csv("optionChainData.csv")

optChain["Date"] = pd.to_datetime(optChain["Date"], format="%d-%m-%Y")
optChain["Expiry_Date"] = pd.to_datetime(optChain["Expiry_Date"], format="%d-%m-%Y")


dateList = [pd.Timestamp(item) for item in sorted(optChain["Date"].unique())]

expiryDateList = [pd.Timestamp(item) for item in sorted(optChain["Expiry_Date"].unique())]



def getOrderBook():
    for dt in dateList:
        tdf = optChain[optChain["Date"] == dt]
        tdf = tdf.reset_index().drop(columns="index")
        yield tdf



class VRP:
    def __init__(self) -> None:
        try:
            self.invested = False
            self.portfolio = netVal
            self.cash_percentage = cash_percentage
            self.order_book = None
            self.available_balance = 0
            self.option_size = 100
            self.unused_balance = 0
            self.current_lots = 0
            self.strike = 0
            self.call_range = 0
            self.put_range = 0
            self.entry_time = None
            self.c_bid = None
            self.p_bid = None
            self.call_delta = None
            self.put_delta = None
            self.pf_delta = None
            self.end_of_month = pd.Timestamp(year=1900, month=1, day=1)
            self.next_month_begin = pd.Timestamp(year=1900, month=1, day=1)
            self.expiry_date = pd.Timestamp(year=1900, month=1, day=1)
            self.expiry_date_list = None
            self.exit_time = None
            self.entry_trades = pd.DataFrame()
            self.exit_trades = pd.DataFrame()
            self.reldf = None
        except Exception as e:
            print(f"ERROR IN INITIALIZING VRP CLASS: \n\t{str(e)}\n")
            traceback.print_exc()
            exit()
        
        return None
    

    def get_MonthEnd(self) -> None:
        self.end_of_month = getMonthEnd(self.entry_time)
        return None
    

    def get_NextMonthBegin(self) -> None:
        self.next_month_begin = getNextMonthBegin(self.entry_time)
        return None
    

    def getMonthExpiry(self):
        # end_of_month = getMonthEnd(self.entry_time)

        for i in range(len(self.expiry_date_list)):
            if self.end_of_month == self.expiry_date_list[i]:
                return self.expiry_date_list[i]
            elif self.end_of_month < self.expiry_date_list[i]:
                return self.expiry_date_list[i-1]
            else:
                pass
        
        return None
    

    def calculateDelta(self):
        c_delta = self.reldf.at[self.reldf["Strike_Dist"].argmin(), "C_Delta"]
        p_delta = self.reldf.at[self.reldf["Strike_Dist"].argmin(), "P_Delta"]

        self.call_delta = self.current_lots * self.option_size * c_delta * (-1)
        self.put_delta = self.current_lots * self.option_size * p_delta * (-1)

        self.pf_delta = self.put_delta - self.call_delta
        return None
    

    def hedge(self):
        if self.pf_delta < 0:
            buy_vix = self.pf_delta * self.reldf.at[self.reldf["Strike_Dist"].argmin(), "VIX_Close"]
            self.portfolio -= buy_vix
            return None
        elif self.pf_delta > 0:
            sell_vix = self.pf_delta * self.reldf.at[self.reldf["Strike_Dist"].argmin(), "VIX_Close"]
            self.portfolio += sell_vix
            return None
        else:
            return None
    

    def main(self) -> None:
        for idx, order_book in enumerate(getOrderBook()):
            self.entry_time = pd.Timestamp(order_book["Date"].unique()[0])
            self.end_of_month = self.get_MonthEnd()
            self.next_month_begin = self.get_NextMonthBegin()
            self.expiry_date_list = sorted([pd.Timestamp(item) for item in order_book["Expiry_Date"].unique()])
            self.expiry_date = self.getMonthExpiry()
            self.reldf = order_book[order_book["Expiry_Date"] == self.expiry_date]

            if self.entry_time < self.expiry_date and self.entry_time < self.end_of_month:
                # TODO: ADD LOGIC FOR ENTRY AND DELTA CALCULATION + HEDGING
                if not self.invested:
                    self.strike = self.reldf.at[self.reldf["Strike_Dist"].argmin(), "Strike"]
                    self.available_balance = int(self.portfolio * (1 - self.cash_percentage))
                    # self.unused_balance = self.portfolio - self.available_balance
                    self.c_bid = self.reldf.at[self.reldf["Strike_Dist"].argmin(), "C_Bid"]
                    self.p_bid = self.reldf.at[self.reldf["Strike_Dist"].argmin(), "P_Bid"]

                    self.call_range = self.strike + self.c_bid
                    self.put_range = self.strike - self.p_bid
                    # c_delta = self.reldf.at[self.reldf["Strike_Dist"].argmin(), "C_Delta"]
                    # p_delta = self.reldf.at[self.reldf["Strike_Dist"].argmin(), "P_Delta"]
                    self.current_lots = int((self.available_balance / (self.c_bid + self.p_bid)) / self.option_size)

                    premium_collected = self.option_size * ((self.current_lots * self.c_bid) + (self.current_lots * self.p_bid))
                    self.portfolio += premium_collected

                    self.calculateDelta()
                    self.hedge()

                    self.invested = True
                    
                else:
                    self.calculateDelta()
                    self.hedge()
            elif self.entry_time == self.expiry_date:
                # TODO: ADD LOGIC FOR SQUARING OFF
                vix_close = self.reldf.at[0, "VIX_Close"]
                if vix_close > self.call_range:
                    # CALL EXERCISED -> CALCULATE LOSS + HEDGE
                    self.invested = False
                elif vix_close < self.put_range:
                    # PUT EXERCISED -> CALCULATE LOSS + HEDGE
                    self.invested = False
                else:
                    # DO NOTHING -> PREMIUM ALREADY COLLECTED
                    self.invested = False
            elif self.expiry_date < self.entry_time <= self.end_of_month:
                # PORTFOLIO IDLE
                pass
            else:
                # CONDITION NEVER REACHED
                pass






if __name__ == "__main__":
    bot = VRP()
    bot.main()