# coding: utf-8
from pickle import TRUE
import urllib.parse
from threading import Thread
import struct
import time
import hashlib
import base64
import socket
import time
import threading
import re
import json
from DecryptLogin import login
import configparser
def main():
    conf = configparser.ConfigParser()
    initConf(conf)
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(('127.0.0.1', int(conf.get("weibo","port"))))
    sock.listen(5)
    while True:
        try:
            connection, address = sock.accept()
            con=returnCrossDomain(connection)
            wb=weibo(conf.get("weibo","username"),conf.get("weibo","password"),con,int(conf.get("weibo","time")))
            con.start()
            with open("uid.txt") as file:
                    for tempStr in file:
                        thre = threading.Thread(target=wb.start, args=(int(tempStr),))   # 创建一个线程
                        thre.start()  # 运行线程
        except:
            time.sleep(1)

def initConf(conf):
    conf.read('config.ini')
    if(not conf.has_section("weibo")):
            conf.add_section("weibo")
            conf.set("weibo", "username", "15595297190")
            conf.set("weibo", "password", "qwer1234")
            conf.set("weibo", "time", "15")
            conf.set("weibo", "port", "9999")
            file = open('config.ini', 'w',encoding='utf-8')
            conf.write(file)
            file.close()

class weibo():
    def __init__(self, username, password,con, time_interval):
        _, self.session = login.Login().weibo(username, password,'pc')
        self.headers ={
        'Accept': 'application/json, text/plain, */*',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'zh-CN,zh;q=0.9',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.51 Safari/537.36'
        }
        self.url='https://weibo.com/ajax/statuses/mymblog?uid={}&page=1&feature=0'
        self.time_interval = time_interval
        self.con=con   
        self.idlist=[] 
        self.replacetext=b' \xe2\x80\x8b\xe2\x80\x8b\xe2\x80\x8b'.decode('utf-8')
    
    def start(self,id):
        res=self.session.get(self.url.format(id),headers=self.headers)
        for message in res.json()['data']['list']:
            self.idlist.append(message['id'])
        while TRUE:
            flag=False
            try:
                res=self.session.get(self.url.format(id),headers=self.headers)
            except BaseException:
                print("During handling of the above exception, another exception occurred:")
                self.con.sendDateToClient(str(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))) + 'During handling of the above exception, another exception occurred:')
            # if res.status_code==200   414
            if res.text!='':
                try:
                    if 'data' in res.json() and 'list' in res.json()['data']:
                        username=""
                        for temp in res.json()['data']['list']:
                            username=temp['user']['screen_name']
                            if temp['id'] not in self.idlist:
                                self.idlist.append(temp['id'])
                                print(str(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))) + ': 用户<%s>发布了新微博'  % username)
                                print('[时间]: %s\n%s',temp['created_at'],temp['text_raw'])
                                mes=re.sub(r'[#][^#]+[#]',"",temp['text_raw'].replace(self.replacetext,""))
                                mes=re.sub(r'[[][^]]+[]]',"",mes)
                                #mes=mes.split('\n')[0]
                                self.con.sendDataToClient('%s:%s' % (username,mes))
                                flag=TRUE
                        if not flag:
                            print(str(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))) + ': 用户<%s>未发布新微博' % username)
                            #发送消息
                    else:
                        print(res.json())
                except json.decoder.JSONDecodeError:
                    print("json.decoder.JSONDecodeError")
            time.sleep(self.time_interval)

    #{'ALC': 'ac%3D2%26bt%3D1646988557%26cv%3D5.0%26et%3D1678524557%26ic%3D710818236%26login_time%3D1646988557%26scf%3D%26uid%3D7630850899%26vf%3D0%26vs%3D1%26vt%3D0%26es%3Dad3483fffb1d91fd99a19a178b50f9fd', 'LT': '1646988557', 'tgc': 'TGT-NzYzMDg1MDg5OQ==-1646988557-yf-D22B1FA8554198CF490A12E798F33BD4-1', 'XSRF-TOKEN': 'c05d3f', 'SUB': '_2A25PL31dDeRhGeFI6FIZ9S7EwjWIHXVs0AMVrDV8PUJbkNB-LWXXkW1NfSSE3U6C9SINgeXRWxCGN9GCvRt8p6Rt', 'SUBP': '0033WrSXqPxfM725Ws9jqgMF55529P9D9W5zaNOu.FQ3OBT47snQmPIc5NHD95QNSoe71h-71h.4Ws4DqcjzKPi9Ug8VMNzt', 'genTime': '1646988558', 'ustat': '__42.94.57.188_1646988558_0.25395900', 'ALF': '1678524557', 'MLOGIN': '1', 'M_WEIBOCN_PARAMS': 'luicode%3D10000011%26lfid%3D231093_-_selffollowed%26fid%3D1005051696181601%26uicode%3D10000011', 'SSOLoginState': '1646988558', 'WEIBOCN_FROM': '1110006030', '_T_WM': '88563495523', 'FID': '2ZWRiKwzyAATtNshruo1UUhTo3MuZ-ICDBWxvZ2lu'}

    #res=requests.get(url=url.format(6226714046),headers=header,cookies=session.cookies)







class returnCrossDomain(Thread):
    def __init__(self, connection):
        Thread.__init__(self)
        self.con = connection
        self.isInitialize = False

    def run(self):
        while True:
            if not self.isInitialize:
                header = self.analyzeReq() 
                secKey = header['Sec-WebSocket-Key']
                acceptKey = self.generateAcceptKey(secKey)

                response = "HTTP/1.1 101 Switching Protocols\r\n"
                response += "Upgrade: websocket\r\n"
                response += "Connection: Upgrade\r\n"
                response += "Sec-WebSocket-Accept: %s\r\n\r\n" % (
                    acceptKey.decode('utf-8'))
                self.con.send(response.encode())
                self.isInitialize = True
       
                print('response:\r\n' + response)
            else:
                opcode = self.getOpcode()
                if opcode == 8:
                    self.con.close()
                    return
                

    def analyzeReq(self):
        reqData = self.con.recv(1024).decode()
        reqList = reqData.split('\r\n')
        print(reqList)
        headers = {}
        for reqItem in reqList:
            if ': ' in reqItem:
                unit = reqItem.split(': ')
                headers[unit[0]] = unit[1]
        return headers

    def generateAcceptKey(self, secKey):
        sha1 = hashlib.sha1()
        sha1.update((secKey + '258EAFA5-E914-47DA-95CA-C5AB0DC85B11').encode())
        sha1_result = sha1.digest()
        acceptKey = base64.b64encode(sha1_result)
        return acceptKey

    def getOpcode(self):
        first8Bit = self.con.recv(1)
        first8Bit = struct.unpack('B', first8Bit)[0]
        opcode = first8Bit & 0b00001111
        return opcode

    def getDataLength(self):
        second8Bit = self.con.recv(1)
        second8Bit = struct.unpack('B', second8Bit)[0]
        masking = second8Bit >> 7
        dataLength = second8Bit & 0b01111111
        # print("dataLength:",dataLength)
        if dataLength <= 125:
            payDataLength = dataLength
        elif dataLength == 126:
            payDataLength = struct.unpack('H', self.con.recv(2))[0]
        elif dataLength == 127:
            payDataLength = struct.unpack('Q', self.con.recv(8))[0]
        self.masking = masking
        self.payDataLength = payDataLength
        #print("payDataLength:", payDataLength)

    def readClientData(self):

        if self.masking == 1:
            maskingKey = self.con.recv(4)
        data = self.con.recv(self.payDataLength)

        if self.masking == 1:
            i = 0
            trueData = ''
            for d in data:
                trueData += chr(d ^ maskingKey[i % 4])
                i += 1
            return trueData
        else:
            return data

    def sendDataToClient(self, text):
        sendData = ''
        sendData = struct.pack('!B', 0x81)
        text = urllib.parse.quote(text)
        length = len(text)
        if length <= 125:
            sendData += struct.pack('!B', length)
        elif length <= 65536:
            sendData += struct.pack('!B', 126)
            sendData += struct.pack('!H', length)
        elif length == 127:
            sendData += struct.pack('!B', 127)
            sendData += struct.pack('!Q', length)

        sendData += struct.pack('!%ds' % (length), text.encode('utf8'))
        dataSize = self.con.send(sendData)






if __name__ == "__main__":
    main()
