#如何扩充多参数（argsVector） 多结果 
import threading , Queue, time
import func



testthreadmode = 0
printmode = 0
StopWhileGetOK    = False
MAX_THREADS_NUM  =    20   #runMT线程池的最大线程数990 ,1000多会创建失败，越多越快



 

RESULT_ERROR     = 0  #错误
RESULT_OK        = 1  #正确
RESULT_TRYAGAIN  = 2  #需要重试 超时或者10055情况下重试 ，配合 MAX_TRYCONNECT_NUM 使用

 
#test mt with different number threads
def runMT(modulename, threadfunc, argslist , 
          create_result_queue=True,   result_queue = None,
          resultfunc=None, resultargs=None, Needlog = False):
    if Needlog:
      fp = open(modulename +'.txt','w')
    if testthreadmode == 1 :
        tslist = [10,100, 200, 400, 500, 600, 900, 1200]
    else:
        tslist =[MAX_THREADS_NUM]#
    for threadsnumber in tslist:         
        timebefore =  time.time()
        mt = MT(threadfunc, argslist, threadsnumber,
                create_result_queue, result_queue, resultfunc , resultargs )
        mt.start()
        mt.join()        
        func._print("%s run over.threads number : %s run cost %s  s." % ( modulename, threadsnumber, time.time()-timebefore))
        if Needlog:
           mt.write_result_que(fp)          
           fp.flush()
    if Needlog:           
       fp.close()

class MT(object):
   def __init__(self, func, argsVector, MAXTHREADS=15,  
                      create_result_queue=True,   result_queue = None,                       
                      result_func = None, result_args = None
                      ):
                self._func = func
                self._lock = threading.Lock() 
                self._nextArgs = iter(argsVector).next #_func的参数列表
                self._threadPool = [ threading.Thread(target = self._doFunc) for i in range (MAXTHREADS)]
                
                self._result_func = result_func
                self._result_args = result_args
                
                self._stoprunallthread = False

                if create_result_queue:
                   self._result_queue = Queue.Queue()  #记录结果 线程安全的
                else:
                   self._result_queue = result_queue
  
                   
   def _doFunc(self):
                func._print( threading.currentThread().getName()  + " thread begin\n")
                while True:
                   if self._stoprunallthread:
                      break
                   #func._print( threading.currentThread().getName()  + " run \n" )
                   if self._lock.acquire(10)== False:
                       func._print (threading.currentThread().getName()  + " acquire false***********************\n")
                   #func._print( threading.currentThread().getName()  + " acquire ok\n" )
                   try:
                       try:
                          args = self._nextArgs()

                       except StopIteration:
                          func._print (threading.currentThread().getName()  + " no more args\n" )
                          break
                   finally:
                       self._lock.release()
                   #func._print (threading.currentThread().getName()  + " func\n" )
                   
                   result = self._func(args)
                   
                   #printmode非None的结果才记录结果到queue
                   #func._print (threading.currentThread().getName()  + " put que\n" )
                   if self._result_func is None : #no indicate result func then store to queue simply
                      if self._result_queue is not None and result is not None:
                         self._result_queue.put((args, result))
                   else:  #run result with the result_func
                      self._result_func(result, self._result_args)  

                   #result不是None且OK就停止标志，则停止   
                   if result is not None  and StopWhileGetOK:
                         self._stoprunallthread = True
                   #func._print( threading.currentThread().getName()  + " leave \n")

                   
                func._print( threading.currentThread().getName()  + " thread exit\n")


   def write_result_withargs(self, fp) :    
               while not self._result_queue.empty():
                  args , result =  self._result_queue.get()
                  fp.write("%s\n%s\n  " %(args, result))  #如多个结果 
               return True                           
 
               
   def get(self, *a, **kw):
                if self._queue is not None:
                    return self._queue.get(*a, **kw)
                else:
                    raise ValueError, ' Not queueing results'
                  

   def start(self):
                for thread in self._threadPool:
                    time.sleep(0)  #give chance to other threads
                    thread.start()
                    func._print ("thread start\n")
                
   def join(self, timeout = None):
                for thread in self._threadPool:
                    thread.join(timeout)


