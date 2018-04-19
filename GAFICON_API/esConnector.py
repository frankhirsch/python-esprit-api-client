'''
Created on 12.11.2017
@author: Frank Hirsch
'''
import json
import dict2xml
import urllib.parse
import urllib.request
import urllib.parse
import base64
import io

class esApi():
    serverUrl      = 'http://127.0.0.1:8080'
    apiUrl         = '/Esprit/public/Interface/rpc'
    username       = 'admin'
    password       = 'admin'
    authentication = False
    session        = False
    cookie         = False
    status         = False
    response       = False
    result         = False
    
    def __init__(self):
        pass
    
    def apiLogin(self):
        actions = [{
            'id': '1',
            'method': 'admin.login'
        }]
        self.response = self.requestBroker(actions)
        #if(self.response[0]['result']['status']=='loggedIn'):
        if("error" not in self.response[0]):
            self.session = self.response[0]['result']['sessionID']
            self.cookie  = 'JSESSIONID='+self.session
            return(True)
        else:
            self.session = False
            self.cookie  = False
            return(False)
    
    def apiLogout(self):
        actions = [{
            'id': '1',
            'method': 'admin.logout'
        }]
        self.response = self.requestBroker(actions)
        if(self.response[0]['result']['status']=='loggedOut'):
            self.session = False
            self.cookie  = False
            return(True)
        else:
            return(False)
        
    def apiDetails(self,type,id):
        actions = [{
            "id":"1",
            "method": type+".get",
            "params": {"ID":id}
        }]
        self.response = self.requestBroker(actions)
        if("error" not in self.response[0]):
            self.result = self.response
            return(True)
        else:
            self.response = [{'error':{'status':self.response[0]['error']['data']["longMessage"]}}]
            return(False)
        
    def apiListing(self,method, type='', searchId=''):
        actions = [{
            "id":"1",
            "method": str(method)+".list",
            'params':{}
        }]
        if(searchId!=''):
            actions[0]['params']['ID'] = searchId
        if(type!=''):
            actions[0]['params']['class'] = type
        #if(type!='' and searchId!=''):
        #    actions[0]['params'] = [{'class': type},{'ID': searchId}]
        print(str(actions))
        self.response = self.requestBroker(actions)
        if("error" not in self.response[0]):
            self.result = self.response
            return(True)
        else:
            self.response = [{'error':{'status':self.response[0]['error']['data']["longMessage"]}}]
            return(False)
        
    def directorySearch(self,method, search=''):
        search = urllib.parse.unquote(search)
        actions = [{
            "id":"1",
            "method": str(method),
            'params':{}
        }]
        if(search!=''):
            actions[0]['params']['substringSearch'] = 'true'
            actions[0]['params']['query'] = search
        #if(type!='' and searchId!=''):
        #    actions[0]['params'] = [{'class': type},{'ID': searchId}]
        print(str(actions))
        self.response = self.requestBroker(actions)
        if("error" not in self.response[0]):
            self.result = self.response
            return(True)
        else:
            self.response = [{'error':{'status':self.response[0]['error']['data']["longMessage"]}}]
            return(False)
    
    def requestDownload(self,method,type,id):
        # method = preview | thumbnail | notes
        # type   = document | production
        # id     = id
        if(method == "notes"):
            method = "noteReport"
        if(type == "document"):
            apiUrl = str(self.serverUrl+self.apiUrl+"/"+id).replace("rpc", method)
        
        request  = urllib.request.Request(apiUrl)
        request.add_header("Content-Type", 'application/json')
        if(self.session):
            request.add_header("Cookie", self.cookie)
        else:
            request.add_header("Authorization", "Basic %s" % self.authentication)
        
        try:
            downloadFile = urllib.request.urlopen(request)
            with downloadFile:
                download = io.BytesIO(downloadFile.read())
            headers = {}
            for downloadHeader in downloadFile.headers:
                if(downloadHeader in ["Content-Type","Last-Modified","Content-Length","Content-Disposition"]):
                    headers[downloadHeader] = downloadFile.headers[downloadHeader]
            if(len(headers)):
                return [True,headers,download]
            else:
                self.response = [{'error':{'status':"No file or empty file"}}]
            return [False]
        except urllib.error.HTTPError as e:
            self.response = [{'error':{'status':e}}]
            return [False]
            
        return True
    
    def requestSql(self,method,search):
        search = urllib.parse.unquote(search)
        actions = [{
            "id":"1",
            "method": "production.executeSQL",
            "params": {"sql":search}
        }]
        self.response = self.requestBroker(actions)
        if("error" not in self.response[0]):
            self.result = self.response
            return(True)
        else:
            self.response = [{'error':{'status':self.response[0]['error']['data']["longMessage"]}}]
            return(False)

    def requestBroker(self, actions):
        request  = urllib.request.Request(self.serverUrl+self.apiUrl, data=json.dumps(actions).encode("utf-8"))
        request.add_header("Content-Type", 'application/json')
        if(self.session):
            request.add_header("Cookie", self.cookie)
        else:
            request.add_header("Authorization", "Basic %s" % self.authentication)
        
        try:
            response = urllib.request.urlopen(request) 
            result = response.read()
            # print("******** DEBUG: \n"+str(result)+'\n')
            return json.loads(result.decode("utf-8"))
        except urllib.error.HTTPError as e:
            return [{'error':{'status':e}}]
    
    def setAuthentication(self, user='admin', password='admin'):
        self.authentication = base64.b64encode((user+":"+password).encode('utf-8')).decode('utf-8')
    
    def setTarget(self, serverUrl, apiUrl):
        self.serverUrl = serverUrl
        self.apiUrl    = apiUrl
    
    def result2xml(self, data):
        return '<?xml version="1.0" encoding="UTF-8" ?>\n<response>\n'+dict2xml.dict2xml(data).strip()+"\n</response>"
    
    def sql2xml(self, data):
        result=[]
        for entry in data[0]['result']['objectList']:
            i=0
            object={}
            for value in entry:
                object[str(data[0]['result']['headers'][i]['name'])] = str(value)
                i+=1
            result.append('<object>'+dict2xml.dict2xml(object).strip()+'</object>')
        return '<?xml version="1.0" encoding="UTF-8" ?>\n<response>\n'+'\n'.join(result)+"\n</response>"
    
    
    
    
    
    
    