import hashlib
import uuid
import socket

def md5(sn_head):
    temp = 0
    #每位当作ASCII字符取十进制数相加
    for i in range(len(sn_head)):
        temp = temp + ord(sn_head[i])
    #temp=0x0837,hex(temp)[-2:]取低8位0x3A
    s1 = (sn_head + hex(temp)[-2:]).upper()
    #补全之后的s1=WNA2018240000123A
    s1 = bytes(s1, encoding="utf8")
    m = hashlib.md5()
    m.update(s1)
    #返回带第16-19位，0D9E
    return(m.hexdigest().upper()[-4:])

def get_mac_address(): 
    mac=uuid.UUID(int = uuid.getnode()).hex[-12:].upper()
    return("".join([mac[e:e+2] for e in range(0,11,2)]))

def get_ip_adrress():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
    finally:
        s.close()
    return(ip)


def generateSN(prefix='WLM'):
    mac = get_mac_address()
    sn = prefix + mac
    sn += md5(sn)
    return(sn)

if __name__ == "__main__":
    tid = b'\xe2\x80\x11``\x00\x02\x0e8%\xd4\x84'
    a = ''.join(['%02X' % b for b in tid])
    #print(generateSN())
    print(get_ip_adrress())