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


class SendoSpider(scrapy.Spider):
    name = 'sendo'
    allowed_domains = ['www.sendo.vn/thuong-hieu']
    endpoint = 'https://api.sendo.vn/onsite-services/brand/list/home'
    page = 1
    offset = 24
    custom_settings = {
        'FEED_FORMAT': 'csv',
        'FEED_URI': './data/' + name + '.csv'
    }

    def start_requests(self):
        yield scrapy.Request(
            url=self.endpoint + '?p=' + str(self.page) + '&s=' + str(self.offset),
            callback=self.parse,
            headers={
                'accept': 'application/json',
                'content-type': 'application/json',
                'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_4) AppleWebKit/537.36 (KHTML, like Gecko) '
                              'Chrome/81.0.4044.122 Safari/537.36 '
            },
            dont_filter=True
        )

    def parse(self, response):
        res = json.loads(response.body)

        if res['message'] != 'Successful' or not res['data']['brands_list']:
            return None

        brand = Brand()

        for item in res['data']['brands_list']:
            brand['BrandId'] = item['brand_id']
            brand['Name'] = item['name']
            brand['Logo'] = item['logo']
            brand['Url'] = 'https://www.sendo.vn' + item['url']

            yield brand

        self.page += 1

        yield scrapy.Request(
            url=self.endpoint + '?p=' + str(self.page) + '&s=' + str(self.offset),
            callback=self.parse,
            headers={
                'accept': 'application/json',
                'content-type': 'application/json',
                'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_4) AppleWebKit/537.36 (KHTML, like Gecko) '
                              'Chrome/81.0.4044.122 Safari/537.36 '
            },
            dont_filter=True
        )
