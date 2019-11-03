import requests
from bs4 import BeautifulSoup
import time
from random import randint
import os.path
import csv
from lxml.html import fromstring
from fake_useragent import UserAgent

def get_proxies(num_proxies):
    url = 'https://free-proxy-list.net/'
    response = requests.get(url)
    parser = fromstring(response.text)
    proxies = set()
    for i in parser.xpath('//tbody/tr')[:num_proxies]:
        if i.xpath('.//td[7][contains(text(),"yes")]'):
            #Grabbing IP and corresponding PORT
            proxy = ":".join([i.xpath('.//td[1]/text()')[0], i.xpath('.//td[2]/text()')[0]])
            proxies.add(proxy)
    return proxies

def localize_posts(href):
  value = False
  if isinstance(href,str):
    if len(href)>1:
      value = ('#' in href and href[1]=='p')
  return value

def remove_citations(post):
  while post.find(class_="post-bbcode-quote-wrapper") is not None:
    post.find(class_="post-bbcode-quote-wrapper").decompose()
  return post

def get_user_posts(user_id,agents,sess):
  #counter_1 = 0
  #counter_2 = 0
  user_posts = []
  headers = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.90 Safari/537.36'}
  page_nr = 1
  while True:
    user_url = 'https://www.flashback.org/find_posts_by_user.php?userid='+user_id+'&page='+str(page_nr)
    page_source = sess.get(user_url,headers=headers)
    #counter_1+=1
    #counter_2+=1
    #if counter_1>=38:
    #  counter_1 = 0
    #  time.sleep(60)
    #if counter_2>=114:
    #  counter_2 = 0
    #  time.sleep(180)
    soup = BeautifulSoup(page_source.content,'html.parser')
    post_links = soup.find_all(href=localize_posts)
    if len(post_links)==0:
      break
    agent_counter = 0
    for post_link in post_links:
    #  print('counter_1:',counter_1)
    #  print('counter_2:',counter_2)
      post_url = 'https://www.flashback.org/'+post_link['href']
      #time.sleep(5)
      if agents == False:
        time.sleep(5)
        post_page = sess.get(post_url,headers=headers)
      else:
        try:
          post_page = requests.get(post_url,proxies={"http": agents[agent_counter]['proxy'], "https": agents[agent_counter]['proxy']},headers=agents[agent_counter]['headers'])
        except:
          time.sleep(5)
          post_page = sess.get(post_url,headers=headers)
      #counter_1+=1
      #counter_2+=1
      #if counter_1>=38:
      #  counter_1=0
      #  time.sleep(60)
      #if counter_2>=114:
      #  counter_2 = 0
      #  time.sleep(180)
      post_soup = BeautifulSoup(post_page.content,'html.parser')
      post_id = post_link['href'][post_link['href'].find('#')+2:]
      post_tag = post_soup.find(id="post_message_"+post_id)
      try:
        cleaned_post_tag = remove_citations(post_tag)
        post = remove_citations(cleaned_post_tag).text
      except:
        time.sleep(30)
        post_page = sess.get(post_url,headers=headers)
        post_soup = BeautifulSoup(post_page.content,'html.parser')
        post_id = post_link['href'][post_link['href'].find('#')+2:]
        post_tag = post_soup.find(id="post_message_"+post_id)
        try:
          post = remove_citations(cleaned_post_tag).text
        except:
          print('Could not retrieve all posts. Got you some, though!')
          return user_posts
      user_post = post.replace('\r',' ').replace('\n',' ').strip()
      print(user_post)
      user_posts.append(user_post)
      if agents is not False:
        agent_counter += 1 % len(agents)
    page_nr +=1
    time.sleep(5)
  print(len(user_posts), ' posts found for user ', user_id)
  return user_posts

def localize_next_page(href,page_nr):
  value = False
  if isinstance(href,str):
    if len(href)>1:
      value = (href[0:2]=='/t' and href[-len(str(page_nr))-1:]==('p'+str(page_nr)))
  return value

def get_posters_from_thread(url,sess):
  headers = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.90 Safari/537.36'}
  page = sess.get(url,headers=headers)
  soup = BeautifulSoup(page.content,'html5lib')
  posters = set()
  page_posters = soup.find_all(class_='post-user-username')
  print('Retrieving poster IDs from thread ...')
  for tag in page_posters:
    posters.add('https://www.flashback.org'+tag['href'])
  page_nr = 2
  while True:
    next_page_tag = soup.find(href=(lambda href: localize_next_page(href,page_nr)))
    if next_page_tag is None:
      break
    time.sleep(5)
    page = sess.get(url+'p'+str(page_nr),headers=headers)
    soup = BeautifulSoup(page.content,'html.parser')
    page_posters = soup.find_all(class_='post-user-username')
    for tag in page_posters:
      posters.add('https://www.flashback.org'+tag['href'])
    page_nr += 1
  print('... posters successfully retrieved!')
  return posters

def scrape_flashback(thread_urls,agents=False):
  with requests.Session() as sess:
    headers = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.90 Safari/537.36'}
    login_data = {'do': 'login',
    'vb_login_username': 'username',
    'vb_login_password':'password'}
    login_url = 'https://www.flashback.org/login.php'
    sess.post(login_url,data=login_data,headers=headers)
    for url in thread_urls:
      posters = get_posters_from_thread(url,sess)
      for poster in posters:
        poster_id = poster.split('/u')[1]
        if not os.path.exists(poster_id+'.csv'):
          with open(poster_id+'.csv','w',newline='\r\n', encoding="utf-8") as csv_file:
            wr = csv.writer(csv_file, quoting=csv.QUOTE_ALL,delimiter='\n')
            wr.writerow(get_user_posts(poster_id,agents,sess))

def load_threads(threads_file):
  file = open(threads_file,'r')
  threads = file.read().split('\n')
  return threads
  
def initialize_agents(ua):
  proxies = get_proxies(150)
  agents = []
  for proxy in proxies:
    agents.append({'proxy':proxy,'headers':{'user-agent':ua.random}})
  return agents

threads = load_threads('FB threads.txt')
#ua = UserAgent()
#agents = initialize_agents(ua)
scrape_flashback(threads)