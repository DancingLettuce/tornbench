"""This filename is tb_lib_selenium.py."""
# stand-alone script to get bazaar data using selenium and firefox headless


import json
import os 
import requests 
  

# pip install selenium
# python -c "import selenium; print(selenium.__version__)" 
# parser.add_argument("--geckopath", type=str,help="where is geckdriver.  instance=gcp /usr/local/bin/geckodriver")

from selenium import webdriver
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.common.by import By # Not strictly needed for plain JSON, but good to import
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import WebDriverException, TimeoutException

REMOTE_ROBOT_URL = None
BAZAAR_API_URL = None
REMOTE_ROBOT_CLIENT_ID = None

def setup_selenium(args=None ):
    ## set up selenium
    os.environ['DISPLAY'] = ':0'
    driver = None # Initialize driver to None
    # --- Set up WebDriver in Headless Mode ---
    if args and args.geckopath:
        if args.geckopath == 'instance':
            GECKODRIVER_PATH='/usr/local/bin/geckodriver'
        else:
            geckopath == args.geckopath
    else:
        GECKODRIVER_PATH = '/opt/geckodriver/geckodriver'  
    SERVICE_TIMEOUT = 100
    # Set a page load timeout for subsequent navigation
    PAGE_LOAD_TIMEOUT = 60
    service = FirefoxService(
        executable_path=GECKODRIVER_PATH,
        timeout=SERVICE_TIMEOUT )
    options = webdriver.FirefoxOptions()
    options.add_argument('--headless')
    options.set_preference('devtools.jsonview.enabled', False)
    options.set_preference('permissions.default.image', 2) # 2 = Block images
    options.set_preference('dom.css.enabled', False)
    options.set_preference('dom.webnotifications.enabled', False)
    options.set_preference("network.manage-offline-status", False)
    options.set_preference("network.dns.disablePrefetch", True)
    options.set_preference("browser.safebrowsing.enabled", False)
    options.set_preference("browser.safebrowsing.malware.enabled", False)
    options.set_preference("browser.startup.page", 0) # Start with a blank page
    options.set_preference("network.captive-portal-service.enabled", False)
    options.set_preference("browser.startup.homepage_override.mstone", "ignore")
    options.set_preference("browser.startup.homepage", "about:blank")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument('--disable-gpu')
    #######options.add_argument('--no-sandbox')
    options.add_argument('--disable-setuid-sandbox') # Good for root/container environments
    options.add_argument('--shm-size=2g')             # Ensure sufficient shared memory
    options.add_argument('--disable-extensions')
    options.add_argument("--width=800") # 800 You can make this even smaller if no UI interaction needed
    options.add_argument("--height=600") # 600 or just 1x1 if truly just getting source
    options.add_argument(f"user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:127.0) Gecko/20100101 Firefox/127.0")
    # Toggles garbage collection more often
    options.set_preference("javascript.options.gc_decommit_timouts", 1)
    # Reduces the number of content processes (high memory saver)
    options.set_preference("dom.ipc.processCount", 1)
    # Reduces the maximum cache size
    options.set_preference("browser.cache.disk.capacity", 0)
    print("Initialising Selenium Driver")
    driver = webdriver.Firefox(service=service, options=options)
    print(f"WebDriver initialized successfully (headless).")
    driver.set_page_load_timeout(PAGE_LOAD_TIMEOUT)
    return driver

def get_data(url=None, action=None, client_id=None, state=None, description=None, command=None):
    #REMOTE_ROBOT_URL/remotecontrol/?action=set&client_id=***&state=idle&description=initial
    if action:
        url += f'&action={action}'
    if client_id:
        url += f'&client_id={client_id}'
    if state:
        url += f'&state={state}'
    if description:
        url += f'&description={description}'
    if command:
        url += f'&command={command}'
    #print(f"Fetching remote control data from URL: {url}" )
    return requests.get(url)

def get_bazaardata(bazaar_api_url:str=None, item_id:int=None, driver=None):
    # https://xxx/1086
    url = bazaar_api_url
    url = url + str(item_id)
    try:
        # Navigate to the URL
        print(f"Fetching URL: {url}")
        driver.get(url)
        wait = WebDriverWait(driver, 20) # Wait up to 20 seconds for the element
        wait.until(EC.presence_of_element_located((By.TAG_NAME, 'pre')))
        #print("Found <pre> tag. Attempting to extract text...")
        #print(driver.page_source[:200])
        # Get the page source (or specific element's text)
        # If the entire page is just the JSON, get the body's text
        json_text = driver.find_element(By.TAG_NAME, 'pre').text

        # Attempt to parse the JSON
        try:
            parsed_json = json.loads(json_text)
            #results_list.append(parsed_json)
            #print(f"Successfully extracted and parsed JSON for {url}.")
            return parsed_json
        except json.JSONDecodeError:
            print(f"Warning: Could not parse JSON for {url}. Raw text: {json_text[:200]}...")
            #results_list.append(f"JSON Parse Error for {url}: {json_text[:500]}...") # Store raw text or error
        except Exception as e:
            print(f"Error processing text for {url}: {e}. Raw text: {json_text[:200]}...")
            #results_list.append(f"Processing Error for {url}: {e} (Raw text: {json_text[:500]}...)")

    except TimeoutException:
        print(f"Timeout waiting for page/element for {url}.")
        #results_list.append(f"Timeout Error for {url}")
    except WebDriverException as e:
        print(f"WebDriver error for {url}: {e}")
        #results_list.append(f"WebDriver Error for {url}: {e}")
    except Exception as e:
        print(f"An unexpected error occurred for {url}: {e}")
        #results_list.append(f"Unexpected Error for {url}: {e}")    

    return None

    if response.status_code in (500,429):
        print(f"The 1 response for item {item_id } was {response} code was {response.status_code} so sleeping 30s and retrying")
        time.sleep(30)
        response = requests.get(apiendpoint)
    if response.status_code  in (500,429) :
        print(f"The 2 response was {response} code was {response.status_code} so sleeping 40s and retrying")
        time.sleep(40)
        response = requests.get(apiendpoint)
    try:
        bizlist = response.json()
    except Exception as e:
        print(f"Error {response} calling api {apiendpoint} {e} for item {item_id}")
        return None
    #bizlist = bizlist.get('listings', None)
    if bizlist is None:
        print(f"Data issue listings is None {bizlist}")
    return bizlist

def getremotecontrolstate(client_id=None):
    #    http://***/remotecontrol/?action=get&client_id=***
    return get_data(url=f'{REMOTE_ROBOT_URL}remotecontrol/?',
        action='get', client_id=client_id)
 

def getbazaar(bazaar_api_url=None):
    print("Setting up Selenium WebDriver...")
    driver = setup_selenium(args=None)   
    data=get_bazaardata(bazaar_api_url=bazaar_api_url, item_id=1086, driver=driver)
    print(f"Data for item 1086: {data}") 
