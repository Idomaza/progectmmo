import socket
import pickle
import threading


class client:
    def __init__(self):
        self.tcp_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.tcp_client.connect(('10.100.102.27', 8080))
        self.tcp_client.send(pickle.dumps(['client']))
        msg = self.tcp_client.recv(1024)
        msg = pickle.loads(msg)
        self.udp_address, self.udp_port = msg[0]
        self.pos = msg[1]
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.sendto(pickle.dumps(self.pos), (self.udp_address, self.udp_port))
        self.start_listen()

    def listen_udp(self):
        while True:
            msg = pickle.loads(self.socket.recvfrom(1024)[0])
            if type(msg) == str:
                if msg.isdigit():
                    self.udp_port = int(msg)
            else:
                self.socket.sendto(pickle.dumps(msg), (self.udp_address, self.udp_port))
    
    def listen_tcp(self):
        while True:
            msg = self.tcp_client.recv(4096)
            msg = pickle.loads(msg)
            if type(msg) == str:
                self.tcp_client.send(pickle.dumps(msg))

    def start_listen(self):
        t1 = threading.Thread(target=self.listen_udp)
        t1.start()
        t2 = threading.Thread(target=self.listen_tcp)
        t2.start()


if __name__ == '__main__':
    cl = client()
