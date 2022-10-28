from bs4 import BeautifulSoup
import requests
from matplotlib import font_manager, rc
import matplotlib.pyplot as plt
import os
from myProject03.settings import STATIC_DIR



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


   
    
    