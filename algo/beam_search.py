from utils.score import score

class BeamSearch():
    def __init__(self,car_in_order,k=3,d=20):
        self.car_in_order=car_in_order #最开始车辆种类的排序，用来查看序号车的种类
        self.length=len(car_in_order)
        self.beam_tree=BeamTree(self.length)
        self.current_node=self.beam_tree.rootnode

    def compute_rotation_proceed(self,rotation,last_rotation):#计算一个轮换的净收益
        '''
        计算一个轮换的净收益需要当前轮换和上一个轮换
        '''
        if last_rotation==None:
            cars_before_order=[self.car_in_order[i] for i in rotation.numlist_before] #轮换前车辆种类的排序
            cars_after_order=[self.car_in_order[i] for i in rotation.numlist_after]   #轮换后车辆种类的排序
            return score(cars_after_order)-score(cars_before_order)-(rotation.take_num+36-rotation.drop_num)*4.5*0.001-0.2
        elif rotation.take_num>last_rotation.drop_num: #返回车道上无车
            cars_before_order=[self.car_in_order[i] for i in rotation.numlist_before] #轮换前车辆种类的排序
            cars_after_order=[self.car_in_order[i] for i in rotation.numlist_after]   #轮换后车辆种类的排序
            return score(cars_after_order)-score(cars_before_order)-(rotation.take_num+36-rotation.drop_num)*4.5*0.001-0.2
        else: #返回车道上有车
            cars_before_order=[self.car_in_order[i] for i in rotation.numlist_before] #轮换前车辆种类的排序
            cars_after_order=[self.car_in_order[i] for i in rotation.numlist_after]   #轮换后车辆种类的排序
            return score(cars_after_order)-score(cars_before_order)-(last_rotation.drop_num+rotation.take_num-last_rotation.take_num-rotation.drop_num)*4.5*0.001-0.2

    def search_step(self): #拓展当前节点的子节点
        #bbbbbbbbbbbb程序可能存在因为没有输出序列功能而存在的问题
        if self.current_node==self.beam_tree.rootnode: #当前节点是根节点
            max_list=[] #存储当前最大的k个total_proceed
            for i in range(36): #寻找最大的k个轮换进行扩建子树
                rotation_current=Rotation(list(range(self.length)),0,i+1)
                proceed_current=self.compute_rotation_proceed(rotation_current,None)
                if len(max_list)<=self.k and proceed_current>0: #k个还没有存满
                    max_list.append(proceed_current)
                    self.current_node.children_list.append(BeamTreeNode(rotation_current,self.current_node.total_proceed+proceed_current,self.current_node,[]))
                else: #k个存满了
                    if min(max_list)<proceed_current: #当前价值比最小的大
                        min_index=max_list.index(min(max_list))
                        max_list.pop(min_index)
                        self.current_node.children_list.pop(min_index)
                        max_list.append(proceed_current)
                        self.current_node.children_list.append(BeamTreeNode(rotation_current,self.current_node.total_proceed+proceed_current,self.current_node,[]))
        else: #当前节点不是根节点
            max_list=[]
            numlist_current=self.current_node.rotation.numlist_after

            for i in range(self.current_node.rotation.drop_num,1+self.current_node.rotation.drop_num+numlist_current[0]-self.current_node.rotation.take_num):
                rotation_current=Rotation(numlist_current,numlist_current[0],i)
                proceed_current=self.compute_rotation_proceed(rotation_current,self.current_node.rotation)
                if len(max_list)<=self.k and proceed_current>0:
                    max_list.append(proceed_current)
                    self.current_node.children_list.append(BeamTreeNode(rotation_current,self.current_node.total_proceed+proceed_current,self.current_node,[]))
                else:
                    if min(max_list)<proceed_current:
                        min_index=max_list.index(min(max_list))
                        max_list.pop(min_index)
                        self.current_node.children_list.pop(min_index)
                        max_list.append(proceed_current)
                        self.current_node.children_list.append(BeamTreeNode(rotation_current,self.current_node.total_proceed+proceed_current,self.current_node,[]))

    
    
class BeamTree():
    def __init__(self,length):
        self.length=length
        self.rootnode=BeamTreeNode(None,0,None,[])

class BeamTreeNode():
    def __init__(self,rotation,total_proceed,parent,children_list):
        self.rotation=rotation #当前节点的上一个节点到当前节点的轮换
        self.total_proceed=total_proceed #从开始到当前节点的总收益
        self.parent=parent
        self.children_list=children_list

class Rotation(): #轮换
    def __init__(self,numlist_before,take_num,drop_num):
        self.take_num=take_num #拿取的车在初始序列中的序号(m)
        self.drop_num=drop_num #放置在哪辆车后面(n)
        self.numlist_before=numlist_before #轮换发生之前的排列，其中的元素是序号不是车的种类
    
    @property
    def numlist_after(self):
        if self.take_num==self.drop_num:
            return self.numlist_before
        numlist_copy=self.numlist_before
        pop_num=numlist_copy.pop(numlist_copy.index(self.take_num))
        numlist_copy.insert(numlist_copy.index(self.drop_num)+1,pop_num)
        return numlist_copy


