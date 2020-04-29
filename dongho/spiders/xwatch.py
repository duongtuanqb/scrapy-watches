# -*- coding: utf-8 -*-
import scrapy
from scrapy import Field
from scrapy.loader import ItemLoader
from scrapy.loader.processors import TakeFirst
from scrapy.spiders import XMLFeedSpider


class Product(scrapy.Item):
    Url = Field(output_processor=TakeFirst())
    Title = Field(output_processor=TakeFirst())
    Price = Field(output_processor=TakeFirst())
    PriceSale = Field(output_processor=TakeFirst())
    Images = Field()


class XwatchSpider(XMLFeedSpider):
    name = 'xwatch'
    allowed_domains = ['xwatch.vn']
    custom_settings = {
        'FEED_FORMAT': 'csv',
        'FEED_URI': './data/' + name + '.csv'
    }

    start_urls = ['https://xwatch.vn/sitemap_product.xml']
    iterator = 'xml'  # you can change this; see the docs
    itertag = 'n:loc'  # change it accordingly
    namespaces = [('n', 'http://www.sitemaps.org/schemas/sitemap/0.9')]

    def parse_node(self, response, selector):
        yield scrapy.Request(
            url=selector.xpath('text()').get(),
            callback=self.parse_product,
        )

    def parse_product(self, response):
        product = Product()
        loader = ItemLoader(item=product)
        loader.add_value('Url', response.url)
        loader.add_value('Title', response.xpath('//*[@class="product_name"]/h1/text()').get().strip())
        loader.add_value('Price', response.xpath('//*[@class="price"]/h3[1]/text()').get().strip())
        loader.add_value('PriceSale', response.xpath('//*[@class="price"]/h3[2]/text()').get().strip())

        images = response.xpath('//*[@class="frame_left"]//img[@class="img-responsive"]/@src').getall()
        images = images + [img.get() for img in response.xpath('//*[@class="thumbs"]//*[@class="item"]//img/@longdesc')]
        loader.add_value('Images', images)

        thong_so = response.xpath('//*[@class="bottom-detail-r"]//table//tr')
        for item in thong_so:
            key = item.xpath('./*[@class="title_charactestic"]/text()').get().strip()[:-1]
            value = item.xpath('./*[@class="content_charactestic"]/text()').get().strip()
            if key not in product:
                product.fields[key] = Field(output_processor=TakeFirst())
            loader.add_value(key, value)

        return loader.load_item()
