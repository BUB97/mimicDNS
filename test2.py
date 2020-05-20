# coding=utf-8
import forward

# 第一种调用调度模块方法，先将网址按照这种格式输入，注意是字符串。
obj_ip = ['116.57.115.90', '116.57.115.91', '116.57.115.92', '116.57.115.93', '116.57.115.94']
forward.forward_ran(obj_ip, 3)  # 从第一个变量数组中选出数量为第二个变量的执行体。这是完全随机调度。
# forward.forward_adv(obj_ip, 3)  # 第二种调度算法，这是我还在研究的优化种子调度算法的简化方法

# 第二种调用调度模块方法，每次调用均需要自己输入各个ip，输入时不需引号。
# forward.forward_adv(forward.ip_input(5),3)  #优化种子调度算法，5个选出3个
# forward.forward_ran(forward.ip_input(5),3)  #完全随机调度
