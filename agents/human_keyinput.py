
class Human1():
    def __init__(self):
        pass

    def take_action(self,state): 
        '''
        从键盘上读取动作，返回一个action
        state为一个字典，想调用什么直接用字典就行
        action的列表组成为[左还是右,动作]
        '''
        if not state['which_to_chose']:#读取一个给接车横移机的动作
            if state['parking_arr'][2][0]!=-1:
                action_list=range(6,12)
                while True:#知道输入正确的动作指令为止
                    action=[0,eval(input('请输入接车横移机(左)动作[6~11]：'))]
                    if action[1] in action_list:
                        break
            else:
                action_list=range(-1,12)
                while True:
                    action=[0,eval(input('请输入接车横移机(左)动作[-1~11]：'))]
                    if action[1] in action_list:
                        break
        else:#读取一个给送车横移机的动作
            action_list=state['deliver_chose_target']
            while True:
                action=[1,eval(input('请输入送车横移机(右)动作{}：'.format(state['deliver_chose_target'])))]
                if action[1] in action_list:
                    break
        return action
            
class Human2():
    def __init__(self):
        pass

    def take_action(self,state): 
        '''
        从键盘上读取动作，返回一个action
        state为一个字典，想调用什么直接用字典就行
        action的列表组成为[左还是右,动作]
        '''
        if not state['which_to_chose']:#读取一个给接车横移机的动作
            action_list=range(-1,12)
            while True:
                action=[0,eval(input('请输入接车横移机(左)动作[-1~11]：'))]
                if action[1] in action_list:
                    break
        else:#读取一个给送车横移机的动作
            action_list=range(-1,12)
            while True:
                action=[1,eval(input('请输入送车横移机(右)动作[-1~11]：'))]
                if action[1] in action_list:
                    break
        return action