# -*- coding: utf-8 -*-
import scrapy
from scrapy import Field
from scrapy.loader import ItemLoader
from scrapy.loader.processors import TakeFirst


class Product(scrapy.Item):
    Url = Field(output_processor=TakeFirst())
    Title = Field(output_processor=TakeFirst())
    Price = Field(output_processor=TakeFirst())
    PriceSale = Field(output_processor=TakeFirst())
    Images = Field()


class DangquangwatchSpider(scrapy.Spider):
    name = 'dangquangwatch'
    allowed_domains = ['www.dangquangwatch.vn']
    custom_settings = {
        'FEED_FORMAT': 'csv',
        'FEED_URI': './data/' + name + '.csv',
    }
    HEADER = {
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.122 Safari/537.36'
    }

    start_urls = [
            'https://www.dangquangwatch.vn/sp/dong-ho-chinh-hang.html',
            'https://www.dangquangwatch.vn/sp/dong-ho-philippe-auguste.html',
            'https://www.dangquangwatch.vn/sp/dong-ho-epos-swiss.html',
            'https://www.dangquangwatch.vn/sp/dong-ho-atlantic-swiss.html',
            'https://www.dangquangwatch.vn/sp/dong-ho-diamond-d.html',
            'https://www.dangquangwatch.vn/sp/dong-ho-aries-gold.html',
            'https://www.dangquangwatch.vn/sp/dong-ho-jacques-lemans.html',
            'https://www.dangquangwatch.vn/sp/dong-ho-qq.html',
            'https://www.dangquangwatch.vn/sp/bruno-sohnle-glashutte.html',
            'https://www.dangquangwatch.vn/sp/jacques-du-manoir.html',
            'https://www.dangquangwatch.vn/sp/dong-ho-citizen.html',
            'https://www.dangquangwatch.vn/sp/tourbillon-memorigin.html',
            'https://www.dangquangwatch.vn/sp/stuhrling-original-swiss.html',
            'https://www.dangquangwatch.vn/sp/stuhrling-tourbillon.html',
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
        urls = response.xpath('//*[@id="product"]/div[@class="colright"]/div[@class="group"]//div['
                              '@class="wImage"]/a/@href')
        for url in urls:
            yield scrapy.Request(
                url=response.urljoin(url.get()),
                callback=self.parse_product,
                headers=self.HEADER,
                dont_filter=True
            )

        next_page = response.xpath('//*[@id="product"]/div[2]/nav/span/span['
                                   '@class="span_select_class"]/following::span[@class="span_a_class"][1]/a/@href').get()

        if next_page:
            yield scrapy.Request(
                url=response.urljoin(next_page),
                callback=self.parse,
                headers=self.HEADER
            )

    def parse_product(self, response):
        product = Product()
        loader = ItemLoader(item=product)
        loader.add_value('Url', response.url)
        loader.add_value('Title', response.css('.namePro::text').extract_first())
        loader.add_value('Images', [
            img.get() for img in response.xpath('//*[@id="product"]/div[2]/div[1]/div[1]/div/a/img/@data-lazy')
        ])
        loader.add_value('Price', response.css('.priceNew::text').extract_first())
        loader.add_value('PriceSale', response.xpath('//*[@class="btnCart"][1]//span[2]/b/text()').extract_first())

        thong_so_ky_thuat = response.xpath('//*[@id="product"]/div[2]/div[2]/div/div[1]/div[5]/div/div[@class="item"]')
        for item in thong_so_ky_thuat:
            key = item.css('.text1::text').extract_first()
            value = item.css('.text2::text').extract_first()
            if key not in product:
                product.fields[key] = Field(output_processor=TakeFirst())
            loader.add_value(key, value)

        yield loader.load_item()
