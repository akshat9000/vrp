import numpy as np
import pandas as pd
import datetime
import traceback

from tqdm import tqdm

from helpers import *
from params import netVal, cash_percentage



"""
v1
optChain = pd.read_csv("optionChainData.csv")

optChain["Date"] = pd.to_datetime(optChain["Date"], format="%d-%m-%Y")
optChain["Expiry_Date"] = pd.to_datetime(optChain["Expiry_Date"], format="%d-%m-%Y")


dateList = [pd.Timestamp(item) for item in sorted(optChain["Date"].unique())]

expiryDateList = [pd.Timestamp(item) for item in sorted(optChain["Expiry_Date"].unique())]
"""
# File now stored as HDF5 format
optChain = pd.read_hdf("optionDataClean.h5")
dateList = [item for item in sorted(optChain["Date"].unique())]
expiryDateList = [item for item in sorted(optChain["Expiry_Date"].unique())]


def getOrderBook():
    for dt in dateList:
        tdf = optChain[optChain["Date"] == dt]
        tdf = tdf.reset_index().drop(columns="index")
        yield tdf


class Queue:
    def __init__(self):
        self.queue = []
        return None
    
    def enqueue(self, item):
        self.queue.append(item)
        return None
    
    def dequeue(self, id=None):
        if id == None:
            if len(self.queue) > 0:
                t = self.queue.pop(0)
                return t
            else:
                raise Exception("Queue is Empty")
        else:
            _arg = None
            for i in range(len(self.queue)):
                if id == self.queue[i].id:
                    _arg = self.queue.index(self.queue[i])  # Unnecessary but idc
            if _arg is not None:
                t = self.queue.pop(_arg)
                return t
            else:
                raise Exception("ID doesn't exist in Queue")
    
    def peak(self, ln=1):
        if len(self.queue) > 0:
            return self.queue[:ln+1]
        else:
            raise Exception("Queue is Empty!")
    

    def items(self):
        if len(self.queue) > 0:
            for i in range(len(self.queue)):
                yield self.queue[i]
        else:
            raise Exception("Queue is Empty!")
        
    def sortQueue(self):
        return sorted(self.queue, key = lambda x: x.entry_time)



class Straddle:
    def __init__(self, _id, entry_time, expiry_time, strike, c_bid, c_ask, p_bid, p_ask, lots, option_size=100):
        self.id = _id
        self.entry_time = entry_time
        self.expiry_time = expiry_time
        self.strike = strike
        self.c_bid = c_bid
        self.c_ask = c_ask
        self.p_bid = p_bid
        self.p_ask = p_ask
        self.lots = lots
        self.trade_value = (c_bid + p_bid) * self.lots * option_size
        return None



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
            self.c_bid = 0
            self.p_bid = 0
            self.c_ask = 0
            self.p_ask = 0
            self.call_delta = None
            self.put_delta = None
            self.pf_delta = None
            self.ids = []
            self.q = Queue()
            self.end_of_3month = pd.Timestamp(year=1900, month=1, day=1)
            self.next_4month_begin = pd.Timestamp(year=1900, month=1, day=1)
            self.expiry_date = pd.Timestamp(year=1900, month=1, day=1)
            self.expiry_date_list = None
            self.past_expiry_list = []
            self.exit_time = None
            self.entry_trades = pd.DataFrame()
            self.exit_trades = pd.DataFrame()
            self.reldf = None
        except Exception as e:
            print(f"ERROR IN INITIALIZING VRP CLASS: \n\t{str(e)}\n")
            traceback.print_exc()
            exit()
        return None
    

    def get_3MonthEnd(self) -> None:
        self.end_of_month = get3MonthEnd(self.entry_time)
        return None
    

    def get_4MonthBegin(self) -> None:
        self.next_4month_begin = get4MonthBegin(self.entry_time)
        return None
    

    def get3MonthExpiry(self):
        for i in range(len(self.expiry_date_list)):
            if self.end_of_3month == self.expiry_date_list[i]:
                return self.expiry_date_list[i]
            elif self.end_of_3month < self.expiry_date_list[i]:
                return self.expiry_date_list[i-1]
            else:
                pass
        return None
    

    def main(self) -> None:
        for idx, order_book in enumerate(getOrderBook()):
            self.entry_time = pd.Timestamp(order_book["Date"].unique()[0])
            self.end_of_3month = self.get_3MonthEnd()
            self.next_4month_begin = self.get_4MonthBegin()
            self.expiry_date_list = sorted(order_book["Expiry_Date"].unique())
            self.expiry_date = self.get3MonthExpiry()
            self.reldf = order_book[order_book["Expiry_Date"] == self.expiry_date]

            min_strike_dist = self.reldf['Strike_Dist'].argmin()

            if self.expiry_date in self.past_expiry_list:
                # TRAVERSE QUEUE, MARK TO MARKET FOR EACH, SQUARE OFF IF EXPIRY REACHED, IF INVESTED
                if self.invested:
                    for conts in self.q.items():
                        s_expiry_time = self.entry_time
                        if s_expiry_time < self.entry_time:
                            # TODO: ADD LOGIC TO DEQUEUE USING ID -> Done
                            t = self.q.dequeue(conts.id)
                            continue    # Continue or Pass?
                        else:
                            if s_expiry_time == self.entry_time:
                                # SQUARE OFF POSITION, MARK TO MARKET, HEDGE, DEQUEUE CONTRACT
                                pass
                            else:
                                # MARK TO MARKET, HEDGE
                                pass
                else:
                    # MARK TO MARKET OTHER TRADES OR SIT IDLE
                    pass
            else:
                self.past_expiry_list.append(self.expiry_date)
                # LOGIC TO SELL STRADDLE AND HEDGE FOR FIRST TIME EXPIRY DATE
                strike = self.reldf.at[min_strike_dist, 'Strike']
                c_bid = self.reldf.at[min_strike_dist, 'C_Bid']
                c_ask = self.reldf.at[min_strike_dist, 'C_Ask']
                p_bid = self.reldf.at[min_strike_dist, 'P_Bid']
                p_ask = self.reldf.at[min_strike_dist, 'P_Ask']
                c_delta = self.reldf.at[min_strike_dist, 'C_Delta']
                p_delta = self.reldf.at[min_strike_dist, 'P_Delta']
                







if __name__ == "__main__":
    bot = VRP()
    bot.main()