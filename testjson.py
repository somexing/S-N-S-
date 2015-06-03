
import json

import sys, re, Queue, time,os
sys.path.append("../mymodule")
import func
import mt
from lxml import etree

printmode = True
MAX_TRY_TIMES  = 2


func.SHOW_LOG = False


focus_iid_list = [] #'89384484' # #default, 开始id     322782894'  #
deep_level =  1 #爬取深度
focus_value = 3 #关注度超过多少，才会进一步挖掘

 
mt.MAX_THREADS_NUM = 600 #线程池大小

fans_file_name = 'fans.dat'
subs_file_name = 'subs.dat'
focus_subid_file_name = "focus_subs.dat"

# get  first_iid,  deep_levelm focus_value (only dig the sub which's focus value > this value)


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
      

td_first_video_url = 'http://www.tudou.com/programs/view/KCByQcmiCHc/'

td = 'http://tdrec.youku.com/tjpt/tdrec?encode=utf-8&count=20&juid=019fd7i8t9vb9&pcode=20000300&userid=68259393&itemid=202693301&_=1432960070475'
td_url = 'http://tdrec.youku.com/tjpt/tdrec?encode=utf-8&count=20&itemid=202693301&pcode=20000300'
	
yk = 'http://ykrec.youku.com/video/packed/list.json?guid=1425299560757n5F&vid=227687152&sid=0&cate=90&apptype=1&pg=1&module=1&pl=20&needTags=1&atrEnable=true&callback=RelationAsync.videoCallback&uid=59780527&t=0.028587819542735815'
resp = func.GetHttpContent( yk )           
print resp
if resp is not None :
        id_name_xpath = '//*[@id="tjptList"]/li[1]/div[2]/h6/a'
        play_times_xpath = '//*[@id="tjptList"]/li[1]/div[2]/p[2]'
        yk_xpath = '//*[@id="relationvideo_async"]/div/div[1]/div[3]/div[1]/a'
        tree = etree.HTML(resp)
        
        r_list =  tree.xpath(id_name_xpath)
 
        if len(r_list) > 0:    
           print  r_list[0].text.strip() 
   
        r_list =  tree.xpath(play_times_xpath)
        if len(r_list) > 0:    
           print   r_list[0].text.strip() 
           
        fp = open('testrel.htm','w')     
        fp.write(resp)
        fp.close()        
       

