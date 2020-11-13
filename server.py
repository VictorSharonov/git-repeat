import os, sys, socket, subprocess
from os import environ

#makes an error message for the client
def makeError(statusCode, errorMessage):
    bodyMessage = (statusCode + ' ' + errorMessage)
    contentLength = len(bodyMessage)
    sendMessage = ('HTTP/1.1 {} {}\n'
                    'Content-Type: text/html\n\n').format(statusCode, errorMessage)
    sendMessage = sendMessage + bodyMessage
    return sendMessage


#makes a responese (content) for the client
def makeSuccess(result, isDynamic):
    sendMessage = 'HTTP/1.1 200 OK\n'

    #if it is not cgi we have to set the content type
    if isDynamic == False:
        contentType = 'Content-Type: text/html\n\n'
        sendMessage = sendMessage + contentType
    
    sendMessage = sendMessage + result
    return sendMessage
    


#parses headers from request until empty line is found, returns dict of headers and values
def parseHeaders(sFile):
    headers = []
    headersDict = {}
    line = sFile.readline()

    #parse line by line until empty line is found
    while (line != '' and line != '\n' and line != '\r\n'):
        headers.append(line.strip())
        line = sFile.readline()
    
    for header in headers:
        key, value = header.split(':', 1)
        headersDict[key.strip()] = value.strip()
    return headersDict


#handles get request and returns the content to send to the client
def handleGetRequest(path):
    newPath = '/Users/vityansh/ServerPy/site' + path #path of current directory + path from client

    #if url contain query string
    if '?' in newPath:
        newPath, fields = newPath.split('?') #split url and query 
        environ['QUERY_STRING'] = fields #enter cookie in environ

    #execute cgi or just send content if no cgi
    if newPath.endswith('.cgi'):
        #check if such file exsits
        if os.path.exists(newPath):
            try:
                stdOut = (subprocess.check_output(newPath))
                message = makeSuccess(stdOut, True)
            except:
                status = '500'
                error = 'Internal Server Error'
                message = makeError(status, error)
        else:
            status = '404'
            error = 'Not Found'
            message = makeError(status, error)
    else:
        # if path is directory -> access index.html
        if os.path.isdir(newPath):
            newPath = newPath + '/index.html'

        try:
            reqFile = open(newPath)
            fileContent = reqFile.read()
            message = makeSuccess(fileContent, False)
            reqFile.close()
        except:
            status = '404'
            error = 'Not Found'
            message = makeError(status, error)

    return message


#handles post request and returns the content to send to the client
def handlePostRequest(path, body):
    newPath = '/Users/vityansh/ServerPy/site' + path #path of current directory + path from client

    if newPath.endswith('.cgi'):
        #check if such file exsits
        if os.path.exists(newPath):
            try:
                procObj = subprocess.Popen(newPath, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
                (stdOut, stdErr) = procObj.communicate(input=body)
                if stdErr != None:
                    status = '500'
                    error = 'Internal Server Error'
                    message = makeError(status, error)
                else:
                    stdOut = stdOut.decode()
                    message = makeSuccess(stdOut, True)
            except:
                status = '500'
                error = 'Internal Server Error'
                message = makeError(status, error)
        else:
            status = '404'
            error = 'Not Found'
            message = makeError(status, error)

    else:
        # if path is directory -> access index.html
        if os.path.isdir(newPath):
            newPath = newPath + '/index.html'

        try:
            reqFile = open(newPath)
            fileContent = reqFile.read()
            message = makeSuccess(fileContent, False)
            reqFile.close()
        except:
            status = '404'
            error = 'Not Found'
            message = makeError(status, error)

    return message


address = ('', 15029)
mySocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
try:
    mySocket.bind(address)
    mySocket.listen(socket.SOMAXCONN) # max num of cons os can give us

    print ("*** Start ***")
    while True:
        requestSocket, addr = mySocket.accept()
        socketFile = None
        try:
            socketFile = requestSocket.makefile()

            #reads the first line of the request
            firstRaw = socketFile.readline()
            firstRaw = firstRaw.strip()
            values = firstRaw.split() #splits for method, path, http version

            #errors and messages
            error = False
            statusCode = ''
            errorMessage = ''
            message = ''
            

            #check for method type and handle request
            if values[0] == "GET" or values[0] == "HEAD":
                headers = parseHeaders(socketFile)
                #sets cookie
                if 'Cookie' in headers:
                    environ['HTTP_COOKIE'] = headers['Cookie']
                
                message = handleGetRequest(values[1])

            elif values[0] == "POST":
                headers = parseHeaders(socketFile)
                #sets cookie
                if 'Cookie' in headers:
                    environ['HTTP_COOKIE'] = headers['Cookie']

                #sets content-length to know the body syze
                if 'Content-Length' in headers:
                    contentLength = headers['Content-Length']
                    environ['CONTENT_LENGTH'] = contentLength
                    body = socketFile.read(int(contentLength))
                    message = handlePostRequest(values[1], body)
                else:
                    #no content length
                    statusCode = '400'
                    errorMessage = 'Bad Request: no content length'
                    error = True
            else:
                #not supported method
                statusCode = '405'
                errorMessage = 'Method Not Allowed'
                error = True

            if error == True:
                message = makeError(status, error)

            #send content and close 
            socketFile.write(message)
            socketFile.close()
            requestSocket.close()

        finally:
            #free environ vars and close file and socket
            environ['QUERY_STRING'] = ''
            environ['HTTP_COOKIE'] = ''
            environ['CONTENT_LENGTH'] = ''
            if socketFile is not None:
                socketFile.close
            requestSocket.close()

        
except:
    print ("*** Done ***")
    mySocket.close()