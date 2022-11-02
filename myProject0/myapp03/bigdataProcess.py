from collections import Counter
import re
from bs4 import BeautifulSoup
import requests
from matplotlib import font_manager, rc
import matplotlib.pyplot as plt
import os
from pandas import DataFrame
import folium
from wordcloud import WordCloud
from konlpy.tag import Okt
from myProject03.settings import STATIC_DIR, TEMPLATE_DIR

# 멜론 차트
def melon_crawling(datas):

   header = {'User-Agent': 'Mozilla/5.0'}
   req = requests.get('https://www.melon.com/chart/index.htm', headers=header)
   soup = BeautifulSoup(req.content, 'html.parser')
   
   tbody = soup.select_one('#frm > div > table > tbody')
   
   for i in tbody.select('tr')[:50]:
      tds = i.select('td')
      rank = tds[1].get_text()
      title = tds[5].select_one('span > a').get_text()
      singer = tds[5].select_one('div.ellipsis.rank02 > a').get_text()
      album = tds[6].select_one('div.ellipsis.rank03 > a').get_text()

      tmp = {}
      tmp['rank'] = rank
      tmp['title'] = title
      tmp['singer'] = singer
      tmp['album'] = album

      datas.append(tmp)

# 날씨
def weather_crawling(last_date, weather):
   res = requests.get('https://www.weather.go.kr/weather/forecast/mid-term-rss3.jsp?stnld=108')
   soup = BeautifulSoup(res.content, 'lxml')
   
   for i in soup.find_all('location'):
      weather[i.find('city').text] = []
      for j in i.find_all('data'):
         temp = []
         if(len(last_date)==0) or (j.find('tmef').text > last_date[0]['tmef']):
            temp.append(j.find('tmef').text)
            temp.append(j.find('wf').text)
            temp.append(j.find('tmn').text)
            temp.append(j.find('tmx').text)
            weather[i.find('city').string].append(temp)
   print(weather['부산'])

# 날씨 그래프
def weather_make_chart(result, wfs, dcounts):
   font_location = 'c:/Windows/fonts/malgun.ttf'
   font_name = font_manager.FontProperties(fname=font_location).get_name()
   rc('font', family=font_name)

   high = []
   low = []
   xdata = []

   for row in result.values_list():
      high.append(row[5])
      low.append(row[4])
      xdata.append(row[2].split('-')[2])
   
   plt.figure(figsize=(10, 6))
   plt.plot(xdata, low, label='최저기온')
   plt.plot(xdata, high, label='최고기온')
   plt.legend()
   plt.savefig(os.path.join(STATIC_DIR, 'images\\weather_busan.png'), dpi=300)
   
   plt.cla()
   plt.bar(wfs, dcounts)
   plt.savefig(os.path.join(STATIC_DIR, 'images\\weather_busan_bar.png'), dpi=300)
   
   plt.cla()
   plt.pie(dcounts, labels=wfs, autopct='%.1f%%')
   plt.savefig(os.path.join(STATIC_DIR, 'images\\weather_busan_pie.png'), dpi=300)
   
   image_dic = {
      'plot' : 'weather_busan.png',
      'bar' : 'weather_busan_bar.png',
      'pie' : 'weather_busan_pie.png'
   }
   return image_dic

# 지도
def map():
   ex = {'경도' : [127.061026,127.047883,127.899220,128.980455,127.104071,127.102490,127.088387,126.809957,127.010861,126.836078
                ,127.014217,126.886859,127.031702,126.880898,127.028726,126.897710,126.910288,127.043189,127.071184,127.076812
                ,127.045022,126.982419,126.840285,127.115873,126.885320,127.078464,127.057100,127.020945,129.068324,129.059574
                ,126.927655,127.034302,129.106330,126.980242,126.945099,129.034599,127.054649,127.019556,127.053198,127.031005
                ,127.058560,127.078519,127.056141,129.034605,126.888485,129.070117,127.057746,126.929288,127.054163,129.060972],
     '위도' : [37.493922,37.505675,37.471711,35.159774,37.500249,37.515149,37.549245,37.562013,37.552153,37.538927,37.492388
              ,37.480390,37.588485,37.504067,37.608392,37.503693,37.579029,37.580073,37.552103,37.545461,37.580196,37.562274
              ,37.535419,37.527477,37.526139,37.648247,37.512939,37.517574,35.202902,35.144776,37.499229,35.150069,35.141176
              ,37.479403,37.512569,35.123196,37.546718,37.553668,37.488742,37.493653,37.498462,37.556602,37.544180,35.111532
              ,37.508058,35.085777,37.546103,37.483899,37.489299,35.143421],
     '구분' : ['음식','음식','음식','음식','생활서비스','음식','음식','음식','음식','음식','음식','음식','음식','음식','음식'
             ,'음식','음식','소매','음식','음식','음식','음식','소매','음식','소매','음식','음식','음식','음식','음식','음식'
             ,'음식','음식','음식','음식','소매','음식','음식','의료','음식','음식','음식','소매','음식','음식','음식','음식'
             ,'음식','음식','음식']}
      
   ex = DataFrame(ex)
   
   lat = ex['위도'].mean()
   long = ex['경도'].mean()

   m = folium.Map([lat, long], zoom_start=9)

   for i in ex.index:
    sub_lat = ex.loc[i, '위도']
    sub_long = ex.loc[i, '경도']
    title = ex.loc[i, '구분']
    # 지도에 데이터 찍어서 보여주기
    folium.Marker([sub_lat, sub_long], tooltip=title).add_to(m)
    m.save(os.path.join(TEMPLATE_DIR, 'bigdata/map.html'))

# 워드클라우드    
def make_wordCloud(data):
   font_path = "c:/Windows/fonts/malgun.ttf"
   
   message = ''
   for item in data:
      if 'message' in item.keys():
         message = message + re.sub(r'[^\w]', ' ', item['message'])+''
   
   nlp = Okt()
   message_N = nlp.nouns(message)
   count = Counter(message_N)
   word_count = {}

   for tag, counts in count.most_common(80):
      if(len(str(tag)) > 1):
         word_count[tag] = counts
      
   wc = WordCloud(font_path, background_color='ivory', width=800, height=600)
   cloud = wc.generate_from_frequencies(word_count)
   plt.figure(figsize=(8, 8))
   plt.imshow(cloud)
   plt.axis('off')
   cloud.to_file('./static/images/k_wordCloud.png')

def movie_crawling(data):
   for i in range(10):
      base_url ='https://movie.naver.com/movie/point/af/list.nhn?&page='
      url =base_url+str(i+1)
      req= requests.get(url)
      
      if req.ok:
        html =req.text

        soup =BeautifulSoup(html,'html.parser')
        titles =soup.select('td.title > a.movie')
        points =soup.select('td.title em')
        contents =soup.select('td.title')
        
        for i in range(len(titles)):
          title = titles[i].get_text()
          point = points[i].get_text()
          content_arr = contents[i].get_text().replace('신고', '').split("\n\n")
          content = content_arr[2].replace("\t", '').replace("\n", '')
          
          data.append([title, point, content])
         
def crawling():
   res = requests.get('https://movie.daum.net/ranking/reservation')
   soup = BeautifulSoup(res.content, 'html.parser')

   ols = soup.find('ol', class_="list_movieranking")
   rankcont = ols.find_all('div', class_='thumb_cont')

   ratio = []
   labels = []
   explode = []

   for i in rankcont[:10]:
      title = i.find('a', class_='link_txt').get_text()
      reser = float(re.sub(r'[%^]', '', i.find('span', {'class':'txt_num'}).get_text()))

      labels.append(title)  
      ratio.append(reser)
      explode.append(0.03)
    
   font_location = 'c:/Windows/fonts/malgun.ttf'
   font_name = font_manager.FontProperties(fname=font_location).get_name()
   rc('font', family=font_name, size=6)
   
   plt.cla()
   plt.pie(ratio, labels=labels, explode=explode, autopct='%.1f%%')
   plt.savefig(os.path.join(STATIC_DIR, 'images\\graph.png'), dpi=800)