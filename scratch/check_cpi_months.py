import pandas as pd
import numpy as np
from backend.config import settings

cpi = pd.read_csv(settings.CPI_BENCHMARK_PATH)
print("CPI months count:", len(cpi))
for _, r in cpi.head(10).iterrows():
    print(f"{r['year']}-{r['month']}: index={r['index']}, inflation={r['inflation']}%")
