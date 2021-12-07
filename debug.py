# %%
from sklearn import datasets
import pandas as pd

df = pd.DataFrame(datasets.load_iris())

# %%
df
# %%
df.to_csv("test/iris.csv")
# %%
