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

DETAILS_PATH = "details.json"

detail_ids = ['first_name', 'last_name', 'address1', 'address2', 'city', 'country',
    'zip', 'phone', 'province'];

card_ids = ['number', 'name', 'expiry', 'verification_value']

selectors = {
    "product_title": "//*[@class='product_name title']",
    "hidden_price": "//*[@class='current_price hidden']",
    "page_not_found": "//*[@class='page-not-found__title title']",
    "add_to_cart": "//*[@data-label='Add to cart']",
    "sold_out": "//*[@class='sold_out']",
    "increment_quantity": "//*[@class='control plus-control']",
    "quantity_input": "//*[@class='quantity-input quantity-element input']",
    "checkout": "//*[@class='cart__checkout']",
    "checkout_details": "checkout_shipping_address",
    "discount_code": "//*[contains(@id, 'checkout_reduction_code')]",
    "apply_discount": "//*[@class='field__input-btn btn']",
    "cart_price": "//*[@class='order-summary__emphasis total-recap__final-price skeleton-while-loading']",
    "payment_iframe": "//iframe[@class='card-fields-iframe']",
    "pay_button": "//button[@id='continue_button']"  
}

def get_details_id(name):
    return f'{selectors["checkout_details"]}_{name}'

class Gorilla_Mind:
    def __init__(self, item, quantity):
        self.driver = webdriver.Chrome(executable_path=binary_path, options=options)
        self.wait = WebDriverWait(self.driver, 10)
        self.short_wait = WebDriverWait(self.driver, 1)
        self.item_url = GORILLA_PRODUCTS[item]
        self.quantity = quantity
        self.driver.get("https://gorillamind.com/collections/supplements")
        time.sleep(3)

    def run_item(self, item_url, quantity=1, interval=5, config={}):
        log.info(f"Loading page: {item_url}")
        self.driver.get(item_url)
        item = ""
        try:
            product_title = self.wait.until(
                presence_of_element_located((By.XPATH, selectors["product_title"]))
            ).text
            log.info(f"Loaded page for {product_title}")
            item = product_title[:100].strip()
        except:
            product_title = ""
            log.error(self.driver.current_url)
        availability = True
        try:
            if (self.driver.find_element_by_xpath( selectors["hidden_price"]) 
                or self.driver.find_element_by_xpath(selectors["page_not_found"])):
                availability = False
                log.info(f"{product_title} out of stock")
        except: 
            if(product_title != ""):
                log.info(f"{product_title} in stock!")


        while not self.driver.find_elements_by_xpath(selectors["add_to_cart"]):
            try:
                self.driver.refresh()
                log.info(f"Refreshing for {item}...")
                try:
                    availability = self.driver.find_element_by_xpath(selectors["sold_out"]).text.replace("\n", " ")
                    log.info(f"Current status message: {availability}")
                except:
                    log.info("Page not found - looks like the url doesn't lead to a product")
                time.sleep(interval)
            except TimeoutException as _:
                log.warn("A polling request timed out. Retrying.")
        

        log.info("Item in stock, buy now button found!")
        log.info(f"Attempting to buy item: {product_title}")
        self.buy_now(quantity, config)

    def buy_now(self, quantity, config):

        plus_icon = self.driver.find_element_by_xpath(selectors["increment_quantity"])
        for i in range(quantity-1):
               plus_icon.click()
        
        self.driver.find_element_by_xpath(selectors["add_to_cart"]).click()
        self.driver.find_element_by_xpath(selectors["quantity_input"]).send_keys(
            Keys.RETURN)
        
        try:
            self.driver.find_element_by_xpath(selectors["checkout"]).click()
        except:
            log.debug("Went to check out page.")
        
        try:
            log.info('Applying user details')
            self.driver.find_element_by_id('checkout_email').send_keys(
                    config['email']
            )
            for index, key in enumerate(detail_ids):
                if(index == 8):
                    self.driver.find_element_by_id(get_details_id(key)).send_keys(
                            config[key] + Keys.RETURN
                    )  
                else:
                    self.driver.find_element_by_id(get_details_id(key)).send_keys(
                            config[key]
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
        if(config["discount"]):   
            discount_input = ""      
            try:
                log.info('Applying discount code: ' + str(config['discount']))
                discount_input = self.driver.find_element_by_xpath(selectors["discount_code"])
                discount_input.send_keys(
                    config['discount']
                )
                self.driver.find_element_by_xpath(selectors["apply_discount"]).click()
            except NoSuchElementException:
                log.info('error adding discount code')
                
        time.sleep(2.8)            
        total_price = self.driver.find_element_by_xpath(selectors["cart_price"]).text
        log.info("Total order price: " + str(total_price))
        log.info('Inputting payment details')


        payment_iframes = self.driver.find_elements_by_xpath(selectors["payment_iframe"])
        parent_window = self.driver.window_handles[0]
        card_ids = ['number', 'name', 'expiry', 'verification_value']
        for index, frame in enumerate(payment_iframes):
            self.driver.switch_to_window(parent_window)
            self.driver.switch_to.frame(frame)
            if(index is 0 or index is 2):
                number_split = config[card_ids[index]].split()
                for n in number_split:
                    self.driver.find_element_by_id(card_ids[index]).send_keys(
                    n
                    ) 
            else: 
                self.driver.find_element_by_id(card_ids[index]).send_keys(
                    list(config[card_ids[index]])
                ) 
        #exit the iframe
        self.driver.switch_to_window(parent_window)
        if(config["full_buy"] == "true"):
            self.driver.find_element_by_xpath(selectors["pay_button"]).click()  
        time.sleep(300)