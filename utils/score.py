'''
0：四驱燃油；1：两驱混动；2：两驱燃油
'''
def score(cars_list):
    return score1(cars_list)*0.4+score2(cars_list)*0.3


def score1(car_list):
    last_hybrid_num=-1
    score=100
    for i in range(len(car_list)):
        if car_list[i]==1:
            if last_hybrid_num!=-1:
                if i-last_hybrid_num!=3:
                    score-=1
            last_hybrid_num=i
    return score


def score2(cars_list):
    #四驱车：0；两驱车：1、2
    #转化成是否是四驱
    car_class=[0,1,1] #索引车的类型，转化为是不是四驱
    out_cars_class=[car_class[i] for i in cars_list]

    #分块
    block_list=[]
    last_car_num=0
    cut=False
    for i in range(1,len(cars_list)):
        if out_cars_class[i]!=out_cars_class[last_car_num] and not cut:
            cut=True
            continue
        if out_cars_class[i]==out_cars_class[last_car_num] and cut:
            block_list.append(out_cars_class[last_car_num:i])
            cut=False
            last_car_num=i
    block_list.append(out_cars_class[last_car_num:])
    print(block_list)
    #算分
    score=100
    for block in block_list:
        if block.count(0)!=block.count(1):
            score-=1
    
    return score

if __name__=='__main__':
    cars_list=eval(input('请输入序列：'))
    print(score(cars_list))