import pandas as pd

ID = 0

def getMonthEnd(x: pd.Timestamp):
    return x + pd.offsets.BMonthEnd()


def getMonthBegin(x: pd.Timestamp):
    return x - pd.offsets.BMonthBegin()


def getNextMonthBegin(x: pd.Timestamp):
    return x + pd.offsets.BMonthBegin()


def get3MonthEnd(x: pd.Timestamp):
    t = x + pd.offsets.MonthEnd(3)
    if t.weekday() == 6:
        return t - pd.Timedelta(2, unit='D')
    elif t.weekday() == 5:
        return t - pd.Timedelta(1, unit='D')
    else:
        return t


def get4MonthBegin(x: pd.Timestamp):
    t = x + pd.offsets.MonthBegin(3)
    if t.weekday() == 6:
        return t + pd.Timedelta(1, unit='D')
    elif t.weekday() == 5:
        return t + pd.Timedelta(2, unit='D')
    else:
        return t
    

def idGenerate():
    ID += 1
    return ID


def resetID():
    ID = 0
    return None
