import os
import json
import time
import pickle
from database import DataBase
from urllib.parse import urlparse
from colorama import Fore
from seleniumwire import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains

login_url = "https://freelancer.com/login"
project_url = "https://www.freelancer.com/search/projects?projectUpgrades=NDA"

page = 1
projects = []
gecko_path = ""
script_path = os.path.dirname(os.path.realpath(__file__))
config_path = os.path.join(script_path, 'config.json')
cookies_path = os.path.join(script_path, 'cookies.pkl')
config = {}

def read_config():
    global config
    print("Config:")
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
            for k, v in config.items():
                if v == '':
                    if k == 'username' or k == 'password':
                        raise Exception('Invalid username or password')
                    print(Fore.RED + k + ": Null" + Fore.RESET)
                else:
                    print(f"{k}: {v}")
    except Exception as e:
        print(Fore.RED + "Failed to read config file: " + str(e) + Fore.RESET)
    print()

def save_cookies():
    pickle.dump(driver.get_cookies(), open(cookies_path,"wb"))

def load_cookies():
    cookies = pickle.load(open(cookies_path, "rb"))
    for cookie in cookies:
        driver.add_cookie(cookie)

def login():
    try:
        print("Loading login page")
        driver.get(login_url)

        try:
            cookie_failed = False
            print("Opening login cookies")
            load_cookies()
            driver.get(login_url)
            while True:
                try:
                    if urlparse(driver.current_url).path == '/':
                        raise Exception()
                    if urlparse(driver.current_url).path == urlparse(login_url).path:
                        cookie_failed = True
                    break
                except Exception as e:
                    time.sleep(0.2)
            if cookie_failed:
                raise Exception("Invalid cookies")

        except Exception as e:
            print(Fore.RED + "Failed to use cookies, using login credentials..." + Fore.RESET)

            driver.execute_script(f"document.querySelector('input[type=\"email\"]').value = '{config['username']}'")
            driver.execute_script(f"document.querySelector('input[type=\"password\"]').value = '{config['password']}'")
            driver.execute_script(f"document.querySelector('fl-checkbox[fltrackinglabel=\"CredentialsForm-RememberMe\"] input').checked = true")
            driver.execute_script(f"document.querySelector('button[type=\"submit\"]').click()")
            print("Login submitted, Waiting for verification...")

            while True:
                try:
                    if urlparse(driver.current_url).path != urlparse(login_url).path:
                        save_cookies()
                        break
                except:
                    time.sleep(0.2)
        print(Fore.GREEN + "Login completed successfully" + Fore.RESET)
    except Exception as e:
        print(Fore.RED + "Failed to login: " + str(e) + Fore.RESET)
    print()

def do_nda_contract():
    try:
        NDALink = driver.execute_script("return document.querySelector('fl-link[fltrackinglabel=\"NDALink\"] a').href")
        driver.get(NDALink)

        fullname = config.get('fullname')
        phone = config.get('phone')
        address = config.get('address')
        state = config.get('state')
        city = config.get('city')
        country = config.get('country')

        if fullname:
            driver.execute_script(f'document.getElementById(\'fullname\').value = "{fullname}"')

        if phone:
            driver.execute_script(f'document.getElementById(\'phone\').value = "{phone}"')
            
        if address:
            driver.execute_script(f'document.getElementById(\'address\').value = "{address}"')

        if state:
            driver.execute_script(f'document.getElementById(\'tbx_state\').value = "{state}"')
        
        if city:
            driver.execute_script(f'document.getElementById(\'tbx_city\').value = "{city}"')
        
        if country:
            driver.execute_script(f'document.getElementById(\'sel_country\').value = "{country}"')

        driver.execute_script('document.getElementById(\'chkbx_agree_term\').checked = true')

        driver.execute_script('document.querySelector(\'.btn_sign_contract\').click()')

        time.sleep(1)
        is_error = driver.find_elements(by=By.CSS_SELECTOR, value='#ns_sidebar .ns_error p')
        if is_error:
            print(Fore.RED + "Failed to agree NDA contract: " + is_error[0].text + Fore.RESET)
        else:
            print("NDA Contract agreed")
    except Exception as e:
        print(Fore.RED + "Failed to agree NDA contract: " + str(e) + Fore.RESET)

def do_ip_agreement():
    try:
        driver.execute_script("document.querySelector('fl-link[fltrackinglabel=\"IPAgreementLink\"] button').click()")
        driver.switch_to.window(driver.window_handles[-1])
        
        while True:
            try:
                driver.execute_script("document.querySelector('.InlineSignature').click()")
                break
            except:
                time.sleep(0.2)

        sig = driver.find_element(by=By.CSS_SELECTOR, value='#signature')

        ActionChains(driver).move_to_element(sig).click(sig).perform()

        driver.execute_script('document.querySelector(".Modal-footer-btn.Button").click()')

        body = driver.find_elements(by=By.CSS_SELECTOR, value=".ContractView-steps-btn")[1]

        ActionChains(driver).move_to_element(body).click(body).perform()
        ActionChains(driver).move_to_element(body).click(body).perform()

        driver.execute_script('document.querySelector(".ContractView-control-submit").click()')

        while "Project Details" not in driver.page_source:
            time.sleep(0.2)

        driver.close()
        driver.switch_to.window(driver.window_handles[0])
        print("IP Agreement signed")
    except Exception as e:
        print(Fore.RED + "Failed to sign IP Agreement: " + str(e) + Fore.RESET)

def get_projects():
    global projects, page
    is_empty = False
    delay = config['delay']

    while True:
        try:
            print("Opening page: " + str(page))
            driver.get(f"{project_url}&page={page}")

            # Wait for loading finish
            while True:
                item_a = driver.find_elements(by=By.CSS_SELECTOR, value='fl-list-item a')
                no_p = driver.find_elements(by=By.CSS_SELECTOR, value='.EmptyViewContainer')

                if item_a:
                    break
                if no_p:
                    is_empty = True
                    break
                time.sleep(0.2)

            if is_empty:
                print("Reached the last page")
                break

            projects_elem = WebDriverWait(driver, 20).until(
                EC.visibility_of_all_elements_located((By.CSS_SELECTOR, "fl-list-item"))
            )
            projects = []
            for project in projects_elem:
                url = project.find_element(by=By.CSS_SELECTOR, value='a').get_attribute("href")
                name = project.find_element(by=By.CSS_SELECTOR, value='.Project-title').text
                projects.append({ 'name': name, 'url': url })

            for project in projects:
                try:
                    url = project['url']
                    name = project['name']
                    
                    if DataBase.Status(url):
                        print(f"Skipping {name}\n")
                        continue

                    try:
                        driver.get(url)

                        while True:
                            is_nda = driver.find_elements(by=By.CSS_SELECTOR, value='fl-link[fltrackinglabel="NDALink"]')
                            is_nda_done = driver.find_elements(by=By.CSS_SELECTOR, value='.BidFormHeaderTitle fl-bit')
                            is_detail = driver.find_elements(by=By.CSS_SELECTOR, value='app-project-details-freelancer fl-banner-alert')
                            if is_nda_done:
                                is_nda_done = is_nda_done[0].text
                            if is_nda or is_nda_done or is_detail:
                                break
                            time.sleep(0.2)
                        
                        time.sleep(5)
                        has_nda = driver.find_elements(by=By.CSS_SELECTOR, value='fl-banner-alert[bannertitle="This Project requires an NDA"]')
                        has_ip_agreement = driver.find_elements(by=By.CSS_SELECTOR, value='fl-banner-alert[bannertitle="This Project requires an IP Agreement"]')
                        
                        if has_nda or is_nda:
                            do_nda_contract()
                            driver.get(url)
                        else:
                            print(Fore.YELLOW + "NDA has already agreed" + Fore.RESET)

                        if has_ip_agreement:
                            time.sleep(5)
                            do_ip_agreement()
                        else:
                            print(Fore.YELLOW + "Doesn't have an IP Agreement or Has been Signed" + Fore.RESET)

                        DataBase.GoToDB(url)
                        print(name + ': ' + Fore.GREEN + "Success" + Fore.RESET)
                    except Exception as e:
                        print(name + Fore.RED + ": " + str(e) + Fore.RESET)
                except Exception as e:
                    print(Fore.RED + str(e) + Fore.RESET)

                if delay:
                    print("Waiting for " + str(delay) + " seconds")
                    time.sleep(config['delay'])
                print()

            page += 1
            if delay:
                print("Waiting for " + str(delay) + " seconds")
                time.sleep(config['delay'])
        except Exception as e:
            print(Fore.RED + str(e) + Fore.RESET)

if __name__ == '__main__':
    read_config()
    options = {}

    if config['proxy']['ip'] != "":
        p_username = config['proxy']['username']
        p_password = config['proxy']['password']
        p_host = config['proxy']['ip']
        p_port = config['proxy']['port']
        proxy_url = f'{p_username}:{p_password}@{p_host}:{p_port}'
        options = {
            'proxy': {
                'http': 'http://' + proxy_url, 
                'https': 'https://' + proxy_url,
                'no_proxy': 'localhost,127.0.0.1'
            }
        }

    if not config['chrome']:
        if gecko_path:
            driver = webdriver.Firefox(executable_path=gecko_path, seleniumwire_options=options)
        else:
            driver = webdriver.Firefox(seleniumwire_options=options)
    else:
        driver = webdriver.Chrome(seleniumwire_options=options)

    login()

    get_projects()