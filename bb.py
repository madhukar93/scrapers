import requests
import json
import sqlite3
from rq import Queue
from redis import Redis
from unidecode import unidecode

# redis_conn = Redis()
# q = Queue(connection=redis_conn)

# 'https://bigbasket.com/mapi/v2.3.0/product-list/?sorted_on=alpha&slug=bread-dairy-eggs&page=1&type=pc'
# dest_slug = "type=pc&slug=mineral-water"


class BigBasket:
    redis_conn = Redis()
    q = Queue(connection=redis_conn)
    product_url = 'https://bigbasket.com/mapi/v2.3.0/product-list/?sorted_on=alpha&{dest_slug}&page={page}'
    product_paginated_url = 'https://www.bigbasket.com/mapi/v2.3.0/product-next-page/?{dest_slug}&page={page}&sorted_on=alpha&filter_on=[]&tab_type=[%22all%22]'
    menu_url = 'https://www.bigbasket.com/mapi/v2.3.0/get-main-menu/'
    db_conn = sqlite3.connect('competitor_inventory_test1.db')

    def _get_auth_headers(self, url="https://www.bigbasket.com/skip_explore/?c=1&l=0&s=0&n=/"):
        init_headers = {
            'Host': 'www.bigbasket.com',
            'Connection': 'keep-alive',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.106 Safari/537.36',
            'DNT': '1',
            'Accept-Encoding': 'gzip, deflate, sdch',
            'Accept-Language': 'en-US,en;q=0.8',
        }
        r = requests.get(url, headers=init_headers)
        self.api_headers = r.request.headers

    def _get_category_slugs(self):
        r_menu = requests.get(
            BigBasket.menu_url,
            headers=self.api_headers
        )
        response_data = r_menu.json()['response']
        category_section = response_data['section_info']['sections'][0]
        category_dicts = category_section['items']
        self.parent_categories = [
            category['sub_items'][1]
            for category in category_dicts
        ]

    def __init__(self, *args, **kwargs):
        self._get_auth_headers()
        self._get_category_slugs()
        self.dbcursor = BigBasket.db_conn.cursor()

    def scrape_category(self, category_dict):
        category_slug = category_dict['destination']['dest_slug']
        product_page = requests.get(
            BigBasket.product_url.format(
                dest_slug=category_slug,
                page=1
            ),
            headers=self.api_headers
        ).json()
        product_tab = product_page['response']['tab_info'][0]
        page_count = product_tab['product_info']['p_count']

        for page in range(0, page_count + 1):
            self.get_product_page(
                category_slug,
                page
            )

    def get_product_page(self, category_slug, page):
        product_page_response = requests.get(
            BigBasket.product_paginated_url.format(
                dest_slug=category_slug,
                page=page
            ),
            headers=self.api_headers
        ).json()

        product_list = product_page_response['response']['product_map']['all']
        for product_dict in product_list:
            insert_query = """
            INSERT INTO bigbasket_product
            values ({values})
            """.format(
                values=', '.join(
                    map(
                        lambda x: "'{}'".format(x),
                        [str(product_dict['sku']),
                         str(product_dict['p_img_url']),
                         str(product_dict['tlc_s']),
                         str(product_dict['sp']),
                         str(product_dict['mrp']),
                         str(product_dict['p_brand']),
                         str(product_dict['w']),
                         str(product_dict['pc_n']),
                         str(product_dict['tlc_n']),
                         str(product_dict['p_desc'])
                         ]
                    )
                ),
            )
            try:
                self.dbcursor.execute(insert_query)
            except Exception as inst:
                print insert_query
                print "{type}: {message}".format(
                    type=type(inst),
                    message=str(inst)
                )

    def scrape_all_categories(self):
        for category in self.parent_categories:
            self.scrape_category(category)
