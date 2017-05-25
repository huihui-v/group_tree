# -*-coding: utf-8 -*-
import socket
import sys
import json
import random
import threading

f = open("/home/xingjf/桌面/py/group_tree/config.json", 'r+b')
setting = json.load(f)
host = setting['host']
port = int(setting['port'])
bind_port = random.randint(50000, 60000)
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
    #print 'Socket Created'
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
        print 'New node trying to connect: '+ h + ':'+ str(p) + ';'
    except socket.error, msg:
        print 'FAILED to connect. Error code: ' + str(msg[0]) + ', Error message: ' + msg[1]
    return s;

def get_command():
    command = raw_input();
    return str(command).split(' ')


def handle_msg_for_RP(s):
    while 1:
        conn, addr = s.accept()
        self_addr = conn.getsockname()
        recv_info = json.loads(conn.recv(1024))
        if recv_info['status'] == 'REQ':
            if recv_info['body'] == 'new_connection':
                ack = pack('ACK', 'req_connection_recved', self_addr[0], self_addr[1], addr[0], addr[1])
                conn.sendall(ack)
                if len(son_cons) < MAX_DEGREE:
                    new_conn = connect_to_new(recv_info['sourceip'], recv_info['sourceport'])
                    son_cons.append(new_conn);
                    son_addrs.append(new_conn.getsockname());
                    print new_conn.getsockname()
                    print "Respond: Request of new connection from "+ recv_info['sourceip'] + ':' + str(recv_info['sourceport'])
                else:
                    if len(son_cons) == 0:
                        print "Drop: Request of new connection from "+ recv_info['sourceip'] + ':' + str(recv_info['sourceport'])
                    else:
                        print "Pass: Request of new connection from "+ recv_info['sourceip'] + ':' + str(recv_info['sourceport'])
                    for i in range(0, len(son_cons)):
                        son_cons[i].sendall(json.dumps(recv_info));
            else:
                print recv_info['body'];
        elif recv_info['status'] == 'MSG':
            ack = pack('ACK', 'send_msg_recved', self_addr[0], self_addr[1], addr[0], addr[1])
            conn.sendall(ack)
            if self_addr[0] == recv_info['targetip'] and str(self_addr[1]) == str(recv_info['targetport']):
                print 'Message from '+recv_info['sourceip']+':'+str(recv_info['sourceport'])+' :'
                print recv_info['body']
                handle_reply(recv_info)
            else:
                if len(son_cons) == 0:

                    print "Drop: Message from "+recv_info['sourceip']+':'+str(recv_info['sourceport'])+' to '+recv_info['targetip']+':'+str(recv_info['targetport'])
                else:
                    print "Pass: Message from "+recv_info['sourceip']+':'+str(recv_info['sourceport'])+' to '+recv_info['targetip']+':'+str(recv_info['targetport'])
                for i in range(0, len(son_cons)):
                    son_cons[i].sendall(json.dumps(recv_info));
        elif recv_info['status'] == 'RPL':
            reply_ack = pack('ACK', 'reply_msg_recved', self_addr[0], self_addr[1], addr[0], addr[1])
            conn.sendall(reply_ack)
            if self_addr[0] == recv_info['targetip'] and str(self_addr[1]) == str(recv_info['targetport']):
                print 'Got confirm from target. Message transportation complete!'
            else:
                if len(son_cons) == 0:
                    print "Drop: Reply from "+recv_info['sourceip']+':'+str(recv_info['sourceport'])+' to '+recv_info['targetip']+':'+str(recv_info['targetport'])
                else:
                    print "Pass: Reply from "+recv_info['sourceip']+':'+str(recv_info['sourceport'])+' to '+recv_info['targetip']+':'+str(recv_info['targetport'])
                for i in range(0, len(son_cons)):
                    son_cons[i].sendall(json.dumps(recv_info));
        else:
            print recv_info['status'];

        """something that handle the message that received from all nodes"""
        continue;

def handle_msg_for_normal_node(conn, addr):
    self_addr = conn.getsockname();
    reply_ack = pack("RPL", "new_connection_confirm", self_addr[0], self_addr[1], addr[0], addr[1])
    conn.sendall(reply_ack)
    while 1:
        recv_info = json.loads(conn.recv(1024))
        if recv_info['status'] == 'REQ':
            if recv_info['body'] == 'new_connection':
                if len(son_cons) < MAX_DEGREE:
                    new_conn = connect_to_new(recv_info['sourceip'], recv_info['sourceport'])
                    recv_info_conn = json.loads(new_conn.recv(1024))
                    if recv_info_conn['status'] == "RPL" and recv_info_conn['body'] == 'new_connection_confirm':
                        son_cons.append(new_conn)
                        son_addrs.append(new_conn.getsockname())
                        print new_conn.getsockname()
                        print "Respond: Request of new connection from "+ recv_info['sourceip'] + ':' + str(recv_info['sourceport'])
                else:
                    if len(son_cons) == 0:
                        print "Drop: Request of new connection from "+ recv_info['sourceip'] + ':' + str(recv_info['sourceport'])
                    else:
                        print "Pass: Request of new connection from "+ recv_info['sourceip'] + ':' + str(recv_info['sourceport'])
                    for i in range(0, len(son_cons)):
                        son_cons[i].sendall(json.dumps(recv_info))
            else:
                print recv_info['body'];
        elif recv_info['status'] == 'MSG':
            if self_addr[0] == recv_info['targetip'] and str(self_addr[1]) == str(recv_info['targetport']):
                print 'Message from '+recv_info['sourceip']+':'+str(recv_info['sourceport'])+' :'
                print recv_info['body']
                handle_reply(recv_info)
            else:
                if len(son_cons) == 0:
                    print "Drop: Message from "+recv_info['sourceip']+':'+str(recv_info['sourceport'])+' to '+recv_info['targetip']+':'+str(recv_info['targetport'])
                else:
                    print "Pass: Message from "+recv_info['sourceip']+':'+str(recv_info['sourceport'])+' to '+recv_info['targetip']+':'+str(recv_info['targetport'])
                for i in range(0, len(son_cons)):
                    son_cons[i].sendall(json.dumps(recv_info))
        elif recv_info['status'] == 'RPL':
            if self_addr[0] == recv_info['targetip'] and str(self_addr[1]) == str(recv_info['targetport']):
                print 'Got confirm from target. Message transportation complete!'
            else:
                if len(son_cons) == 0:
                    print "Drop: Reply from "+recv_info['sourceip']+':'+str(recv_info['sourceport'])+' to '+recv_info['targetip']+':'+str(recv_info['targetport'])
                else:
                    print "Pass: Reply from "+recv_info['sourceip']+':'+str(recv_info['sourceport'])+' to '+recv_info['targetip']+':'+str(recv_info['targetport'])
                for i in range(0, len(son_cons)):
                    son_cons[i].sendall(json.dumps(recv_info));
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
        s.listen(1)
        print 'Listening from father node'
    except socket.error, msg:
        print 'FAILED to bind socket. Error code: ' + str(msg[0]) + ', Error message: ' + msg[1]
    return s;

def create_connection_with_father_node(con_port):
    global CON_STATUS
    s = wait_for_call_of_father_node(con_port)
    if CON_STATUS == 0:
        conn, addr = s.accept()
        CON_STATUS = CON_STATUS + 1
    handle_msg_for_normal_node(conn, addr)
    return;


def handle_message(target, msg, s):
    self_addr = s.getsockname()
    package = pack("MSG", msg, self_addr[0], bind_port, target.split(':')[0], target.split(':')[1])
    if RP == 1:
        s.close();
        if self_addr[0] == target.split(':')[0] and str(self_addr[1]) == str(target.split(':')[1]):
            print 'Message from '+recv_info['sourceip']+':'+str(recv_info['sourceport'])+' :'
            print recv_info['body']
            handle_reply(package)
        else:
            for i in range(0, len(son_cons)):
                son_cons[i].sendall(package);
    else:
        s.sendall(package);
        recv_info = json.loads(s.recv(1024))
        if recv_info['status'] == 'ACK' and recv_info['body'] == 'send_msg_recved':
            s.close()


def handle_reply(recv_info):
    s = connect_or_bind()
    self_addr = s.getsockname();
    confirm_package = pack("RPL", "send_msg_confirm", recv_info['targetip'], recv_info['targetport'], recv_info['sourceip'], recv_info['sourceport'])
    if RP == 1:
        s.close();
        if self_addr[0] == confirm_package['targetip'] and str(self_addr[1]) == str(confirm_package['targetport']):
            print 'Got confirm from target. Message transportation complete!'
        else:
            for i in range(0, len(son_cons)):
                son_cons[i].sendall(comfirm_package);
    else:
        s.sendall(confirm_package);
        recv_info = json.loads(s.recv(1024))
        if recv_info['status'] == 'ACK' and recv_info['body'] == 'reply_msg_recved':
            s.close()

def index():
    print 'Running on port: ' + str(bind_port)
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
