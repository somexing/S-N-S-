#输入一个用户，得到所粉丝的所有订阅用户页的主页url记录到结果文件 
#记录用户，粉丝id到文件
#进一步，得到所有订阅用户的所有粉丝，再获取这些粉丝的所有订阅用户页的主页url记录到结果文件
'''

参数说明：

-u 指定爬虫开始地址

-d 指定爬虫深度

--thread 指定线程池大小，多线程爬取页面，可选参数，默认10

--dbfile 存放结果数据到指定的数据库（sqlite）文件中

--key 页面内的关键词，获取满足该关键词的网页，可选参数，默认为所有页面

-l 日志记录文件记录详细程度，数字越大记录越详细，可选参数，默认spider.log

--testself 程序自测，可选参数

 

功能描述：

1、指定网站爬取指定深度的页面，将包含指定关键词的页面内容存放到sqlite3数据库文件中

2、程序每隔10秒在屏幕上打印进度信息

3、支持线程池机制，并发爬取网页

4、代码需要详尽的注释，自己需要深刻理解该程序所涉及到的各类知识点

5、需要自己实现线程池

 

提示1：使用re  urllib/urllib2  beautifulsoup/lxml2  threading optparse Queue  sqlite3 logger  doctest等模块

提示2：注意是“线程池”而不仅仅是多线程

提示3：爬取sina.com.cn两级深度要能正常结束
''' 

#sub_fan_url  用户的粉丝页      
#fan_sub_url  粉丝的订阅页
#fan_home     粉丝主页
#sub_home     用户主页

import json

import sys, re, Queue, time,os
sys.path.append("../mymodule")
import func
import mt
from lxml import etree

printmode = True
MAX_TRY_TIMES  = 2


func.SHOW_LOG = False


focus_sub_id_list = [] #'89384484' # #default, 开始id     322782894'  #
deep_level =  1 #爬取深度
focus_value = 3 #关注度超过多少，才会进一步挖掘

 
mt.MAX_THREADS_NUM = 600 #线程池大小

fans_file_name = 'fans.txt'
subs_file_name = 'subs.txt'
focus_subid_file_name = "focus_subs.txt"

TOP_N = 20
topn_sub_file_name = 'topsub.txt'

# get  first_sub_id,  deep_levelm focus_value (only dig the sub which's focus value > this value)


def get_html_func(_url):
    resp = func.GetHttpContent ( _url )           
    if resp is None :
      func._print ("failed get html .The url = %s \n"%(_url ))                  
    return resp
    
def get_tudou_json(_url):
    resp = func.GetHttpContent ( _url )           
    if resp is None :
       func._print ("failed get html .The url = %s \n"%(_url ))      
       return None
    id_list = []       
    #print json_txt
    jsn = json.loads(resp) 
    ttl_num = jsn['data']['total']
    for each_data in  jsn['data']['dataList']:
        id = each_data['uid'] 
        id_list.append(id)                   
    return id_list
      


        
        
        
def store_to_dict(result_list, id_dict):
     
    for each_id in result_list:
      str_id = str(each_id)
      id_focus_number = 1
      if id_dict.has_key(str_id):
         id_focus_number = id_dict[str_id] + 1                
      id_dict[str_id] = id_focus_number    
    
    return 
      
  
def store_to_list( result_list, all_id_list):   
  
    all_id_list.extend( result_list)
    return   
  

class SNS ():
  def __init__(self ,  f_s,  s_f,  s):
      self.f_s_list =  f_s
      self.s_f_list =  s_f
      self.s_list = s
  def read_arg(self) :   
    global focus_sub_id_list, deep_level, focus_value        
    if (len(sys.argv) > 1):
       first_sub_id = sys.argv[1]      # video id            
       focus_sub_id_list.append(first_sub_id)
       self.write_unique_idlist_to_file(focus_sub_id_list, focus_subid_file_name)
       print("I will run first_sub_id %s" % first_sub_id)
    else:
       print("No indicate argument, By Default read from %s "%focus_subid_file_name)
       focus_sub_id_list = self.get_id_list_from_file(focus_subid_file_name)
    if (len(sys.argv) > 2):
       deep_level = int(sys.argv[2])            
    print("I will dig %s level" %  deep_level)
    if (len(sys.argv) > 3):
       focus_value = int(sys.argv[3])
    print("I will dig only focus value > %s" %  focus_value)       
      
  def get_fan_sub_first_url(self, fan_id):
      return  self.f_s_list[0] + str(fan_id) + self.f_s_list[1] 

  def get_sub_fan_first_url(self, sub_id):
      return  self.s_f_list[0] + str(sub_id) + self.s_f_list[1] 


  def get_fan_sub_page(self, fan_id, page_num):
      return  self.f_s_list[0] + str(fan_id) + self.f_s_list[2] + str(page_num) + self.f_s_list[3] 

  def get_sub_page_from_sub_url(self, fan_sub_url, page_num):       
      idx = fan_sub_url.find(self.f_s_list[3])
      new_url = fan_sub_url[0:idx-1] + str(page_num) + self.f_s_list[3] 
      #print("get_sub_page_from_sub_url %s %s %s"%(fan_sub_url, page_num, new_url))
      return new_url

  def get_fan_page_from_fan_url(self,  sub_fan_url, page_num):        
      idx = sub_fan_url.find(self.s_f_list[3])
      new_url = sub_fan_url[0:idx-1] + str(page_num) + self.s_f_list[3]       
      return new_url


     
  def getsubfanurl(self, sub_id):
      return self.s_f_list[0] + str(sub_id) + self.s_f_list[1] 

  def getsubfanurl_page(self, sub_id, page_num):
      return  self.s_f_list[0] + str(sub_id) + self.s_f_list[2] + str(page_num) + self.s_f_list[3] 
      
  def getsubinfourl(self, sub_id):
      return  self.s_list[0] + str(sub_id) +  self.s_list[1] 



  '''
      this_page_num = ttl_num - (pagenum - 1) * max_num_per_page
      if this_page_num > max_num_per_page:          
         this_page_num =  max_num_per_page
         
      if this_page_num != len(jsn['data']['dataList']) : # 页面datalist长度和计算得到的数量不符
         print (" this_page_num = %s,jsn data number is %s, ttl_num is %s ,pagenum is %s"
                %(this_page_num, len(jsn['data']['dataList']),  ttl_num, pagenum)) 
         this_page_num =       
      for  i in range(this_page_num):     
        id = jsn['data']['dataList'][i]['uid']
        id_list.append(id)          
  '''

      
  def get_uid_from_tudou_response(self, json_txt, id_list):   
      #print json_txt
      jsn = json.loads(json_txt) 
      ttl_num = jsn['data']['total']
      for each_data in  jsn['data']['dataList']:
        id = each_data['uid'] 
        id_list.append(id)
        
      return ttl_num
      
  def store_id_to_dict(self, id_list, id_dict):
    for each_id in id_list:
      str_id = str(each_id)
      id_focus_number = 1
      if id_dict.has_key(str_id):
         id_focus_number = id_dict[str_id] + 1                
      id_dict[str_id] = id_focus_number    
  
  def store_id_to_list(self, id_list, all_id_list):
    all_id_list = all_id_list + id_list
    return   
  
      
  #return all fan usr id list of one sub( given one sub_id)
  def get_fans(self,  sub_id):
    all_fan_id_list = []
    
    #要获取到页数，无法mt
    sub_fan_url = self.getsubfanurl(sub_id)
    #get fan's home url from sub_fan_url
    resp = func.GetHttpContent( sub_fan_url )           
    if resp is None :
       func._print ("failed get html .The url = %s \n"%(sub_fan_url ))      
       return
    fan_id_list = []          
    ttl_fans_num = self.get_uid_from_tudou_response(resp, fan_id_list) 
    all_fan_id_list = all_fan_id_list + fan_id_list    
    page_ttl = ttl_fans_num / max_num_per_page    
    if (ttl_fans_num % max_num_per_page > 0) :
        page_ttl = page_ttl + 1    
    #print("the number of fans found from sub id %s: %s "% (sub_id, len(all_fan_id_list)))    
    #print("the number of pages of fans of sub id %s: %s "% (sub_id, page_ttl )) 
    if (page_ttl > 1) :
      sub_fan_url_list = []     
      for  pagenum  in range(2, page_ttl  + 1):  #next page from 2 to page_ttl , more fans      
            sub_fan_url = self.getsubfanurl_page(sub_id, pagenum)
            sub_fan_url_list.append(sub_fan_url)
   
      mt.runMT("get_fans", get_tudou_json, sub_fan_url_list, 
             False,  None,
             store_to_list, all_fan_id_list)  
    #print("found %s fans   from sub id %s: %s "% (len(all_fan_id_list), sub_id  )) 
    return all_fan_id_list
  
  def get_all_subs(self, all_fan_id_list, sub_id_dict):
    all_sub_id_counter = 0     
    all_sub_url_list = []
    #get every fan's sub's url, get first page first step
    for fan_id  in all_fan_id_list :     
        sub_url =  self.get_fan_sub_first_url(fan_id)
        all_sub_url_list.append(sub_url) #first page
    first_page_result_queue = Queue.Queue() 
    mt_create_queue_flag = False
    mt.runMT("get_all_subs", get_html_func, all_sub_url_list, mt_create_queue_flag, first_page_result_queue)
    #for every sub's url , 
    other_page_sub_url_list = []     # other page
    while (not first_page_result_queue.empty()):
        sub_url , resp  =   first_page_result_queue.get()
        sub_id_list = []       
        ttl_subs_num = self.get_uid_from_tudou_response(resp, sub_id_list)           
        sub_id_counter = len(sub_id_list)
        #print("the number of subs found from  the fan id  %s 's first page : %s "% (sub_url, sub_id_counter))                
        self.store_id_to_dict(sub_id_list ,  sub_id_dict)   
        page_ttl = ttl_subs_num / max_num_per_page    # ttl_subs_num max is 999, per page max_num_per_page
        if (ttl_subs_num % max_num_per_page > 0) :
          page_ttl = page_ttl + 1       
        if page_ttl > 1 :# has more page 
           for   pagenum  in range(2, page_ttl + 1):  #next page from 2 to page_ttl , more subs
              other_sub_url = self.get_sub_page_from_sub_url(sub_url, pagenum)
              other_page_sub_url_list.append( other_sub_url )
    #print("the number of other page of subs need to get  : %s "% (len(other_page_sub_url_list)))                             
    mt.runMT("get_all_subs 2", get_tudou_json, other_page_sub_url_list,
             False,  None,
             store_to_dict, sub_id_dict)          
    #this_counter = self.get_subs(fan_id, sub_id_dict)
    #all_sub_id_counter = all_sub_id_counter + this_counter  
  
  def get_all_fans(self, all_sub_id_list, fan_id_dict):
    all_fan_id_counter = 0     
    all_fan_url_list = []
    #get every sub's fan's url, get first page first step
    for sub_id  in all_sub_id_list :     
        fan_url =  self.get_sub_fan_first_url(sub_id)
        all_fan_url_list.append(fan_url) #first page
    first_page_result_queue = Queue.Queue() 
    mt_create_queue_flag = False
    mt.runMT("get_all_subs", get_html_func, all_fan_url_list, mt_create_queue_flag, first_page_result_queue)
    #for every fan's url , 
    other_page_url_list = []     # other page
    while (not first_page_result_queue.empty()):
        _url , resp  =   first_page_result_queue.get()
        fan_id_list = []       
        ttl_fans_num = self.get_uid_from_tudou_response(resp, fan_id_list)           
        fan_id_counter = len(fan_id_list)
        ##print("the number of subs found from  the fan id  %s 's first page : %s "% (sub_url, sub_id_counter))                
        self.store_id_to_dict(fan_id_list ,  fan_id_dict)   
        page_ttl = ttl_fans_num / max_num_per_page    # ttl_subs_num max is 999, per page max_num_per_page
        if (ttl_fans_num % max_num_per_page > 0) :
          page_ttl = page_ttl + 1       
        if page_ttl > 1 :# has more page 
           for   pagenum  in range(2, page_ttl + 1):  #next page from 2 to page_ttl , more subs
              other_url = self.get_fan_page_from_fan_url(fan_url, pagenum)
              other_page_url_list.append( other_url )
    #print("the number of other page of subs need to get  : %s "% (len(other_page_sub_url_list)))                             
    mt.runMT("get_all_fans", get_tudou_json, other_page_url_list,
             False,  None,
             store_to_dict, fan_id_dict)     
      
  #add one fan's all subscribed user ids and relative focus value to sub_id_dict (global varible)
  def get_subs(self, fan_id, sub_id_dict):   #error runing! get nothing! need fix!     
        fan_sub_url =  self.get_fan_sub_first_url(fan_id)
        resp = func.GetHttpContent("GET", fan_sub_url )           
        if resp is None :
           func._print ("failed get html .The url = %s \n"%(fan_sub_url ))      
           return 0     
        sub_id_list = []       
        ttl_subs_num = self.get_uid_from_tudou_response(resp, sub_id_list,pagenum = 1)           
        #print("the number of subs in the json from the fan id %s : %s "% (fan_id, ttl_subs_num)) 
        self.store_id_to_dict(sub_id_list ,  sub_id_dict)   
        page_ttl = ttl_subs_num / max_num_per_page    # ttl_subs_num max is 999, per page max_num_per_page
        if (ttl_subs_num % max_num_per_page > 0) :
          page_ttl = page_ttl + 1
        sub_id_counter = len(sub_id_list)
        for   pagenum  in range(2, page_ttl + 1): #next page from 2 to page_ttl , more subs
            fan_sub_url = self.get_sub_page(fan_id, pagenum) 
            resp = func.GetHttpContent("GET", fan_sub_url )           
            if resp is None :
               func._print ("failed get html .The url = %s \n"%(fan_sub_url ))      
               continue      
            sub_id_list = []       
            self.get_uid_from_tudou_response(resp, sub_id_list, pagenum)           
            self.store_id_to_dict(sub_id_list ,  sub_id_dict)   
            sub_id_counter = sub_id_counter + len(sub_id_list)
        print("scrapy %s subs found from the fan id %s : %s "% (sub_id_counter, fan_id ))                
        return sub_id_counter
  
      
  #get sub's fans' subscribed sub url , write to file
  def get_sub_fan_sub(self, sub_id, sub_id_dict):          
    
    all_fans_id_list = self.get_fans(sub_id)
    print("scrapy found %s fans from the sub id %s   "% (len(all_fans_id_list), sub_id))                    
    self.write_unique_idlist_to_file(all_fans_id_list, fans_file_name)
    self.write_unique_idlist_to_file(all_fans_id_list, sub_id + fans_file_name)
    
        
    self.get_all_subs( all_fans_id_list, sub_id_dict)   
    all_sub_id_counter = len(sub_id_dict)
              
    print("scrapy found %s subs from the fans of sub id %s "% (all_sub_id_counter, sub_id))                
    return sub_id_dict
    
 

     
  def write_sub_info(self, sub_id_dict, file_name, file_mode = 'w'):
    sub_id_focus_pair_list = sorted(sub_id_dict.items(), lambda x, y: cmp(x[1], y[1]), reverse=True)    
   
    all_sub_url_list = []    
    for  _pair in sub_id_focus_pair_list:
           sub_id = _pair[0]
           sub_url = self.getsubinfourl(sub_id)
           all_sub_url_list.append(sub_url)
    #get url's page
    sub_page_result_queue = Queue.Queue() 
    mt_create_queue_flag = False
    mt.runMT("get_all_subs", get_html_func, all_sub_url_list, mt_create_queue_flag, sub_page_result_queue)
    #for every sub's url , 

    sub_url_name_dict = {}
    id_name_xpath = '//*[@id="topTitle"]/h3'
    while (not sub_page_result_queue.empty()):
        _url , html  =   sub_page_result_queue.get()
        tree = etree.HTML(html)
        r_list =  tree.xpath(id_name_xpath)
        #sub_url_name_dict[_url] = str(_url)
        if len(r_list) > 0:    
           id_name = r_list[0].text.strip() 
          # print id_name
           sub_url_name_dict[_url] = id_name

    fp = open(file_name ,file_mode) 
    for  _pair in sub_id_focus_pair_list:
           sub_id = _pair[0]
           focus_num = _pair[1]          
           sub_url = self.getsubinfourl(sub_id)
           id_name = str(sub_id)
           if  sub_url_name_dict.has_key(sub_url):
             id_name = sub_url_name_dict[sub_url]
           fp.write('<a href = "' +sub_url +  '" target="_blank">' + 
                      (str(id_name.encode("GBK", 'ignore'))) +' </a>  ' + str(focus_num))
           fp.write('<br>')
    fp.close()   
    print("%s sub's url and focus value writed to %s!"%(len(sub_id_focus_pair_list),file_name ))
    return sub_id_focus_pair_list

  #read id from file named file_name，write id from id_list to file if unique
  def write_unique_idlist_to_file(self, id_list, id_file_name):   
    fp = open(id_file_name,'a+')         
    id_lines = fp.readlines()
    fp.close()
            
    id_writed_counter = 0 
    fp = open(id_file_name,'a')     
    for id in id_list:
      if str(id)+os.linesep in id_lines: #for id_lines with os.linesep
        continue
      fp.write(str(id))
      fp.write(os.linesep)
      id_writed_counter = id_writed_counter + 1 
    fp.close()   
    print("%s id writed to %s !" % (id_writed_counter, id_file_name))     
    
  def get_need_deepdig_sub(self, sub_id_focus_pair_list):
     focus_sub_id_list = []
     for  _pair in sub_id_focus_pair_list:
           sub_id = _pair[0]
           focus_num = _pair[1]
           focus_sub_id_list.append(sub_id)
           if focus_num < focus_value : #只挖关注度值高于 focus_value 的用户                         
             break           #for the list is sorted by focus_num
     return focus_sub_id_list           
     
  def get_id_list_from_file(self, id_file_name):    
    fp = open(id_file_name,'a+')         
    id_lines = fp.readlines()
    fp.close()    
    
    all_id_list = []
    for  id_line in id_lines:
       a_id = id_line.strip(os.linesep)
       all_id_list.append(a_id)    
    print("get %s id from the file named   %s "% (len(all_id_list), id_file_name))                                                    
    return all_id_list     
  
  def get_new_sub_dict_compared_file(self, new_sub_id_dict, old_file_name):
    new_sub_id_list = new_sub_id_dict.keys()
    old_sub_id_list = self.get_id_list_from_file(old_file_name)
    id_dict_compared = {}
    
    #print("new_sub_id_list : %s , old_sub_id_list : %s" %(len(new_sub_id_list),len(old_sub_id_list)))
    for the_id in new_sub_id_list :
      if str(the_id) not in old_sub_id_list :
         id_dict_compared[the_id] = new_sub_id_dict[the_id]    
    return id_dict_compared
        
  def write_TopN_sub_id(self, sub_id_dict, file_name, file_mode = 'w'):
    sub_id_focus_pair_list = sorted(sub_id_dict.items(), lambda x, y: cmp(x[1], y[1]), reverse=True)    

    fp = open(file_name ,file_mode) 
    for  _pair in sub_id_focus_pair_list:
           sub_id = _pair[0]
           fp.write(str(sub_id)+os.linesep)
    fp.close()   
    print("%s top sub's id writed to %s!"%(len(sub_id_focus_pair_list),file_name ))
    
     
  def deep_dig_sub(self, first_sub_id):
    
    sub_id_dict = {}
    last_dig_sub_id_list = []
    dig_sub_id_list = [first_sub_id] #only get one id from argv, use     
    for i in range(deep_level): #loop from 0 to  deep_level - 1
       this_level = i + 1
       print("scrapy sub id %s, level %s "% (first_sub_id, this_level))
       for sub_id in dig_sub_id_list:   # dig each sub id  ,get all sub to sub_id_dict
           self.get_sub_fan_sub(sub_id, sub_id_dict)                         
       
       
       sub_id_dict_compared = self.get_new_sub_dict_compared_file(sub_id_dict, subs_file_name)
       #new_sub_html_name = "new_"+first_sub_id+"_"+str(this_level)+".htm"  
       new_sub_html_name = "new_sub.htm"  
       self.write_sub_info(sub_id_dict_compared, new_sub_html_name, 'a+' ) 
       
       all_sub_html_name = "all_"+first_sub_id+"_"+str(this_level)+".htm"      
       sub_id_focus_pair_list = self.write_sub_info(sub_id_dict, all_sub_html_name ) # every level will record              

       this_sub_file_name = first_sub_id + subs_file_name       #?
      # self.write_unique_idlist_to_file(sub_id_dict.keys(), this_sub_file_name)
       
       last_dig_sub_id_list = last_dig_sub_id_list + dig_sub_id_list  # id has digged
       if (i  <   deep_level - 1) : #need dig again
         focus_sub_id_list = self.get_need_deepdig_sub( sub_id_focus_pair_list )
         dig_sub_id_list = list(set(focus_sub_id_list) - set(last_dig_sub_id_list)) # clean id  which has digged   
    
    self.write_unique_idlist_to_file(sub_id_dict.keys(), subs_file_name)
    self.write_TopN_sub_id(sub_id_dict, topn_sub_file_name)     
    
  def getnewsubfromfansfile(self, new_all_sub_id_dict):
       #read all fans' ids from file
       all_fans_id_list = self.get_id_list_from_file(fans_file_name)
       print("get %s fans id from the file named   %s "% (len(all_fans_id_list), fans_file_name))                              
       self.getnewsubfromallfans(all_fans_id_list, new_all_sub_id_dict)

  def getnewsubfromallfans(self, all_fans_id_list, new_all_sub_id_dict):
       #get every fan's sub list        
       self.get_all_subs( all_fans_id_list, new_all_sub_id_dict)   
       print("scrapy get %s subs from the fans get from the file named  %s "% (len(new_all_sub_id_dict), fans_file_name))
       
       sub_id_dict_compared = self.get_new_sub_dict_compared_file(new_all_sub_id_dict, subs_file_name)
       new_sub_html_name = "new_sub_from_f.htm"  
       self.write_sub_info(sub_id_dict_compared, new_sub_html_name ) 
       #record new sub id
       self.write_unique_idlist_to_file(sub_id_dict_compared.keys(), subs_file_name)
  
  def getnewsubfromsubsfile(self, new_all_sub_id_dict):
      subs_id_list_in_file = self.get_id_list_from_file(subs_file_name)
      print("get %s subs id from the file named   %s "% (len(old_subs_id_list), subs_file_name))                                     
      new_all_fans_id_dict = {}
      self.getnewsubfromallsubs( subs_id_list_in_file, new_all_sub_id_dict) 
      
  #从 old_subs_id_list 获取fans ，再获取fans的所有sub ,store to    new_all_sub_id_dict  
  def getnewsubfromallsubs(self, old_subs_id_list, new_all_sub_id_dict):          
       #get every fan's fans list        
       new_all_fans_id_dict = {}
       self.get_all_fans( old_subs_id_list, new_all_fans_id_dict)   
       print("scrapy get %s fans from the list contained %s subs "% (len(new_all_fans_id_dict), len(old_subs_id_list)))
       
       new_all_fans_id_list = new_all_fans_id_dict.keys()       
       self.get_all_subs( new_all_fans_id_list, new_all_sub_id_dict)   
       all_sub_id_counter = len(new_all_sub_id_dict)
       print("scrapy found %s subs from the fans get from the file named %s "% (all_sub_id_counter, subs_file_name))
       
       #compare to get new sub id and record      
       sub_id_dict_compared = self.get_new_sub_dict_compared_file(new_all_sub_id_dict, subs_file_name)
       new_sub_html_name = "new_sub_from_s.htm"  
       self.write_sub_info(sub_id_dict_compared, new_sub_html_name , 'a+' ) 
       #record new sub id
       self.write_unique_idlist_to_file(sub_id_dict_compared.keys(), subs_file_name)      
       self.write_TopN_sub_id(new_all_sub_id_dict, topn_sub_file_name)     
           
 
    


#define tudou.com
#粉丝的订阅页f_s        http://www.tudou.com/home/_58523472/usersub?type=0   
#用户/粉丝主页 f,s      http://www.tudou.com/home/_58523472/ 
#用户的粉丝页s_f        http://www.tudou.com/home/_58523472/usersub?type=1

#粉丝id拼凑得到订阅用户页面的url
#td_f_s_pre =  "http://www.tudou.com/home/_"
#td_f_s_post=  "/usersub?type=0" 
td_f_s_pre =  "http://www.tudou.com/uis/sub/userSubList.action?&app=homev2&uid="
td_f_s_post = "&checkSub=1&pageNum=1&pageSize=200&type=2"   
td_f_s_post_page_pre = "&checkSub=1&pageNum="
td_f_s_post_page_post = "&pageSize=200&type=2"   
tudou_f_s = [td_f_s_pre,  td_f_s_post, td_f_s_post_page_pre , td_f_s_post_page_post]

#用户id得到需要的用户info页面的url           
td_s_pre =  "http://www.tudou.com/home/_"
td_s_post = "/item?sort=2"    #排序
tudou_s=[td_s_pre, td_s_post]



#用户id得到用户的粉丝页面的url           
#td_s_f_pre =  "http://www.tudou.com/home/_"
#td_s_f_post = "/usersub?type=1"   

#用户id得到用户的粉丝页面的url 
td_s_f_pre =  "http://www.tudou.com/uis/sub/userFans.action?app=homev2&uid="
td_s_f_post = "&checkSub=1&pageNum=1&pageSize=200&type=2"   
td_s_f_post_page_pre = "&checkSub=1&pageNum="
td_s_f_post_page_post = "&pageSize=200&type=2"   
#每个返回的tudou的json页面最多值
max_num_per_page = 200 
tudou_s_f= [td_s_f_pre, td_s_f_post, td_s_f_post_page_pre,  td_s_f_post_page_post]
        
tudou_sns = SNS(tudou_f_s, tudou_s_f, tudou_s)



tudou_sns.read_arg() 

focus_fans_id_list = tudou_sns.get_id_list_from_file(fans_file_name)

print("I get %s fan id from file named %s  !" % (len(focus_fans_id_list) , fans_file_name))  
topn_sub_id_set = set(tudou_sns.get_id_list_from_file(topn_sub_file_name)[:TOP_N])
print("I get %s topn sub id from file named %s  !" % (len(topn_sub_id_set) , topn_sub_file_name))  


fan_values_dict = {}
for fan_id in focus_fans_id_list: #loop from 0 to  deep_level - 1
    fan_get_sub_id_dict = {}
    tudou_sns.get_all_subs([fan_id],  fan_get_sub_id_dict)   
    fan_get_sub_id_set = set(fan_get_sub_id_dict.keys())    
    fan_values_dict[fan_id] =  len(fan_get_sub_id_set & topn_sub_id_set) #get value
    
fan_values_pair_list_sorted = sorted(fan_values_dict.items(), lambda x, y: cmp(x[1], y[1]), reverse=True)        
  
valuable_fan_id_list = []
for pair in fan_values_pair_list_sorted:
     fan_id = pair [0]
     valuable_fan_id_list.append(fan_id)

new_sub_dict  = {}     
tudou_sns.get_all_subs( valuable_fan_id_list, new_sub_dict)   
print("scrapy get %s subs from the valuable fans   "% (len(new_sub_dict) ))

#sub_id_dict_compared = tudou_sns.get_new_sub_dict_compared_file(new_sub_dict, subs_file_name)
new_sub_html_name = "new_sub_from_valuefans.htm"  
tudou_sns.write_sub_info(new_sub_dict, new_sub_html_name ) 
#record new sub id
tudou_sns.write_unique_idlist_to_file(new_sub_dict.keys(), subs_file_name)
     

   	
''' 
fp = open('valuesub.htm','w')         
for pair in fan_values_pair_list_sorted:
     fan_id = pair [0]
     fan_sub_url = 'http://www.tudou.com/home/_'+str(fan_id)+'/usersub?type=0'
     value = pair[1]     
     #print fan_id ,value
     fp.write('<a href = "' +fan_sub_url +  '" target="_blank">' + 
                      (str(fan_id.encode("GBK", 'ignore'))) +' </a>  ' + str(value))
     fp.write('<br>')
fp.close()   
print("%s fan id and value writed  !" % (len(fan_values_pair_list_sorted) ))   
'''

'''
idx = 1
for each_focus_sub_id in focus_sub_id_list:
   print("################### deal No.%s  id %s. total %s id ##################" 
         % ( idx, each_focus_sub_id, len(focus_sub_id_list)))
   idx = idx + 1 
   tudou_sns.deep_dig_sub(each_focus_sub_id)
'''   
#tudou_sns.getnewsubfromallfans()
#tudou_sns.getnewsubfromallsubs() #very slow!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!


 
      

        
        
    
    
     
