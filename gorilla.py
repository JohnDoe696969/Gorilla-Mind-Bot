import time

from chromedriver_py import binary_path  # this will get you the path variable
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.expected_conditions import presence_of_element_located
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support import expected_conditions as EC


from utils.logger import log
from utils.selenium_utils import options

from products import GORILLA_PRODUCTS

LOGIN_URL = "https://gorillamind.com/account/login"
DUMMY_ADD_TO_CART = "https://gorillamind.com/cart/39523791667245:1"
DETAILS_PATH = "details.json"
ID = '?variant='
SKIP_SHIPPING = "?previous_step=shipping_method&step=payment_method"

detail_ids = ['first_name', 'last_name', 'address1', 'address2', 'city', 'country',
    'zip', 'phone', 'province'];

card_ids = ['number', 'name', 'expiry', 'verification_value']

selectors = {
    "product_title": "//*[@class='product_name title']",
    "hidden_price": "//*[@class='current_price hidden']",
    "page_not_found": "//*[@class='page-not-found__title title']",
    "add_to_cart": "//button[@data-label='Add to cart']",
    "sold_out": "//*[@class='sold_out']",
    "checkout_details": "checkout_shipping_address",
    "apply_discount": "//button[@class='field__input-btn btn']",
    "cart_price": "//*[@class='order-summary__emphasis total-recap__final-price skeleton-while-loading']",
    "payment_iframe": "//iframe[@class='card-fields-iframe']",
    "pay_button": "//button[@id='continue_button']"  
}

def get_details_id(name):
    return f'{selectors["checkout_details"]}_{name}'

class Gorilla_Mind:
    def __init__(self, item, quantity, interval, config):
        self.driver = webdriver.Chrome(executable_path=binary_path, options=options)
        self.wait = WebDriverWait(self.driver, 10)
        self.short_wait = WebDriverWait(self.driver, 1)
        self.item_url = GORILLA_PRODUCTS[item]
        self.quantity = quantity
        self.interval = interval
        self.config = config
        self.should_login = self.config["email"] != "" and self.config["password"] != ""
        self.driver.get("https://gorillamind.com/collections/supplements")
        self.driver.maximize_window()
        #time.sleep(3)
        if(self.should_login):
            time.sleep(5)
            self.populate_cookies()

        self.run_item(self.should_login)
        time.sleep(300)

    def login(self, redirect=False):
        if(not redirect):
            self.driver.get(LOGIN_URL)

        log.info("Attempting login")
        self.driver.find_element_by_id('customer_email').send_keys(
        self.config['email']
        ) 
        self.driver.find_element_by_id('customer_password').send_keys(
        self.config['password'] + Keys.RETURN
        ) 
    
    def populate_cookies(self):
        self.driver.get(DUMMY_ADD_TO_CART)
        self.driver.find_element_by_partial_link_text('Log in').click()
        self.login(redirect=True)
        if(self.config["province"] != ""):
            discount_input = self.wait.until(presence_of_element_located((By.ID, get_details_id("province"))))
            discount_input.send_keys(
                self.config["province"] + Keys.RETURN
            )
        if(self.config["discount"]):
            self.apply_discount()
            time.sleep(3)
        
        self.driver.find_element_by_id('continue_button').click() 
        time.sleep(2)
        while True:
            try:
                element = self.wait.until(EC.element_to_be_clickable((By.ID, 'continue_button')))
                element.click()
                log.info('Clicking continue on shipping page')
                break;
            except TimeoutException:
                log.info('Error locating continue button')
            
        try:
            self.wait.until(EC.element_to_be_clickable((By.XPATH, selectors["pay_button"])))
            log.info("Successfully saved cookies for expedited checkout process")
        except TimeoutException:
            log.info("Error saving cookies for expedited checkout")
  
    def check_stock(self):
        self.driver.get(self.item_url)
        while True:
            log.info(f"Loading page: {self.item_url}")
            source = str(self.driver.page_source.encode("utf-8"))
            if(source.find('"available":true') != -1):
                log.info("Item in stock!")
                item_id = source.partition(ID)[2][:100].split('"')[0]
                log.info("Item id: " + str(item_id))
                return item_id
            elif(source.find('"available":false') != 1):
                log.info("Item not stock!")
                time.sleep(self.interval)
            else:
                log.info("Couldn't check the stock")
                time.sleep(self.interval)
            self.driver.refresh()

    def apply_discount(self):
        discount_input = ""      
        try:
            log.info('Applying discount code: ' + str(self.config['discount']))
            discount_input = self.driver.find_element_by_id('checkout_reduction_code')
            discount_input.send_keys(
                self.config['discount']
            )
            self.driver.find_element_by_xpath(selectors["apply_discount"]).click()
        except NoSuchElementException:
            log.info('error adding discount code')        

    def pay(self):

        total_price = self.wait.until(presence_of_element_located((By.XPATH,selectors["cart_price"]))).text
        log.info("Total order price: " + str(total_price))
        log.info('Inputting payment details')
        payment_iframes = self.driver.find_elements_by_xpath(selectors["payment_iframe"])
        self.driver.switch_to.frame(payment_iframes[0])
        self.wait.until(presence_of_element_located((By.ID, 'number')))
        parent_window = self.driver.window_handles[0]
        card_ids = ['number', 'name', 'expiry', 'verification_value']
        for index, frame in enumerate(payment_iframes):
            self.driver.switch_to_window(parent_window)
            self.driver.switch_to.frame(frame)
            if(index == 0 or index == 2):
                number_split = self.config[card_ids[index]].split()
                for n in number_split:
                    self.driver.find_element_by_id(card_ids[index]).send_keys(
                    n
                    ) 
            else: 
                self.driver.find_element_by_id(card_ids[index]).send_keys(
                    list(self.config[card_ids[index]])
                ) 
        #exit the iframe
        self.driver.switch_to_window(parent_window)
        if(self.config["full_buy"] == "true"):
            self.driver.find_element_by_xpath(selectors["pay_button"]).click()          

    def run_item(self, fast_checkout):
        
        item_id = self.check_stock()
        self.driver.get(f"https://gorillamind.com/cart/{item_id}:{self.quantity}")

        if(not fast_checkout):
            self.no_login()
        else:
            log.info("Speedy checkout incoming!")
            current_url = self.driver.current_url
            self.driver.get(f"{current_url}{SKIP_SHIPPING}")
            self.pay()

    def no_login(self):     
        try:
            log.info('Applying user details')
            self.driver.find_element_by_id('checkout_email').send_keys(
                    self.config['email']
            )
            for index, key in enumerate(detail_ids):
                if(index == 8):
                    self.driver.find_element_by_id(get_details_id(key)).send_keys(
                            self.config[key] + Keys.RETURN
                    )  
                else:
                    self.driver.find_element_by_id(get_details_id(key)).send_keys(
                            self.config[key]
                    )  
            self.driver.find_element_by_id('continue_button').click() 
                             
        except Exception as e:
            log.info('Couldn\'t fill out your personal details: ' +str(e))

        while True:
            try:
                element = self.wait.until(EC.element_to_be_clickable((By.ID, 'continue_button')))
                element.click()
                log.info('Clicking continue on shipping page')
                break;
            except TimeoutException:
                log.info('Error locating continue button')
                break

        if(self.config["discount"]):   
            self.apply_discount()
                
        time.sleep(2.8)            
        self.pay()  
        time.sleep(300)