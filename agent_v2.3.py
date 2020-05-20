import socket
import threading
import forward
import time

# 执行体池中所有dns服务器数量
dns_all = 3
# dns服务器（执行体）数量
dns_num = 3
# 与dns服务器通信的socket列表
dns_skt = [None] * dns_all
# 存储各dns服务器响应报文的列表,按dns报文id存储
rsp_pkt = [None] * 0xFFFF
for i in range(0, 0xFFFF, 1):
    rsp_pkt[i] = [None] * dns_all

# 存储从各响应报文中提取的ip地址的列表，4节分别存储,按dns报文id存储
ip = [None] * 0xFFFF
for i in range(0, 0xFFFF, 1):
    ip[i] = [None] * dns_all
    for j in range(0, dns_all, 1):
        ip[i][j] = [None, None, None, None]

# 创建socket，分别用于与客户端和dns服务器通信；设置通信端口
cli_skt = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
cli_skt.bind(('', 53))
for i in range(0, dns_all, 1):
    dns_skt[i] = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # dns_skt[i].setblocking(0)
    dns_skt[i].bind(('', 11111 * (i + 1)))

# 存储客户端ip&端口信息的缓存区，防止客户端报文发送速度过快导致客户端信息丢失,按dns报文id存储
client_addr = [('', 0)] * 0xFFFF

buf_size = 1024
# 在线dns执行体代号列表
dns_selected = [[None] * dns_num] * buf_size
# 存储客户端dns查询报文id的缓存区，防止因dns服务器无响应等原因导致响应报文混乱
dns_id = [None] * buf_size
# 用于存储各dns服务器响应结果的票数
count = [0] * dns_all


# 接收客户端的查询请求，并转发至各dns服务器
def query():
    global client_addr
    global dns_selected
    global dns_id
    # 所有dns服务器地址和端口列表
    dns_addr = [('10.0.3.4', 53), ('10.0.3.8', 53), ('10.0.3.9', 53)]
    # dns服务器代号
    dns_code = [0] * dns_all
    for k in range(0, dns_all, 1):
        dns_code[k] = k
    j = 0
    while True:
        # 因为后续需要对客户端回复，因此使用带有发送端ip地址和端口信息的recvfrom()
        rec_pkt = cli_skt.recvfrom(1024)
        # 提取需要转发的dns查询报文
        dns_pkt = rec_pkt[0]
        # 定位到dns查询类型字段
        k = 12
        while dns_pkt[k] != 0x00:
            k += 1
        # 只转发ipv4查询类型的dns请求
        if dns_pkt[k+1] == 0x00 and dns_pkt[k+2] == 0x01:
            # 从第一个变量数组中选出数量为第二个变量的执行体。这是完全随机调度。
            dns_selected[j] = forward.forward_ran(dns_code, dns_num)
            # 提取客户端ip和端口
            dns_id[j] = dns_pkt[0] * 256 + dns_pkt[1]
            client_addr[dns_id[j]] = rec_pkt[1]
            # 发送数据包
            for k in range(0, dns_num, 1):
                dns_skt[dns_selected[j][k]].sendto(dns_pkt, dns_addr[dns_selected[j][k]])
            if j == buf_size - 1:
                j = 0
            else:
                j += 1
            dns_selected[j] = [None] * dns_num


# 接收各dns服务器的响应报文，并提取关键的ip地址字段
def dns_response(k):
    global rsp_pkt
    global ip

    # 通过try..except写法可以以非阻塞方式接收响应报文，但使用非阻塞方式测试时有时会报错
    # 调试变量发现较早生成的线程所对应的dns响应报文不存在
    # 猜测可能是由于dns服务器响应有延误或无响应，非阻塞的接收函数没有接收到响应报文就执行裁决步骤
    # try:
    s = dns_skt[k].recv(2048)
    # 获取报文id 256 == 16 * 16
    s_id = s[0] * 256 + s[1]
    # 按报文id存储报文
    rsp_pkt[s_id][k] = s
    # 获取响应报文中回答区域数量
    answer_num = s[6] * 256 + s[7]
    # 把索引定位至回答区域
    a = 12
    while s[a] != 0:
        a += 1
    a += 5
    # 提取ip地址
    for b in range(0, answer_num, 1):
        # 把索引定位至
        while s[a] != 0xC0:
            a += 1
        # 获取回答资源的查询类型
        answer_type = s[a + 2] * 256 + s[a + 3]
        # 获取回答资源的数据长度
        answer_len = s[a + 10] * 256 + s[a + 11]
        # 查询类型是ipv4地址，获取该地址;否则跳过该回答区域
        if answer_type == 0x01:
            ip[s_id][k][0] = s[a + 12]
            ip[s_id][k][1] = s[a + 13]
            ip[s_id][k][2] = s[a + 14]
            ip[s_id][k][3] = s[a + 15]
        a = a + 12 + answer_len
    # except BlockingIOError:
    # pass


# 多数表决
def voter(m):
    global count
    # 用于存储各dns服务器响应结果的票数
    count = [0] * dns_all
    # 统计票数
    for x in range(0, dns_num, 1):
        if ip[dns_id[m]][dns_selected[m][x]] != [None, None, None, None]:
            count[dns_selected[m][x]] += 1
            for y in range(x + 1, dns_num, 1):
                if ip[dns_id[m]][dns_selected[m][x]] == ip[dns_id[m]][dns_selected[m][y]]:
                    count[dns_selected[m][x]] += 1
                    count[dns_selected[m][y]] += 1
                # 若票数超过一半，则作为裁决结果，返回这个结果的索引
                if count[dns_selected[m][x]] > dns_num/2:
                    return dns_selected[m][x]
    # 不存在票数多于一半的结果，则返回最大票数所对应的索引
    # 若同时存在多个票数相同的不同结果，index()函数会取索引最小的一个
    return count.index(max(count))


# 开启接收响应报文的线程，对dns查询结果进行裁决，把裁决结果返回至客户端
def agent_response():
    global ip
    # dns并行线程列表
    dns_threads = [None] * dns_num
    while True:
        m = 0
        while m < buf_size:
            if dns_selected[m] != [None] * dns_num:
                for n in range(0, dns_num, 1):
                    # 建立线程，分别接收各dns响应
                    dns_threads[n] = threading.Thread(target=dns_response, args=(dns_selected[m][n], ))
                # print(time.time())
                for n in range(0, dns_num, 1):
                    # 开启线程
                    dns_threads[n].start()
                for n in range(0, dns_num, 1):
                    # 阻塞主线程，等子线程结束
                    dns_threads[n].join()
                # print(time.time())
                # 各子线程结束后，进行裁决
                # 将票数最多的结果（之一）采纳为裁决结果，向客户端发送响应报文
                res = voter(m)
                for n in range(0, dns_all, 1):
                    ip[dns_id[m]][n] = [None, None, None, None]
                if count != [0] * dns_all:
                    cli_skt.sendto(rsp_pkt[dns_id[m]][res], client_addr[dns_id[m]])
                # print(m, count)
                m += 1
                # print(time.time())


if __name__ == '__main__':
    print('running...')
    # 建立线程，分别用于查询和响应
    que = threading.Thread(target=query)
    rsp = threading.Thread(target=agent_response)
    # 开启线程
    que.start()
    rsp.start()
    # 阻塞主线程，等子线程结束
    que.join()
    rsp.join()
    # 关闭连接
    cli_skt.close()
    for c in range(0, dns_num, 1):
        dns_skt[c].close()
