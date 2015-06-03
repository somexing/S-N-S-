#输入一个vido，得到relation video id ,deep dig it!  
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


first_iid = ' '
deep_level =   2#爬取深度
 

 
mt.MAX_THREADS_NUM = 600 #线程池大小

 

# get  first_iid,  deep_levelm focus_value (only dig the sub which's focus value > this value)

def read_arg() :   
    global first_iid, deep_level
    if (len(sys.argv) > 1):
       first_iid = sys.argv[1]      # video id            
       print("I will run first_iid %s" % first_iid)
    else:
       print("No indicate argument, By Default  %s" % first_iid)
       
    if (len(sys.argv) > 2):
       deep_level = int(sys.argv[2])            
    print("I will dig %s level" %  deep_level)
 
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
      id_focus_number = 1
      if id_dict.has_key(each_id):
         id_focus_number = id_dict[each_id] + 1                
      id_dict[each_id] = id_focus_number    
    
    return 
      
  
def store_to_list( result_list, all_id_list):   
  
    all_id_list.extend( result_list)
    return   
  
 

def get_tudou_tj_json_url( iid):
    url_ = 'http://tdrec.youku.com/tjpt/tdrec?encode=utf-8&count=20&itemid=' + str(iid)+'&pcode=20000300'  
    #print url_
    return url_
 
       
def get_tjinfo_from_tudou_response( json_txt,  ttl_iid_set, playinfo_dict):       
    #print json_txt
    jsn = json.loads(json_txt) 
 
    for each_item in  jsn['recommendItems'] :
        iid = each_item['itemId'] 
        ttl_iid_set.add(iid)    
        
        item_title = each_item['title']                           
        playLink = each_item['playLink']  
        str_playAmount = each_item['playAmount']
        str_playAmount = (each_item['playAmount'].replace(',','')) #del ,   
        str_playAmount = (each_item['playAmount'].replace('k','000')) #del k   
        str_playAmount = filter(lambda ch: ch in '0123456789', str_playAmount)    
        #
        playAmount =  int(str_playAmount)            
        playinfo_dict[playLink] = [playAmount, item_title]
    
 
             
def deep_dig_relation( first_iid, deep_level):    
    ttl_iid_set = set()
    playinfo_dict = {}
    has_diged_iid_set = set()    
    dig_iid_set = set([first_iid])  #only get one id from argv, use     

    for i in range(deep_level): #loop from 0 to  deep_level - 1
       this_level = i + 1
       print("scrapy iid number %s, level %s "% (len(dig_iid_set), this_level))
       url_list = []
       for iid in dig_iid_set:   # dig each iid  ,get all sub to iid_dict
           url_list.append( get_tudou_tj_json_url(iid))
                      
       html_result_queue = Queue.Queue() 
       mt_create_queue_flag = False
       mt.runMT("deep_dig_relation", get_html_func, url_list, mt_create_queue_flag, html_result_queue)
       #for every sub's url ,        
       while (not html_result_queue.empty()):
          _url , resp  =   html_result_queue.get()
          get_tjinfo_from_tudou_response( resp,  ttl_iid_set, playinfo_dict )   
           
       has_diged_iid_set = has_diged_iid_set | dig_iid_set 
       dig_iid_set = dig_iid_set | ttl_iid_set - has_diged_iid_set
   
    relation_html_name = "relation"+str(first_iid)+"_"+str(deep_level)+".htm"  
    write_relation_result(playinfo_dict, relation_html_name ) 
  
def write_relation_result(playinfo_dict, file_name)   :
    fp = open(file_name ,'w') 
    playinfo_pair_list = sorted(playinfo_dict.items(), lambda x, y: cmp(x[1], y[1]), reverse=False)    
   
    all_sub_url_list = []    
    for  _pair in playinfo_pair_list:
           url = _pair[0]
           viewed = _pair[1][0]
           title_ = _pair[1][1]
           #print title_
           fp.write('<a href = "' + url +  '" target="_blank">'  
                   + (str(title_.encode("GBK", 'ignore'))) +' </a>  ' + str(viewed) +'<br>')          
    fp.close()   
    print("%s  url and viewed value writed to %s!"%(len(playinfo_dict), file_name ))
    
 
#每个返回的tudou的json页面最多值
 
reload(sys)
sys.setdefaultencoding('GBK')

read_arg()

deep_dig_relation(first_iid, deep_level)

td_first_video_url = 'http://www.tudou.com/programs/view/zAG4tl8H_JU/'

 
