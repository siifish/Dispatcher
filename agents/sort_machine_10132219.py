

class SortMachine2():
    def __init__(self):
        self.machine_state=[0,-1]
        self.carclass_to_lanposition=[[1,0,6],[5],[4]]
        self.receive_state=[0,0]
        self.out_fire_num=0 
        self.lanposition_to_target=[0,1,-1,2,3,4,5]
        self.out_fourpower_num=-3

    def take_action(self,state):

        next_car=state['next_car']
        parking_arr=state['parking_arr']
        cars_out_order=state['cars_out_order']
        
        
        lanposition_to_target=[0,1,-1,2,3,4,5] #对于返回道返回的是-1，可以注意一下
        
        if state['which_to_chose']==0:#当前接车横移机操作
            
            if self.is_class_lane_full(2,parking_arr) and self.is_class_lane_full(1,parking_arr):
                self.machine_state[0]=1 
            if next_car==-1:
                return [0,-1]
            if self.machine_state[0]==1:#进入正常状态
                is_full=True
                for lane_position in self.carclass_to_lanposition[next_car]:#判断车型的每个车道有没有满                   
                    for j in range(10):
                        if parking_arr[lane_position][j]==-1:
                            is_full=False
                            break
                        if is_full:break
                
                if is_full:#如果当前车型的车道满了
                    if parking_arr[3,0]!=-1:               
                        return [0,-1]
                    else:    
                        return [0,2]
                else:#如果当前车型的车道没有满，将车放到对应车道中，要是有多个空闲车道的话就找个最近的
                    if len(self.carclass_to_lanposition[next_car])==1:#当前车型只有一个选择车道
                        return [0,lanposition_to_target[self.carclass_to_lanposition[next_car][0]]]
                    else: #当前车型有多个选择车道
                        #寻找空闲车道
                        free_lane_position=[]
                        for lane_position in self.carclass_to_lanposition[next_car]:
                            #判断这个车道有没有满，如果没有满就在free_lan_position上加上
                            for j in range(10):
                                if parking_arr[lane_position][j]==-1:
                                    free_lane_position.append(lane_position)
                                    break
                        
                        #寻找最优空闲车道并插入
                        distance_list=[abs(i-3) for i in free_lane_position]
                        position_index=distance_list.index(min(distance_list))
                        return [0,lanposition_to_target[free_lane_position[position_index]]]
            else:#进入不正常状态
                if self.is_empty(parking_arr,3):#主车道空
                    if next_car==1:
                        return [0,2]
                    else:#放到类型2的车道里
                        if len(self.carclass_to_lanposition[next_car])==1:#当前车型只有一个选择车道
                            return [0,lanposition_to_target[self.carclass_to_lanposition[next_car][0]]]
                        else: #当前车型有多个选择车道
                            #寻找空闲车道
                            free_lane_position=[]
                            for lane_position in self.carclass_to_lanposition[next_car]:
                                #判断这个车道有没有满，如果没有满就在free_lan_position上加上
                                for j in range(10):
                                    if parking_arr[lane_position][j]==-1:
                                        free_lane_position.append(lane_position)
                                        break
                            
                            #寻找最优空闲车道并插入
                            distance_list=[abs(i-3) for i in free_lane_position]
                            position_index=distance_list.index(min(distance_list))
                            return [0,lanposition_to_target[free_lane_position[position_index]]]
                else:#主车道有车
                    #判断当前车型对应车道是否满
                    is_full=True
                    for lane_position in self.carclass_to_lanposition[next_car]:
                        #判断车型的每个车道有没有满
                        for j in range(10):
                            if parking_arr[lane_position][j]==-1:
                                is_full=False
                                break
                        if is_full:break
                    
                    if is_full:#如果当前车型的车道满了
                        return [0,2]
                    else:#如果当前车型的车道没有满，将车放到对应车道中，要是有多个空闲车道的话就找个最近的
                        if len(self.carclass_to_lanposition[next_car])==1:#当前车型只有一个选择车道
                            return [0,lanposition_to_target[self.carclass_to_lanposition[next_car][0]]]
                        else: #当前车型有多个选择车道
                            #寻找空闲车道
                            free_lane_position=[]
                            for lane_position in self.carclass_to_lanposition[next_car]:
                                #判断这个车道有没有满，如果没有满就在free_lan_position上加上
                                for j in range(10):
                                    if parking_arr[lane_position][j]==-1:
                                        free_lane_position.append(lane_position)
                                        break
                            
                            #寻找最优空闲车道并插入
                            distance_list=[abs(i-3) for i in free_lane_position]
                            position_index=distance_list.index(min(distance_list))
                            return [0,lanposition_to_target[free_lane_position[position_index]]]

        else:#当前送车横移机操作              
            if self.machine_state[0]==0:
                return[1,2]
             #判断是不是只剩下对应数量的车辆
            if len(cars_out_order)==253: #神秘数字253\261
                self.machine_state[1]=1              
            if self.machine_state[1]==-1 and (not self.is_empty(parking_arr,3)):
                self.machine_state[1]=0
                return [1,2]
            #判断停车区还有没有四驱车
            if self.is_class_lane_empty(0,parking_arr):
                    self.out_fire_num=0
                    self.machine_state[1]=0
            #判断停车区够不够进入四驱状态
            if self.machine_state[1]==0:
                if self.out_fire_num==0:
                    if self.main_closest_to_deliver(parking_arr)==2:
                        self.out_fire_num+=1
                    elif self.is_empty(parking_arr,3) and (not self.is_empty(parking_arr,self.carclass_to_lanposition[1][0])):
                        return [1,lanposition_to_target[self.carclass_to_lanposition[1][0]]]
                    elif self.is_empty(parking_arr,3) and (not self.is_empty(parking_arr,self.carclass_to_lanposition[2][0])):
                        return [1,lanposition_to_target[self.carclass_to_lanposition[2][0]]]
                    return [1,2]
                elif self.out_fire_num==1:
                    if self.main_closest_to_deliver(parking_arr)==2:
                        self.out_fire_num+=1
                        return [1,2]
                    elif self.main_closest_to_deliver(parking_arr)==1 and (not self.is_empty(parking_arr,self.carclass_to_lanposition[2][0])):
                        self.out_fire_num+=1
                        return [1,lanposition_to_target[self.carclass_to_lanposition[2][0]]]
                    else:
                        self.out_fire_num=0
                        return [1,2]
                elif self.out_fire_num==2:
                    if self.main_closest_to_deliver(parking_arr)==1:
                        self.out_fire_num=0
                        return [1,2]
                    elif self.main_closest_to_deliver(parking_arr)==2 and (not self.is_empty(parking_arr,self.carclass_to_lanposition[1][0])):
                        self.out_fire_num=0
                        return [1,lanposition_to_target[self.carclass_to_lanposition[1][0]]]
                    elif self.is_empty(parking_arr,3) and (not self.is_empty(parking_arr,self.carclass_to_lanposition[1][0])):
                        self.out_fire_num=0
                        return [1,lanposition_to_target[self.carclass_to_lanposition[1][0]]]
                    elif self.is_empty(parking_arr,3) and self.is_empty(parking_arr,self.carclass_to_lanposition[1][0]):
                        return [1,lanposition_to_target[self.carclass_to_lanposition[2][0]]]
                    else:
                        return [1,2]
                else:
                    raise ValueError('out_fire_num没这种情况啊？！')
            elif self.machine_state[1]==1:
                if self.out_fourpower_num==-3:
                    self.out_fourpower_num+=1
                    return [1,self.nearest_fourpower_lane_target(parking_arr)]
                elif self.out_fourpower_num==-2:
                    self.out_fourpower_num+=1
                    return [1,self.nearest_fourpower_lane_target(parking_arr)]
                elif self.out_fourpower_num==-1:
                    self.out_fourpower_num+=1
                    if not self.is_empty(parking_arr,3):
                        return [1,2]
                    else:
                        return [1,self.lanposition_to_target[self.carclass_to_lanposition[1][0]]]
                    
                elif self.out_fourpower_num==0:
                    self.out_fourpower_num+=1

                    return [1,self.nearest_fourpower_lane_target(parking_arr)]
                elif self.out_fourpower_num==1:
                    self.out_fourpower_num+=1
                    if not self.is_empty(parking_arr,3) and self.main_closest_to_deliver(parking_arr)==2:
                        return [1,2]
                    else:    
                        return [1,self.lanposition_to_target[self.carclass_to_lanposition[2][0]]]
                elif self.out_fourpower_num==2:
                    self.out_fourpower_num+=1
                    if not self.is_empty(parking_arr,3) and self.main_closest_to_deliver(parking_arr)==1:
                        return [1,2]
                    else:
                        return [1,self.lanposition_to_target[self.carclass_to_lanposition[1][0]]]
                elif self.out_fourpower_num==3:
                    self.out_fourpower_num+=1
                    return [1,self.nearest_fourpower_lane_target(parking_arr)]
                elif self.out_fourpower_num==4:
                    self.out_fourpower_num+=1
                    return [1,self.nearest_fourpower_lane_target(parking_arr)]
                elif self.out_fourpower_num==5:
                    self.out_fourpower_num=0
                    if not self.is_empty(parking_arr,3) and self.main_closest_to_deliver(parking_arr)==1:
                        return [1,2]
                    else:
                        return [1,self.lanposition_to_target[self.carclass_to_lanposition[1][0]]]
            else:
                raise ValueError('也没别的情况啊？！')
    
    def is_full(self,parking_arr,lane_position):#判断车道是否有车
        is_full=True
        for j in range(10):
            if parking_arr[lane_position][j]==-1:
                is_full=False
                break
        return is_full

    def is_empty(self,parking_arr,lane_position):#判断车道是否空
        is_empty=True
        for j in range(10):
            if parking_arr[lane_position][j]!=-1:
                is_empty=False
                break
        return is_empty

    def num_car(self,parking_arr): #输出车厂内各种车型各有几辆
        num_car=[0,0,0]
        for i in range(7):
            for j in range(10):
                if parking_arr[i][j]==0:
                    num_car[0]+=1
                elif parking_arr[i][j]==1:
                    num_car[1]+=1
                elif parking_arr[i][j]==2:
                    num_car[2]+=1
        return num_car


    def is_class_lane_empty(self,class_car,parking_arr): #判断类型车道有没有车
        is_empty=True
        for lane_position in self.carclass_to_lanposition[class_car]:
            #判断车型的每个车道有没有车
            for j in range(10):
                if parking_arr[lane_position][j]!=-1:
                    is_empty=False
                    break
        return is_empty

    def is_class_lane_full(self,class_car,parking_arr): #判断类型车道有没有满
        is_full=True
        for lane_position in self.carclass_to_lanposition[class_car]:
            #判断车型的每个车道有没有满
            for j in range(10):
                if parking_arr[lane_position][j]==-1:
                    is_full=False
                    break
            if is_full:break
        return is_full

    def main_closest_to_deliver(self,parking_arr):
        #找一下当前主车道最靠近送车横移机的车型
        closest_to_deliver=-1
        for j in range(9,-1,-1):
            if parking_arr[3][j]!=-1:
                closest_to_deliver=parking_arr[3][j]
                break
        return closest_to_deliver
    
    def nearest_fourpower_lane_target(self,parting_arr): #返回最近的有车四驱车道目标
        have_car_list=[]
        for laneposition in self.carclass_to_lanposition[0]:
            if not self.is_empty(parting_arr,laneposition):
                have_car_list.append(laneposition)
        distance_list=[abs(i-3) for i in have_car_list]
        position_index=distance_list.index(min(distance_list))
        return self.lanposition_to_target[have_car_list[position_index]]