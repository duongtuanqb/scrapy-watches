# -*- coding: utf-8 -*-
import string

import scrapy
from scrapy import Field
from scrapy.loader.processors import TakeFirst


class Brand(scrapy.Item):
    Name = Field(output_processor=TakeFirst())
    URL = Field(output_processor=TakeFirst())
    Thumbnail = Field(output_processor=TakeFirst())


class AblogtowatchSpider(scrapy.Spider):
    name = 'ablogtowatch'
    allowed_domains = ['www.ablogtowatch.com']
    HEADER = {
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_4) AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/81.0.4044.122 Safari/537.36 '
    }
    custom_settings = {
        'FEED_FORMAT': 'csv',
        'FEED_URI': './data/' + name + '.csv'
    }

    def start_requests(self):
        url = 'https://www.ablogtowatch.com/watch-brands/?pg=1&letter='
        alphabet = list(string.ascii_uppercase)
        for _chr in alphabet:
            yield scrapy.Request(
                url=url+_chr,
                callback=self.parse,
                headers=self.HEADER,
                dont_filter=True
            )

    def parse(self, response):
        brand = Brand()
        wrapper = response.xpath('//*[contains(@class, "page-content")]//div[contains(@class, "searchedBoxSec")]//ul['
                                 'contains(@class, "brndWtchList")]/li')

        for item in wrapper:
            brand['Name'] = item.xpath('.//*[@class="brndWtchName"]/text()').get()
            brand['URL'] = item.xpath('.//a/@href').get()
            brand['Thumbnail'] = item.xpath('.//a/img/@src').get()
            yield brand

        next_page = response.xpath('//*[@class="pagination"]//a[contains(@class, "next")]/@href').get()

        if not next_page:
            return None

        yield scrapy.Request(
            url=next_page,
            callback=self.parse,
            headers=self.HEADER,
            dont_filter=True
        )