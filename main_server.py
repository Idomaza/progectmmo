import socket
import threading
import queue
import time
import pickle
import random

outgoingQ = queue.Queue()


class ThreadedServer(threading.Thread):
    def __init__(self, host, port):
        super(ThreadedServer, self).__init__()
        self.player_list = []
        self.servers_list = []
        self.map_segments = []
        self.host = host
        self.port = port
        self.tcp_q = queue.Queue()
        self.udp_q = queue.Queue()
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        self.sock.bind((self.host, self.port))

        p = sendTCP(self.tcp_q)
        p.start()
        p = sendUDP(self.udp_q)
        p.start()

    def run(self):
        self.sock.listen(5)
        while True:
            client, address = self.sock.accept()
            message = client.recv(1024)
            message = pickle.loads(message)
            if message[0] == 'server':
                map_seg = ''
                if len(self.servers_list) == 0:
                    map_seg = mapSegment(0, 0, 3200, 2400)
                if len(self.servers_list) == 1:
                    map_seg = mapSegment(3200, 0, 6400, 2400)
                if len(self.servers_list) == 2:
                    map_seg = mapSegment(0, 2400, 3200, 4800)
                if len(self.servers_list) == 3:
                    map_seg = mapSegment(3200, 2400, 6400, 4800)
                self.map_segments.append(map_seg)
                server = listenToServer(client, (address[0], message[1]), self.player_list, self.servers_list, map_seg, self.tcp_q, self.udp_q)
                self.servers_list.append(server)
                server.start()
            if message[0] == 'client':
                index = self.which_server()
                pos = self.map_segments[index].give_pos()
                self.tcp_q.put([client, [self.servers_list[index].tcp_address, pos]])
                clients = listenToClient(client, address, self.player_list, self.servers_list, self.tcp_q)
                self.player_list.append(clients)
                clients.start()

    def which_server(self):
        number_of_client = []
        for server in self.servers_list:
            number_of_client.append(server.players)
        min_value = min(number_of_client)
        min_index = number_of_client.index(min_value)
        self.servers_list[min_index].players += 1
        return min_index


class listenToServer(threading.Thread):
    def __init__(self, client, address, player_list, server_list, map_seg, tcp_q, udp_q):
        super(listenToServer, self).__init__()
        self.tcp_client = client
        self.tcp_address = address

        while True:
            try:
                udp_address = (self.tcp_address[0], random.randint(5000, 50000))
                self.udp_client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                self.udp_client.bind(udp_address)
                break
            except Exception:
                print('try to give port again')
                pass

        self.server_list = server_list
        self.player_list = player_list
        self.map_seg = map_seg
        self.players = 0

        self.size = 1024

        self.tcp_q = tcp_q
        self.udp_q = udp_q
        self.tcp_q.put([client, udp_address])
        self.tcp_q.put([client, ['map', map_seg]])

        data = self.udp_client.recvfrom(self.size)
        self.udp_address = data[1]

        self.listen_tcp = threading.Thread(target=self.tcp_listen)
        self.listen_tcp.start()
        self.listen_udp = threading.Thread(target=self.udp_listen)
        self.listen_udp.start()

    def tcp_listen(self):
        print('running ', self.tcp_address)
        while True:
            try:
                data = self.tcp_client.recv(self.size)
                massage = pickle.loads(data)
                print(massage)
            except Exception as error:
                print(error)
                self.tcp_client.close()
                return

    def udp_listen(self):
        while True:
            try:
                data = self.udp_client.recvfrom(self.size)
                massage = pickle.loads(data[0])
                for server in self.server_list:
                    if server != self:
                        self.udp_q.put([massage, server.udp_address, server.udp_client])
            except Exception as error:
                print(error)
                self.udp_client.close()
                return


class listenToClient(threading.Thread):
    def __init__(self, client, address, player_list, server_list, q):
        super(listenToClient, self).__init__()
        self.client = client
        self.address = address
        self.server_list = server_list
        self.player_list = player_list
        self.players = 0
        self.size = 1024
        self.q = q

    def run(self):
        print('running ', self.address)
        while True:
            try:
                data = self.client.recv(self.size)
                massage = pickle.loads(data)
                if massage != '1':
                    print(massage)
                if type(massage) == list:
                    for server in self.server_list:
                        if not server.map_seg.is_out_of_bounds(massage):
                            self.q.put([self.client, server.tcp_address])
                else:
                    if massage == 'exit':
                        for i, player in enumerate(self.player_list):
                            if player == self:
                                self.player_list[i] = ''
                        self.client.close()
                        return
            except Exception:
                for i, player in enumerate(self.player_list):
                    if player == self:
                        self.player_list[i] = ''
                self.client.close()
                return


class sendTCP(threading.Thread):
    def __init__(self, q):
        super(sendTCP, self).__init__()

        self.size = 1024
        self.q = q

    def run(self):
        while True:
            try:
                if not self.q.empty():
                    message = self.q.get()
                    message[0].send(pickle.dumps(message[1]))
                time.sleep(0.00001)
            except:
                pass


class sendUDP(threading.Thread):
    def __init__(self, q):
        super(sendUDP, self).__init__()
        self.size = 1024
        self.q = q

    def run(self):
        while True:
            try:
                if not self.q.empty():
                    message = self.q.get()
                    client = message[2]
                    client.sendto(pickle.dumps(message[0]), message[1])
                time.sleep(0.00001)
            except:
                pass


class mapSegment:
    def __init__(self, start_x, start_y, end_x, end_y):
        self.start_x = start_x
        self.start_y = start_y
        self.end_x = end_x
        self.end_y = end_y

    def give_pos(self):
        while True:
            position = [random.randint(self.start_x, self.end_x), random.randint(self.start_y, self.end_y)]
            if 640 < position[0] < 5792 and 480 < position[1] < 4352:
                break
        return position

    def is_edge(self, pos):
        if 0 < self.start_x:
            if abs(pos[0] - self.start_x) < 320:
                return True
        if 6400 > self.end_x:
            if abs(pos[0] - self.end_x) < 320:
                return True
        if 0 < self.start_y:
            if abs(pos[1] - self.start_y) < 240:
                return True
        if 4800 > self.end_y:
            if abs(pos[1] - self.end_y) < 240:
                return True
        return False

    def is_out_of_bounds(self, pos):
        if self.start_x > pos[0]:
            return True
        if self.end_x < pos[0]:
            return True
        if self.start_y > pos[1]:
            return True
        if self.end_y < pos[1]:
            return True
        return False


if __name__ == "__main__":
    Ts = ThreadedServer('0.0.0.0', 8080)
    Ts.start()
    Ts.join()
