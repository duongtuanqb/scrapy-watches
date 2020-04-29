# -*- coding: utf-8 -*-
import json
import re
from scrapy import Item, Field
from scrapy.http import HtmlResponse
from scrapy.linkextractors import LinkExtractor
from scrapy.loader import ItemLoader
from scrapy.loader.processors import TakeFirst, Compose, Join
from scrapy.spiders import CrawlSpider, Rule


class Article(Item):
    title = Field(output_processor=TakeFirst())
    publish_date = Field(output_processor=TakeFirst())
    content = Field(
        output_processor=Compose(lambda v: filter(None, v), Join(''))
    )
    image_urls = Field()
    links = Field()


def process_value(value):
    match = re.search(r'\d+/\d+/\d+/(.+)/', value)
    if not match:
        return None

    slug = match.group(1)
    api_pattern = 'https://techcrunch.com/wp-json/wp/v2/posts?slug={}'
    return api_pattern.format(slug)


class TechcrunchSpider(CrawlSpider):
    name = 'techcrunch'
    allowed_domains = ['techcrunch.com']
    start_urls = ['http://techcrunch.com/']

    rules = (
        Rule(
            LinkExtractor(
                allow_domains=allowed_domains,
                process_value=process_value
            ),
            callback='parse_item'
        ),
    )

    def parse_item(self, response):
        json_res = json.loads(response.body)
        if not isinstance(json_res, list) or len(json_res) < 1:
            return None

        data = json_res[0]
        content = HtmlResponse(
            response.url,
            body=bytes(data['content']['rendered'], 'utf-8')
        )
        loader = ItemLoader(item=Article(), response=content)
        loader.add_value('title', data['title']['rendered'])
        loader.add_value('publish_date', data['date_gmt'])

        loader.add_css('content', '*::text')
        loader.add_css('image_urls', 'img::attr(src)')
        loader.add_css('links', 'a::attr(href)')
        return loader.load_item()
