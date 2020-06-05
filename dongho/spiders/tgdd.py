# -*- coding: utf-8 -*-
import json
import re

import scrapy
from scrapy import Field, Selector
from scrapy.loader import ItemLoader
from scrapy.loader.processors import TakeFirst


class Product(scrapy.Item):
    Url = Field(output_processor=TakeFirst())
    Title = Field(output_processor=TakeFirst())
    Price = Field(output_processor=TakeFirst())
    PriceSale = Field(output_processor=TakeFirst())
    Images = Field()
    ImagesDemo = Field()


class TgddSpider(scrapy.Spider):
    name = 'tgdd'
    allowed_domains = ['www.thegioididong.com']
    HEADER = {
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_4) AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/81.0.4044.122 Safari/537.36 '
    }
    custom_settings = {
        'ITEM_PIPELINES': {
           'dongho.pipelines.TgddExcelPipeline': 300,
        }
    }

    start_urls = [
        'https://www.thegioididong.com/dong-ho-thong-minh',
        'https://www.thegioididong.com/dong-ho-deo-tay-nam',
        'https://www.thegioididong.com/dong-ho-deo-tay-nu',
        'https://www.thegioididong.com/dong-ho-deo-tay-cap-doi',
        'https://www.thegioididong.com/dong-ho-deo-tay-tre-em'
    ]

    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(
                url=url,
                callback=self.parse,
                headers=self.HEADER,
                dont_filter=True
            )

    def parse(self, response):
        if response.css('.emptystate').get():
            return None

        for url in response.xpath('//*[contains(@class,"homeproduct")]/li/a/@href'):
            yield scrapy.Request(
                url=response.urljoin(url.get()),
                callback=self.parse_product,
                headers=self.HEADER,
                dont_filter=True
            )

        if not response.meta.get('query'):
            query_raw = response.xpath('//script[contains(., "var query")]/text()').re(
                re.compile(r"{(.*?)}", re.MULTILINE | re.DOTALL)
            )[0]

            query = {}
            for i in ' '.join(query_raw.split()).split(','):
                item = i.split(':')
                query[item[0].strip()] = item[1].strip()
        else:
            query = response.meta['query']

        query['PageIndex'] = str(int(query['PageIndex']) + 1)

        yield scrapy.FormRequest(
            url="https://www.thegioididong.com/aj/CategoryV5/Product",
            method="POST",
            headers=self.HEADER,
            callback=self.parse,
            formdata=query,
            meta={'query': query},
            dont_filter=True
        )

    def parse_product(self, response):
        product = Product()
        loader = ItemLoader(item=product)

        loader.add_value('Url', response.url)
        loader.add_value('Title', response.xpath('//script[contains(., "var PAGE_TYPE")]/text()').re(
            re.compile(r"var PAGE_TYPE = '(.*?)';", re.MULTILINE | re.DOTALL)
        )[0] or "")
        loader.add_value('PriceSale', response.css('.area_price strong::text').get())
        loader.add_value('Price', response.css('.area_price .hisprice::text').get())
        loader.add_value('Images', [
            response.urljoin(img.get()) for img in response.xpath('//div[contains(@class, '
                                                                  '"colorandpic")]//li//img/@data-img | '
                                                                  '//*[contains(@class, "picture")]//img/@src')
        ])
        loader.add_value('ImagesDemo', [
            response.urljoin(img.get()) for img in response.xpath('//div[contains(@class, '
                                                                  '"boximgHighlight")]//img/@data-original')
        ])

        getFullSpec = response.css('.viewparameterfull::attr(onclick)').re(
            re.compile(r"getFullSpec\(([^,]*)[,]?(.*)[,]?\)"))
        product_id = getFullSpec[0] or ""

        if product_id:
            query_attr = {'productID': product_id}
            if getFullSpec[1] is not None:
                yield scrapy.FormRequest(
                    url='https://www.thegioididong.com/aj/ProductV4/GetFullSpec_DMX/',
                    method='POST',
                    headers=self.HEADER,
                    formdata=query_attr,
                    callback=self.parse_attribute,
                    meta={'loader': loader},
                    dont_filter=True
                )
            else:
                yield scrapy.FormRequest(
                    url='https://www.thegioididong.com/aj/ProductV4/GetFullSpec/',
                    method='POST',
                    headers=self.HEADER,
                    formdata=query_attr,
                    callback=self.parse_attribute,
                    meta={'loader': loader},
                    dont_filter=True
                )
        else:
            yield loader.load_item()

    @staticmethod
    def parse_attribute(response):
        loader = response.meta['loader']
        product = loader.load_item()
        to_html = Selector(text=json.loads(response.body)['spec'])

        for attr in to_html.xpath('//li'):
            key = attr.xpath('.//span//text()').get()
            value = attr.xpath('.//div//text()').get()
            product.fields[key] = Field(output_processor=TakeFirst())
            loader.add_value(key, value)

        yield loader.load_item()
