import socket
import hashlib
import re

class CTP:
    'Help Help'
    def __init__(self,ip,port,username="admin",password="admin"):
        self.host = (ip,port)
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect(self.host)
        self.logged = False
        self.clientid = "bG1ubW4"
        self.logged = self.cfgusr(username,password)          #User information verification
        # self.cfgsvr()                                         #Get cameras information
        # self.reloadcfg()
        # self.cfgsvr()
        # self.readfile('/home/hwcfg.ini')
        # self.initsess()
        # self.cfgwnic()
        # self.iwlist()

        # Do not modify this line
        self.uploaded = self.upload()                       #very important

        ### data for response
        self.raw = None
        self.status_code = None
        self.headers = None
        self.content = None
        self.content_Length = None

    def ConstructingRequestPacket(self,features,data):
        if data == "":
            requestBody = ""
        else:
            requestBody = data + "\x0D\x0A\x0D\x0A"
        if features == "readfile":
            requestBody = requestBody[:-4]
        contentLength = len(requestBody)
        request = "CMD {} CTP/1.0\x0D\x0AContent-Length: {}\x0D\x0A\x0D\x0A{}".format(features,contentLength,requestBody)
        return request

    def cfgusr(self,username,password):

        requestBody = "-login {}:{}\x0D\x0A-oemid ".format(username,password)
        cfgusr_data = self.ConstructingRequestPacket('cfgusr',requestBody)
        data = self.socketSendAndRecv(cfgusr_data)
        clientid = "bmlhbmh1YQ"
        if self.status_code == 200:
            clientid = re.findall(r'-clientid (.*?)\x0D\x0A',data)[0]
        if clientid =="bmlhbmh1YQ":
            return False
        else:
            self.clientid = clientid
            return True

    def cfgsvr(self):
        requestBody = "-list"
        cfgsvr_data = self.ConstructingRequestPacket('cfgsvr',requestBody)
        data = self.socketSendAndRecv(cfgsvr_data)
        return data

    def reloadcfg(self):
        requestBody = ""
        reloadcfg_data = self.ConstructingRequestPacket('reloadcfg',requestBody)
        data = self.socketSendAndRecv(reloadcfg_data)
        return data

    def initsess(self):
        requestBody = "-chn 0\x0D\x0A-transport tcp"
        initsess_data = self.ConstructingRequestPacket('initsess',requestBody)
        data = self.socketSendAndRecv(initsess_data)
        sessid = re.findall(r'-sessid (.*?)\x0D\x0A',data)[0]
        self.sessid = sessid
        return data

    def readfile(self,filename):
        requestBody = filename
        readfile_data = self.ConstructingRequestPacket('readfile',requestBody)  
        data = self.socketSendAndRecv(readfile_data)
        return data

    def cfgwnic(self):
        requestBody = "-list"
        cfgwnic_data = self.ConstructingRequestPacket('cfgwnic',requestBody)
        data = self.socketSendAndRecv(cfgwnic_data)
        return data

    def iwlist(self):
        requestBody = ""
        iwlist_data = self.ConstructingRequestPacket('iwlist',requestBody)
        data = self.socketSendAndRecv(iwlist_data)
        return data
 
    def openLight(self):
        requestBody = "-mode on\x0D\x0A-act on"
        openLight_data = self.ConstructingRequestPacket('whitelight',requestBody)
        data = self.socketSendAndRecv(openLight_data)
        return data       

    def closeLight(self):
        requestBody = "-mode off\x0D\x0A-act off"
        closeLight_data = self.ConstructingRequestPacket('whitelight',requestBody)
        data = self.socketSendAndRecv(closeLight_data)
        return data       

    def alertLight(self):
        requestBody = ""
        alertLight_data = self.ConstructingRequestPacket('alert_light',requestBody)
        data = self.socketSendAndRecv(alertLight_data)
        return data    

    def setparam(self):
        requestBody = "-sessid {}\x0D\x0A-media -audio0".format(self.sessid)
        setparam_data = self.ConstructingRequestPacket('setparam',requestBody)
        data = self.socketSendAndRecv(setparam_data)
        return data 

    def stopsess(self):
        requestBody = "-sessid " + self.sessid
        stopsess_data = self.ConstructingRequestPacket('stopsess',requestBody)
        data = self.socketSendAndRecv(stopsess_data)
        return data

    def upload(self):

        if not self.logged:
            return False
        self.uploadsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.uploadsocket.connect(self.host)
        requestBody = "-clientid " + self.clientid
        upload_data = self.ConstructingRequestPacket('upload',requestBody)
        data = self.uploadSocketSendAndRecv(upload_data)
        return True

    def command(self,cmd):

        if not self.uploaded:
            return False
        command_data = "dst=&size={}&md5={}\x0D\x0A\x0D\x0A{}".format(len(cmd),hashlib.md5(cmd).hexdigest(),cmd)
        data = self.uploadSocketSendAndRecv(command_data)
        return data
        
    def uploadSocketSendAndRecv(self,data):
        self.uploadsocket.send(data)
        Response = ""
        while True:
            Response += self.uploadsocket.recv(1024)
            if self.dataCompleteVerification(Response):
                break
        Response = self.uploadReceiveDataProcessing(Response)   #Data processing
        return Response

    def uploadReceiveDataProcessing(self,data):
        if not data.startswith("CTP/1.0"): return (-1,"")
        headers = re.findall(r'(.*?)\x0D\x0A\x0D\x0A',data,re.S)[0]
        headers_len = len(headers) + 4
        status_code = int(re.findall(r'CTP/1.0 (.*?) ',data)[0])   #Is it really appropriate to get the code this way? Is there a better way?
        if "Content-Length" not in headers:
            if status_code == 200:
                return (1,"")
            else:
                return (-1,"")        
        content = data[headers_len:].split('\x0D\x0A')
        return (int(content[0]),data[headers_len+len(content[0])+2:])

    def receiveDataProcessing(self,data):
        self.raw = None
        self.status_code = None
        self.headers = None
        self.content = None
        self.content_Length = None
        if not data.startswith("CTP/1.0"): return False
        headers = re.findall(r'(.*?)\x0D\x0A\x0D\x0A',data,re.S)[0]
        headers_len = len(headers) + 4
        if "Content-Length" not in headers:
            return False
        self.raw = data
        self.status_code = int(re.findall(r'CTP/1.0 (.*?) ',data)[0])   #Is it really appropriate to get the code this way? Is there a better way?
        self.headers = headers
        self.content = data[headers_len:]
        self.content_Length = len(self.content)
        return True

    def dataCompleteVerification(self,data):            #Data integrity check
        if not data.startswith("CTP/1.0"): return True  #If it does not start with CTP, then exit the reception
        header = re.findall(r'(.*?)\x0D\x0A\x0D\x0A',data,re.S)[0]
        header_len = len(header) + 4
        if "Content-Length" not in header:
            return True
        content_len = int(re.findall(r'Content-Length: (.*?)\x0D\x0A\x0D\x0A',data)[0])  #con
        real_content_len = len(data[header_len:])
        if real_content_len < content_len:
            return False
        else:
            return True

    def socketSendAndRecv(self,data):
        print data
        self.socket.send(data)
        Response = ""
        while True:
            Response += self.socket.recv(1024)
            if self.dataCompleteVerification(Response):
                break
        self.receiveDataProcessing(Response)   #Data processing
        return Response
        
def main():
    ip = '192.168.1.133'
    port = 8001
    CTPObj = CTP(ip,port)
    result = CTPObj.command("uname")
    if result[0] == 0:
        print result[1]
    print CTPObj.openLight()

if __name__ == "__main__":
    main()
