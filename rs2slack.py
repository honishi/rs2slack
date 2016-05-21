#!/usr/bin/env python
# -*- coding: utf-8 -*-

import configparser
import logging
import logging.config
import time
import urllib.parse

import lxml.html
import redis
import requests
from slackclient import SlackClient


CONFIG_FILE = "rs2slack.config"
REALTIME_PREFIX = "http://realtime.search.yahoo.co.jp/search?p="
REALTIME_SUFFIX = "&ei=UTF-8"
XPATH_TWEET = "//*[@id=\"TSm\"]/div/div/p[1]/a[2]"
CRAWL_INTERVAL = 60
REDIS_HASH_NAME = "tweet-history"


class RealtimeSearchToSlack(object):

    # magic methods
    def __init__(self):
        logging.config.fileConfig(CONFIG_FILE)

        cp = configparser.ConfigParser()
        cp.read(CONFIG_FILE)

        section = "rs2slack"
        self.keyword = cp.get(section, "keyword")
        self.redis_host = cp.get(section, "redis_host")
        self.redis_port = cp.getint(section, "redis_port")
        self.redis_db = cp.getint(section, "redis_db")
        self.slack_token = cp.get(section, "slack_token")
        self.slack_channel_id = cp.get(section, "slack_channel_id")

        logging.debug("keyword:{0}".format(self.keyword))
        logging.debug("redis_host:{0}".format(self.redis_host))
        logging.debug("redis_port:{0}".format(self.redis_port))
        logging.debug("redis_db:{0}".format(self.redis_db))
        logging.debug("slack_token:{0}".format(self.slack_token))
        logging.debug("slack_channel_id:{0}".format(self.slack_channel_id))

    # public methods
    def start(self):
        first_run = True

        while True:
            try:
                logging.debug("start crawling...")
                urls = self.crawl_yahoo_realtime()
                logging.debug("crawled {0} tweets.".format(len(urls)))

                if first_run:
                    self.update_tweet_history(urls)
                    first_run = False

                for url in urls:
                    if self.should_post(url):
                        self.post_slack(self.slack_token, self.slack_channel_id, url)
                        logging.debug("posted: {0}".format(url))
                        time.sleep(5)
                    self.update_tweet_history(url)
            except Exception as e:
                # XXX: ignores all exceptions for now
                logging.error(e)
            finally:
                logging.debug("waiting for next crawl...")
                time.sleep(CRAWL_INTERVAL)

    # private methods
    def crawl_yahoo_realtime(self):
        url = REALTIME_PREFIX + urllib.parse.quote_plus(self.keyword) + REALTIME_SUFFIX
        logging.debug(url)
        request = requests.get(url)
        if request.status_code != 200:
            return []

        dom = lxml.html.fromstring(request.content)
        elements = dom.xpath(XPATH_TWEET)

        return [element.get('href') for element in elements]

    def should_post(self, url):
        return not self.redis_client().hexists(REDIS_HASH_NAME, url)

    def update_tweet_history(self, url):
        if isinstance(url, list):
            urls = url
        else:
            urls = [url]

        redis = self.redis_client()

        for u in urls:
            redis.hset(REDIS_HASH_NAME, u, 1)

    def redis_client(self):
        return redis.Redis(host=self.redis_host, port=self.redis_port, db=self.redis_db)

    def post_slack(self, token, channel, url):
        sc = SlackClient(token)
        res = sc.api_call("chat.postMessage", channel=channel, text=url)


RealtimeSearchToSlack().start()
