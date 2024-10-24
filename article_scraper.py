import json
import requests
from dateutil import parser
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

#pip install requests beautifulsoup4 python-dateutil selenium webdriver-manager

URLS=[
    "https://bistrolubie.pl/pierniki-z-miodem-tradycyjny-przepis-na-swiateczne-ciasteczka-pelne-aromatu",
    "https://bistrolubie.pl/piernik-z-mascarpone-kremowy-i-pyszny-przepis-na-deser-idealny-na-swieta",
    "https://spidersweb.pl/2024/07/metamorfoza-w-centrum-warszawy.html",
    "https://spidersweb.pl/2024/07/kontrolery-na-steam-rosnie-popularnosc.html",
    "https://www.chip.pl/2024/06/wtf-obalamy-mity-poprawnej-pozycji-przy-biurku",
    "https://www.chip.pl/2024/07/sony-xperia-1-vi-test-recenzja-opinia",
    "https://newonce.net/artykul/chief-keef-a-sprawa-polska-opowiadaja-benito-gicik-crank-all",
    "https://newonce.net/artykul/glosna-gra-ktorej-akcja-toczy-sie-w-warszawie-1905-roku-gralismy-w-the-thaumaturge"
]

ALLOWED_TAGS=[
    "h2",
    "h3",
    "p",
    "strong"
]

def date_parser(date):
    p_date=parser.parse(date)
    return p_date.strftime("%d.%m.%Yr.")

def search_category_position(data):
    for item in data:
        if item["position"]==2:
            return item.get("name")
        
def clean_html(content):
    soup=BeautifulSoup(content,"html.parser")

    for tag in soup.find_all(True):
        if tag.name not in ALLOWED_TAGS:
            tag.unwrap()
    return str(soup)

def scr_title(soup):
    title=soup.find("meta",attrs={"property":"og:title"})
    if title:
        return title.get("content")
    else:
        return "----"

def scr_category(soup):
    script_tags=soup.find_all("script",type="application/ld+json")
    if script_tags:
        for script_tag in script_tags:
            data=json.loads(script_tag.string)
            if "articleSection" in data:
                return data.get("articleSection")
            elif "itemListElement" in data:
                return search_category_position(data["itemListElement"])
            elif "@graph" in data:
                for item in data["@graph"]:
                    if "articleSection" in item:
                        return item.get("articleSection").split(",")[0]
    else:
        return "----"
    
def scr_date_pub(soup):
    script_tags=soup.find_all("script", type="application/ld+json")
    if script_tags:
        for script_tag in script_tags:
            data=json.loads(script_tag.string)
            if "datePublished" in data:
                return date_parser(data.get("datePublished"))
            elif "@graph" in data:
                for item in data["@graph"]:
                    if "datePublished" in item:
                        return date_parser(item.get("datePublished"))
    else:
        return "----"

def scr_arc_content(soup):
    article_tag=soup.find("article")

    if article_tag:
        content_arc=article_tag.find("section",class_=lambda class_name:class_name and "content" in class_name.lower()) or \
                    article_tag.find("div",class_=lambda class_name:class_name and "content" in class_name.lower()) or \
                    article_tag.find("div",class_=lambda class_name:class_name and "post" in class_name.lower()) or \
                    soup.find("div",class_="content")
    
    if content_arc:
        return clean_html(str(content_arc))
    else:
        return clean_html(str(article_tag))
    
def article_data(soup):
    title=scr_title(soup)
    category=scr_category(soup)
    date_pub=scr_date_pub(soup)
    arc_content=scr_arc_content(soup)

    return {
        "Tytuł": title,
        "Kategoria": category,
        "Data publikacji": date_pub,
        "Treść": arc_content
    }

def save_to_json(data):
    with open("response.json","w",encoding="utf-8") as file:
        json.dump(data,file,ensure_ascii=False,indent=4)

def get_p_code(url,driver):
    try:
        response=requests.get(url,timeout=15)
        if response.status_code==200:
            print(f"Scraping... {url}")
            return response.text
        else:
            raise Exception
    except Exception:
        print(f"Scraping przez selenium, błedny status code {url}")
        driver.implicitly_wait(10)
        driver.get(url)
        page_s=driver.page_source
        if page_s:
            return page_s
        else:
            return None        

def article_scraper():
    options=Options()
    options.add_argument("--headless")

    driver=webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    articles=[]

    for url in URLS:
        page_code=get_p_code(url,driver)  
        if page_code:      
            soup=BeautifulSoup(page_code,"html.parser")

            article_d=article_data(soup)
            articles.append(article_d)
            print("Zakończone")
        else:
            print("Błąd pobierania strony")
        

    save_to_json(articles)
    print(f"Pobrano {len(articles)} artykułów")

    driver.quit()

article_scraper()