from agents.human_keyinput import Human1,Human2
from agents.sort_machine_10132219 import SortMachine2,SortMachine1
from env.PBS import PBSEnv
import datetime
import pandas as pd


if __name__=='__main__':
    agent_list={'0':'human1','1':'huamn2','2':'SortMachine1','3':'SortMachine2'}
    cars_list2=[2,1,1,2,1,2,2,2,1,1,2,2,1,1,1,2,1,1,1,1,2,0,2,1,1,0,1,2,1,2,0,2,1,1,0,1,1,1,1,1,1,1,0,1,0,1,1,1,1,1,2,2,1,2,1,2,2,2,1,2,1,2,1,0,1,2,1,2,1,2,1,2,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0,1,2,2,2,1,0,2,2,2,2,1,2,1,2,2,1,2,1,2,2,1,1,2,1,1,2,2,2,1,2,2,1,2,0,2,1,2,2,2,2,2,0,2,1,1,1,1,1,2,2,1,1,1,1,1,1,1,1,1,2,1,1,1,1,1,2,1,1,1,1,1,2,1,1,1,1,1,2,1,1,1,1,1,1,1,1,2,1,1,1,1,1,1,1,1,1,1,1,2,1,1,1,0,1,2,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0,2,0,1,1,0,1,2,2,2,2,2,2,1,2,1,1,2,1,2,1,1,1,1,1,1,1,0,0,1,1,1,1,1,1,1,1,0,0,0,0,1,0,1,0,1,0,1,1,1,1,1,1,1,1,1,1,0,0,0,1,1,0,1,1,2,1,2,1,2,1,2,1,1,1,1,1,1,1,1,1,2,2,1,1,1,0,1,1,1,1,1,1]
    cars_list1=[2,1,1,2,2,2,2,2,1,1,2,2,1,1,1,2,1,1,1,2,2,0,2,1,2,0,2,2,1,2,0,2,1,1,0,1,2,1,1,1,1,1,0,1,0,1,1,1,1,2,2,2,1,2,1,2,2,2,2,2,1,2,2,0,1,2,2,2,1,2,1,2,2,2,2,1,1,1,2,1,1,2,1,1,1,2,1,1,2,1,1,1,2,1,1,2,2,1,1,0,1,2,2,2,1,0,2,2,2,2,1,2,1,2,2,2,2,1,2,2,1,1,2,2,1,2,2,2,2,2,2,1,2,0,2,1,2,2,2,2,2,0,2,1,1,1,1,1,2,2,1,1,1,2,1,2,1,1,1,2,1,1,1,2,1,2,1,1,2,1,1,2,1,1,2,2,1,2,1,1,2,1,2,2,1,1,2,1,1,1,1,2,2,2,1,1,2,2,2,1,1,1,0,1,2,1,1,1,1,1,1,1,2,1,1,1,1,2,1,2,1,1,1,1,2,0,2,0,2,2,0,1,2,2,2,2,2,2,1,2,1,1,2,1,2,1,1,1,1,1,1,1,0,0,1,2,1,1,1,1,1,2,0,0,0,0,1,0,1,0,1,0,1,1,1,1,1,1,1,1,1,1,0,0,0,2,1,0,2,2,2,2,2,1,2,2,2,1,1,2,2,1,1,2,1,1,2,2,1,2,1,0,1,1,1,1,1,1]
    logdir='log/log.csv'
    agent_choice=eval(input('请输入使用的智能体{}：'.format(agent_list)))
    which_car_list=eval(input('请输入使用的车辆序列[1,2]'))
    cars_list=cars_list1 if which_car_list==1 else cars_list2
    if agent_choice==0:
        human=Human1()
        my_env=PBSEnv(cars_list,0)
        state=my_env.reset()
        while True:
            action=human.take_action(state)
            my_env.render()
            state,done=my_env.step(action)
            my_env.render()
            if done:
                break
    elif agent_choice==1:
        human=Human2()
        my_env=PBSEnv(cars_list,1)
        state=my_env.reset()
        while True:
            action=human.take_action(state)
            my_env.render()
            state,done=my_env.step(action)
            my_env.render()
            if done:
                break
    elif agent_choice==3:
        agent=SortMachine2()
        my_env=PBSEnv(cars_list,1)
        state=my_env.reset()
        while True:
            action=agent.take_action(state)
            my_env.render()
            state,done=my_env.step(action)
            my_env.render()
            if done:
                break
    elif agent_choice==2:
        agent=SortMachine1()
        my_env=PBSEnv(cars_list,0)
        state=my_env.reset()
        while True:
            action=agent.take_action(state)
            my_env.render()
            state,done=my_env.step(action)
            my_env.render()
            if done:
                break
    print('游戏结束')
    my_env.logdf.to_csv(logdir)
