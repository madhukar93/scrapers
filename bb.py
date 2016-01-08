import requests
import json
import sqlite3
from rq import Queue
from redis import Redis
from unidecode import unidecode
import logging
requests.packages.urllib3.disable_warnings()

logger = logging.getLogger('bigbasket')
logger.setLevel(logging.ERROR)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh = logging.FileHandler('errors.log')
fh.setFormatter(formatter)
logger.addHandler(fh)


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
        page_count = product_tab['product_info']['tot_pages']
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
            try:
                insert_query = "INSERT INTO bigbasket_product values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, )"

                print unidecode(str(product_dict['p_desc']))
                # print insert_query
                self.dbcursor.execute(
                    insert_query,
                    (
                        unidecode(str(product_dict['sku'])),
                        unidecode(str(product_dict['p_img_url'])),
                        unidecode(str(product_dict['tlc_s'])),
                        unidecode(str(product_dict['sp'])),
                        unidecode(str(product_dict['mrp'])),
                        unidecode(str(product_dict['p_brand'])),
                        unidecode(str(product_dict['w'])),
                        unidecode(str(product_dict['pc_n'])),
                        unidecode(str(product_dict['tlc_n'])),
                        unidecode(str(product_dict['p_desc'])),
                    )
                )
                BigBasket.db_conn.commit()
            except Exception as inst:
                logger.error(
                    "{type}: {message}: {dict}\n\t=====\n".format(
                        type=type(inst),
                        message=str(inst),
                        dict=str(product_dict)
                    )
                )

    def scrape_all_categories(self):
        for category in self.parent_categories:
            self.scrape_category(category)
