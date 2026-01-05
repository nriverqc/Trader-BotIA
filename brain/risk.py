def calculate_sl_tp(entry_price, atr, side):
    sl_distance = atr * 1.2
    tp_distance = sl_distance * 1.5

    if side == "LONG":
        stop_loss = entry_price - sl_distance
        take_profit = entry_price + tp_distance
    elif side == "SHORT":
        stop_loss = entry_price + sl_distance
        take_profit = entry_price - tp_distance
    else:
        return None, None

    return round(stop_loss, 2), round(take_profit, 2)
