import numpy as np

from SimpleVWAP import SimpleVWAP
import pandas as pd
import matplotlib.pyplot as plt

symbol = 'AAPL'
window_size = 1
leverage = 200
lot_size = 1
initial_money = 10000
initial_imm = 1000
unit = 1000
reward = 10
rv = 2
risk = -5


trader = SimpleVWAP(symbol=symbol, window_size=window_size, leverage=leverage,
                    lot_size=lot_size, initial_money=initial_money,
                    initial_imm=initial_imm,
                    unit=unit,
                    rv = rv,
                    reward=reward,
                    risk=risk)


df = pd.read_csv('IB_INFO_AAPL.CSV', delimiter=',')

df.columns = ['price', 'bid', 'ask', 'volume', 'date']


#
# print(df[350:400])
df_values = df.values[:374]






# print(len(df_values))
#
for idx, item in enumerate(df_values):


    print(f'step={idx}')


    trader.update_data(
        item[0],
        item[2],
        item[1],
        item[3],
    )

    trader.trade(len(trader.price_list) - 1)

    print(f'action = {trader.action}')
    print(f'profit = {trader.profit_track[-1]}')
    print(f'have_bought: {trader.have_bought}')
    print(f'have_sold: {trader.have_sold}')
    print(f'reward={trader.reward}')
    print(f'risk={trader.risk}')
    print(f'docheckfor: {trader.DoCheckFor}')
    print(f'crv: {trader.crv}')
    print('----------------------------------------')


abs_vwap = []


for idx in range(len(trader.price_list)):

    spv = np.sum([p*v for p, v in zip(trader.price_list[:idx], trader.volume_list[:idx])])
    sv = np.sum(trader.volume_list[:idx])
    abs_vwap.append(spv/sv)




fig, axs = plt.subplots(5)


print(len(trader.crv_list))
axs[0].plot(range(len(trader.price_list)),trader.price_list, color='black')
axs[0].plot(range(len(abs_vwap)),abs_vwap, color='blue')
axs[0].scatter([i for i in trader.go_long_indexes], [trader.price_list[i] for i in trader.go_long_indexes], color='red')
axs[0].scatter([i for i in trader.close_long_indexes], [trader.price_list[i] for i in trader.close_long_indexes], color='cyan')
axs[0].scatter([i for i in trader.stop_index], [trader.price_list[i] for i in trader.stop_index], color='purple')


axs[1].plot(range(len(trader.price_list)),trader.price_list, color='black')
axs[1].plot(range(len(abs_vwap)),abs_vwap, color='blue')
axs[1].scatter([i for i in trader.go_short_indexes], [trader.price_list[i] for i in trader.go_short_indexes], color='green')
axs[1].scatter([i for i in trader.close_short_indexes], [trader.price_list[i] for i in trader.close_short_indexes], color='pink')
axs[1].scatter([i for i in trader.stop_index], [trader.price_list[i] for i in trader.stop_index], color='purple')
axs[2].plot(range(len(trader.profit_track)), trader.profit_track)


axs[3].plot(range(len(trader.crv_list)), trader.crv_list)

axs[4].plot(range(len(trader.volume_list)), trader.volume_list)
plt.show()
