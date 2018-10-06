from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import StaleElementReferenceException
import time
import os
import configparser

from googleapiclient.discovery import build
from httplib2 import Http
from oauth2client import file, client, tools

import requests

import datetime as dt


# If modifying these scopes, delete the file token.json.
SCOPES = 'https://www.googleapis.com/auth/spreadsheets'

# The ID and range of a sample spreadsheet.
config = configparser.ConfigParser()
config.read('./config/config.ini')

credentials = config['googlesheet']['credentials']
spreadsheet_id = config['googlesheet']['spreadsheet_id']
range_name = config['googlesheet']['range_name']

user = config['mw']['user']
pwd = config['mw']['pwd']
login_page = config['mw']['login_page']
rama2 = config['mw']['rama2']

url = 'https://notify-api.line.me/api/notify'
token = config['line']['token']
headers = {'content-type':'application/x-www-form-urlencoded','Authorization':'Bearer '+token}


def line_notify_h1(current_bid_val):
    msg = current_bid_val
    r = requests.post(url, headers=headers , data = {'message':msg})
    print(r.text)


def line_notify_volatility(current_bid_val):
    msg = 'ดิ้นดุ๊กดิ๊ก ' + current_bid_val
    r = requests.post(url, headers=headers , data = {'message':msg})
    print(r.text)

def line_notify_diffchkpoint(current_bid_val):
    msg =  'โวมาจ้า ' + current_bid_val
    r = requests.post(url, headers=headers , data = {'message':msg})
    print(r.text)

def googledrive_write(current_bid_val):
    """Shows basic usage of the Sheets API.
    Prints values from a sample spreadsheet.
    """
    store = file.Storage('token.json')
    creds = store.get()
    if not creds or creds.invalid:
        flow = client.flow_from_clientsecrets(credentials, SCOPES)
        creds = tools.run_flow(flow, store)
    service = build('sheets', 'v4', http=creds.authorize(Http()))

    values = [[current_bid_val]]
    body = {
        'values':values
    }

    result = service.spreadsheets().values().update(
        spreadsheetId=spreadsheet_id, range=range_name,
        valueInputOption='USER_ENTERED',body=body).execute()


if __name__ == '__main__':

    current_bid_value = 0

    bv1, bv2, bv3, bv4, bv5 = 0, 0, 0, 0, 0

    current_time = 25

    diffchkpoint = 0.0
    diff = 40.0

    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--window-size=1920x1080")

    if os.name == 'nt':
        chrome_driver = './config/chromedriver.exe'
    else:
        chrome_driver = './config/chromedriver'
        
    browser = webdriver.Chrome(options=chrome_options, executable_path=chrome_driver)
    browser.get(login_page)

    elem = browser.find_element_by_id("login-form-login")
    elem.send_keys(user)
    elem = browser.find_element_by_id("login-form-password")
    elem.send_keys(pwd)
    elem.send_keys(Keys.RETURN)

    wait = WebDriverWait( browser, 10 )

    try:
        page_loaded = wait.until_not(
            lambda browser: browser.current_url == login_page
        )
    except TimeoutException:
        print("Loading timeout expired")
        print("*                         *")
        print("*                         *")
        print("---------------------------")

    browser.get(rama2)
    time.sleep(5)

    while True:
        try:
            bid_table = browser.find_elements_by_xpath('//*[@id="current_price"]/tbody/tr[20]/td')
            bid_value = bid_table[1].get_attribute("innerHTML")
            #bid_value = bid_table[1].get_attribute("innerHTML").encode("UTF-8")
            print(bid_value)
        except StaleElementReferenceException:
            pass

        if(bid_value != current_bid_value):
            googledrive_write(bid_value)
            current_bid_value = bid_value

        #print("current bid value = "+current_bid_value+"\n")
        #print("bid value = "+bid_value)

        """ begin diffchkpoint """
        bid_value_float = bid_value
        bid_value_float = float(bid_value_float.replace(",",""))
        if(abs(float(bid_value_float)-diffchkpoint)>=diff):
            diffchkpoint = bid_value_float
            line_notify_diffchkpoint(current_bid_value)
        """ end diffchkpoint """

        """ begin check volatility """
        bv4 = bv3
        bv3 = bv2
        bv2 = bv1
        bv1 = bid_value

        if( (bv1 != bv2) and (bv2 != bv3) and (bv3 != bv4) ):
            line_notify_volatility(current_bid_value)
        """ end check volatility """

        """ begin Hr announce """
        now = dt.datetime.now().hour
        if(now != current_time):
            current_time = now
            line_notify_h1(current_bid_value)
        """ end Hr announce """

        time.sleep(1)
