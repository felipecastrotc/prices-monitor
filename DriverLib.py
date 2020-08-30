import os
import re
import time

import numpy as np
import pandas as pd
import unidecode
from babel import numbers
from bs4 import BeautifulSoup
from fuzzywuzzy import fuzz
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait


def get_browser(headless=True):

    # Download options
    profile = webdriver.FirefoxProfile()
    profile.set_preference("browser.download.folderList", 2)  # custom location
    profile.set_preference("browser.download.manager.showWhenStarting", False)
    profile.set_preference("browser.download.dir", os.getcwd())
    profile.set_preference("browser.helperApps.neverAsk.saveToDisk", "text/csv")
    # Options
    options = Options()
    options.headless = headless
    # Start broswer
    browser = webdriver.Firefox(profile, options=options)
    browser.delete_all_cookies()

    return browser


def clean_price(price, replace=None):
    if replace is not None:
        price = price.replace(*replace)
    return re.sub("[^-0-9.,]", "", price)


def create_prod_detail(price, info=None, shop=None, locale="pt_BR", **kwargs):

    prod_lst = []

    if type(price) is str:
        price = clean_price(price, **kwargs)

        prod_detail = {"info": info}
        prod_detail["price"] = float(numbers.parse_decimal(price, locale=locale))

        if shop is not None:
            prod_detail["shop"] = shop

        prod_lst += [prod_detail]
    else:
        for p in price:
            if "price" not in p.keys():
                continue
            p["price"] = clean_price(p["price"], **kwargs)
            p["price"] = float(numbers.parse_decimal(p["price"], locale=locale))
            if info is not None:
                p["info"] = info
            if shop is not None:
                p["shop"] = shop

            prod_lst += [p]

    return prod_lst


def filter_products(target, products, exclude=[], include=[], or_include=False):
    fuzz_limit = 90

    # Transform filters to lower case
    exclude_set = set([e.lower() for e in exclude])
    include_set = set([i.lower() for i in include])

    out = []
    for i, p in enumerate(products):
        # i = 0
        # p = products[i]
        # Check similarity
        fuzz_val = fuzz.token_set_ratio(target, p["info"])
        if fuzz_val > fuzz_limit:
            # Lower case info
            info_set = set(p["info"].lower().split(" "))
            # Filter products
            if len(info_set - exclude_set) != len(info_set):
                continue
            add_factor = (len(include) - 1) * or_include
            if len(info_set | include_set) > (len(info_set) + add_factor):
                continue
            out += [p]
    return out


def extract_products(grid, class_name=None, id_val=None):
    n_trials = 10

    # Get grid products
    for i in range(n_trials):
        if class_name is not None:
            products = grid.find_elements_by_class_name(class_name)
        elif id_val is not None:
            products = grid.find_elements_by_id(id_val)
        else:
            products = []
        # Wait 1 second in case the grid was not loaded
        if len(products) == 0:
            time.sleep(1)
        else:
            break

    return products


def craw_products(items, class_name={}, id_val={}):
    # example class_name = {"info": "class_name1", "price": "class_name2"}
    out = []  # variable to return
    aux = {}  # temporary store the info from items
    for i in items:
        try:
            # Iterate over passed classes
            for k in class_name.keys():
                tmp = i.find_elements_by_class_name(class_name[k])
                if len(tmp) == 0:
                    raise "A element was not found!"
                aux[k] = tmp[0].text
            # Iterate over passed id
            for k in id_val.keys():
                tmp = i.find_elements_by_id(id_val[k])
                if len(tmp) == 0:
                    raise "A element was not found!"
                aux[k] = tmp[0].text
        except:
            aux = {}

        out += [aux]
        aux = {}
    return out


class ShopDriver(object):

    link = "https://www.shopdriver.io/"
    locale = "pt_BR"
    currency = "BRL"

    timed_out = 10

    def __init__(self, browser):
        self.browser = browser
        self.wait = WebDriverWait(browser, self.timed_out)
        pass

    def get_product(self, product, exclude=[], include=[], or_include=False):
        self.search(product)
        data, success = self.scan_search()
        if success:
            data = filter_products(product, data, exclude, include, or_include)
            return data
        else:
            return []

    pass


class GoogleShopDriver(ShopDriver):

    shop = "Google Shopping"
    link = "https://www.google.com/shopping?hl=pt-br"
    locale = "pt_BR"
    currency = "BRL"

    timed_out = 10

    def search(self, product):
        browser = self.browser
        link = self.link
        # id for search bar
        search_id = "gLFyf"

        # Open shop link
        browser.get(link)

        # Search product
        search = browser.find_element_by_class_name(search_id)
        search.send_keys(product)
        search.send_keys(Keys.ENTER)
        pass

    def scan_search(self):

        # Procedure:
        # 1. Find the product grid: "sh-pr__product-results"
        # 2. Get the grid products: "sh-dlr__list-result"
        # 3. Get product(s) prices and information
        #   * Price: "sc-fznWqX"
        #   * Info: "xsRiS"
        # 4. Return info

        def scan_grid():
            # Wait to "memu-products-container" to load
            grid_val = "sh-pr__product-results"
            wait.until(presence_of((By.CLASS_NAME, grid_val)))
            # Get grid
            grid = browser.find_elements_by_class_name(grid_val)
            products = extract_products(grid[0], class_name="sh-dlr__list-result")
            return products

        browser = self.browser
        wait = self.wait
        locale = self.locale
        presence_of = ec.presence_of_element_located

        # wait = WebDriverWait(browser, timed_out)
        try:
            # Scan products
            out = []

            # Initial product scan to get the product titles
            products = scan_grid()

            # Build a list with
            lst_title = []
            for p in products:
                # Get info
                title = p.find_elements_by_class_name("xsRiS")[0].text
                lst_title += [title]

            while len(lst_title) > 0:
                for p in products:
                    # Get info
                    title = p.find_elements_by_class_name("xsRiS")[0].text
                    if title in lst_title:
                        lst_title.remove(title)
                    else:
                        continue

                    # Get price
                    compare_class = "C1iIFb"
                    comp_btt = p.find_elements_by_class_name(compare_class)
                    if len(comp_btt) > 0:
                        # browser.execute_script("arguments[0].scrollIntoView(true);", comp_btt[0])
                        comp_btt[0].click()
                        # Get table of shops
                        table_id = "sh-osd__online-sellers-cont"
                        table = browser.find_elements_by_id(table_id)

                        table_shops = "sh-osd__offer-row"
                        t_shops = extract_products(table[0], class_name=table_shops)

                        class_name = {"shop": "sh-osd__seller-link", "price": "QXiyfd"}
                        price = craw_products(t_shops, class_name=class_name)

                    else:
                        class_name = {"price": "Nr22bf", "shop": "shntl"}
                        price = craw_products([p], class_name=class_name)

                    out += create_prod_detail(price, title, locale=locale)

                    if len(comp_btt) > 0:
                        browser.execute_script("window.history.go(-1)")
                        products = scan_grid()
                        break

            success = True if len(out) > 0 else False
        except Exception as e:
            print("Fail to find the products container!")
            print(e)
            out = []
            success = False

        return out, success

    pass


class AmazonDriver(ShopDriver):

    shop = "Amazon"
    link = "https://www.amazon.com.br/"
    locale = "pt_BR"
    currency = "BRL"

    timed_out = 10

    def search(self, product):
        browser = self.browser
        link = self.link
        # id for search bar
        search_id = "twotabsearchtextbox"

        # Open shop link
        browser.get(link)

        # Search product
        search = browser.find_element_by_id(search_id)
        search.send_keys(product)
        search.send_keys(Keys.ENTER)
        pass

    def scan_search(self):
        browser = self.browser
        wait = self.wait
        locale = self.locale
        presence_of = ec.presence_of_element_located

        # wait = WebDriverWait(browser, timed_out)

        # Procedure:
        # 1. Find the product grid: "listagem-produtos"
        # 2. Get the grid products: "sc-fzqNqU"
        # 3. Get product(s) prices and information
        #   * Price: "sc-fznWqX"
        #   * Info: "sc-fzoLsD"
        # 4. Return info

        try:
            # Wait to "memu-products-container" to load
            grid_val = "s-main-slot"
            wait.until(presence_of((By.CLASS_NAME, grid_val)))
            # Get grid
            grid = browser.find_elements_by_class_name(grid_val)

            products = extract_products(grid[0], class_name="celwidget")

            # Scan products
            class_name = {"price": "a-price", "info": "a-size-medium"}
            price = craw_products(products, class_name=class_name)
            out = create_prod_detail(
                price, shop=self.shop, locale=locale, replace=["\n", ","]
            )

            success = True if len(out) > 0 else False
        except Exception as e:
            print("Fail to find the products container!")
            print(e)
            out = []
            success = False

        return out, success

    pass


class MagaLuDriver(ShopDriver):

    shop = "Magazine Luiza"
    link = "https://www.magazineluiza.com.br/"
    locale = "pt_BR"
    currency = "BRL"

    timed_out = 10

    def search(self, product):
        browser = self.browser
        link = self.link
        # id for search bar
        search_id = "inpHeaderSearch"

        # Open shop link
        browser.get(link)

        # Search product
        search = browser.find_element_by_id(search_id)
        search.send_keys(product)
        search.send_keys(Keys.ENTER)
        pass

    def scan_search(self):
        browser = self.browser
        wait = self.wait
        locale = self.locale
        presence_of = ec.presence_of_element_located

        # Procedure:
        # 1. Find the product grid: "neemu-products-container"
        # 2. Get the grid products: "nm-product-item"
        # 3. Get product(s) prices and information
        #   * Price: "nm-price-container"
        #   * Info: "nm-product-name"
        # 4. Return info

        try:
            # Check it was found something or not and wait
            not_found = browser.find_elements_by_class_name("nm-not-found-container")
            if len(not_found) > 0:
                raise "I cannot find the product requested"

            # Wait to "memu-products-container" to load
            grid_val = "neemu-products-container"
            wait.until(presence_of((By.CLASS_NAME, grid_val)))
            # Get grid
            grid = browser.find_elements_by_class_name(grid_val)

            products = extract_products(grid[0], class_name="nm-product-item")

            # Scan products
            time.sleep(3)
            class_name = {"price": "nm-price-container", "info": "nm-product-name"}
            price = craw_products(products, class_name=class_name)
            out = create_prod_detail(price, shop=self.shop, locale=locale)

            success = True if len(out) > 0 else False
        except Exception as e:
            print("Fail to find the products container!")
            print(e)
            out = []
            success = False

        return out, success

    def scan_search_alternate(self):
        log = []
        browser = self.browser
        wait = self.wait

        presence_of = ec.presence_of_element_located
        visibility_of = ec.visibility_of_element_located
        wait = WebDriverWait(browser, timed_out)

        # Procedure:
        # 1. Find the product grid: "neemu-products-container"
        # 2. Get the grid products: "nm-product-item"
        # 3. Get product(s) prices and information
        #   * Price: "nm-price-container"
        #   * Info: "nm-product-name"
        # 4. Return info

        try:
            # Check it was found something or not and wait
            not_found = browser.find_elements_by_class_name("nm-not-found-container")
            if len(not_found) > 0:
                raise "I cannot find the product requested"

            # Wait to "memu-products-container" to load
            wait.until(presence_of((By.CLASS_NAME, "productShowCaseContent")))

            # Get grid
            grid = browser.find_elements_by_class_name("productShowCaseContent")

            # Get grid products
            for i in range(10):
                products = grid[0].find_elements_by_class_name("product-li")
                if len(products) == 0:
                    time.sleep(1)
                else:
                    break

            # Scan products
            time.sleep(3)
            out = []
            for p in products:
                # Get price
                # Occurs when it has discount
                price = p.find_elements_by_class_name("price-value")
                if len(price) == 0:
                    price = p.find_elements_by_class_name("price")
                # Occurs when it does not have discount
                if len(price) == 0:
                    continue
                price = price[0].text

                # Get info
                title = p.find_element_by_class_name("productTitle").text

                price = clean_price(price)
                info = title
                out += [{"info": info}]
                out[-1]["price"] = float(numbers.parse_decimal(price, locale="pt_BR"))

            success = True if len(out) > 0 else False
        except Exception as e:
            print("Fail to find the products container!")
            print(e)
            out = []
            success = False

        return out, success

    pass


class KabumDriver(ShopDriver):

    shop = "Kabum"
    link = "https://www.kabum.com.br/"
    locale = "pt_BR"
    currency = "BRL"

    timed_out = 10

    def search(self, product):
        browser = self.browser
        link = self.link
        # id for search bar
        search_id = "sprocura"

        # Open shop link
        browser.get(link)

        # Search product
        search = browser.find_element_by_class_name(search_id)
        search.send_keys(product)
        search.send_keys(Keys.ENTER)
        pass

    def scan_search(self):
        browser = self.browser
        wait = self.wait
        locale = self.locale
        presence_of = ec.presence_of_element_located

        # wait = WebDriverWait(browser, timed_out)

        # Procedure:
        # 1. Find the product grid: "listagem-produtos"
        # 2. Get the grid products: "sc-fzqNqU"
        # 3. Get product(s) prices and information
        #   * Price: "sc-fznWqX"
        #   * Info: "sc-fzoLsD"
        # 4. Return info

        try:
            # Wait to "listagem-produtos" to load
            grid_val = "listagem-produtos"
            wait.until(presence_of((By.ID, grid_val)))
            # Get grid
            grid = browser.find_elements_by_id(grid_val)

            # Check it was found something or not and wait
            not_found = browser.find_elements_by_class_name("sc-fzomME")
            if len(not_found) > 0:
                raise "I cannot find the product requested"

            products = extract_products(grid[0], class_name="sc-fzqNqU")

            time.sleep(3)
            # Scan products
            class_name = {"price": "sc-fznWqX", "info": "sc-fzoLsD"}
            price = craw_products(products, class_name=class_name)
            out = create_prod_detail(price, shop=self.shop, locale=locale)

            success = True if len(out) > 0 else False
        except Exception as e:
            print("Fail to find the products container!")
            print(e)
            out = []
            success = False

        return out, success

    pass


class B2WDriver(ShopDriver):

    shop = "B2W"
    link = "https://www.b2wmarketplace.com.br/"
    locale = "pt_BR"
    currency = "BRL"

    timed_out = 10

    def search(self, product):
        browser = self.browser
        link = self.link
        # id for search bar
        search_id = "h_search-input"

        # Open shop link
        browser.get(link)

        # Search product
        search = browser.find_element_by_id(search_id)
        search.send_keys(product)
        search.send_keys(Keys.ENTER)
        pass

    def scan_search(self):
        browser = self.browser
        wait = self.wait
        locale = self.locale
        shop = self.shop

        presence_of = ec.presence_of_element_located

        # wait = WebDriverWait(browser, timed_out)
        # Procedure:
        # 1. Find the product grid: "main-grid"
        # 2. Get the grid products: "product-grid-item"
        # 3. Get product(s) prices and information
        #   * Price: Beautiful soup ->  'span', {'class' : re.compile("Price")}
        #   * Info: Beautiful soup ->  'h2', {'class' : re.compile("TitleUI")}
        # 4. Return info

        # Regex search

        re_price = re.compile("Price")
        re_info = re.compile("TitleUI")

        # Wait to "main-grid" to load
        try:
            wait.until(presence_of((By.CLASS_NAME, "main-grid")))
            grid = browser.find_elements_by_class_name("main-grid")

            products = extract_products(grid[0], class_name="product-grid-item")

            # Scan products
            out = []
            for p in products:
                # Parse the html
                soup = BeautifulSoup(p.get_attribute("outerHTML"))
                # Find the product price and info
                price = soup.find_all("span", {"class": re_price})
                title = soup.find_all("h2", {"class": re_info})

                # Check for empty info
                if len(price) == 0:
                    continue
                if len(title) == 0:
                    continue

                # Append item
                out += create_prod_detail(price[0].text, title[0].text, shop, locale)

            success = True if len(out) > 0 else False
        except:
            out = []
            success = False

        return out, success

    pass


class ShoptimeDriver(B2WDriver):

    shop = "Shoptime"
    link = "https://www.shoptime.com.br/"
    locale = "pt_BR"
    currency = "BRL"

    timed_out = 10

    pass


class AmericanasDriver(B2WDriver):

    shop = "Americanas"
    link = "https://www.americanas.com.br/"
    locale = "pt_BR"
    currency = "BRL"

    timed_out = 10

    pass


class SubmarinoDriver(B2WDriver):

    shop = "Submarino"
    link = "https://www.submarino.com.br/"
    locale = "pt_BR"
    currency = "BRL"

    timed_out = 10

    pass


# TODO: Hide selenium usage for Pão de Açucar Driver
class PaoAcucarDriver(ShopDriver):

    shop = "Grupo Pão de Açúcar"
    link = "https://www.paodeacucar.com.br/"
    locale = "pt_BR"
    currency = "BRL"

    timed_out = 10

    def search(self, product):
        browser = self.browser
        link = self.link

        # The procedure like B2W driver is being detected as bot
        # try to conceive it or use direct search. It is still
        # limited to one page.

        browser.delete_all_cookies()
        product = unidecode.unidecode(product)
        # Open shop link
        browser.get("{}{}/b".format(link, product))
        browser.delete_all_cookies()

        # browser.delete_all_cookies()
        # id for search bar
        # search_id = "strBusca"

        # # Open shop link
        # browser.get(link)

        # # Search product
        # search = browser.find_element_by_id(search_id)
        # browser.delete_all_cookies()
        # search.send_keys(product)
        # search.send_keys(Keys.ENTER)
        # browser.delete_all_cookies()
        pass

    def scan_search(self):
        browser = self.browser
        wait = self.wait
        locale = self.locale
        presence_of = ec.presence_of_element_located

        # wait = WebDriverWait(browser, timed_out)

        # Procedure:
        # 1. Find the product grid: "ProductsGrid__ProductsGridWrapper-yqpqna-0"
        # 2. Get the grid products: "sc-fzqNqU"
        # 3. Get product(s) prices and information
        #   * Price: "sc-fznWqX"
        #   * Info: "sc-fzoLsD"
        # 4. Return info

        try:
            # Check it was found something or not and wait
            not_found = browser.find_elements_by_class_name(
                "Container-ylum0o-0 pages__Main-sc-4fgpoh-1"
            )
            if len(not_found) > 0:
                raise "I cannot find the product requested"

            # Wait to "ProductsGrid__ProductsGridWrapper-yqpqna-0" to load
            product_grid = "ProductsGrid__ProductsGridWrapper-yqpqna-0"
            wait.until(presence_of((By.CLASS_NAME, product_grid)))
            # Get grid
            grid = browser.find_elements_by_class_name(product_grid)

            # Get grid products
            class_name = "ProductCard__ProductContainer-sc-2vuvzo-3"
            products = extract_products(grid[0], class_name=class_name)

            time.sleep(3)
            # Scan products
            class_name = {
                "price": "ProductPrice__Price-sc-1tzw2we-3",
                "info": "ProductCard__Title-sc-2vuvzo-0",
            }
            price = craw_products(products, class_name=class_name)
            out = create_prod_detail(price, shop=self.shop, locale=locale)

            success = True if len(out) > 0 else False
        except Exception as e:
            print("Fail to find the products container!")
            print(e)
            out = []
            success = False

        browser.delete_all_cookies()
        return out, success

    pass


class PontoFrioDriver(PaoAcucarDriver):

    shop = "Ponto Frio"
    link = "https://www.pontofrio.com.br/"
    locale = "pt_BR"
    currency = "BRL"

    timed_out = 10

    pass


class CasasBahiaDriver(PaoAcucarDriver):

    shop = "Casas Bahia"
    link = "https://www.casasbahia.com.br/"
    locale = "pt_BR"
    currency = "BRL"

    timed_out = 10

    pass


class Scan(object):
    def __init__(self, browser=None):
        self.browser = get_browser(headless=True) if browser is None else browser
        self.drivers = [
            SubmarinoDriver,
            AmericanasDriver,
            ShoptimeDriver,
            MagaLuDriver,
            # PontoFrioDriver,
            # CasasBahiaDriver,
            AmazonDriver,
            KabumDriver,
            GoogleShopDriver,
        ]
        pass

    def scan(self, product, exclude=[], include=[], or_include=False):
        out = []
        # Iterate over all shops
        for shop in self.drivers:
            s = shop(self.browser)
            out += s.get_product(product, exclude, include)
        return pd.DataFrame.from_dict(out)

    pass
