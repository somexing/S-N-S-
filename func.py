 
from __future__ import print_function
from threading import Lock
import time, hashlib
import socket,cookielib,urllib,urllib2,httplib, urlparse, os
import gzip 
import StringIO
#import requests .....

from gzip import GzipFile
from StringIO import StringIO

USE_PROXY = False
PROXY_SERVER = None
DEFAULT_PROXY_SERVER  =   "10.45.22.124:808"
 
MAX_TRY_TIMES = 2
TIME_OUT    = 2     #1S

SHOW_LOG = False 
 
#BR_MODE , HTTPLIB_MODE ,URLLIB2_MODE
BR_MODE = 1
HTTPLIB_MODE = 2
URLLIB2_MODE = 3 

RUN_MODE = 3#func.URLLIB2_MODE
 

USE_COOKIE = 0
conn = None
br = None


 

default_header = {
                 'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                 'Accept-Language':'zh-cn,zh;q=0.8,en-us;q=0.5,en;q=0.3',
                 'User-Agent':'Mozilla/5.0 (Windows NT 6.1; rv:33.0) Gecko/20100101 Firefox/33.0' ,
                 'Accept-Encoding':'deflate' ,
                 'Connection':'Keep-Alive'    
                 }

funclogfp = None

def openlog(modulename ):
    global funclogfp
    funclogfp = open(modulename +'_log.txt','w')

def flushlog():
    global funclogfp
    funclogfp.flush()

def Showlog(*args, **kwargs):
    print(time.strftime("%Y-%m-%d %H:%M:%S"))
    print (*args, **kwargs)     

def closelog():
    global funclogfp
    funclogfp.flush()
    funclogfp.close()   
    funclogfp = None 


def _print2(*args, **kwargs):
	  None
	  

print_lock = Lock()
def _print(*args, **kwargs):
    global funclogfp
    if SHOW_LOG:
        print(time.strftime("%Y-%m-%d %H:%M:%S"))
        print (*args, **kwargs) 
    if  funclogfp is not None:
        with print_lock:
          funclogfp.write("%s %.0f "%(time.strftime("%Y-%m-%d %H:%M:%S"), time.time())) 
          funclogfp.write(*args, **kwargs)
          

def getPROXY_SERVER():
    if not USE_PROXY :
       print("no proxy set")
       return None
    proxy = DEFAULT_PROXY_SERVER
    try:
        fp = open("proxycfg.txt","r")
        proxy = fp.readline().strip('\n')
        fp.close()
    except Exception ,e :
        proxy = DEFAULT_PROXY_SERVER

    _print("func using proxy server %s" % proxy)
    return proxy

PROXY_SERVER = getPROXY_SERVER()            
    
def getURLHash(url):
    return hashlib.md5(url).hexdigest()   
 
def getTimeStr(timestamp):
    ltime = time.localtime(timestamp)
    return time.strftime("%Y-%m-%d %H:%M:%S", ltime)
#入口


       
def GetHttpContent( url , method = "GET", header = default_header ,postdata = None ):
      
     _print(("%s %s\n")%(method, url))
     if RUN_MODE == BR_MODE:
         return br_version(method, url, header, postdata)
     elif RUN_MODE == HTTPLIB_MODE  :
         return httplib_version(method, url, header, postdata)
     #elif RUN_MODE == URLLIB2_MODE :
     else:
         return urllib2_version(method, url, header, postdata)

def  getUTF8EncodedURL(urlprefix, key , urlpostfix):
        key_utf8 = key.decode('gbk').encode('gbk')     
        return urlprefix + urllib.quote(key_utf8) + urlpostfix

    
#ff profile下的cookie文件地址
def getcookiefilename():
   cookiepath =  r"C:\Documents and Settings\Administrator\Application Data\Mozilla\Firefox\Profiles"
   flist = os.listdir(cookiepath)
   for f in flist:
      if  (os.path.isdir(cookiepath + '/' + f)) and os.path.splitext(f)[1] == '.default':
          
         return cookiepath + '\\' + f + r'\cookies.sqlite'
def getffcookiejar():
    from cStringIO import StringIO
    from pysqlite2 import dbapi2 as sqlite
    
   
    filename = getcookiefilename()

    if filename is None:
      return 
    _print("open cookie named:%s"%filename)
    con = sqlite.connect(filename)
    cur = con.cursor()
    cur.execute("select host, path, isSecure, expiry, name, value from moz_cookies")
    ftstr = ["FALSE","TRUE"]
    s = StringIO()
    s.write("""\
# Netscape HTTP Cookie File
# http://www.netscape.com/newsref/std/cookie_spec.html
# This is a generated file!  Do not edit.
""")
    for item in cur.fetchall():
        s.write("%s\t%s\t%s\t%s\t%s\t%s\t%s\n" % (
            item[0], ftstr[item[0].startswith('.')], item[1],
            ftstr[item[2]], item[3], item[4], item[5]))


        #print ("%s\t%s\t%s\t%s\t%s\t%s\t%s\n" % (
           # item[0], ftstr[item[0].startswith('.')], item[1],
           # ftstr[item[2]], item[3], item[4], item[5]))
    s.seek(0)
    cookie_jar = cookielib.MozillaCookieJar()
    cookie_jar._really_load(s, '', True, True)

    cur.close()
    return cookie_jar


#python如何保存Transfer-Encoding: chunked类型图片??
#use mechanize
class NoHistory(object):
    def add(self, *a, **k): pass
    def clear(self): pass
  
 





def closeConn():
    global conn 
    if conn != None:
       conn.close()  #notice!  if conn.close, resp.read will read nothing
       conn = None  
#visit the website which no support Keep-Alive
def httplib_version(method, url , header = None ,postdata = None , proxyserver = None):
    
        if url is None :
           return
    
        conn = None
        try_times  = 0
        while (try_times < MAX_TRY_TIMES):
            try:
                 try_times += 1
                 timebefore =  time.time()

                 if conn != None:
                    conn.close()  #notice!  if conn.close, resp.read will read nothing
                    conn = None
                 
                 
                 connecturl = url #should be useful host ?? 150404 while codeing tudou sns thinking                      

                 if proxyserver is not None:
                 	     connecturl = proxyserver
                 	     _print("httplib_version use  proxyserver %s\n"%connecturl)
                 elif PROXY_SERVER is not None :
                 	    
                 	     connecturl = PROXY_SERVER
                 	     _print("httplib_version use PROXY_SERVER %s\n"%connecturl)
                 	  
     
                 if TIME_OUT is None:
                       conn = httplib.HTTPConnection( connecturl)
                 else:
                       conn = httplib.HTTPConnection( connecturl,  timeout=TIME_OUT)
                                           
                 conn.connect()
                  
                 if (method == "GET"):
                     if header is None :

                         conn.request("GET", url ,headers = default_header)
                     else:
                         conn.request("GET", url, headers = header)                         
                 elif (method == "POST"):
                     if header is None :
                         conn.request("POST", url, postdata) 
                     else:
                         conn.request("POST", url, postdata, headers = header)
                         
                    
                 resp = conn.getresponse() #notice!  if conn.close, resp.read will read nothing
                 _print( "httplib_version visit %s times: %s ,resp.status : %s ,resp.reason: %s. cost %s s.\n"%( url, try_times, resp.status, resp.reason, time.time()-timebefore)) 

                 content = resp.read()     
                 
                 _print (content)
                 
                 if resp.status == 200 or resp.status == 302 :
                
                    content_encoding = resp.getheader('Content-Encoding')                  
                    if  content_encoding == "gzip" or content_encoding == "deflate" :
                        _print( "httplib_version get Content-Encoding is %s. Perhaps Not support !\n"%content_encoding)
                       # return None
                 
                    transfer_encoding = resp.getheader('Transfer-Encoding')               
                    if  transfer_encoding == "chunked" :
                        _print( "httplib_version get Transfers-Encoding is %s. Perhaps Not support !\n"%transfer_encoding)
                      #  return None

                    content_length = resp.getheader('Content-Length')
                    _print( "httplib_version get content_length %s.\n"%(content_length))


                    

                 conn.close()
                 conn = None      
                 if content != None:            
                     return content
                     

            except Exception ,e:
                  _print( "httplib_version Exception! visit %s %s . cost %s s.\n"%(url, e, time.time()-timebefore))
                  continue




class ContentEncodingProcessor(urllib2.BaseHandler):
  """A handler to add gzip capabilities to urllib2 requests """
 
  # add headers to requests
  def http_request(self, req):
    req.add_header("Accept-Encoding", "gzip, deflate")
    return req
 
  # decode
  def http_response(self, req, resp):
    old_resp = resp
    # gzip
    if resp.headers.get("content-encoding") == "gzip":
        gz = GzipFile(
                    fileobj=StringIO(resp.read()),
                    mode="r"
                  )
        resp = urllib2.addinfourl(gz, old_resp.headers, old_resp.url, old_resp.code)
        resp.msg = old_resp.msg
    # deflate
    if resp.headers.get("content-encoding") == "deflate":
        gz = StringIO( deflate(resp.read()) )
        resp = urllib2.addinfourl(gz, old_resp.headers, old_resp.url, old_resp.code)  # 'class to add info() and
        resp.msg = old_resp.msg
    return resp
 
# deflate support
import zlib
def deflate(data):   # zlib only provides the zlib compress format, not the deflate format;
  try:               # so on top of all there's this workaround:
    return zlib.decompress(data, -zlib.MAX_WBITS)
  except zlib.error:
    return zlib.decompress(data)          



def urllib2_version(method, url , header = None ,postdata = None , proxyserver = None):
    
    
            try_times  = 0
            while (try_times < MAX_TRY_TIMES):
                 try:
                      try_times += 1
                      timebefore =  time.time()
                      #encoding_support = ContentEncodingProcessor
                      #cj = cookielib.CookieJar()
                      #opener = urllib2.build_opener( encoding_support, urllib2.HTTPHandler ,urllib2.HTTPCookieProcessor(cj))
                      request  = urllib2.Request(url)
                      if USE_PROXY  :
                          if proxyserver is not None:
                            request.set_proxy( proxyserver , 'http' )
                            _print("urllib2_version use proxy %s\n"%proxyserver)
                          elif PROXY_SERVER is not None:
                            request.set_proxy( PROXY_SERVER , 'http' )
                          else:
                            _print("urllib2_version PROXY_SERVER or proxyserver not set !\n")
                            return                        
                      if TIME_OUT is None:
                        resp = urllib2.urlopen(request)
                      else:
                        resp = urllib2.urlopen(request, timeout = TIME_OUT)
                      content = resp.read()
                      
                      
                      if resp.headers.get("Content-Encoding") == 'gzip':
                         _print("urllib2_version Content-Encoding is gzip !\n")                       
                         content = gzip.GzipFile(fileobj = StringIO.StringIO(content)).read()
                         
                      resp.close()
                      
                      
                 except  urllib2.URLError  , e:
                     #e.reason
                      _print( "urllib2_version Exception ! visit %s %s . cost %s s.\n"%(url, e, time.time()-timebefore))
                      continue
                 except urllib2.HTTPError , e:
                      #e.code()
                      _print( "urllib2_version Exception ! vis it %s %s . cost %s s.\n"%(url, e, time.time()-timebefore))
                      continue
                 except Exception , e:
                      _print( "urllib2_version Exception ! visit %s %s . cost %s s.\n"%(url, e, time.time()-timebefore))
                      continue
                 else:
                      _print( "urllib2_version visit %s over . cost %s s.\n"%(url,   time.time()-timebefore))
                      return content
                      break
            return None


        

def excepthookinfo(type, value, tb):
    if hasattr(sys, 'ps1') or not (
          sys.stderr.isatty() and sys.stdin.isatty()
          ) or issubclass(type, SyntaxError):
        # Interactive mode, no tty-like device, or syntax error: nothing
        # to do but call the default hook
        sys.__excepthook__(type, value, tb)
    else:
        import traceback, pdb
        # You are NOT in interactive mode; so, print the exception...
        traceback.print_exception(type, value, tb)
        print
        # ...then start the debugger in post-mortem mode
        pdb.pm()
