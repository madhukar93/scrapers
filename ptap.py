import requests
import json
import sqlite3
from rq import Queue
from redis import Redis
from unidecode import unidecode
import logging
requests.packages.urllib3.disable_warnings()
logger = logging.getLogger('ptap')
logger.setLevel(logging.ERROR)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh = logging.FileHandler('ptap_errors.log')
fh.setFormatter(formatter)
logger.addHandler(fh)


class PepperTap:
    base_url = "https://api.peppertap.com"
    # should be imported from database connection file
    db_conn = sqlite3.connect('competitor_inventory_test1.db')

    def _get_cities(self):
        cities_url = "/location/v1/cities/"
        response = requests.get(
            PepperTap.base_url + cities_url,
            verify=False
        )
        self.cities = [
            {'id': city['id'], 'name': city['name']}
            for city in response.json()
        ]

    def _get_areas(self):
        zones_url = "/location/v1/areas/"
        response = requests.get(
            PepperTap.base_url + zones_url,
            verify=False
        )
        self.areas = response.json()

    def _write_zones(self):
        zones = {}
        for area in self.areas:
            try:
                zones[area['zone_id']]['city'] = area['city'],
                zones['areas'].append(area['area'])
            except KeyError:
                zones[area['zone_id']] = {
                    'city': area['city'],
                    'areas' = [area['area']]
                }
        for zone_id, values in zones.iteritems():
            self._insert_zone(
                (
                    zone_id,
                    values['area'],
                    values['city'],
                )
            )

    def _insert_zone(self, values):
        insert_query = "insert into peppertap_zone (?, ?, ?, ?)"
        self.db_cursor.execute(
            insert_query,
            values
        )

    def _insert_product(self, values):
        insert_query = "insert into peppertap_product (?, ?, ?, ?, ?, ?, ?)"
        self.db_cursor.execute(
            insert_query,
            values
        )

    def _insert_product_zone_mapping(self, values):
        insert_query = "insert into peppertap_zone_product_map (?, ?)"
        self.db_cursor.execute(
            insert_query,
            values
        )

    def _get_categories(self, zone_id):
        categories_url = "/user/shop/categories/"
        response = requests.get(
            PepperTap.base_url + categories_url,
            params={'zone_id': zone_id},
            verify=False
        )
        return response.json()['categories']

    def __init__(self, args, kwargs):
        try:
            import setup_db_ptap
        except:
            pass
        self._get_zones()
        self.db_cursor = PepperTap.db_conn.cursor()

    def get_products_by_category(self, category_dict, zone_dict):
        products_url = "/user/shop/{cid}/products/"
        params = {'zone_id': zone['zone_id']}
        response = requests.get(
            PepperTap.base_url + products_url.format(
                cid=category_id
            ),
            params=params
        )
        products = response.json()['pl']
        for product in products:
            insert_product(
                (
                    product['ps']['uid'],
                    product['ps']['sp'],
                    product['ps']['mrp'],
                    product['tle'],
                    ", ".join(product['typ']),
                    category['name'],
                    product['ps']['da'],
                )
            )

    def get_products_by_zone(self, zone_id):
        categories = self._get_categories_by_zone(zone_id)
        for category in categories:
            for child in category['children']:
                # should be pushing this to the task queue
                pass
