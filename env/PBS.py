import numpy as np
import pandas as pd
from cmath import nan

class PBSEnv():
    def __init__(self,cars_in_order,mode) -> None:
        '''
        只有三种车：四驱燃油、两驱混动、两驱燃油。
        -1:没车；0：四驱燃油；1：两驱混动；2：两驱燃油
        0:进车道6； 1:进车道5； 2:返回道； 3:进车道4； 4:进车道3； 5:进车道2； 6:进车道1
        3秒为一个step进行计算
        self.receive_target    -1:没有目标；0-5:将来车放到进车道6-1；6-11:将返回道车放到进车道6-1
        self.deliver_target    -1:没有目标；0-5:将进车道6-1车放到出口；6-11:将进车道6-1车放到返回道

        接车横移机和送车横移机在有目标时不会接受任何action
        '''

        #车辆进入顺序合法性检查
        for car in cars_in_order:
            if car not in [0,1,2]:
                raise ValueError('车辆进入顺序不合法')

        self.num_cars=len(cars_in_order) #输入车辆数
        self.cars_in_order=[Car(cars_in_order[i],i) for i in range(len(cars_in_order))] #车辆进入顺序
        self.mode=mode #环境的模式，0是第一种模式，1是第二种模式
        self.logdf=pd.DataFrame()
    
    def step(self,action):
        #判断当前动作会不会让环境死锁，对于动作操作对象对不对的判断在step1和step2中都内置了
        if self.__will_env_lock(action):
            self.render()
            raise ValueError('警告：输入的动作{}会造成当前环境的死锁'.format(action))
        
        if self.mode==0:
            return self.__step1(action)
        elif self.mode==1:
            return self.__step2(action)
        else:
            raise ValueError('当前状态mode错误')

    def reset(self): #环境初始化
        self.next_car_num=0  #下一辆要出来的车在cars_in_order中的顺序
        self.cars_out_order=[] #汽车输出序列
        self.return_used_time=0 #返回车道使用次数

        self.parking_arr=[[],[],[],[],[],[],[]]  #当前停车位停车情况
        for i in range(7):
            for j in range(10):
                self.parking_arr[i].append(Car(-1,-1))
        self.parking_time=np.zeros([7,10],dtype=int) #当前停车位停车时间

        self.receive_activate=True #当前接车横移机是否活跃
        self.deliver_activate=True #当前送车横移机是否活跃
        self.receive_position=3 #当前接车横移机位置
        self.deliver_position=3 #当前送车横移机位置
        self.receive_target=-1 #-1:没有目标；0-5:将来车放到进车道6-1；6-11:将返回道车放到进车道6-1
        self.deliver_target=-1 #-1:没有目标；0-5:将进车道6-1车放到出口；6-11:将进车道6-1车放到返回道
        self.receive_hold=Car(-1,-1) #-1:没车；0：四驱燃油；1：两驱混动；2：两驱燃油
        self.deliver_hold=Car(-1,-1) #-1:没车；0：四驱燃油；1：两驱混动；2：两驱燃油

        self.step_num=0  #当前步骤数，3秒为一个step
        self.which_to_chose=0 #用来记录当前该谁选择动作了，是接车横移机(0)还是送车横移机(1)
        self.done=False

        self.render()
        return self.state

    def render(self): #环境可视化
        position_to_target=[[0,6],[1,7],[],[2,8],[3,9],[4,10],[5,11]]
        raw_name=['进车道6','进车道5','返回道 ','进车道4','进车道3','进车道2','进车道1']
        print('********************'*6)
        print('当前来车序列：',self.cars_in_order[self.next_car_num:],' 输出序列:',self.cars_out_order)
        print('接车横移机目标:',self.receive_target,'  送车横移机目标:',self.deliver_target,' step',self.step_num,'score1:',self.__score1(),'score2:',self.__score2(),'score3:',self.__score3(),'score4:',self.__score4(),'score:',self.__score())
        print('\t\t10\t9\t8\t7\t6\t5\t4\t3\t2\t1\t')
        print('+'+'------------------------------'*3+'-------------+')
        for row in range(7):
            if row==self.receive_position:
                print('{}\t  {}\t'.format(raw_name[row],self.receive_hold),end='')
            else:
                print('{}\t\t'.format(raw_name[row]),end='')
            for col in range(10):
                if self.parking_arr[row][col]==-1:
                    if row==2:
                        print('<--\t',end='')
                    else:
                        print('-->\t',end='')
                else:
                    print('{}~{}\t'.format(self.parking_arr[row][col],self.parking_time[row][col]),end='')
            if row==self.deliver_position:
                print('{}\t|  {}'.format(self.deliver_hold,position_to_target[row]))
            else:
                print('\t|  {}'.format(position_to_target[row]))
            print('+'+'------------------------------'*3+'-------------+')
        return None
    
    @property
    def state(self):
        #[self.which_to_chose,self.parking_arr,self.parking_time]
        state_dict={
            'which_to_chose':self.which_to_chose,
            'parking_arr':self.parking_arr,
            'parking_time':self.parking_time,
            'deliver_chose_target':self.__deliver_chose_target(),
            'next_car':(int(str(self.cars_in_order[self.next_car_num])) if self.next_car_num<self.num_cars else -1),
            'cars_out_order':self.cars_out_order,
            'score':self.__score(),
            'score1':self.__score1(),
            'score2':self.__score2(),
            'score3':self.__score3(),
            'score4':self.__score4(),
            'receive_hold':self.receive_hold,
            'deliver_hold':self.deliver_hold
        }
        return state_dict

    #总环境控制
    def __step1(self,action): #用来和智能体交互来更新。
        '''
        用来和智能体交互来更新。action是一个两个元素list，分别代表[左还是右,动作]
        每step一次就运行到需要下一次输入动作，每一次step当前步骤数不一定+1,可能不加也可能加很多
        step_num的更新要紧跟parking_step
        step函数返回done
        '''
        done=False
        if len(self.cars_in_order)==len(self.cars_out_order): #当前状态已经结束
            self.done=True
            self.done_step=self.step_num
            self.done_score=self.__score()
            return self.state,True

        if action[0]!=self.which_to_chose: #输入的action对象错了
            raise ValueError('当前智能体的操作对象不对')
        
        if not self.which_to_chose:#当前动作要给接车横移机
            #当前动作合法性判断
            if self.parking_arr[2][0]!=-1 and (action[1] not in range(6,12)):
                raise ValueError('接车横移机输入动作值有误，应[6~11]')
            elif action[1] not in range(-1,12):
                raise ValueError('输入动作值非法')
            
            if self.__receive_step1(action[1]):#占用时间
                while True:#直到下一次需要输入动作的时候就终止
                    need_action=False

                    #传送带更新
                    self.__parking_step()
                    self.step_num+=1
                    self.__export_state_col()
                    self.render()

                    #送车横移机更新
                    while True: #占用一个时间步或者需要输入动作就退出
                        if self.deliver_target==-1 and self.__deliver_chose_target()!=[]:
                            need_action=True
                            self.which_to_chose=1
                            break
                        else:
                            deliver_taken_time=self.__deliver_step1(-1)
                        if deliver_taken_time:
                            break
                    if need_action:
                        break

                    #接车横移机更新
                    while True: #占用一个时间步或者需要输入动作就退出
                        if self.receive_target==-1 and (self.parking_arr[2][0]!=-1 or self.next_car_num<self.num_cars):
                            need_action=True
                            self.which_to_chose=0
                            break
                        else:
                            receive_taken_time=self.__receive_step1(-1)
                        if receive_taken_time:
                            break
                    if need_action:
                        break
            else:#没占用时间
                while True:#直到下一次需要输入动作的时候就终止
                    need_action=False
                    #接车横移机更新
                    while True: #占用一个时间步或者需要输入动作就退出
                        if self.receive_target==-1 and (self.parking_arr[2][0]!=-1 or self.next_car_num<self.num_cars):
                            need_action=True
                            self.which_to_chose=0
                            break
                        else:
                            receive_taken_time=self.__receive_step1(-1)
                        if receive_taken_time:
                            break
                    if need_action:
                        break

                    #传送带更新
                    self.__parking_step()
                    self.step_num+=1
                    self.__export_state_col()
                    self.render()

                    #送车横移机更新
                    while True: #占用一个时间步或者需要输入动作就退出
                        if self.deliver_target==-1 and self.__deliver_chose_target()!=[]:
                            need_action=True
                            self.which_to_chose=1
                            break
                        else:
                            deliver_taken_time=self.__deliver_step1(-1)
                        if deliver_taken_time:
                            break
                    if need_action:
                        break
                    
        else: #当前动作要给送车横移机
            #当前动作合法性判断
            if action[1] not in self.__deliver_chose_target():
                raise ValueError('送车横移机输入动作值有误，应{}'.format(self.__deliver_chose_target()))
            if self.__deliver_step1(action[1]):#占用时间
                while True:#直到下一次需要输入动作的时候就终止
                    #如果排序已经完成，就不再继续了
                    if len(self.cars_in_order)==len(self.cars_out_order): #当前状态已经结束
                        self.done=True
                        self.done_step=self.step_num
                        self.done_score=self.__score()
                        return self.state,True

                    need_action=False

                    #接车横移机更新
                    while True: #占用一个时间步或者需要输入动作就退出
                        if self.receive_target==-1 and (self.parking_arr[2][0]!=-1 or self.next_car_num<self.num_cars):
                            need_action=True
                            self.which_to_chose=0
                            break
                        else:
                            receive_taken_time=self.__receive_step1(-1)
                        if receive_taken_time:
                            break
                    if need_action:
                        break

                    #传送带更新
                    self.__parking_step()
                    self.step_num+=1
                    self.__export_state_col()
                    self.render()

                    #送车横移机更新
                    while True: #占用一个时间步或者需要输入动作就退出
                        if self.deliver_target==-1 and self.__deliver_chose_target()!=[]:
                            need_action=True
                            self.which_to_chose=1
                            break
                        else:
                            deliver_taken_time=self.__deliver_step1(-1)
                        if deliver_taken_time:
                            break
                    if need_action:
                        break
            
            else:#不占用时间
                
                while True:#直到下一次需要输入动作的时候就终止
                    #如果排序已经完成，就不再继续了
                    if len(self.cars_in_order)==len(self.cars_out_order): #当前状态已经结束
                        self.done=True
                        self.done_step=self.step_num
                        self.done_score=self.__score()
                        return self.state,True

                    need_action=False
                    #送车横移机更新
                    while True: #占用一个时间步或者需要输入动作就退出
                        if self.deliver_target==-1 and self.__deliver_chose_target()!=[]:
                            need_action=True
                            self.which_to_chose=1
                            break
                        else:
                            deliver_taken_time=self.__deliver_step1(-1)
                        if deliver_taken_time:
                            break
                    if need_action:
                        break

                    #接车横移机更新
                    while True: #占用一个时间步或者需要输入动作就退出
                        if self.receive_target==-1 and (self.parking_arr[2][0]!=-1 or self.next_car_num<self.num_cars):
                            need_action=True
                            self.which_to_chose=0
                            break
                        else:
                            receive_taken_time=self.__receive_step1(-1)
                        if receive_taken_time:
                            break
                    if need_action:
                        break

                    #传送带更新
                    self.__parking_step()
                    self.step_num+=1
                    self.__export_state_col()
                    self.render()
        
        if len(self.cars_in_order)==len(self.cars_out_order): #当前状态已经结束
            self.done=True
            self.done_step=self.step_num
            self.done_score=self.__score()
            done=True
        else:
            done=False
        return self.state,done #返回当前state和done

    def __step2(self,action): #用来和智能体交互来更新。
        '''
        用来和智能体交互来更新。action是一个两个元素list，分别代表[左还是右,动作]
        每step一次就运行到需要下一次输入动作，每一次step当前步骤数不一定+1,可能不加也可能加很多
        step_num的更新要紧跟parking_step
        step函数返回done
        '''
        if len(self.cars_in_order)==len(self.cars_out_order): #当前状态已经结束
            self.done=True
            self.done_step=self.step_num
            self.done_score=self.__score()
            return self.state,True
        if action[0]!=self.which_to_chose: #输入的action对象错了
            raise ValueError('当前智能体的操作对象不对')
        
        if not self.which_to_chose:#当前动作要给接车横移机
            #当前动作合法性判断
            #可以在这里加入死循环动作判断aaaaaaaaaaaaaaaaaaaaaaaaaaaa
            if action[1] not in range(-1,12):
                raise ValueError('输入动作值非法')
            
            if self.__receive_step2(action[1]):#占用时间
                while True:#直到下一次需要输入动作的时候就终止
                    need_action=False

                    #传送带更新
                    self.__parking_step()
                    self.step_num+=1
                    self.__export_state_col()
                    self.render()

                    #送车横移机更新
                    while True: #占用一个时间步或者需要输入动作就退出
                        if self.deliver_target==-1 and (not self.__is_cominglane_empty()):
                            need_action=True
                            self.which_to_chose=1
                            break
                        else:
                            deliver_taken_time=self.__deliver_step2(-1)
                        if deliver_taken_time:
                            break
                    if need_action:
                        break

                    #接车横移机更新
                    while True: #占用一个时间步或者需要输入动作就退出
                        if self.receive_target==-1 and (self.next_car_num<self.num_cars or not self.__is_backlane_empty()):
                            need_action=True
                            self.which_to_chose=0
                            break
                        else:
                            receive_taken_time=self.__receive_step2(-1)
                        if receive_taken_time:
                            break
                    if need_action:
                        break
            else:#没占用时间
                while True:#直到下一次需要输入动作的时候就终止
                    need_action=False

                    #接车横移机更新
                    while True: #占用一个时间步或者需要输入动作就退出
                        if self.receive_target==-1 and (self.next_car_num<self.num_cars or not self.__is_backlane_empty()):
                            need_action=True
                            self.which_to_chose=0
                            break
                        else:
                            receive_taken_time=self.__receive_step2(-1)
                        if receive_taken_time:
                            break
                    if need_action:
                        break

                    #传送带更新
                    self.__parking_step()
                    self.step_num+=1
                    self.__export_state_col()
                    self.render()

                    #送车横移机更新
                    while True: #占用一个时间步或者需要输入动作就退出
                        if self.deliver_target==-1 and (not self.__is_cominglane_empty()):
                            need_action=True
                            self.which_to_chose=1
                            break
                        else:
                            deliver_taken_time=self.__deliver_step2(-1)
                        if deliver_taken_time:
                            break
                    if need_action:
                        break
                    
        else: #当前动作要给送车横移机
            #当前动作合法性判断
            #可以在这里加入死循环动作判断aaaaaaaaaaaaaaaaaaaaaaaaaaaa
            if action[1] not in range(-1,12):
                raise ValueError('输入动作值非法')
            
            if self.__deliver_step2(action[1]):#占用时间
                while True:#直到下一次需要输入动作的时候就终止
                    #如果排序已经完成，就不再继续了
                    if len(self.cars_in_order)==len(self.cars_out_order): #当前状态已经结束
                        self.done=True
                        self.done_step=self.step_num
                        self.done_score=self.__score()
                        return self.state,True

                    need_action=False
                    #接车横移机更新
                    while True: #占用一个时间步或者需要输入动作就退出
                        if self.receive_target==-1 and (self.next_car_num<self.num_cars or not self.__is_backlane_empty()):
                            need_action=True
                            self.which_to_chose=0
                            break
                        else:
                            receive_taken_time=self.__receive_step2(-1)
                        if receive_taken_time:
                            break
                    if need_action:
                        break

                    #传送带更新
                    self.__parking_step()
                    self.step_num+=1
                    self.__export_state_col()
                    self.render()

                    #送车横移机更新
                    while True: #占用一个时间步或者需要输入动作就退出
                        if self.deliver_target==-1 and (not self.__is_cominglane_empty()):
                            need_action=True
                            self.which_to_chose=1
                            break
                        else:
                            deliver_taken_time=self.__deliver_step2(-1)
                        if deliver_taken_time:
                            break
                    if need_action:
                        break
            
            else:#不占用时间
                
                while True:#直到下一次需要输入动作的时候就终止
                    #如果排序已经完成，就不再继续了
                    if len(self.cars_in_order)==len(self.cars_out_order): #当前状态已经结束
                        self.done=True
                        self.done_step=self.step_num
                        self.done_score=self.__score()
                        return self.state,True

                    need_action=False
                    #送车横移机更新
                    while True: #占用一个时间步或者需要输入动作就退出
                        if self.deliver_target==-1 and (not self.__is_cominglane_empty()):
                            need_action=True
                            self.which_to_chose=1
                            break
                        else:
                            deliver_taken_time=self.__deliver_step2(-1)
                        if deliver_taken_time:
                            break
                    if need_action:
                        break

                    #接车横移机更新
                    while True: #占用一个时间步或者需要输入动作就退出
                        if self.receive_target==-1 and (self.next_car_num<self.num_cars or not self.__is_backlane_empty()):
                            need_action=True
                            self.which_to_chose=0
                            break
                        else:
                            receive_taken_time=self.__receive_step2(-1)
                        if receive_taken_time:
                            break
                    if need_action:
                        break

                    #传送带更新
                    self.__parking_step()
                    self.step_num+=1
                    self.__export_state_col()
                    self.render()
        
        if len(self.cars_in_order)==len(self.cars_out_order): #当前状态已经结束
            self.done=True
            self.done_step=self.step_num
            self.done_score=self.__score()
            done=True
        else:
            done=False
        return self.state,done #返回当前state和done

    def step_command(self): #用命令行input来step更新
        if len(self.cars_in_order)==len(self.cars_out_order):
            self.done=True
            self.done_step=self.step_num
            self.done_score=self.__score()
        stop=False #控制连续step状态是否终止，可以在接受横移机动作选择的时候输入-2终止动作

        self.render()
        while True: #接车横移机step更新
            if self.receive_target==-1:
                if self.parking_arr[2][0]!=-1: #当前返回道已经有车在等待
                    action=eval(input('请输入接车横移机(左)动作[6~11]：'))
                    if action==-2: #输入-2的时候跳出连续step模式
                        return True
                    receive_taken_time=self.__receive_step1(action)
                elif self.next_car_num<self.num_cars: #当前序列还有车，但是没有考虑返回道上是否有车，要是去返回道等待就太傻了bbbbbbbbbbbb
                    action=eval(input('请输入接车横移机(左)动作[-1~11]：'))
                    if action==-2: #输入-2的时候跳出连续step模式
                        return True
                    receive_taken_time=self.__receive_step1(action)
                else:#当前序列没车了，随便输入目标
                    receive_taken_time=self.__receive_step1(-1)
            else: #当receive_target不是-1的时候，随便输入目标
                receive_taken_time=self.__receive_step1(-1)
            self.render()
            if receive_taken_time:
                break
        
        self.__parking_step()
        self.step_num+=1
        self.__export_state_col()
        
        self.render()
        while True: #送车横移机step更新
            if self.deliver_target==-1 and self.__deliver_chose_target()!=[]: #给送车横移机选择目标
                deliver_taken_time=self.__deliver_step1(eval(input('请输入送车横移机(右)动作{}：'.format(self.__deliver_chose_target()))))
            else: #当deliver_target不是-1，或者当前所有车道都没车的时候，随便输入目标
                deliver_taken_time=self.__deliver_step1(-1)
            self.render()
            if deliver_taken_time:
                break
        return stop

    #接车横移机操控
    def __receive_step1(self,action):#接车横移机状态转移，需要输入动作action，默认-1是不能操作。返回一个布尔值，代表有没有占用时间
        '''
        如果返回车道有车，优先以抓取返回车道车为目标，需要读取一个返回车道到来车道的任务目标
        
        '''
        target_to_position=[0,1,3,4,5,6,0,1,3,4,5,6] #将目标任务变成位置
        
        if self.receive_target==-1: #此时接车横移机一定在位置3处，不一定手里有车
            #进行合法性检查
            if action not in range(-1,12):
                raise ValueError('接车横移机输入action值有误')
            if self.receive_position!=3:
                raise ValueError('当receive_target==-1的时候，接车横移机应该在位置3处')

            #接车横移机选择目标
            if self.parking_arr[2][0]!=-1: #当返回道有车到达的时候，优先以返回道为目标
                if action not in [6,7,8,9,10,11]:
                    raise ValueError('此时返回道有车在等待，接车横移机应去返回道，action给错了')
                self.receive_target=action
            elif self.next_car_num>=self.num_cars:#当前没有进车了，接车横移机停滞一个时间步
                return True
            else:
                self.receive_target=action
            
            #接车横移机开始执行任务
            if self.receive_target==-1: #没有任务分配，接车横移机停滞一个时间步
                return True
            elif self.receive_target==2: #将来车放到进车道4
                if self.next_car_num<self.num_cars:
                    self.receive_hold=self.cars_in_order[self.next_car_num]
                else:
                    raise ValueError('没有车了无法抓取')
                self.next_car_num+=1
                if self.parking_arr[3][0]==-1:
                    self.parking_arr[3][0]=self.receive_hold
                    self.receive_hold=Car(-1,-1)
                    self.receive_target=-1
                    return False #这一步没有占用时间
                return True #等待放车占用时间
            elif self.receive_target in [6,7,8,9,10,11]: #去返回道取车
                if self.receive_hold!=-1:
                    raise ValueError('此时接受横移机有车不能到返回道取车')
                self.receive_position-=1
                return True
            else:#去在车道6、5、3、2、1放车
                self.receive_hold=self.cars_in_order[self.next_car_num]
                self.next_car_num+=1
                self.__receive_move_towards(target_to_position[self.receive_target])
                return True
        elif self.receive_target==2:#目标是将来车放到进车道4，现在接车横移机一定在3位置上，而且接受横移机应该有车
            if self.receive_position!=3:
                raise ValueError("你车为啥不在位置3上啊，有问题！")
            if self.receive_hold==-1:
                raise ValueError('接受横移机上怎么没车啊？！')
            if self.parking_arr[3][0]==-1:
                self.parking_arr[3][0]=self.receive_hold
                self.receive_hold=Car(-1,-1)
                self.receive_target=-1
                return False
            return True
        elif self.receive_target==8:#目标是将回来的车放在进车道4上
            if self.receive_position==2:
                if self.receive_hold!=-1:
                    raise ValueError("接收横移机里不应该有车鸭！")
                if self.parking_arr[2][0]==-1: #返回道还没来车，再等一会
                    return True
                else: #返回道有车
                    #拿车
                    self.receive_hold=self.parking_arr[2][0]
                    self.parking_arr[2][0]=Car(-1,-1)
                    #移动
                    self.receive_position+=1
                    return True
            elif self.receive_position==3:
                if self.receive_hold==-1:
                    raise ValueError('接车横移机在执行任务8时，当前接车横移机上没有车，无法放置到行车道4上。')
                if self.parking_arr[3][0]==-1:
                    self.parking_arr[3][0]=self.receive_hold
                    self.receive_hold=Car(-1,-1)
                    self.receive_target=-1
                    return False
                return True #如果当前行车道4上有车，等待一个时间步
        elif self.receive_target in [0,1,3,4,5]:
            if self.receive_position==target_to_position[self.receive_target]: #已经到达目标位置，现在手里应该是有车的
                if self.receive_hold==-1:
                    raise ValueError('接车横移机里怎么没车呢？！')
                if self.parking_arr[self.receive_position][0]==-1:
                    self.parking_arr[self.receive_position][0]=self.receive_hold
                    self.receive_hold=Car(-1,-1)
                    self.__receive_move_towards(3)
                    return True
                return True #如果当前车道上有车，等待一个时间步
            elif self.receive_position==3:#已经完成任务回到了初始位置
                self.receive_target=-1
                return False
            elif self.receive_hold==-1: #已经放下车再往初始位置走了
                self.__receive_move_towards(3)
                if self.receive_position==3:
                    self.receive_target=-1
                return True
            else:
                self.__receive_move_towards(target_to_position[self.receive_target])
                return True
        elif self.receive_target in [6,7,9,10,11]:
            if self.receive_position==2 and self.receive_hold==-1:#在返回车道等待来车
                if self.parking_arr[2][0]==-1: #返回道还没来车，再等一会
                    return True
                else: #返回道有车
                    self.receive_hold=self.parking_arr[2][0]
                    self.parking_arr[2][0]=Car(-1,-1)
                    self.__receive_move_towards(target_to_position[self.receive_target])
                    return True
            elif self.receive_position==target_to_position[self.receive_target]: #已经到达目标位置，现在手里应该有车
                if self.receive_hold==-1:
                    raise ValueError('错误：接车横移机执行任务{}时到达目的地后手里没车'.format(self.receive_target))
                if self.parking_arr[self.receive_position][0]==-1:
                    self.parking_arr[self.receive_position][0]=self.receive_hold
                    self.receive_hold=Car(-1,-1)
                    self.__receive_move_towards(3)
                    return True
                return True #如果当前车道上有车，等待一个时间步
            elif self.receive_position==3 and self.receive_hold==-1:#已经完成任务回到初始位置
                self.receive_target=-1
                return False
            elif self.receive_hold!=-1:#拿到了车在往目标方向走
                self.__receive_move_towards(target_to_position[self.receive_target])
                return True
            elif self.receive_hold==-1: #已经放下车往初始位置走了
                self.__receive_move_towards(3)
                return True
            raise ValueError('错误：接车横移机执行任务{}时没有返回值'.format(self.receive_target))
        else:
            raise ValueError('当前接车横移机target错误')
    
    def __receive_step2(self,action):#接车横移机状态转移，需要输入动作action，默认-1是不能操作。返回一个布尔值，代表有没有占用时间
        '''
        没有优先抓取返回车道的条件限制，需要读取一个返回车道到来车道的任务目标
        '''
        target_to_position=[0,1,3,4,5,6,0,1,3,4,5,6] #将目标任务变成位置
        
        if self.receive_target==-1: #此时接车横移机一定在位置3处，不一定手里有车
            #进行合法性检查
            if action not in range(-1,12):
                raise ValueError('接车横移机输入action值有误')
            if self.receive_position!=3:
                raise ValueError('当receive_target==-1的时候，接车横移机应该在位置3处')

            #接车横移机选择目标
            if self.next_car_num>=self.num_cars and self.__is_lane_empty(2):#当前没有进车了，返回车道也没有车，接车横移机停滞一个时间步
                return True
            else:
                self.receive_target=action
            
            #接车横移机开始执行任务
            if self.receive_target==-1: #没有任务分配，接车横移机停滞一个时间步
                return True
            elif self.receive_target==2: #将来车放到进车道4
                if self.next_car_num<self.num_cars:
                    self.receive_hold=self.cars_in_order[self.next_car_num]
                else:
                    raise ValueError('没有车了无法抓取')
                self.next_car_num+=1
                if self.parking_arr[3][0]==-1:
                    self.parking_arr[3][0]=self.receive_hold
                    self.receive_hold=Car(-1,-1)
                    self.receive_target=-1
                    return False #这一步没有占用时间
                return True #等待放车占用时间
            elif self.receive_target in [6,7,8,9,10,11]: #去返回道取车
                if self.receive_hold!=-1:
                    raise ValueError('此时接受横移机有车不能到返回道取车')
                self.receive_position-=1
                return True
            else:#去在车道6、5、3、2、1放车
                self.receive_hold=self.cars_in_order[self.next_car_num]
                self.next_car_num+=1
                self.__receive_move_towards(target_to_position[self.receive_target])
                return True
        elif self.receive_target==2:#目标是将来车放到进车道4，现在接车横移机一定在3位置上，而且接受横移机应该有车
            if self.receive_position!=3:
                raise ValueError("你车为啥不在位置3上啊，有问题！")
            if self.receive_hold==-1:
                raise ValueError('接受横移机上怎么没车啊？！')
            if self.parking_arr[3][0]==-1:
                self.parking_arr[3][0]=self.receive_hold
                self.receive_hold=Car(-1,-1)
                self.receive_target=-1
                return False
            return True
        elif self.receive_target==8:#目标是将回来的车放在进车道4上
            if self.receive_position==2:
                if self.receive_hold!=-1:
                    raise ValueError("接收横移机里不应该有车鸭！")
                if self.parking_arr[2][0]==-1: #返回道还没来车，再等一会
                    return True
                else: #返回道有车
                    #拿车
                    self.receive_hold=self.parking_arr[2][0]
                    self.parking_arr[2][0]=Car(-1,-1)
                    #移动
                    self.receive_position+=1
                    return True
            elif self.receive_position==3:
                if self.receive_hold==-1:
                    raise ValueError('接车横移机在执行任务8时，当前接车横移机上没有车，无法放置到行车道4上。')
                if self.parking_arr[3][0]==-1:
                    self.parking_arr[3][0]=self.receive_hold
                    self.receive_hold=Car(-1,-1)
                    self.receive_target=-1
                    return False
                return True #如果当前行车道4上有车，等待一个时间步
        elif self.receive_target in [0,1,3,4,5]:
            if self.receive_position==target_to_position[self.receive_target]: #已经到达目标位置，现在手里应该是有车的
                if self.receive_hold==-1:
                    raise ValueError('接车横移机里怎么没车呢？！')
                if self.parking_arr[self.receive_position][0]==-1:
                    self.parking_arr[self.receive_position][0]=self.receive_hold
                    self.receive_hold=Car(-1,-1)
                    self.__receive_move_towards(3)
                    return True
                return True #如果当前车道上有车，等待一个时间步
            elif self.receive_position==3:#已经完成任务回到了初始位置
                self.receive_target=-1
                return False
            elif self.receive_hold==-1: #已经放下车再往初始位置走了
                self.__receive_move_towards(3)
                if self.receive_position==3:
                    self.receive_target=-1
                return True
            else:
                self.__receive_move_towards(target_to_position[self.receive_target])
                return True
        elif self.receive_target in [6,7,9,10,11]:
            if self.receive_position==2 and self.receive_hold==-1:#在返回车道等待来车
                if self.parking_arr[2][0]==-1: #返回道还没来车，再等一会
                    return True
                else: #返回道有车
                    self.receive_hold=self.parking_arr[2][0]
                    self.parking_arr[2][0]=Car(-1,-1)
                    self.__receive_move_towards(target_to_position[self.receive_target])
                    return True
            elif self.receive_position==target_to_position[self.receive_target]: #已经到达目标位置，现在手里应该有车
                if self.receive_hold==-1:
                    raise ValueError('错误：接车横移机执行任务{}时到达目的地后手里没车'.format(self.receive_target))
                if self.parking_arr[self.receive_position][0]==-1:
                    self.parking_arr[self.receive_position][0]=self.receive_hold
                    self.receive_hold=Car(-1,-1)
                    self.__receive_move_towards(3)
                    return True
                return True #如果当前车道上有车，等待一个时间步
            elif self.receive_position==3 and self.receive_hold==-1:#已经完成任务回到初始位置
                self.receive_target=-1
                return False
            elif self.receive_hold!=-1:#拿到了车在往目标方向走
                self.__receive_move_towards(target_to_position[self.receive_target])
                return True
            elif self.receive_hold==-1: #已经放下车往初始位置走了
                self.__receive_move_towards(3)
                return True
            raise ValueError('错误：接车横移机执行任务{}时没有返回值'.format(self.receive_target))
        else:
            raise ValueError('当前接车横移机target错误')

    def __receive_move_towards(self,moving_target_position):#接车横移机向着目标移动
        if self.receive_position<moving_target_position:
            self.receive_position+=1
        elif self.receive_position>moving_target_position:
            self.receive_position-=1
        else:
            raise ValueError('接车横移机没必要进行移动')

    #停车区操控
    def __parking_step(self):#停车区状态转移
        for i in [0,1,3,4,5,6]:#进车道
            for j in range(9,-1,-1):
                if j!=9 and self.parking_time[i][j]>=2 and self.parking_arr[i][j+1]==-1:
                    if self.parking_arr[i][j]==-1:
                        raise ValueError('没有停车但是在计算停车时间')
                    self.parking_arr[i][j+1]=self.parking_arr[i][j]
                    self.parking_arr[i][j]=Car(-1,-1)
                    self.parking_time[i][j]=0
                    self.parking_time[i][j+1]=0
                elif self.parking_arr[i][j]!=-1:
                    self.parking_time[i][j]+=1    
        for j in range(10):
            if j!=0 and self.parking_time[2][j]>=2 and self.parking_arr[2][j-1]==-1:
                if self.parking_arr[2][j]==-1:
                    raise ValueError('没有停车但是在计算停车时间')
                self.parking_arr[2][j-1]=self.parking_arr[2][j]
                self.parking_arr[2][j]=Car(-1,-1)
                self.parking_time[2][j]=0
                self.parking_time[2][j-1]=0
            elif self.parking_arr[2][j]!=-1:
                self.parking_time[2][j]+=1

    #送车横移机操控
    def __deliver_step1(self,action):#送车横移机状态转移，谁先到抓谁
        '''
        优先选择已经在停车位1的车进行定制目标，如果所有1停车位都没有车的话
        一起到的话读取action进行选择抓取
        在选择目标的时候可以选择送走还是送到返回道上
        '''
        target_to_position=[0,1,3,4,5,6,0,1,3,4,5,6] #将目标任务变成位置
        if self.deliver_target==-1: #此时送车横移机一定在位置3处，当前送车横移机上不应该有车
            #进行合法性检查
            if self.deliver_position!=3:
                raise ValueError('错误：在deliver_target为-1的时候，送车横移机没有在位置3处')
            if action not in range(-1,12):
                raise ValueError('送车横移机输入action值有误')
            if self.deliver_hold!=-1:
                raise ValueError('错误：当前送车横移机没有目标但是有车')

            #送车横移机选择目标，假设在问题1里面，送车横移机会以最早到达（或已到达）的为目标，如果有多个目标，从action中读取选择
            action_list=self.__deliver_chose_target()
            if action_list==[]: #当前所有进车道都没有车，选择空间为空，直接休息一个时间步
                return True
            if action not in action_list:
                print(action_list)
                raise ValueError('送车横移机输入action不在可选目标列表中')
            self.deliver_target=action

            #送车横移机开始执行任务
            if self.deliver_target==-1: #没有任务分配，当前应该不会出现这种情况，所以先不写了
                pass
            elif self.deliver_target==2: #将进车道4的车送走
                if self.parking_arr[3][9]==-1: #当前进车道4车还没到
                    return True
                else: #当前进车道4车到了
                    self.cars_out_order.append(self.parking_arr[3][9])
                    self.parking_arr[3][9]=Car(-1,-1)
                    self.deliver_target=-1
                    return False
            elif self.deliver_target==8: #将进车道4的车放到返回道中
                if self.parking_arr[3][9]==-1:
                    return True
                else:
                    self.deliver_hold=self.parking_arr[3][9]
                    self.parking_arr[3][9]=Car(-1,-1)
                    self.deliver_position-=1
                    return True
            else: #将进车道6、5、3、2、1的车送走 或者 将进车道6、5、3、2、1的车放到返回道
                if self.deliver_hold!=-1:
                    raise ValueError('当前送车横移机里有车，不能去别的进车道取车')
                self.__deliver_move_towards(target_to_position[self.deliver_target])
                return True          
        elif self.deliver_target==2: #目标时将进车道4的车送走，现在送车横移机一定在位置3上，并且送车横移机应该有车
            #合法性检查
            if self.deliver_position!=3:
                raise ValueError('送车横移机在执行任务2时不在位置3')
            if self.deliver_hold!=-1:
                raise ValueError('在执行任务2时送车横移机当前有车，不需要继续等待来车')
            
            #执行任务
            if self.parking_arr[3][9]==-1: #当前进车道4车还没到
                return True
            else: #当前进车道4车到了
                self.cars_out_order.append(self.parking_arr[3][9])
                self.parking_arr[3][9]=Car(-1,-1)
                self.deliver_target=-1
                return False
        elif self.deliver_target==8: #目标是将进车道4来车放到返回车道
            if self.deliver_position==3:#还在进车道4等待来车
                if self.deliver_hold!=-1:
                    raise ValueError('错误：当前送车横移机还有车但是在等待车道4来车')
                if self.parking_arr[3][9]==-1:
                    return True
                else:
                    self.deliver_hold=self.parking_arr[3][9]
                    self.parking_arr[3][9]=Car(-1,-1)
                    self.deliver_position-=1
                    return True
            elif self.deliver_position==2: #在返回道等待放车
                if self.deliver_hold==-1:
                    raise ValueError('错误：当前送车横移机没有车无法在返回道放车')
                if self.parking_arr[2][9]==-1:
                    self.parking_arr[2][9]=self.deliver_hold
                    self.return_used_time+=1
                    self.deliver_hold=Car(-1,-1)
                    self.deliver_position+=1
                    self.deliver_target=-1
                    return True
                else:#当前返回道有车，无法放车
                    return True
        elif self.deliver_target in [0,1,3,4,5]: #目标是将进车道6、5、3、2、1的车送走
            if self.deliver_position==3 and self.deliver_hold!=-1:#送车横移机载车已经到达初始位置
                self.cars_out_order.append(self.deliver_hold)
                self.deliver_hold=Car(-1,-1)
                self.deliver_target=-1
                return False
            elif self.deliver_position==target_to_position[self.deliver_target] and self.deliver_hold==-1:#已经到达目标位置
                if self.parking_arr[self.deliver_position][9]==-1:
                    return True
                else:
                    self.deliver_hold=self.parking_arr[self.deliver_position][9]
                    self.parking_arr[self.deliver_position][9]=Car(-1,-1)
                    self.__deliver_move_towards(3)
                    return True
            elif self.deliver_hold!=-1:#送车横移机已经拿到车，在回到初始位置的路上
                self.__deliver_move_towards(3)
                if self.receive_position==3:
                    self.receive_target=-1
                return True
            elif self.deliver_hold==-1: #送车横移机还没拿到车，在去目标进车道的路上
                self.__deliver_move_towards(target_to_position[self.deliver_target])
                return True
        elif self.deliver_target in [6,7,9,10,11]: #目标是将进车道6\5\3\2\1的车送到返回道上
            if self.deliver_position==2 and self.deliver_hold!=-1:#运送横移机到达返回道
                if self.parking_arr[2][9]==-1:
                    self.parking_arr[2][9]=self.deliver_hold
                    self.return_used_time+=1
                    self.deliver_hold=Car(-1,-1)
                    self.deliver_position+=1
                    self.deliver_target=-1
                    return True
                else:#当前返回车道有车，无法放车
                    return True
            elif self.deliver_position==target_to_position[self.deliver_target] and self.deliver_hold==-1: #送车横移机到达目标位置
                if self.parking_arr[self.deliver_position][9]==-1:
                    return True
                else:
                    self.deliver_hold=self.parking_arr[self.deliver_position][9]
                    self.parking_arr[self.deliver_position][9]=Car(-1,-1)
                    self.__deliver_move_towards(2)
                    return True
            elif self.deliver_hold!=-1: #送车横移机已经拿到车，在去返回道的路上
                self.__deliver_move_towards(2)
                return True
            elif self.deliver_hold==-1: #送车横移机还没拿到车，在去目标的路上
                self.__deliver_move_towards(target_to_position[self.deliver_target])
                return True

    def __deliver_step2(self,action):#送车横机状态转移，有很多动作选择
        '''
        优先选择已经在停车位1的车进行定制目标，如果所有1停车位都没有车的话
        一起到的话读取action进行选择抓取
        在选择目标的时候可以选择送走还是送到返回道上
        '''
        target_to_position=[0,1,3,4,5,6,0,1,3,4,5,6] #将目标任务变成位置
        if self.deliver_target==-1: #此时送车横移机一定在位置3处，当前送车横移机上不应该有车
            #进行合法性检查
            if self.deliver_position!=3:
                raise ValueError('错误：在deliver_target为-1的时候，送车横移机没有在位置3处')
            if action not in range(-1,12):
                raise ValueError('送车横移机输入action值有误')
            if self.deliver_hold!=-1:
                raise ValueError('错误：当前送车横移机没有目标但是有车')

            #送车横移机选择目标，不再约束先拿走先到的
            action_list=self.__deliver_chose_target()
            if action_list==[]: #当前所有进车道都没有车，选择空间为空，直接休息一个时间步
                return True
            self.deliver_target=action

            #送车横移机开始执行任务
            if self.deliver_target==-1: #送车横移机停滞一个时间步
                return True
            elif self.deliver_target==2: #将进车道4的车送走
                if self.parking_arr[3][9]==-1: #当前进车道4车还没到
                    return True
                else: #当前进车道4车到了
                    self.cars_out_order.append(self.parking_arr[3][9])
                    self.parking_arr[3][9]=Car(-1,-1)
                    self.deliver_target=-1
                    return False
            elif self.deliver_target==8: #将进车道4的车放到返回道中
                if self.parking_arr[3][9]==-1:
                    return True
                else:
                    self.deliver_hold=self.parking_arr[3][9]
                    self.parking_arr[3][9]=Car(-1,-1)
                    self.deliver_position-=1
                    return True
            else: #将进车道6、5、3、2、1的车送走 或者 将进车道6、5、3、2、1的车放到返回道
                if self.deliver_hold!=-1:
                    raise ValueError('当前送车横移机里有车，不能去别的进车道取车')
                self.__deliver_move_towards(target_to_position[self.deliver_target])
                return True          
        elif self.deliver_target==2: #目标时将进车道4的车送走，现在送车横移机一定在位置3上，并且送车横移机应该有车
            #合法性检查
            if self.deliver_position!=3:
                raise ValueError('送车横移机在执行任务2时不在位置3')
            if self.deliver_hold!=-1:
                raise ValueError('在执行任务2时送车横移机当前有车，不需要继续等待来车')
            
            #执行任务
            if self.parking_arr[3][9]==-1: #当前进车道4车还没到
                return True
            else: #当前进车道4车到了
                self.cars_out_order.append(self.parking_arr[3][9])
                self.parking_arr[3][9]=Car(-1,-1)
                self.deliver_target=-1
                return False
        elif self.deliver_target==8: #目标是将进车道4来车放到返回车道
            if self.deliver_position==3:#还在进车道4等待来车
                if self.deliver_hold!=-1:
                    raise ValueError('错误：当前送车横移机还有车但是在等待车道4来车')
                if self.parking_arr[3][9]==-1:
                    return True
                else:
                    self.deliver_hold=self.parking_arr[3][9]
                    self.parking_arr[3][9]=Car(-1,-1)
                    self.deliver_position-=1
                    return True
            elif self.deliver_position==2: #在返回道等待放车
                if self.deliver_hold==-1:
                    raise ValueError('错误：当前送车横移机没有车无法在返回道放车')
                if self.parking_arr[2][9]==-1:
                    self.parking_arr[2][9]=self.deliver_hold
                    self.return_used_time+=1
                    self.deliver_hold=Car(-1,-1)
                    self.deliver_position+=1
                    self.deliver_target=-1
                    return True
                else:#当前返回道有车，无法放车
                    return True
        elif self.deliver_target in [0,1,3,4,5]: #目标是将进车道6、5、3、2、1的车送走
            if self.deliver_position==3 and self.deliver_hold!=-1:#送车横移机载车已经到达初始位置
                self.cars_out_order.append(self.deliver_hold)
                self.deliver_hold=Car(-1,-1)
                self.deliver_target=-1
                return False
            elif self.deliver_position==target_to_position[self.deliver_target] and self.deliver_hold==-1:#已经到达目标位置
                if self.parking_arr[self.deliver_position][9]==-1:
                    return True
                else:
                    self.deliver_hold=self.parking_arr[self.deliver_position][9]
                    self.parking_arr[self.deliver_position][9]=Car(-1,-1)
                    self.__deliver_move_towards(3)
                    return True
            elif self.deliver_hold!=-1:#送车横移机已经拿到车，在回到初始位置的路上
                self.__deliver_move_towards(3)
                if self.receive_position==3:
                    self.receive_target=-1
                return True
            elif self.deliver_hold==-1: #送车横移机还没拿到车，在去目标进车道的路上
                self.__deliver_move_towards(target_to_position[self.deliver_target])
                return True
        elif self.deliver_target in [6,7,9,10,11]: #目标是将进车道6\5\3\2\1的车送到返回道上
            if self.deliver_position==2 and self.deliver_hold!=-1:#运送横移机到达返回道
                if self.parking_arr[2][9]==-1:
                    self.parking_arr[2][9]=self.deliver_hold
                    self.return_used_time+=1
                    self.deliver_hold=Car(-1,-1)
                    self.deliver_position+=1
                    self.deliver_target=-1
                    return True
                else:#当前返回车道有车，无法放车
                    return True
            elif self.deliver_position==target_to_position[self.deliver_target] and self.deliver_hold==-1: #送车横移机到达目标位置
                if self.parking_arr[self.deliver_position][9]==-1:
                    return True
                else:
                    self.deliver_hold=self.parking_arr[self.deliver_position][9]
                    self.parking_arr[self.deliver_position][9]=Car(-1,-1)
                    self.__deliver_move_towards(2)
                    return True
            elif self.deliver_hold!=-1: #送车横移机已经拿到车，在去返回道的路上
                self.__deliver_move_towards(2)
                return True
            elif self.deliver_hold==-1: #送车横移机还没拿到车，在去目标的路上
                self.__deliver_move_towards(target_to_position[self.deliver_target])
                return True

    def __deliver_chose_target(self):
        position_to_target=[[0,6],[1,7],[],[2,8],[3,9],[4,10],[5,11]]
        target_list=[]
        for j in range(9,-1,-1):
            is_this_column=False
            longest_parking_time=0
            for i in [0,1,3,4,5,6]:
                if self.parking_arr[i][j]!=-1:
                    is_this_column=True
                    longest_parking_time=max(longest_parking_time,self.parking_time[i][j])
            if is_this_column:
                for i in [0,1,3,4,5,6]:
                    if self.parking_time[i][j]==longest_parking_time and self.parking_arr[i][j]!=-1:
                        target_list+=position_to_target[i]
                break
        return target_list

    def __deliver_move_towards(self,moving_target_position):#送车横移机向着目标移动
        if self.deliver_position<moving_target_position:
            self.deliver_position+=1
        elif self.deliver_position>moving_target_position:
            self.deliver_position-=1
        else:
            raise ValueError('接车横移机没必要进行移动')

    #记录当前状态的log
    def __export_state_col(self):#将当前当前状态拓展到logdf中
        column = []
        state_order = [[],[],[],[],[],[],[]]
        for row in state_order:
            for col in self.state['parking_arr'][state_order.index(row)]:
                row.append(col.car_order)
        for i in range(len(self.cars_in_order)):
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
            elif i == self.state['receive_hold'].car_order:
                column.append('1')
            elif i == self.state['deliver_hold'].car_order:
                column.append('2')
            else:
                column.append(nan)
        self.logdf['{}'.format(self.step_num*3-3)]=column
        self.logdf['{}'.format(self.step_num*3-2)]=column
        self.logdf['{}'.format(self.step_num*3-1)]=column

    #计算得分
    def __score(self): #当前得分情况
        return 0.4*self.__score1()+0.3*self.__score2()+0.2*self.__score3()+0.1*self.__score4()
    
    def __score1(self):
        #注意程序没有运行完会出现的bug bbbbbbbbbbbb
        last_hybrid_num=-1
        score=100
        for i in range(len(self.cars_out_order)):
            if self.cars_out_order[i]==1:
                if last_hybrid_num!=-1:
                    if i-last_hybrid_num!=3:
                        score-=1
                last_hybrid_num=i
        return score

    def __score2(self):
        #四驱车：0；两驱车：1、2
        #转化成是否是四驱
        car_class=[0,1,1] #索引车的类型，转化为是不是四驱
        out_cars_class=[car_class[int(str(i))] for i in self.cars_out_order]

        #分块
        block_list=[]
        last_car_num=0
        cut=False
        for i in range(1,len(self.cars_out_order)):
            if out_cars_class[i]!=out_cars_class[last_car_num] and not cut:
                cut=True
                continue
            if out_cars_class[i]==out_cars_class[last_car_num] and cut:
                block_list.append(out_cars_class[last_car_num:i])
                cut=False
                last_car_num=i
        block_list.append(out_cars_class[last_car_num:])

        #算分
        score=100
        for block in block_list:
            if block.count(0)!=block.count(1):
                score-=1
        
        return score

    def __score3(self):
        return 100-self.return_used_time

    def __score4(self):
        return 100-0.01*(self.step_num*3-9*len(self.cars_out_order)-72)
    
    #一些判断状态函数
    def __is_cominglane_empty(self):#判断当前所有来进道有没有车
        is_empty=True
        for i in [0,1,3,4,5,6]:
            this_lane_empty=True
            for j in range(10):
                if self.parking_arr[i][j]!=-1:
                    this_lane_empty=False
                    break
            if not this_lane_empty:
                is_empty=False
                break
        return is_empty

    def __is_backlane_empty(self): #判断当前返回车道有没有车
        is_empty=True
        for j in range(10):
            if self.parking_arr[2][j]!=-1:
                is_empty=False
                break
        return is_empty
        
    def __will_env_lock(self,action): #判断当前动作会不会让环境死锁
        #进行动作合法性判断
        if (action[0] not in [0,1]) or (action[1] not in range(-1,12)):
            raise ValueError('在进行死锁判断时输入的action不合法')
        
        will_lock=False
        target_to_position=[0,1,3,4,5,6,0,1,3,4,5,6]

        if not action[0]:#接车横移机
            if action[1] in range(0,6):
                if self.__is_lane_full(target_to_position[action[1]]) and self.__is_dangerously_waiting(1):
                    will_lock=True
            elif action[1] in range(6,12):
                if self.__is_lane_full(target_to_position[action[1]]) and self.__is_dangerously_waiting(1):
                    will_lock=True
                elif self.__is_lane_empty(2) and self.__is_dangerously_waiting(1):
                    will_lock=True
        else:#送车横移机
            if action[1] in range(0,6):
                if self.__is_lane_empty(target_to_position[action[1]]) and self.__is_dangerously_waiting(0):
                    will_lock=True
                elif self.__is_lane_empty(target_to_position[action[1]]) and self.__is_lane_empty(2) and self.next_car_num>=self.num_cars and self.receive_target==-1:
                    will_lock=True
            elif action[1] in range(6,12):
                if self.__is_lane_empty(target_to_position[action[1]]) and self.__is_dangerously_waiting(0):
                    will_lock=True
                elif self.__is_lane_empty(target_to_position[action[1]]) and self.__is_lane_empty(2) and self.next_car_num>=self.num_cars and self.receive_target==-1:
                    will_lock=True
                elif self.__is_lane_full(2) and self.__is_dangerously_waiting(0):
                    will_lock=True
        return will_lock

    def __is_dangerously_waiting(self,which):#判断当前接车横移机或者送车横移机是否在危险等待
        '''
        危险等待指的是等着拿车但是当前车道没车、或者等着放车当前车道车满
        '''
        target_to_position=[0,1,3,4,5,6,0,1,3,4,5,6]

        is_dangerously_waiting=False
        if which==0:#接车横移机
            if self.receive_target in range(0,6):
                if self.receive_position==target_to_position[self.receive_target] and self.receive_hold!=-1 and self.__is_lane_full(self.receive_position):
                    is_dangerously_waiting=True
            elif self.receive_target in range(6,12):
                if self.receive_position==target_to_position[self.receive_target] and self.receive_hold!=-1 and self.__is_lane_full(self.receive_position):
                    is_dangerously_waiting=True
                elif self.receive_position==2 and self.receive_hold==-1 and self.__is_lane_empty(2):
                    is_dangerously_waiting=True
        elif which==1: #送车横移机
            if self.deliver_target in range(0,6):
                if self.deliver_position==target_to_position[self.deliver_target] and self.deliver_hold==-1 and self.__is_lane_empty(self.deliver_position):
                    is_dangerously_waiting=True
            elif self.deliver_target in range(6,12):
                if self.deliver_position==target_to_position[self.deliver_target] and self.deliver_hold==-1 and self.__is_lane_empty(self.deliver_position):
                    is_dangerously_waiting=True
                elif self.deliver_position==2 and self.deliver_hold!=-1 and self.__is_lane_full(2):
                    is_dangerously_waiting=True
        else:
            raise
        return is_dangerously_waiting

    def __is_lane_empty(self,lane_position): #判断车道有没有空
        is_empty=True
        for j in range(10):
            if self.parking_arr[lane_position][j]!=-1:
                is_empty=False
                break
        return is_empty

    def __is_lane_full(self,lane_position): #判断车道有没有满
        is_full=True
        for j in range(10):
            if self.parking_arr[lane_position][j]==-1:
                is_full=False
                break
        return is_full

class Car():
    def __init__(self,car_class,car_order):
        self.car_class=car_class
        self.car_order=car_order

    def __call__(self):
        return self.car_class
    
    def __str__(self):
        return str(self.car_class)

    def __repr__(self):
        return str(self.car_class)

    def __eq__(self,other):
        return other==self.car_class

if __name__=='__main__':
    env=PBSEnv([0,2,1,2,0,2])
    env.reset()

    while True:
        print('指令：1、环境step；2、环境可视化；3、连续step模式（在接车横移机选择目标时输入-2跳出）；4、重置系统；0、退出系统 ')
        command=input('请输入您的指令：')
        if command=='0':
            print('已退出系统，谢谢使用！')
            break
        elif command=='1':
            env.step_command()
        elif command=='2':
            env.render()
        elif command=='3':
            while True:
                if env.done:
                    print('游戏结束！最终输出序列为：{}，最终得分为：{}'.format(env.cars_out_order,env.done_score))
                    break
                if env.step_command():
                    print('已经跳出连续step模式，')
                    break
        elif command=='4':
            env.reset()

