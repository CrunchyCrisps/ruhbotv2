import socket
import sys
import time
import os
import config
from multiprocessing import Pool

log_path = 'C:\\Users\\Raffael\\Desktop\\logs\\'

class ChatBot(object):
    def __init__(self, channel):
        self.channel = channel
        self.server = config.SERVER
        self.port = config.PORT
        self.token = config.OAUTH_TOKEN
        self.socket = socket.socket()
        self.nick = config.NICK

    def connect(self):
        try:
            self.socket.connect((self.server, self.port))
            return True
        except:
            return False

    def login(self):
        self.socket.send("PASS {}\r\n".format(self.token).encode('utf-8'))
        self.socket.send("NICK {}\r\n".format(self.nick).encode('utf-8'))
        self.socket.send("JOIN #{}\r\n".format(self.channel).encode('utf-8'))

    def get_message(self):
        return self.socket.recv(1024).decode('utf-8')

def run(channel):
    bot = ChatBot(channel)
    pre_login = time.time()
    if bot.connect():
        print('Connected to the server in {} seconds.\n'.format(round(time.time() - pre_login, 2)))
        bot.login()
    else:
        print('Failed to connect. Please try again.')
        sys.exit()

    # logging
    bot_names = ['streamelements', 'nightbot', 'moobot', 'hnlbot']
    collected_messages = 0
    while 1:
        response = bot.get_message()
        if len(response.split()) > 2:
            type = response.split()[1]
            if type == 'PRIVMSG':
                # logging messages
                user = response.split('!')[0][1:]
                message = response.split('#{} :'.format(channel.lower()))[1]
                if user not in bot_names and not message.startswith('!'):
                    with open('{}{}.csv'.format(log_path, channel), 'a', encoding='utf-8') as log_file:
                        log_file.write('"{}","{}"\n'.format(user, message.rstrip()))
                    # update message count and print it
                    collected_messages += 1
                    if collected_messages % 100 == 0:
                        print('{}: {} messages.'.format(channel, collected_messages))

if __name__ == '__main__':
    channels = sys.argv[1:]
    try:
        p = Pool(os.cpu_count())
        p.map(run, channels)
    finally:
        p.close()
        p.join()