##Börja testa ML här 
from database.queryTool import fetch_and_return_data
import matplotlib.pyplot as plt
import pandas as pd

def plot_workload(df):
  #  df = df.set_index('time')
    plt.plot(df.index, df['method_count'])
    plt.show()

if __name__ == "__main__":
    df = fetch_and_return_data("1998-05", "60s")
    plot_workload(df)

    print("hej")