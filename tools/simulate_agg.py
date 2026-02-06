import sys
import os
import datetime

# ensure project root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from tools.aggregator import aggregate_votes

prediction = "Bitcoin will reach $100,000 by December 31, 2026"
criteria = "Check coinmarketcap.com for BTC price"
deadline = datetime.datetime.fromisoformat('2026-12-31T23:59:59')
res = aggregate_votes(prediction, criteria, deadline, validators=5)
print(res)
