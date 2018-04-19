import http.server
import socketserver
import sys, re
from GAFICON_API import esConnector
from urllib.parse import urlparse, parse_qsl


class requestBroker(http.server.BaseHTTPRequestHandler):
    
    _debug = True
    
    def _set_headers(self,code=200,headers={}):
        self.send_response(code)
        if len(headers):
            for header in headers:
                self.send_header(header, headers[header])
        else:
            self.send_header('Content-Type', "text/html")
        self.end_headers()
    
    def do_HEAD(self):
        self._set_headers()
        
    def do_GET(self):
        # Check path for actions
        # /xml/customer/{id}      = Get customer details
        # /xml/production/{id}    = Get job details
        # /xml/document/{id}      = Get document details
        # /xml/document/preview/{id}      = Get document preview
        # /xml/document/thumbnail/{id}    = Get document thumbnail
        # /xml/directory/{class}          = Get full directory of a given class
        # /xml/directory/search/{string}  = Search the directory (substring)
        # /xml/sql/{statement}    = Execute some SQL
        detailsPath = re.compile("/xml/(customer|production|document|folder)/([0-9]+)")
        previewPath = re.compile("/xml/(production|document|)/(thumbnail|preview)/([0-9]+)")
        filePath    = re.compile("/xml/(document)/(file)/([0-9]+)")
        notesPath   = re.compile("/xml/(document)/(notes)/([0-9]+)")
        productionPath = re.compile("/xml/(production|customer)")
        directorySearchPath = re.compile("/xml/directory/search/(.*)")
        directoryPath = re.compile("/xml/directory/([a-zA-Z]+)/(.*)")
        sqlPath = re.compile("/xml/sql/(.*)")
        
        details = detailsPath.search(self.path)
        preview = previewPath.search(self.path)
        notes   = notesPath.search(self.path)
        production = productionPath.search(self.path)
        file = filePath.search(self.path)
        sql = sqlPath.search(self.path)
        directorySearch = directorySearchPath.search(self.path)
        directory = directoryPath.search(self.path)
        
        if(details):
            self.esDetails('DETAILS',details.group(1),details.group(2))
        elif(preview):
            self.esDetails(preview.group(2).upper(),preview.group(1),preview.group(3))
        elif(notes):
            self.esDetails(notes.group(2).upper(),notes.group(1),notes.group(3))
        elif(production):
            self.esDetails("PRODUCTION",0,0,production.group(1))
        elif(file):
            self.esDetails(file.group(2).upper(),file.group(1),file.group(3))
        elif(sql):
            self.esDetails('SQL',0,0,sql.group(1))
        elif(directorySearch):
            self.esDetails('DIRECTORY.SEARCH',0,0,directorySearch.group(1))
        elif(directory):
            self.esDetails('DIRECTORY',0,0,directory.group(1),directory.group(2))
        else:
            self._set_headers(code=404)
            self.wfile.write(bytes("<body><p>No method found</p></body>", "utf-8"))
            print("UNDEFINED URL method")
        
    def esDetails(self,method,type=0,id=0,search='',searchId=''):
        # Get API instance
        apiObject   = esConnector.esApi()
        
        # Set environment parameters
        apiObject.setAuthentication(user='esapi',password='esapi')
        apiObject.setTarget(serverUrl='http://127.0.0.1:8080',apiUrl=apiObject.apiUrl)
        
        # Execute login
        apiResponse = apiObject.apiLogin()
        if(not(apiResponse)):
            self.esError(apiObject)
            return False
        apiResponse = False
        
        # Get object details
        if(method == "DETAILS"):
            apiResponse = apiObject.apiDetails(type, id)
            if(apiResponse):
                self._set_headers(headers={"Content-Type":"application/xml"})
                self.wfile.write(bytes(apiObject.result2xml(apiObject.result) , "utf-8"))
            else:
                self.esError(apiObject)
        # Get production
        elif(method == "PRODUCTION"):
            apiResponse = apiObject.apiListing(method.lower(), search)
            if(apiResponse):
                self._set_headers(headers={"Content-Type":"application/xml"})
                self.wfile.write(bytes(apiObject.result2xml(apiObject.result) , "utf-8"))
            else:
                self.esError(apiObject)
        # Get object previews
        elif(method == "PREVIEW" or method == "THUMBNAIL"):
            apiResponse = apiObject.requestDownload(method.lower(), type, id)
            if(apiResponse[0]):
                self._set_headers(headers=apiResponse[1])
                self.wfile.write(apiResponse[2].read())
            else:
                self.esError(apiObject)
                return False
        # Get object file
        elif(method == "FILE"):
            apiResponse = apiObject.requestDownload(method.lower(), type, id)
            if(apiResponse[0]):
                self._set_headers(headers=apiResponse[1])
                self.wfile.write(apiResponse[2].read())
            else:
                self.esError(apiObject)
                return False
        # Get object notes
        elif(method == "NOTES"):
            apiResponse = apiObject.requestDownload(method.lower(), type, id)
            if(apiResponse[0]):
                self._set_headers(headers=apiResponse[1])
                self.wfile.write(apiResponse[2].read())
            else:
                self.esError(apiObject)
                return False
        # Search the directory
        elif(method == "DIRECTORY.SEARCH"):
            apiResponse = apiObject.directorySearch(method.lower(), search)
            if(apiResponse):
                self._set_headers(headers={"Content-Type":"application/xml"})
                self.wfile.write(bytes(apiObject.result2xml(apiObject.result) , "utf-8"))
            else:
                self.esError(apiObject)
        # Get the directory
        elif(method == "DIRECTORY"):
            apiResponse = apiObject.apiListing(method.lower(), search, searchId)
            if(apiResponse):
                self._set_headers(headers={"Content-Type":"application/xml"})
                self.wfile.write(bytes(apiObject.result2xml(apiObject.result) , "utf-8"))
            else:
                self.esError(apiObject)
        # Execute the SQL
        elif(method == "SQL"):
            apiResponse = apiObject.requestSql(method.lower(), search)
            if(apiResponse):
                self._set_headers(headers={"Content-Type":"application/xml"})
                self.wfile.write(bytes(apiObject.sql2xml(apiObject.result) , "utf-8"))
            else:
                self.esError(apiObject)
                return False
            
        # Execute logout
        apiResponse = apiObject.apiLogout()
        if(not(apiResponse)):
            self.esError(apiObject)
            return False
            
    def esError(self,apiObject):
        self._set_headers(code=401)
        self.wfile.write(bytes("<body><p>"+str(apiObject.response[0]['error']['status'])+"</p></body>", "utf-8"))
    
try:
    server = http.server.HTTPServer((sys.argv[1], int(sys.argv[2])), requestBroker)
    print('Started http server')
    server.serve_forever()
except KeyboardInterrupt:
    print('^C received, shutting down server')
    server.socket.close()
    