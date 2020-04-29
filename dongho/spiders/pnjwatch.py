# -*- coding: utf-8 -*-
import json

import scrapy
from scrapy import Field
from scrapy.loader import ItemLoader
from scrapy.loader.processors import TakeFirst, MapCompose, SelectJmes


class Product(scrapy.Item):
    Url = Field(output_processor=TakeFirst())
    Title = Field(output_processor=TakeFirst())
    Price = Field(output_processor=TakeFirst())
    PriceSell = Field(output_processor=TakeFirst())
    SKU = Field(output_processor=TakeFirst())
    Images = Field(
        output_processor=MapCompose(SelectJmes('content'))
    )


class PnjwatchSpider(scrapy.Spider):
    name = 'pnjwatch'
    custom_settings = {
        'FEED_FORMAT': 'csv',
        'FEED_URI': './data/' + name + '.csv',
        'DOWNLOAD_DELAY': 1
    }

    fromIndex = 0

    product_urls = []

    def start_requests(self):
        url = 'https://api.pnjwatch.com.vn/api/product/getproductlist'
        yield scrapy.Request(
            url=url,
            callback=self.parse,
            method='POST',
            headers={
                'accept': 'application/json',
                'content-type': 'application/json',
                'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_4) AppleWebKit/537.36 (KHTML, like Gecko) '
                              'Chrome/81.0.4044.122 Safari/537.36 '
            },
            body=json.dumps(
                {
                    "pagination": {
                        "fromIndex": self.fromIndex, "pageSize": 24
                    },
                    "productType": 0,
                    "searchCriteria": [],
                    "sortCriteria": [
                        {
                            "key": 0,
                            "descending": True
                        }
                    ]
                }
            )
        )

    def parse(self, response):
        res = json.loads(response.body)
        if not isinstance(res, dict) or len(res) < 1:
            return None

        if len(res['result']) == 0:
            for url in self.product_urls:
                yield scrapy.Request(
                    url=url,
                    callback=self.parse_item
                )

        self.fromIndex += len(res['result'])

        for item in res['result']:
            self.product_urls.append('https://api.pnjwatch.com.vn/api/product/' + item['seoUrl'])

        yield scrapy.Request(
            url=response.url,
            callback=self.parse,
            method='POST',
            headers={
                'accept': 'application/json',
                'content-type': 'application/json',
                'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_4) AppleWebKit/537.36 (KHTML, '
                              'like Gecko) '
                              'Chrome/81.0.4044.122 Safari/537.36 '
            },
            body=json.dumps({"pagination": {"fromIndex": self.fromIndex, "pageSize": 24}})
        )

    @staticmethod
    def parse_item(response):
        res = json.loads(response.body)
        if not isinstance(res, dict) or len(res) < 1:
            return None
        data = res['data']
        product = Product()
        loader = ItemLoader(item=product)
        loader.add_value('Url', "https://pnjwatch.com.vn/san-pham/" + data['seoUrl'])
        loader.add_value('Title', data['title'])
        loader.add_value('Price', data['price'])
        loader.add_value('PriceSell', data['priceSell'])
        loader.add_value('SKU', data['sku'])
        loader.add_value('Images', data['images'])

        for key, item in data['subFilters'].items():
            if key not in product:
                product.fields[key] = Field(output_processor=TakeFirst())
            loader.add_value(key, item[0]['value'] if len(item) > 0 else "")

        for key, item in data['technicalSpecification'].items():
            if key not in product:
                product.fields[key] = Field(output_processor=TakeFirst())
            loader.add_value(key, item['value'])

        return loader.load_item()
