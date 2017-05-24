import socket
import sys
import json
import random
import threading

f = open("config.json", 'r+b')
setting = json.load(f)
host = setting['host']
port = int(setting['port'])
RP = 0
CON_STATUS = 0
MAX_DEGREE = 2
son_cons = []
son_addrs = []
info = {"status": "", "body": "", "sourceip": "", "sourceport": "", "targetip": "", "targetport": ""}

def pack(s, b, sip, sp, tip, tp):
    new_info = info
    new_info['status'] = s
    new_info['body'] = b
    new_info['sourceip'] = sip
    new_info['sourceport'] = sp
    new_info['targetip'] = tip
    new_info['targetport'] = tp
    in_json = json.dumps(new_info);
    return in_json

def create_socket():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    except socket.error, msg:
        print 'FAILED to create socket. Error code: ' + str(msg[0]) + ', Error message: ' + msg[1]
        sys.exit()
    print 'Socket Created'
    return s;

def connect_or_bind():
    global RP
    s = create_socket();
    try:
        s.connect((host, port))
        print 'Connected to server!'
    except socket.error, msg:
        print 'FAILED to connect. Error code: ' + str(msg[0]) + ', Error message: ' + msg[1]
        print 'Trying to bind this port.'
        RP = 1
    if RP == 1:
        try:
            s.bind(('', port))
            s.listen(10)
            print 'socket now listening...'
        except socket.error, msg:
            print 'FAILED to bind socket. Error code: ' + str(msg[0]) + ', Error message: ' + msg[1]
            #sys.exit()
    return s;

def connect_to_new(h, p):
    s = create_socket();
    try:
        s.connect((h, p))
        print 'New node connected! '+ h + ':'+ str(p) + ';'
    except socket.error, msg:
        print 'FAILED to connect. Error code: ' + str(msg[0]) + ', Error message: ' + msg[1]
    return s;

def get_command():
    command = raw_input();
    return str(command).split(' ')


def handle_msg_for_RP(s):
    while 1:
        conn, addr = s.accept()
        recv_info = json.loads(conn.recv(1024))
        if recv_info['status'] == 'REQ':
            if recv_info['body'] == 'new_connection':
                ack = pack('ACK', 'req_connection_recved', recv_info['targetip'], recv_info['targetport'], addr[0], addr[1])
                conn.sendall(ack)
                if len(son_cons) < MAX_DEGREE:
                    new_conn = connect_to_new(recv_info['sourceip'], recv_info['sourceport'])
                    son_cons.append(new_conn);
                    son_addrs.append(new_conn.getsockname());
                else:
                    for i in len(son_cons):
                        son_cons[i].sendall(json.dumps(recv_info));
            else:
                print recv_info['body'];
        else:
            print recv_info['status'];

        """something that handle the message that received from all nodes"""
        continue;

def handle_msg_for_normal_node(conn):
    while 1:
        recv_info = json.loads(conn.recv(1024))
        if recv_info['status'] == 'REQ':
            if recv_info['body'] == 'new_connection':
                if len(son_cons) < MAX_DEGREE:
                    new_conn = connect_to_new(recv_info['sourceip'], recv_info['sourceport'])
                    son_cons.append(new_conn)
                    son_addrs.append(new_conn.getsockname())
                else:
                    for i in len(son_cons):
                        son_cons[i].sendall(json.dumps(recv_info))
            else:
                print recv_info['body'];
        else:
            print recv_info['status'];

        """something that handle the message that received from father node"""
        continue;


def handle_connection(s):
    if RP == 1:
        print 'Current tree is empty! You are the root node of this group tree!'
        thread = threading.Thread(target=handle_msg_for_RP, args=(s,))
        thread.start()
        return;
    else:
        self_addr = s.getsockname()
        bind_port = random.randint(50000, 60000)
        thread = threading.Thread(target=create_connection_with_father_node, args=(bind_port,))
        thread.start()
        package = pack("REQ", "new_connection", self_addr[0], bind_port, host, port)
        s.sendall(package)
        recv_info = json.loads(s.recv(1024))
        if recv_info['status'] == 'ACK' and recv_info['body'] == 'req_connection_recved':
            s.close()


def wait_for_call_of_father_node(con_port):
    s = create_socket();
    try:
        s.bind(('', con_port))
        s.listen(10)
        print 'socket with father node now listening...'
    except socket.error, msg:
        print 'FAILED to bind socket. Error code: ' + str(msg[0]) + ', Error message: ' + msg[1]
    return s;

def create_connection_with_father_node(con_port):
    global CON_STATUS
    s = wait_for_call_of_father_node(con_port)
    while CON_STATUS != 1:
        conn, addr = s.accept()
        CON_STATUS = 1
    handle_msg_for_normal_node(conn)
    return;


def handle_message(target, msg, s):
    package = pack("""package for message""")
    if RP == 1:
        s.close();
        for i in len(son_cons):
            son_cons[i].sendall(package);
    else:
        s.sendall(package);
        recv_info = json.loads(s.recv(1024))
        if """ack from RP confirming package pass""":
            s.close()

def index():
    while 1:
        command = get_command();
        if (command[0] == 'connect'):
            s = connect_or_bind()
            handle_connection(s)
            continue;
        elif (command[0] == 'send' and CON_STATUS == 1):
            s = connect_or_bind()
            handle_message(command[1], command[2], s)
            continue;
        elif (command[0] == 'quit' and CON_STATUS == 1):
            s = connect_or_bind()
            handle_quit(s)
            continue;
        elif (CON_STATUS == 0):
            print 'The connection is not exist. Maybe you should type "connect" first?'
            continue;
        else:
            print command;

index();
#connect_or_bind();
