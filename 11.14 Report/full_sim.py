import historical_sim as hs
import pandas as pd
import datetime

dates = list(pd.date_range(datetime.datetime(2020,7,1), datetime.datetime(2020,7,31)).to_pydatetime())
for date in dates:
    hs.simulate(str(date.date()))