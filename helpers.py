import numpy as np
import pandas as pd
import datetime


def getMonthEnd(x: pd.Timestamp):
    return x + pd.offsets.BMonthEnd()


def getMonthBegin(x: pd.Timestamp):
    return x - pd.offsets.BMonthBegin()


def getNextMonthBegin(x: pd.Timestamp):
    return x + pd.offsets.BMonthBegin()


def getNextMonthEnd(x: pd.Timestamp):
    return x + getNextMonthBegin(x)