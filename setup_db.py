import sqlite3

conn = sqlite3.connect('competitor_inventory_test1.db')
c = conn.cursor()

# "sku": 10000019,
# "p_img_url": "10000019_16-fresho-baby-corn-unpeeled.jpg",
# "tlc_s": "fruits-vegetables",
# "dis_val": "10",
# "sp": "32.40",
# "mrp": "36.00",
# "p_brand": "Fresho",
# "store_ids": [],
# "dis_t": "P",
# "w": "1 kg",
# "pc_n": "Exotic Vegetables",
# "tlc_n": "Fruits & Vegetables",
# "p_promo_info": {},
# "p_desc": "Baby Corn - Unpeeled"

c.execute(
    '''CREATE TABLE bigbasket_product
       (
            sku text PRIMARY KEY,
            p_img_url text,
            tlc_s text,
            sp real,
            mrp real,
            p_brand text,
            w text,
            pc_n text,
            tlc_n text,
            p_desc text
        )
    '''
)
