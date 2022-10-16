def export_state_col(cars_in_order, state):
    from cmath import nan
    column = []
    state_order = [[],[],[],[],[],[],[]]
    for row in state_order:
        for col in state['parking_arr'][state_order.index(row)]:
            row.append(col.car_order)
    for i in range(len(cars_in_order)):
        if i in state_order[0]:
            column.append('6%d'%(10-i))
        elif i in state_order[1]:
            column.append('5%d'%(10-i))
        elif i in state_order[2]:
            column.append('7%d'%(10-i))
        elif i in state_order[3]:
            column.append('4%d'%(10-i))
        elif i in state_order[4]:
            column.append('3%d'%(10-i))
        elif i in state_order[5]:
            column.append('2%d'%(10-i))
        elif i in state_order[6]:
            column.append('1%d'%(10-i))
        elif i == state['receive_hold'].car_order:
            column.append('1')
        elif i == state['deliver_hold'].car_order:
            column.append('2')
        else:
            column.append(nan)
    return column