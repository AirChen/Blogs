import feedparser
import time
import os
import re
import pytz
from datetime import datetime
import yagmail
import requests
from jinja2 import FileSystemLoader, Environment
import json
import copy
from urllib import parse, request

def get_rss_info(feed_url):
    result = {"result": []}
    # 如何请求出错,则重新请求,最多五次
    for i in range(5):
        try:
            headers = {
                # 设置用户代理头(为狼披上羊皮)
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36",
                "Content-Encoding": "gzip"
            }
            # 设置15秒钟超时
            feed_url_content = requests.get(feed_url,  timeout= 15 ,headers = headers).content
            feed = feedparser.parse(feed_url_content)
            feed_entries = feed["entries"]
            feed_entries_length = len(feed_entries)
            print("==feed_url=>>", feed_url, "==len=>>", feed_entries_length)
            for entrie in feed_entries[0: feed_entries_length-1]:
                title = entrie["title"]
                link = entrie["link"]
                result["result"].append({
                    "title": title,
                    "link": link
                })
            break
        except Exception as e:
            print(feed_url+"第+"+str(i)+"+次请求出错==>>",e)
            pass

    return result["result"]

def process_line(line):
    # 获取link
    link = re.findall(r'\[订阅地址\]\((.*)\)', line)[0]
    # 生成超链接
    rss_info = get_rss_info(link)    

    if(len(rss_info) > 0):
        rss_info[0]["title"] = rss_info[0]["title"].replace("|", "\|")
        rss_info[0]["title"] = rss_info[0]["title"].replace("[", "\[")
        rss_info[0]["title"] = rss_info[0]["title"].replace("]", "\]")        

    if(len(rss_info) > 1):
        rss_info[1]["title"] = rss_info[1]["title"].replace("|", "\|")
        rss_info[1]["title"] = rss_info[1]["title"].replace("[", "\[")
        rss_info[1]["title"] = rss_info[1]["title"].replace("]", "\]")                    
    
    return copy.copy(rss_info)
 
def replace_readme():    
    session_list = []

    global g_rss_datetime
    global g_rss_num
    # 读取EditREADME.md
    with open(os.path.join(os.getcwd(),"EditREADME.md"),'r') as load_f:
        edit_readme_lines = load_f.readlines()
        session = {}
        session['list'] = []
        g_rss_num = 0
        for line in edit_readme_lines:
            if re.match(r'.*\[订阅地址\]\(.*\).*\{\{latest_content\}\}.*', line) != None:
                entity_list = process_line(line)                
                session['list'] += entity_list[:5]
                g_rss_num += 1
            elif re.match(r'.*\<h2 id\=\".*\"\>.*\<\/h2\>.*', line) != None:
                if g_rss_num != 0:
                    session_list.append(session)
                    session = {}
                    session['list'] = []
                
                t = re.findall(r'\<h2 id\=\"(.*)\"\>(.*)\<\/h2\>', line)[0][0]
                session['title'] = t                                
            elif re.match(r'.*\{\{ga_rss_datetime\}\}.*', line) != None:                
                # 填充统计时间
                g_rss_datetime = datetime.fromtimestamp(int(time.time()),pytz.timezone('Asia/Shanghai')).strftime('%Y-%m-%d %H:%M:%S')                
            
        if len(session['list']) > 0:
            session_list.append(session)        

    # 将新内容
    with open(os.path.join(os.getcwd(),"README.md"),'w') as load_f:
        load_f.write(new_edit_readme_md)
    
    return session_list

def get_bing_img_url():
    BING_API = "https://cn.bing.com/HPImageArchive.aspx?format=js&idx=0&n=10&nc=1612409408851&pid=hp&FORM=BEHPTB&uhd=1&uhdwidth=3840&uhdheight=2160"
    BING_URL = "https://cn.bing.com"
    
    header_info = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36"}
    req = request.Request(url=BING_API, headers=header_info)
    res = request.urlopen(req)
    res = res.read()

    json_obj = json.loads(res)     

    url_params = json_obj['images'][0]['url']
    url_img = BING_URL + url_params.split('&')[0]

    return url_img

def main():
    session_list = replace_readme()
    bing_img = get_bing_img_url()

    env = Environment(loader=FileSystemLoader('./templates'))
    template = env.get_template('basic.html')
    cout_html = template.render(web_title="RSS订阅", 
                rss_num=g_rss_num, ga_rss_datetime=g_rss_datetime,
                back_img=bing_img,
                session_list=session_list)

    with open(os.path.join(os.getcwd(),"render.html"),'w') as load_f:
        load_f.write(cout_html)

main()
