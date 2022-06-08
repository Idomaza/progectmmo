import time
from sprites import *
from config import *
import threading
import socket
import queue
import pickle


class Game:
    def __init__(self):
        self.client = ThreadedClient('10.100.102.27', 8080)
        self.client.start()
        self.client.start_listen()

        pygame.init()
        self.screen = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT))
        self.background = pygame.image.load('img/map9.png')

        self.serial = 0

        self.clock = pygame.time.Clock()
        self.running = True

        time.sleep(0.5)

        try:
            self.playing = True

            self.all_sprites = pygame.sprite.LayeredUpdates()
            self.all_shots = pygame.sprite.LayeredUpdates()
            self.other_shots = pygame.sprite.LayeredUpdates()
            self.other_players = pygame.sprite.LayeredUpdates()

            self.player = Player(self, self.client.pos)

        except Exception as error:
            print(error)
            self.client.exit = True
            exit(1)

    def events(self):
        # if error
        if type(self.client.massage) == str:
            if self.client.massage == 'exit':
                self.playing = False
                self.running = False
        # game loop event
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.playing = False
                self.running = False
                self.client.exit = True
            if event.type == pygame.MOUSEBUTTONDOWN:
                if pygame.mouse.get_pressed()[0]:
                    Shot(self, [self.player.x, self.player.y], [pygame.mouse.get_pos()[0], pygame.mouse.get_pos()[1]])
                    self.serial += 1

    def update(self):
        # game loop update
        self.all_sprites.update()
        self.all_shots.update()
        self.other_players.update()
        self.other_shots.update()

    def draw(self):
        self.screen.blit(self.background, (0, 0), (self.player.pos[0] - 320, self.player.pos[1] - 240, WIN_WIDTH, WIN_HEIGHT))
        if type(self.client.massage) == list:
            for pos in self.client.massage:
                self.create_enemy(pos)
            self.other_shots.draw(self.screen)
            self.other_players.draw(self.screen)
            hits = self.player.collide()
            if hits:
                self.client.exit = True
                exit(1)
            self.other_shots = pygame.sprite.LayeredUpdates()
            self.other_players = pygame.sprite.LayeredUpdates()
        self.all_sprites.draw(self.screen)
        self.clock.tick(FPS)
        pygame.display.update()

    def main(self):
        # game loop
        while self.playing:
            start = time.time()

            self.events()
            self.update()
            self.draw()

            player_pos = self.player.get_pos()
            player_pos = player_pos[:-1:]
            positions = [player_pos]

            for shot in self.all_shots:
                pos = shot.get_pos()
                positions.append(pos)
            self.client.add_message([positions, (self.client.host, self.client.port)])

            time.sleep(max(1 / 60 - (time.time() - start), 0))
        self.running = False

    def create_enemy(self, pos):
        x = 32
        y = 32
        if pos[1] < 0:
            x = 32 + pos[1]
        if pos[2] < 0:
            y = 32 + pos[2]

        if pos[0] == 'p':
            Other_Player(self, x, y, [pos[1], pos[2]])
        else:
            Other_Shot(self, pos[1], pos[2])

    def game_over(self):
        pass

    def intro_screen(self):
        pass


class ThreadedClient(threading.Thread):
    def __init__(self, host, port):
        threading.Thread.__init__(self)
        # set up queues
        self.send_q = queue.Queue()
        # connect to main_server
        message, self.main_server = connect_to_main_server(host, port)
        self.main_port = port
        self.main_host = host

        self.host, self.port = message[0]
        self.pos = message[1]
        # connect to the server
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # get port
        # self.add_message([self.pos, (self.host, self.port)])
        self.add_message([self.pos, (self.host, self.port)])
        # massage received
        self.massage = None
        # if player exit
        self.exit = False
        self.pause = False

    # LISTEN
    def listenToServer(self):
        while True:  # loop forever
            try:
                if not self.pause:
                    if self.exit:
                        self.add_message(['exit', (self.host, self.port)])
                        self.socket.close()
                        self.main_server.close()
                        return
                    message = pickle.loads(self.socket.recvfrom(4096)[0])
                    print(message)
                    if type(message) == str:
                        if message.isdigit():
                            self.port = int(message)
                    else:
                        if message[0] == 'move':
                            self.add_message_main(message[1])
                            print(message[1])
                            self.pause = True
                        else:
                            message.pop(0)
                            self.massage = message
            except Exception as error:
                print(error)
                self.add_message(['exit', (self.host, self.port)])
                self.massage = 'exit'
                self.socket.close()
                return

    def listenToMainServer(self):
        self.add_message_main('1')
        while True:  # loop forever
            try:
                if self.exit:
                    self.add_message_main('exit')
                    self.socket.close()
                    self.main_server.close()
                    return
                message = self.main_server.recv(4096)
                message = pickle.loads(message)
                if type(message) == str:
                    self.add_message_main(message)
                else:
                    self.host, self.port = message
                    # get port
                    self.add_message([self.pos, (self.host, self.port)])
                    self.pause = False
            except Exception as error:
                print(error)
                self.add_message_main('exit')
                self.massage = 'exit'
                self.main_server.close()
                return

    def start_listen(self):
        t1 = threading.Thread(target=self.listenToServer)
        t1.start()
        t2 = threading.Thread(target=self.listenToMainServer)
        t2.start()

    # ADD MESSAGE
    def add_message(self, msg):
        # put message into the send queue
        if msg[0] != '':
            self.send_q.put(msg)
            self.send_message()

    def add_message_main(self, msg):
        # put message into the send queue
        if msg[0] != '':
            self.send_q.put(msg)
            self.send_message_main()

    # SEND MESSAGE
    def send_message(self):
        # send message
        msg = self.get_send_q()
        # send all hte position to the server
        try:
            self.socket.sendto(pickle.dumps(msg), msg[1])
            time.sleep(0.001)
        except:
            pass

    def send_message_main(self):
        # send message
        msg = self.get_send_q()
        # send all hte position to the server
        try:
            self.main_server.send(pickle.dumps(msg))
            time.sleep(0.001)
        except:
            pass

    # if nothing in q, prints "empty" instead of stalling program
    def get_send_q(self):
        if self.send_q.empty():
            return "empty!"
        else:
            msg = self.send_q.get()
            return msg


def connect_to_main_server(host, port):
    main_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    main_server.connect((host, port))

    message = ['client']
    main_server.send(pickle.dumps(message))

    message = main_server.recv(1024)
    return pickle.loads(message), main_server


if __name__ == '__main__':
    g = Game()
    while g.running:
        g.main()
    pygame.quit()
