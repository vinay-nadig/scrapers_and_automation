#!/usr/bin/env python

from BeautifulSoup import BeautifulSoup
from urllib import urlretrieve
from time import sleep
from selenium import webdriver
from ConfigParser import ConfigParser
from random import randint
import textwrap
import re
import thread
import urllib
import pickle
import twitter

# Global Data
twit_id = 'hobblegobber'
twit_source_url = "https://twitter.com/"
pattern = re.compile('http://t.co/.*? ')

# Configuration

USE_FIREFOX = 1
USE_CHROME = 0
# How many pairs of shoes would you like to purchase?
NUMBER_OF_PURCHASE = 1
# How often would you like to check the twitter feed?
SLEEP_DURATION = 30
# Name of the config file?
CONFIG_FILE = 'config.txt'

parser = ConfigParser()
parser.read(CONFIG_FILE)
dic = parser._sections
if len(dic)/2 < NUMBER_OF_PURCHASE:
    print "Not enough purchase info"
    print "Please add more sections to the configuration file"


def main():
    # Get the source html the first time
    api = twitter.Api(consumer_key='5LTld2weQKmm0QaE7cIADQ', consumer_secret='Um2WSj955KI4YUImoL2ZhhBcv8Hvvy45TgF7Kbvrk', access_token_key='1509832374-jVEVCq2n654PYrNkvWGfKiQZXmJkrMNo0AKt0SJ', access_token_secret='ai6J7Hpn5ZR78bwNWMozpsg7qeLvKR64CIgamUX2w')
    stored_list = []
    while True:
        list_of_tweets = api.GetUserTimeline(screen_name=twit_id, count=10, exclude_replies=True)
        if len(list_of_tweets):
            for tweet in list_of_tweets:
                if tweet.GetId() in stored_list:
                    continue
                print "new tweet detected"
                stored_list.append(tweet.GetId())
                text = tweet.GetText()
                print "text = " + text
                if "now available" in text.lower():
                    product_url = pattern.findall(text)[0]
                    temp = 0
                    while temp != NUMBER_OF_PURCHASE:
                        temp += 1
                        thread.start_new_thread(purchase_product, (product_url, temp))

        sleep(SLEEP_DURATION + randint(10, 30))


def purchase_product(product_url, thread_number):
    shipment_val = "shipment" + str(thread_number)
    payment_val = "payment" + str(thread_number)
    if USE_FIREFOX:
        driver = webdriver.Firefox()
    else:
        driver = webdriver.Chrome()
    driver.get(str(product_url))
    sleep(5)
    if 'shoe' in driver.title.lower():
        # Click on SIZE button
        try:
            size_option = driver.find_element_by_class_name("dropdown-label")
        except:
            print "can't find size"
            driver.quit()
            purchase_product(product_url, thread_number)
        size_option.click()

        # Select shoe size from list
        size1 = dic[shipment_val]["shoe_size1"]
        size_link1 = driver.find_element_by_partial_link_text(size1)
        size_link_parent1 = size_link1.find_element_by_xpath("..")

        if size_link_parent1.get_attribute("class") == 'size-not-in-stock':
            size2 = dic[shipment_val]["shoe_size2"]
            size_link2 = driver.find_element_by_partial_link_text(size2)
            size_link_parent2 = size_link2.find_element_by_xpath("..")

            if size_link_parent2.get_attribute("class") == 'size-not-in-stock':
                size3 = dic[shipment_val]["shoe_size3"]
                size_link3 = driver.find_element_by_partial_link_text(size3)
                size_link_parent3 = size_link3.find_element_by_xpath("..")

                if size_link_parent3.get_attribute("class") == 'size-not-in-stock':
                    driver.quit()
                    return
                else:
                    size_link = size_link3
            else:
                size_link = size_link2
        else:
            size_link = size_link1

        size_link.click()

        # Add to cart
        add_cart_button = driver.find_element_by_link_text("ADD TO CART")
        add_cart_button.click()

        # Wait for javascript to process
        sleep(5)

        # Click on the cart symbot
        try:
            cart_link = driver.find_element_by_class_name("cartCount")
        except:
            driver.quit()
            purchase_product(product_url, thread_number)
        cart_link.click()

        # Wait for a few seconds
        sleep(5)

        # Click on checkout button
        try:
            checkout_button = driver.find_element_by_id("ch4_cartCheckoutBtn")
        except:
            driver.quit()
            purchase_product(product_url, thread_number)
        checkout_button.click()
        sleep(5)

        # Click on guest checkout button
        try:
            guest_checkout_button = driver.find_element_by_id("ch4_loginGuestBtn")
        except:
            driver.quit()
            purchase_product(product_url, thread_number)
        guest_checkout_button.click()

        sleep(5)

        # ENTER SHIPMENT DETAILS

        # First name
        try:
            fname_field = driver.find_element_by_id("fname")
        except:
            driver.quit()
            purchase_product(product_url, thread_number)
        fname_field.send_keys(dic[shipment_val]["fname"].strip("'").strip('"'))

        # Last Name
        lname_field = driver.find_element_by_id("lname")
        lname_field.send_keys(dic[shipment_val]["lname"].strip("'").strip('"'))

        # Address
        # This is a bit trickier. Each address field has a limit
        # of 35 characters. So break down the address into
        # pieces each of which has <= 34 characters
        address = dic[shipment_val]["address"]
        addr_list = textwrap.wrap(address, 34)
        addr1 = addr_list[0].strip("'").strip('"')
        addr2 = addr_list[1].strip("'").strip('"')
        addr_field1 = driver.find_element_by_id("address1Field")
        addr_field1.send_keys(addr1)
        addr_field2 = driver.find_element_by_id("address2Field")
        addr_field2.send_keys(addr2)

        # City
        city_field = driver.find_element_by_id("singleCity")
        city_field.send_keys(dic[shipment_val]["city"].strip("'").strip('"'))

        # State(Dropdown List)
        state = dic[shipment_val]["state"].strip("'").strip('"')
        state_list = driver.find_element_by_id("singleState")
        for option in state_list.find_elements_by_tag_name("option"):
            if option.text.lower() == state.lower():
                option.click()

        # Zip Code
        zip_code_field = driver.find_element_by_id("postalCodeField")
        zip_code_field.send_keys(dic[shipment_val]["zip_code"].strip("'").strip('"'))

        # Shipping submit
        submit_button = driver.find_element_by_id("shippingSubmit")
        submit_button.click()

        sleep(5)

        # Switch to the frame containing the shipping details
        try:
            frame = driver.find_element_by_id("billingFormFrame")
        except:
            driver.quit()
            purchase_product(product_url, thread_number)
        driver.switch_to_frame(frame)

        # PAYMENT
        # Card Type(Dropdown List)
        card_type = dic[payment_val]["card_type"].strip("'").strip('"')
        card_list = driver.find_element_by_id("cardType")
        for option in card_list.find_elements_by_tag_name("option"):
            if option.text.lower() == card_type.lower():
                option.click()

        # Card Number
        card_number = dic[payment_val]["card_number"].strip("'").strip('"')
        card_no_field = driver.find_element_by_id("creditCardNumber")
        card_no_field.send_keys(card_number)

        # Expiry Date(Month)
        month = dic[payment_val]["exp_month"].strip("'").strip('"')
        month_list = driver.find_element_by_id("expirationMonth")
        for option in month_list.find_elements_by_tag_name("option"):
            if option.text == month:
                option.click()

        # Expiry Date(Year)
        year = dic[payment_val]["exp_year"].strip("'").strip('"')
        year_list = driver.find_element_by_id("expirationYear")
        for option in year_list.find_elements_by_tag_name("option"):
            if option.text == year:
                option.click()

        # Security Code
        code_field = driver.find_element_by_id("cvNumber")
        code_field.send_keys(dic[payment_val]["security_code"].strip("'").strip('"'))


        # Check if the billing and shipping address are same
        boolean = dic[payment_val]["same_billandship_addr"]

        # If different
        if not int(boolean):
            fname_field = driver.find_element_by_id("firstName")
            fname_field.send_keys(dic[payment_val]["fname"].strip("'").strip('"'))

            # Last Name
            lname_field = driver.find_element_by_id("lastName")
            lname_field.send_keys(dic[payment_val]["lname"].strip("'").strip('"'))

            # Address
            # This is a bit trickier. Each address field has a limit
            # of 35 characters. So break down the address into
            # pieces each of which has <= 34 characters
            address = dic[payment_val]["address"].strip("'").strip('"')
            addr_list = textwrap.wrap(address, 34)
            addr1 = addr_list[0]
            addr2 = addr_list[1]
            addr_field1 = driver.find_element_by_id("address1")
            addr_field1.send_keys(addr1)
            addr_field2 = driver.find_element_by_id("address2")
            addr_field2.send_keys(addr2)

            # City
            city_field = driver.find_element_by_id("city")
            city_field.send_keys(dic[payment_val]["city"].strip("'").strip('"'))

            # State(Dropdown List)
            state = dic[payment_val]["state"].strip("'").strip('"')
            state_list = driver.find_element_by_id("usState")
            for option in state_list.find_elements_by_tag_name("option"):
                if option.text.lower() == state.lower():
                    option.click()

            # Zip Code
            zip_code_field = driver.find_element_by_id("postalCode")
            zip_code_field.send_keys(dic[payment_val]["zip_code"].strip("'").strip('"'))
        # If same, check the box
        else:
            list_of_checkboxes = driver.find_elements_by_class_name("ch4_formCheckBox")
            checkbox = list_of_checkboxes[0]
            checkbox.click()

        sleep(5)

        # Phone Number
        phone_field = driver.find_element_by_id("phoneNumber")
        phone_field.send_keys(dic[payment_val]["billing_phone"].strip("'").strip('"'))

        # Alternate Phone number
        alt_phone = driver.find_element_by_id("faxNumber")
        alt_phone.send_keys(dic[payment_val]["alt_phone"].strip("'").strip('"'))

        # Mail Id
        mail_field = driver.find_element_by_id("email")
        mail_field.send_keys(dic[payment_val]["email"].strip("'").strip('"'))

        # Click Next Step button
        next_button = driver.find_element_by_id("billingSubmit")
        next_button.click()

        # Wait for sometime
        sleep(5)

        # Place order button
        try:
            place_ord_button = driver.find_element_by_id("submitOrderTopBtn")
        except:
            driver.quit()
            purchase_product(product_url, thread_number)
        place_ord_button.click()
        print "Order {0} placed successfully".format(thread_number)


if __name__ == "__main__":
    main()
