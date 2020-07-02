import csv

from selenium import webdriver
from bs4 import BeautifulSoup
import pandas as pd
import requests
import re
import logging
import configparser
import time

# Basic configs:
logging.basicConfig(filename='log.log', level=logging.INFO, format='%(asctime)s %(message)s')
config = configparser.ConfigParser()
config.read('config.ini')

# Load PICOC terms
picoc = {
    'population': re.compile(config['picoc']['population']) if config['picoc']['population'] != "" else None,
    'intervention': re.compile(config['picoc']['intervention']) if config['picoc']['intervention'] != "" else None,
    'comparison': re.compile(config['picoc']['comparison']) if config['picoc']['comparison'] != "" else None,
    'outcome': re.compile(config['picoc']['outcome']) if config['picoc']['outcome'] != "" else None,
    'context': re.compile(config['picoc']['context']) if config['picoc']['context'] != "" else None
}

# Create a new Chorme session
driver = webdriver.Chrome(config['default']['chromedriver'])
url = "https://scholar.google.com/"
driver.get(url)

# Setting Google Scholar
driver.find_element_by_id("gs_hdr_mnu").click()
driver.find_element_by_class_name("gs_btnP").click()
driver.find_element_by_id("gs_num-b").click()
driver.find_element_by_css_selector('a[data-v="20"').click()
driver.find_element_by_id("gs_settings_import_some").click()
driver.find_element_by_name("save").click()


# Sometimes a Captcha shows up. It needs to be fixed manually. This function makes the code wait until this be fixed
def check_captcha():
    captcha = driver.find_elements_by_css_selector("#captcha")
    captcha += driver.find_elements_by_css_selector("#gs_captcha_f")
    captcha += driver.find_elements_by_css_selector("#g-recaptcha")
    captcha += driver.find_elements_by_css_selector("#recaptcha")
    while captcha:
        logging.info(
            "Captcha found! You need to fill it on browser to continue. Go to the terminal and type 'y' when the Captcha be solved")
        print("Captcha found! You need to fill it on browser to continue...")
        solve = input("Type 'y' when the Captcha be solved: ")
        if solve == "y":
            try:
                driver.find_element_by_id("gs_res_sb_yyc")
                logging.info("Captcha solved, continuing...")
                break
            except:
                print("Captcha not solved, try again! You need to fill it on browser to continue...")
                logging.info("Captcha not solved, try again! You need to fill it on browser to continue...")
        else:
            print("Input error. Try again")


# Filter the PICOC terms inside the Title-Abstract-Keywords
def filterTitleAbsKey(site):
    try:
        page = requests.get(site)
        text = BeautifulSoup(page.text, 'lxml').get_text()
        text = str.lower(text)
        for terms in filter(None, picoc.values()):
            if not terms.search(text):
                logging.info("%s not passed on title-abs-key filter", site)
                return False
        logging.info("%s passed on title-abs-key filter", site)
        return True
    except:
        logging.info("[ERROR] on %s and not passed on title-abs-key filter", site)
    return False


# Parser HTML
def parser(soup, page, year):
    papers = []
    html = soup.findAll('div', {'class': 'gs_r gs_or gs_scl'})
    for result in html:
        paper = {'Link': result.find('h3', {'class': "gs_rt"}).find('a')['href'], 'Additional link': '', 'Title': '',
                 'Authors': '', 'Abstract': '', 'Cited by': '', 'Cited list': '', 'Related list': '', 'Bibtex': '',
                 'Year': year, 'Google page': page}

        # If it does not pass at Title-Abstract-Keyword filter exclude this paper and continue
        if not filterTitleAbsKey(paper['Link']):
            continue

        try:
            paper["Additional link"] = result.find('div', {'class': "gs_or_ggsm"}).find('a')['href']
        except:
            paper["Additional link"] = ''

        paper['Title'] = result.find('h3', {'class': "gs_rt"}).text
        paper['Authors'] = ";".join(
            ["%s:%s" % (a.text, a['href']) for a in result.find('div', {'class': "gs_a"}).findAll('a')])

        try:
            paper['Abstract'] = result.find('div', {'class': "gs_rs"}).text
        except:
            paper['Abstract'] = ''

        for a in result.findAll('div', {'class': "gs_fl"})[-1].findAll('a'):
            if a.text != '':
                if a.text.startswith('Cited'):
                    paper['Cited by'] = a.text.rstrip().split()[-1]
                    paper['Cited list'] = url + a['href']
                if a.text.startswith('Related'):
                    paper['Related list'] = url + a['href']
                if a.text.startswith('Import'):
                    paper['Bibtex'] = requests.get(a['href']).text
                    
        papers.append(paper)
        # Wait 20 seconds until the next request to google
        time.sleep(20)

    return papers, len(html)


if __name__ == '__main__':
    query = config['search']['query']
    year = int(config['search']['start_year'])
    output = config['default']['result_path']

    logging.info("Starting...")
    logging.info("Result path: {}".format(output))
    logging.info("PICOC terms are: {}".format(picoc))
    logging.info("Search query is: {}".format(query))

    with open(output, 'a', newline='') as outcsv:
        csv.writer(outcsv).writerow(['Link', 'Additional link', 'Title', 'Authors', 'Abstract', 'Cited by',
                                     'Cited list', 'Related list', 'Bibtex', 'Year', 'Google page'])

    # String search year by year.
    while year <= int(config['search']['end_year']):
        driver.get(url + "scholar?hl=en&q={0}&as_sdt=1&as_vis=1&as_ylo={1}&as_yhi={1}".format(query, year))
        check_captcha()
        page = 1
        total = 0
        while True:
            art, t = parser(BeautifulSoup(driver.page_source, 'lxml'), page, year)
            total += t
            df = pd.DataFrame(art)
            df.to_csv(output, mode='a', header=False, index=False)
            try:
                driver.find_element_by_class_name("gs_ico_nav_next").click()
                check_captcha()
                page += 1
            except:
                logging.info(
                    "No more pages for {} year, total of {} pages and {} articles processed".format(year, page, total))
                year += 1
                # Wait 10 seconds until the next page request
                time.sleep(10)
                break

    logging.info("Ending...")
    driver.close()
