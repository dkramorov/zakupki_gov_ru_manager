import logging
import os
import re
import requests
import xml.etree.ElementTree as ET

from managers.simple_logger import json_pretty_print, logger
from .fz44 import FZ44
from .fz223 import FZ223


rega_inn = re.compile('<div class="registry-entry__body-title">ИНН</div>.+?<div class="registry-entry__body-value">([0-9]+)</div>', re.I+re.U+re.DOTALL)
rega_short_name = re.compile('<span class="section__title">Сокращенное наименование</span>.+?<span class="section__info">([^<]+)</span>', re.I+re.U+re.DOTALL)
rega_print_link = re.compile('<a[^>]+?href="([^\"]+)"[^>]+?>[^<]+?<img[^>]+?src="/epz/static/img/icons/icon_print_small.svg"', re.I+re.U+re.DOTALL)


class ZakupkiGovRuManager:
    """zakupki.gov.ru менеджер
{
  "auctionNumber": "string",
  "auctionLink": "string",
  "code": "string",
  "name": "string",
  "federalLaw": "string",
  "lotsCount": 0,
  "amount": 0,
  "guaranteeAmount": 0,
  "guaranteeExecutionAmount": 0,
  "guaranteeWarrantyAmount": 0,
  "advance": 0,
  "executionPeriod": "string",
  "executionDates": {
    "from": "string",
    "to": "string"
  },
  "endOrderDateAt": "string",
  "tradingPlatform": {
    "name": "string",
    "url": "string"
  },
  "customer": {
    "fullName": "string",
    "shortName": "string",
    "url": "string",
    "mailAddress": "string",
    "location": "string",
    "responsible": "string",
    "email": "string",
    "phone": "string",
    "region": "string",
    "registrationDate": "string",
    "inn": "string",
    "iku": "string",
    "ikuDate": "string"
  },
  "lots": [
    {
      "number": 0,
      "planingStart": "string",
      "planingEnd": "string",
      "name": "string",
      "description": "string",
      "lotAmountType": "string",
      "lotAmount": "string",
      "lotAmountDescription": "string",
      "lotGuaranteeAmount": "string",
      "lotGuaranteeDescription": "string",
      "lotGuaranteeExecutionAmount": "string",
      "lotGuaranteeExecutionDescription": "string",
      "addressSubject": "string",
      "address": "string",
      "isOnlyForSmallMediumBusiness": true
    }
  ]
}
    """
    domain = 'https://zakupki.gov.ru'
    user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:147.0) Gecko/20100101 Firefox/147.0'

    def __init__(self):
        self.fz = FZ44()
        self.auction_link = None
        self.common_page = None
        self.print_page = None
        self.print_link = None

    @property
    def headers(self):
        """Заголовки для запросов"""
        return {
            'User-Agent': self.user_agent,
        }

    def do_request(self, url):
        for i in range(3):
            logger.info('request: %s' % url)
            try:
                r = requests.get(url, headers=self.headers, timeout=(1, 3))
                logger.info('response: %s' % r.status_code)
                if r.status_code in (200, 201):
                    return r.text
                if str(r.status_code)[0] == '4': # 4xx
                    logger.info('response text: %s' % r.text)
                    return
            except Exception as e:
                logger.info('[ERROR]: %s' % e)

    def get_print_page(self):
        """Получение странички для печати
        """
        search_print_link = rega_print_link.search(self.common_page)
        if search_print_link:
            self.print_link = search_print_link[1]
            if not self.print_link.startswith('https://'):
                self.print_link = '%s%s' % (self.domain, self.print_link)
            search_print_page = self.do_request(url=self.print_link)
            if search_print_page:
                self.print_page = search_print_page

    def get_by_number(self, number: str):
        """Получение заявки по номеру
           :param number: номер заявки
        """
        self.auction_link = '%s/epz/order/notice/zk20/view/common-info.html?regNumber=%s' % (
            self.domain,
            number,
        )

        for i in range(3):
            url = self.fz.url % (
                self.domain,
                number,
            )
            logger.info('request: %s' % url)
            try:
                r = requests.get(url, headers=self.headers, timeout=(1, 3))
                logger.info('response: %s' % r.status_code)
                if r.status_code in (200, 201):
                    self.common_page = r.text
                    self.get_print_page()
                    break
                if r.status_code == 404:
                    self.fz = FZ223()
                    continue
                if str(r.status_code)[0] == '4': # 4xx
                    break
            except Exception as e:
                logger.info('[ERROR]: %s' % e)
        if self.print_page:
            # Находим тело документа
            body = self.find_body(text=self.print_page)
            if body:
                body_html = self.str2html(text=body)
                self.find_data(body_html=body_html)
                self.fill_result()
            else:
                logger.info('[ERROR]: body is absent')
        else:
            logger.info('[ERROR]: text is absent')

    def str2html(self, text: str):
        """Преобразовать в html
           :param text: текст, который переводим в html
        """
        if not text:
            logger.info('[ERROR]: text absent')
            return
        html = ET.fromstring(text)
        return html

    def find_body(self, text: str):
        """Найти тело документа
           :param text: текст, в котором ищем <body></body>
        """
        if not text:
            logger.info('[ERROR]: text absent')
            return
        return self.fz.find_body(text)

    def html2str(self, el):
        """Перевести html обратно в строку
           :param el: элемент ElementTree
        """
        if not el:
            logger.info('[ERROR]: el absent')
            return
        return ET.tostring(el, encoding='utf-8').decode('utf-8')

    def find_data(self, body_html):
        if not body_html:
            logger.info('[ERROR]: body_html absent')
            return
        self.fz.find_data(body_html=body_html)

    def fill_result(self):
        """По полученным данным заполнить результат
           данные по заказчику, например, ИНН придется искать по организации,
           а ссылку на организацию берем из auction_link
        """
        self.fz.fill_result()
        self.fz.result['auction_link'] = self.auction_link
        if not self.common_page:
            return

        # Поиск информации о заказчике
        # <a href="https://zakupki.gov.ru/epz/organization/view/info.html?organizationId=803457"...></a>
        search_org_link = self.fz.rega_org_id.search(self.common_page)
        if search_org_link:
            org_link = '%s%s' % (self.domain, search_org_link[0]) # в search_org_id[1] ид организации
            self.fz.result['customer']['url'] = org_link
            text = self.do_request(url=org_link)
            search_inn = rega_inn.search(text)
            if search_inn:
                inn = search_inn[1]
                self.fz.result['customer']['inn'] = inn
            if not self.fz.result['customer'].get('short_name'):
                search_short_name = rega_short_name.search(text)
                if search_short_name:
                    short_name = search_short_name[1]
                    self.fz.result['customer']['short_name'] = short_name
