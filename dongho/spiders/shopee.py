# -*- coding: utf-8 -*-
import json

import scrapy
from scrapy import Field
from scrapy.loader.processors import TakeFirst


class Brand(scrapy.Item):
    BrandId = Field(output_processor=TakeFirst())
    Name = Field(output_processor=TakeFirst())
    Logo = Field(output_processor=TakeFirst())
    Url = Field(output_processor=TakeFirst())


class ShopeeSpider(scrapy.Spider):
    name = 'shopee'
    allowed_domains = ['shopee.vn']
    custom_settings = {
        'FEED_FORMAT': 'csv',
        'FEED_URI': './data/' + name + '.csv'
    }

    def start_requests(self):
        yield scrapy.Request(
            url='https://shopee.vn/api/v2/brand_lists/get',
            callback=self.parse,
            headers={
                'accept': 'application/json',
                'content-type': 'application/json',
                'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_4) AppleWebKit/537.36 (KHTML, like Gecko) '
                              'Chrome/81.0.4044.122 Safari/537.36 '
            }
        )

    def parse(self, response):
        res = json.loads(response.body)

        brand = Brand()

        for key, item in res['data'].items():
            brand['BrandId'] = item['shopid']
            brand['Name'] = item['brand_name']
            brand['Logo'] = 'https://cf.shopee.vn/file/' + item['logo']
            brand['Url'] = 'https://shopee.vn/' + item['username']

            yield brand
