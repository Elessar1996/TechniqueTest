import numpy as np
import MetaTrader5 as mt5
import time


class SimpleVWAP:


    def __init__(self, symbol, window_size=3, leverage=1, lot_size=1.0,
                 initial_money=10000, rv=1, initial_imm=1000, unit=1, reward=5, risk=-5 ,abs_vwap=[], angle_list=[], price_list=[], volume_list=[],
                 bid_list=[], ask_list=[], softened_signal=[]):
        self.initial_imm = initial_imm
        self.unit = unit
        self.softened_signal = softened_signal
        self.symbol = symbol.upper()
        self.leverage = leverage
        self.initial_money = initial_money
        self.lot_size = lot_size
        self.price_list = price_list
        self.volume_list = volume_list
        self.angle_list = angle_list
        self.bid_list = bid_list
        self.ask_list = ask_list
        self.first_time = True
        self.current_money = initial_money
        self.window_size = window_size
        self.abs_vwap = abs_vwap
        self.property_track = [self.initial_money]
        self.profit_track = [0]
        self.have_bought = False
        self.have_sold = False
        self.total_shares = 0
        self.margin = None
        self.free_margin = None
        self.is_dynamic = True
        self.unit_list = [unit]
        self.total_reward = 0
        self.action = None
        self.go_long_indexes = []
        self.close_long_indexes = []
        self.go_short_indexes = []
        self.close_short_indexes = []
        self.stop_index = []
        self.first_time = True
        self.risk = 1 * risk
        self.reward = reward
        self.bleeding_flag = False
        self.stop_loss = False
        self.take_reward = False
        self.reward_flag = False
        self.DoCheckFor = True
        self.plot_softened_signal = []
        self.plot_abs_vwap = []
        self.general_average = None
        self.partial_average = None
        self.general_average_list = []
        self.partial_average_list = []
        self.rv = rv
        self.crv = float('-inf')
        self.crv_list = [-1 for _ in range(10)]

        self.initial_vwap_calculation()

    def initial_vwap_calculation(self):

        if len(self.price_list) != 0:
            sum_v = 0
            sum_pv = 0
            for p, v in zip(self.price_list, self.volume_list):

                sum_pv += p*v
                sum_v += v

                self.abs_vwap.append(sum_pv/sum_v)
            self.initial_window_vwap()

    def initial_window_vwap(self):

        for idx, item in enumerate(self.price_list):

            if idx + 1 < self.window_size:
                self.window_vwap.append(self.price_list[idx])
            else:
                sum_vol = np.sum(self.volume_list[idx - self.window_size: idx])
                sum_vxp = np.sum([i * j for i, j in zip(self.volume_list[idx - self.window_size:idx],
                                                        self.price_list[idx - self.window_size:idx])])

                self.window_vwap.append(sum_vxp / sum_vol)

    def calculate_unit(self, price):
        unit = self.leverage * self.initial_imm / price
        print(f'unit is {unit}')
        return self.leverage * self.initial_imm / price

    def create_long_request(self):
        symbol_info_tick = mt5.symbol_info_tick(self.symbol)
        point = mt5.symbol_info(self.symbol).point
        deviation = 20
        bid_price = symbol_info_tick.bid
        unit = self.calculate_unit(bid_price)
        print(f'unit = {unit}')

        volume = np.ceil(unit * self.lot_size)

        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": self.symbol,
            "volume": volume,
            "type": mt5.ORDER_TYPE_BUY,
            "price": bid_price,
            "sl": bid_price - 100 * point,
            "tp": bid_price + 100 * point,
            "deviation": deviation,
            "magic": 234000,
            "comment": "python script open",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_FOK,
        }

        return request

    def create_short_request(self):
        symbol_info_tick = mt5.symbol_info_tick(self.symbol)
        # point = mt5.symbol_info(self.symbol).point
        deviation = 20
        ask_price = symbol_info_tick.ask
        unit = self.calculate_unit(ask_price)
        print(f'unit = {unit}')
        volume = np.ceil(unit * self.lot_size)

        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": self.symbol,
            "volume": volume,
            "type": mt5.ORDER_TYPE_SELL,
            "price": ask_price,
            # "sl": ask_price - 100 * point,
            # "tp": ask_price + 100 * point,
            "deviation": deviation,
            "magic": 234000,
            "comment": "python script open",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_FOK,
        }

        return request

    def close_position(self):

        print('closing position')

        all_positions = mt5.positions_get()
        position = all_positions[0]
        deviation = 20
        tick = mt5.symbol_info_tick(position.symbol)
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "position": position.ticket,
            "symbol": position.symbol,
            "volume": position.volume,
            "type": mt5.ORDER_TYPE_BUY if position.type == 1 else mt5.ORDER_TYPE_SELL,
            "price": tick.ask if position.type == 1 else tick.bid,
            "deviation": deviation,
            "magic": 234000,
            "comment": "close open positions",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_FOK
        }

        result = mt5.order_send(request)

        time.sleep(2)

        if result.retcode != mt5.TRADE_RETCODE_DONE:
            print("2. order_send failed, retcode={}".format(result.retcode))
            # request the result as a dictionary and display it element by element
            result_dict = result._asdict()
            for field in result_dict.keys():
                print("   {}={}".format(field, result_dict[field]))
                # if this is a trading request structure, display it element by element as well
                if field == "request":
                    traderequest_dict = result_dict[field]._asdict()
                    for tradereq_filed in traderequest_dict:
                        print("       traderequest: {}={}".format(tradereq_filed, traderequest_dict[tradereq_filed]))
        print("2. order_send done, ", result)

    def go_short_real(self):

        print('going short')
        request = self.create_short_request()
        result = mt5.order_send(request)
        print(f'result: {result}')
        time.sleep(2)

        print(
            "1. order_send(): by {} {} lots at {} .format(self.symbol, self.lot_size"
        )
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            print("2. order_send failed, retcode={}".format(result.retcode))
            # request the result as a dictionary and display it element by element
            result_dict = result._asdict()
            for field in result_dict.keys():
                print("   {}={}".format(field, result_dict[field]))
                # if this is a trading request structure, display it element by element as well
                if field == "request":
                    traderequest_dict = result_dict[field]._asdict()
                    for tradereq_filed in traderequest_dict:
                        print("       traderequest: {}={}".format(tradereq_filed, traderequest_dict[tradereq_filed]))
        print("2. order_send done, ", result)
        print("   opened position with POSITION_TICKET={}".format(result.order))

    def go_long_real(self):

        print('going long')
        request = self.create_long_request()
        result = mt5.order_send(request)

        print(f'result: {result}')
        time.sleep(2)
        print(
            "1. order_send(): by {} {} lots ".format(self.symbol, self.lot_size,
                                                     ))
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            print("2. order_send failed, retcode={}".format(result.retcode))
            # request the result as a dictionary and display it element by element
            result_dict = result._asdict()
            for field in result_dict.keys():
                print("   {}={}".format(field, result_dict[field]))
                # if this is a trading request structure, display it element by element as well
                if field == "request":
                    traderequest_dict = result_dict[field]._asdict()
                    for tradereq_filed in traderequest_dict:
                        print("       traderequest: {}={}".format(tradereq_filed, traderequest_dict[tradereq_filed]))
        print("2. order_send done, ", result)
        print("   opened position with POSITION_TICKET={}".format(result.order))


    def update_data(self, price, ask, bid, volume):

        self.price_list.append(price)
        self.ask_list.append(ask)
        self.bid_list.append(bid)
        self.volume_list.append(volume)

    def calculate_vwap(self, idx):

        sum_v = np.sum(self.volume_list[:idx])
        sum_vxp = np.sum([i * j for i, j in zip(self.price_list[:idx], self.volume_list[:idx])])
        self.abs_vwap.append(sum_vxp / sum_v)

    def calculate_window_vwap(self, idx):

        if idx + 1 < self.window_size:
            self.softened_signal.append(self.price_list[idx])
        else:
            sum_vol = np.sum(self.volume_list[idx - self.window_size: idx])
            sum_vxp = np.sum([i * j for i, j in zip(self.volume_list[idx - self.window_size:idx],
                                                    self.price_list[idx - self.window_size:idx])])

            self.softened_signal.append(sum_vxp / sum_vol)

    def calculate_profit(self, idx):

        if idx == 0:
            return 0
        else:
            return ((self.property_track[-1] - self.initial_money) / self.initial_money) * 100

    def calculate_money(self, idx):
        if not self.have_bought and not self.have_sold:
            return self.current_money
        elif self.have_bought and not self.have_sold:
            m = self.bid_list[
                    idx] * self.total_shares - self.margin * self.leverage + self.free_margin + self.margin
            return m
        elif self.have_sold and not self.have_bought:
            m = -1 * self.ask_list[
                idx] * self.total_shares + self.margin * self.leverage + self.margin + self.free_margin
            return m

        else:
            raise Exception("Something is seriously wrong with algo")



    def unit_updater(self):

        if self.is_dynamic:
            diff = self.property_track[-1] - self.property_track[-2]
            change = diff / 10000
            self.unit += change
            self.unit = 100 if self.unit > 100 else self.unit
            self.unit = 0.01 if self.unit < 0.01 else self.unit
            self.unit_list.append(self.unit)

    def hold(self, idx):

        self.property_track.append(self.calculate_money(idx))
        self.profit_track.append(self.calculate_profit(idx))
        self.action = 'hold'

        return 'hold'
    def go_long(self, idx):

        self.margin = (self.unit * self.lot_size / self.leverage) * self.ask_list[idx]
        self.free_margin = self.current_money - self.margin
        self.total_shares += (self.margin * self.leverage / self.ask_list[idx])
        self.have_bought = True
        self.property_track.append(self.calculate_money(idx))
        self.profit_track.append(self.calculate_profit(idx))
        self.go_long_indexes.append(idx)
        self.action = 'go_long'

        self.go_long_real()

        return self.action

    def close_long(self, idx):

        self.have_bought = False
        self.current_money = self.bid_list[
                                 idx] * self.total_shares - self.margin * self.leverage + self.free_margin + self.margin
        self.total_shares = 0
        self.property_track.append(self.current_money)
        self.profit_track.append(self.calculate_profit(idx))
        self.close_long_indexes.append(idx)
        self.action = 'close_long'
        self.close_position()
        self.reset_memory(idx)
        return self.action

    def go_short(self, idx):

        self.margin = (self.unit * self.lot_size / self.leverage) * self.bid_list[idx]
        self.free_margin = self.current_money - self.margin
        self.total_shares = self.margin * self.leverage / self.bid_list[idx]

        self.have_sold = True
        self.go_short_indexes.append(idx)
        self.property_track.append(self.calculate_money(idx))
        self.profit_track.append(self.calculate_profit(idx))

        self.action = "go_short"
        self.go_short_real()
        return self.action

    def close_short(self, idx):

        self.have_sold = False
        self.current_money = -self.ask_list[
            idx] * self.total_shares + self.margin * self.leverage + self.margin + self.free_margin
        self.total_shares = 0

        self.property_track.append(self.current_money)
        self.profit_track.append(self.calculate_profit(idx))
        self.close_short_indexes.append(idx)
        self.action = "close_short"
        self.close_position()
        self.reset_memory(idx)
        return self.action

    def close_position(self, idx):

        if self.have_sold:
            self.close_short(idx)
        elif self.have_bought:
            self.close_long(idx)
        print(f'we are closing position!!')

    def check_profit(self, idx):
        print('we are in check profit')
        print(f' self.profit_track[-1]<= self.risk: { self.profit_track[-1]<= self.risk}')
        if len(self.profit_track) >= 1 and self.profit_track[-1] >= self.reward:

            self.close_position(idx)
            self.DoCheckFor = False
            return True
        if len(self.profit_track) >= 1 and self.profit_track[-1]<= self.risk:
            print(f'clooooooseeeeee')
            self.close_position(idx)
            self.DoCheckFor = False
            return True
        return False


    def calculate_rv(self, idx):


        if idx >= 10:

            # self.general_average = np.average(self.volume_list[:idx])
            self.partial_average = np.average(self.volume_list[idx - 10: idx])
            # self.general_average_list.append(self.general_average)
            # self.partial_average_list.append(self.partial_average)

            self.crv = self.volume_list[idx]/self.partial_average
            print(f'idx = {idx} --> rv={self.crv} partial_ave={self.partial_average} v={self.volume_list[idx]}')
            self.crv_list.append(self.crv)

    def check_for_volume(self):

        if self.crv >= self.rv:
            return True
        else:
            return False

    def calculate_unit(self, price):
        unit = self.leverage * self.initial_imm / price
        print(f'unit is {unit}')
        return self.leverage * self.initial_imm / price

    def create_long_request(self):
        symbol_info_tick = mt5.symbol_info_tick(self.symbol)
        point = mt5.symbol_info(self.symbol).point
        deviation = 20
        bid_price = symbol_info_tick.bid
        unit = self.calculate_unit(bid_price)
        print(f'unit = {unit}')

        volume = np.ceil(unit * self.lot_size)

        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": self.symbol,
            "volume": volume,
            "type": mt5.ORDER_TYPE_BUY,
            "price": bid_price,
            "sl": bid_price - 100 * point,
            "tp": bid_price + 100 * point,
            "deviation": deviation,
            "magic": 234000,
            "comment": "python script open",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_FOK,
        }

        return request

    def create_short_request(self):
        symbol_info_tick = mt5.symbol_info_tick(self.symbol)
        # point = mt5.symbol_info(self.symbol).point
        deviation = 20
        ask_price = symbol_info_tick.ask
        unit = self.calculate_unit(ask_price)
        print(f'unit = {unit}')
        volume = np.ceil(unit * self.lot_size)

        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": self.symbol,
            "volume": volume,
            "type": mt5.ORDER_TYPE_SELL,
            "price": ask_price,
            # "sl": ask_price - 100 * point,
            # "tp": ask_price + 100 * point,
            "deviation": deviation,
            "magic": 234000,
            "comment": "python script open",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_FOK,
        }

        return request

    def close_position(self):

        print('closing position')

        all_positions = mt5.positions_get()
        position = all_positions[0]
        deviation = 20
        tick = mt5.symbol_info_tick(position.symbol)
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "position": position.ticket,
            "symbol": position.symbol,
            "volume": position.volume,
            "type": mt5.ORDER_TYPE_BUY if position.type == 1 else mt5.ORDER_TYPE_SELL,
            "price": tick.ask if position.type == 1 else tick.bid,
            "deviation": deviation,
            "magic": 234000,
            "comment": "close open positions",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_FOK
        }

        result = mt5.order_send(request)

        time.sleep(2)

        if result.retcode != mt5.TRADE_RETCODE_DONE:
            print("2. order_send failed, retcode={}".format(result.retcode))
            # request the result as a dictionary and display it element by element
            result_dict = result._asdict()
            for field in result_dict.keys():
                print("   {}={}".format(field, result_dict[field]))
                # if this is a trading request structure, display it element by element as well
                if field == "request":
                    traderequest_dict = result_dict[field]._asdict()
                    for tradereq_filed in traderequest_dict:
                        print("       traderequest: {}={}".format(tradereq_filed, traderequest_dict[tradereq_filed]))
        print("2. order_send done, ", result)



    def reset_memory(self, idx):

        print(f'memory has been reseted at idx={idx}')
        self.plot_abs_vwap.extend(self.abs_vwap)
        self.plot_softened_signal.extend(self.softened_signal)
        self.abs_vwap = self.abs_vwap[-self.window_size:]
        self.softened_signal = self.softened_signal[-self.window_size:]



    def trade(self, idx):

        self.calculate_vwap(idx)
        self.calculate_window_vwap(idx)
        self.calculate_rv(idx)


        if self.DoCheckFor:
            r = self.check_profit(idx)
            if r:
                print("checking profit")
                return
        else:
            self.DoCheckFor = True

        if idx <= 10:
            self.hold(idx)
            return

        consecutive_action = False
        # if self.softened_signal[idx] > self.abs_vwap[idx]:
        if self.softened_signal[-1] > self.abs_vwap[-1]:

            if self.check_for_volume():
                if self.have_sold:
                    self.close_short(idx)
                    self.go_long(idx)
                    consecutive_action = True

                elif self.have_bought:
                    self.hold(idx)
                else:
                    self.go_long(idx)
                if consecutive_action:
                    self.profit_track.pop()
                    self.property_track.pop()
            else:
                self.hold(idx)

        # elif self.softened_signal[idx] < self.abs_vwap[idx]:
        if self.softened_signal[-1] < self.abs_vwap[-1]:
            if self.check_for_volume():

                if self.have_bought:
                    self.close_long(idx)
                    self.go_short(idx)
                    consecutive_action = True

                if self.have_sold:
                    self.hold(idx)
                else:

                    self.go_short(idx)

                if consecutive_action:
                    self.profit_track.pop()
                    self.property_track.pop()
            else:
                self.hold(idx)
        else:
            self.hold(idx)

            print(f'at idx={idx} after all is done, profit is {self.profit_track[-1]}')
            print(f'have_bought={self.have_bought}')
            print(f'have_sold={self.have_sold}')

