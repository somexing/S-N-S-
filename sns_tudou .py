﻿#get Social networks relationship ,sub & fan
#输入一个用户，得到所粉丝的所有订阅用户页的主页url记录到结果文件
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
func.USE_PROXY = False
printmode = True
MAX_TRY_TIMES  = 2
#func.PROXY_SERVER  =   "10.204.80.103:8080"
#func.PROXY_SERVER  =   "10.94.235.26:8080"

func.SHOW_LOG = True
#SNS Relations

first_sub_id = '89384484' # #开始id     '322782894'  #
deep_level =  1 #爬取深度
focus_value = 3 #关注度超过多少，才会进一步挖掘

#no use now
CONFIG_THREADPOOL_CAP = 10 #线程池大小



def read_arg() :   
    global first_sub_id, deep_level, focus_value
    if (len(sys.argv) > 1):
       first_sub_id = sys.argv[1]      # video id        
    else:
    	 print("No indicate argument, By Default ")
    
    print("I will run first_sub_id %s" % first_sub_id)

    if (len(sys.argv) > 2):
       deep_level = sys.argv[2]            
    print("I will dig %s level" %  deep_level)

    if (len(sys.argv) > 3):
       focus_value = sys.argv[3]               
    print("I will dig only focus value > %s" %  focus_value)


class SNS ():
  def __init__(self ,  f_s,  s_f,  s):
      self.f_s_list =  f_s
      self.s_f_list =  s_f
      self.s_list = s
       
      
  def getfansuburl(self, fan_id):
      return  self.f_s_list[0] + str(fan_id) + self.f_s_list[1] 

  def getfansuburl_page(self, fan_id, page_num):
      return  self.f_s_list[0] + str(fan_id) + self.f_s_list[2] + str(page_num) + self.f_s_list[3] 

     
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

      
  def get_uid_from_tudou_response(self, json_txt, id_list, pagenum):   
  	  #print json_txt
  	  jsn = json.loads(json_txt) 
  	  ttl_num = jsn['data']['total']
  	  for each_data in  jsn['data']['dataList']:
  	    id = each_data['uid'] 
  	    id_list.append(id)
  	  	
  	  return ttl_num
  	  
  def store_id_to_dict(self, id_list, id_dict):
    for each_id in id_list:
    	id_focus_number = 1
    	if id_dict.has_key(each_id):
    	   id_focus_number = id_dict[each_id] + 1    	       		 
    	id_dict[each_id] = id_focus_number		
  #return all fan usr id list of one sub( given one sub_id)
  def get_sub_fan(self,  sub_id):
    all_fan_id_list = []
    sub_fan_url = self.getsubfanurl(sub_id)
    #get fan's home url from sub_fan_url
    resp = func.GetHttpContent( sub_fan_url )           
    if resp is None :
       func._print ("failed get html .The url = %s \n"%(sub_fan_url ))      
       return
    fan_id_list = []          
    ttl_fans_num = self.get_uid_from_tudou_response(resp, fan_id_list, pagenum = 1) 
    all_fan_id_list = all_fan_id_list + fan_id_list    
    page_ttl = ttl_fans_num / max_num_per_page    
    if (ttl_fans_num % max_num_per_page > 0) :
      	page_ttl = page_ttl + 1    

    for   pagenum  in range(2, page_ttl  + 1):	 #next page from 2 to page_ttl , more fans
            sub_fan_url = self.getsubfanurl_page(sub_id, pagenum)
            resp = func.GetHttpContent(sub_fan_url )           
            if resp is None :
        	     func._print ("failed get html .The url = %s \n"%(sub_fan_url ))      
        	     continue      
            fan_id_list = []       
            self.get_uid_from_tudou_response(resp, fan_id_list, pagenum)  
            all_fan_id_list = all_fan_id_list + fan_id_list   
    print("the number of fans found from sub id %s: %s "% (sub_id, len(all_fan_id_list))) 
    return all_fan_id_list
    
  #add one fan's all subscribed user ids and relative focus value to sub_id_dict (global varible)
  def get_fan_sub(self, fan_id, sub_id_dict):        
        fan_sub_url =  self.getfansuburl(fan_id)
        resp = func.GetHttpContent( fan_sub_url )           
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
        for   pagenum  in range(2, page_ttl + 1):	#next page from 2 to page_ttl , more subs
        	  fan_sub_url = self.getfansuburl_page(fan_id, pagenum)
        	  resp = func.GetHttpContent(fan_sub_url )           
        	  if resp is None :
        	     func._print ("failed get html .The url = %s \n"%(fan_sub_url ))      
        	     continue      
        	  sub_id_list = []       
        	  self.get_uid_from_tudou_response(resp, sub_id_list, pagenum)           
        	  self.store_id_to_dict(sub_id_list ,  sub_id_dict)   
        	  sub_id_counter = sub_id_counter + len(sub_id_list)
        print("the number of subs found from  the fan id %s : %s "% (fan_id, sub_id_counter))                
        return sub_id_counter
  
      
  #get sub's fans' subscribed sub url , write to file
  def get_sub_fan_sub(self, sub_id, sub_id_dict):   
    all_fan_id_list = []   	
    all_fan_id_list = self.get_sub_fan(sub_id)
   
    all_sub_id_counter = 0     
    for fan_id  in all_fan_id_list :           
       this_counter = self.get_fan_sub(fan_id, sub_id_dict)
       all_sub_id_counter = all_sub_id_counter + this_counter
          
    print("the number of subs found from the fans of sub id %s : %s "% (sub_id, all_sub_id_counter))                
    return sub_id_dict
    
  def get_need_deepdig_sub(self, sub_id_focus_pair_list):
  	 focus_sub_id_list = []
  	 for  _pair in sub_id_focus_pair_list:
        	 sub_id = _pair[0]
        	 focus_num = _pair[1]
        	 focus_sub_id_list.append(sub_id)
        	 if focus_num < focus_value : #只挖关注度值高于 focus_value 的用户                         
        	   break           #for the list is sorted by focus_num
  	 return focus_sub_id_list         
  	 
  def write_sub_info(self, sub_id_focus_pair_list, sub_id_dict, this_level):
  	fp = open("url_"+first_sub_id+"_"+str(this_level)+".htm",'w')        
  	for  _pair in sub_id_focus_pair_list:
        	 sub_id = _pair[0]
        	 focus_num = _pair[1]
        	 info_url = self.getsubinfourl(sub_id)
        	 fp.write('<a href = "' +info_url +  '" target="_blank">' +str(sub_id)+' </a>  ' + str(focus_num))
        	 fp.write('<br>')
  	fp.close()   
  	print("%s sub's url and focus value writed!"%len(sub_id_focus_pair_list))
        
  	sub_id_list = sub_id_dict.keys()
  	sub_id_list.sort()
  	fp = open("id_"+first_sub_id+"_"+str(this_level)+".txt",'w')        
  	for  sub_id in sub_id_list:
        	 fp.write(str(sub_id))
        	 fp.write(os.linesep)
  	fp.close()   
  	print("%s sub id writed!"%len(sub_id_list))   	
  	
  	
  	 
  def deep_dig_sub(self):
  	sub_id_dict = {}
  	last_dig_sub_id_list = []
  	dig_sub_id_list = [first_sub_id]
  	for i in range(deep_level): #loop from 0 to  deep_level - 1
    	 for sub_id in dig_sub_id_list:  
           self.get_sub_fan_sub(sub_id, sub_id_dict)                  
    	 last_dig_sub_id_list = last_dig_sub_id_list + dig_sub_id_list  # id has digged
    	 sub_id_focus_pair_list = sorted(sub_id_dict.items(), lambda x, y: cmp(x[1], y[1]), reverse=True)
    	 self.write_sub_info(sub_id_focus_pair_list, sub_id_dict, this_level=i+1) # every level will record
    	 if (i  < 	deep_level - 1) : #need dig again
    	   focus_sub_id_list = self.get_need_deepdig_sub(	sub_id_focus_pair_list )
    	   dig_sub_id_list = list(set(focus_sub_id_list) - set(last_dig_sub_id_list)) # clean id  which has digged	 
  	    	 
 
    


#define tudou.com
#粉丝的订阅页f_s        http://www.tudou.com/home/_58523472/usersub?type=0   
#用户/粉丝主页 f,s      http://www.tudou.com/home/_58523472/ 
#用户的粉丝页s_f        http://www.tudou.com/home/_58523472/usersub?type=1

#用户的粉丝页面解析出粉丝ID <li class="fans_row fix" data-id="359301380" data-role="card" data-ucode="YnIPRVDoKMo">
td_re_f_id = r'<li class="fans_row fix" data-id="(.*?)"'
#粉丝的订阅用户页面解析出用户ID <li class="sub_row fix" data-id="76111775">
td_re_s_id = r'<li class="sub_row fix" data-id="(.*?)">'
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

read_arg()
 
tudou_sns.deep_dig_sub()

 
      

        
        
    
    
     
