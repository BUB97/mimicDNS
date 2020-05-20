# coding=utf-8
import random
import heapq


def ip_input(m):
    b = [0 for i in range(m)]
    key = 1
    for i in range(m):
        key = str(key)
        print("请输入第" + key + "个执行体的ip地址：")
        b[i] = raw_input()
        key = int(key)
        key = key + 1
    print("资源池中执行体的ip地址:")
    print(b)
    return b


def forward_ran(obj_ip, n):
    obj_selected = random.sample(obj_ip, n)
    print("选中的执行体：")
    print(obj_selected)


def forward_adv(obj_ip, n):
    S_A = [0 for i in range(len(obj_ip))]
    for obj_order in range(len(obj_ip)):
        S_A[obj_order] = random.randint(50, 100)
    print("各个执行体的实际性能得分S_A:")  # 生成实际性能评估S_A
    print(S_A)
    S_C = [0 for i in range(len(obj_ip))]
    ip_save = [[0] * (n - 1) for i in range(len(obj_ip))]  # 存储适配执行体的IP顺序编号
    for obj_order in range(len(obj_ip)):  # 以每个执行体依次作为种子执行体
        S_B = [0 for i in range(len(obj_ip))]  # 初始化适配性得分S_B，执行体集合评估S_C
        for obj_order1 in range(len(obj_ip)):  # 得到其余执行体的适配性得分S_B
            if obj_order1 != obj_order:
                S_B[obj_order1] = random.randint(40, 100)
        # print(S_B)
        ip_save[obj_order] = map(S_B.index, heapq.nlargest(n - 1, S_B))  # 存储适配执行体的IP顺序编号
        SB_nlar = heapq.nlargest(n - 1, S_B)  # 得到S_B的n-1个最大值
        S_C[obj_order] = S_A[obj_order] + sum(SB_nlar)  # 计算每个执行体集合的S_C
        # print(ip_save)
    print("将各个执行体依次作为种子执行体，分别得到的适配执行体为：")
    print(ip_save)
    print("各个执行体集合的分数S_C：")
    print(S_C)
    SC_index = map(S_C.index, heapq.nlargest(3, S_C))  # 从S_C中选出得分最高的三个执行体集合，并从中随机选择一个进行调度
    SC_selected = random.sample(SC_index, 1)  # SC_seleted表示被选中的执行体集合编号
    # print(SC_index)
    print("选中的执行体及其集合下标：")
    print(SC_selected)
    ip_selected = [0 for i in range(n)]
    for x in range(n - 1):
        ip_selected[x] = obj_ip[ip_save[SC_selected[0]][x]]  # 先从ip_save中得到选中执行体集合中的适配执行体，并获得对应ip
    ip_selected[n - 1] = obj_ip[SC_selected[0]]  # 再得到选中执行体集合中的种子执行体IP
    print("选中的执行体ip：")
    print(ip_selected)

# obj_ip = ip_input(5)
# forward_adv(obj_ip, 3)
