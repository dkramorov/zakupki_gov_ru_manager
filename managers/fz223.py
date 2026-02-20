import html
import re
from managers.simple_logger import json_pretty_print, logger


rega_body_xml = re.compile('(&lt;ns2:purchaseNotice[EP]?(.+)&lt;/ns2:purchaseNotice[EP]?&gt;)', re.I+re.U+re.DOTALL)


class FZ223:
    fz_id = 223
    name = '223-ФЗ'
    # не всегда страничка для печати с таким адресом
    #url = '%s/223/purchase/public/print-form/show.html?pfid=%s'
    url = '%s/epz/order/notice/notice223/common-info.html?regNumber=%s'
    rega_org_id = re.compile("/epz/organization/view223/info.html.agencyId=([0-9]+)", re.I+re.U+re.DOTALL)

    def __init__(self):
        self.data = {}
        self.result = {}

    def find_body(self, text: str):
        """Найти тело документа 223ФЗ
           :param text: текст, в котором ищем <body></body>
        """
        body = rega_body_xml.search(text)
        if body:
            body = html.unescape(body[0])
            #logger.info(body)
            return body

    def find_data_in_customer(self, el, key: str = 'customer'):
        """Вспомогательный метод для поиска данных в элементе типа customer
           :param el: элемент
        """
        items = []
        for sub_el in el:
            if sub_el.tag.endswith('mainInfo'):
                for sub_item in sub_el:
                    items.append(sub_item)
        fill_to = self.data[key]
        for sub_item in items:
            if sub_item.tag.endswith('fullName'):
                fill_to['full_name'] = sub_item.text.strip()
            elif sub_item.tag.endswith('shortName'):
                fill_to['short_name'] = sub_item.text.strip()
            elif sub_item.tag.endswith('ico'):
                fill_to['ico'] = sub_item.text.strip()
            elif sub_item.tag.endswith('inn'):
                fill_to['inn'] = sub_item.text.strip()
            elif sub_item.tag.endswith('ogrn'):
                fill_to['ogrn'] = sub_item.text.strip()
            elif sub_item.tag.endswith('legalAddress'):
                fill_to['legal_address'] = sub_item.text.strip()
            elif sub_item.tag.endswith('postalAddress'):
                fill_to['postal_address'] = sub_item.text.strip()
            elif sub_item.tag.endswith('okato'):
                fill_to['okato'] = sub_item.text.strip()
            elif sub_item.tag.endswith('okopf'):
                fill_to['okopf'] = sub_item.text.strip()
            elif sub_item.tag.endswith('okopfName'):
                fill_to['okopf_name'] = sub_item.text.strip()
            elif sub_item.tag.endswith('okpo'):
                fill_to['okpo'] = sub_item.text.strip()
            elif sub_item.tag.endswith('okfs'):
                fill_to['okfs'] = sub_item.text.strip()
            elif sub_item.tag.endswith('okfsName'):
                fill_to['okfs_name'] = sub_item.text.strip()
            elif sub_item.tag.endswith('timeZone'):
                # offset, name sub elements
                pass
            elif sub_item.tag.endswith('region'):
                fill_to['region'] = sub_item.text.strip()

    def find_data_in_contact(self, el):
        """Вспомогательный метод для поиска данных в элементе customer
           :param el: элемент
        """
        fill_to = self.data['contact']
        for sub_item in el:
            if sub_item.tag.endswith('firstName'):
                fill_to['first_name'] = sub_item.text.strip()
            elif sub_item.tag.endswith('middleName'):
                fill_to['middle_name'] = sub_item.text.strip()
            elif sub_item.tag.endswith('lastName'):
                fill_to['last_name'] = sub_item.text.strip()
            elif sub_item.tag.endswith('phone'):
                fill_to['phone'] = sub_item.text.strip()
            elif sub_item.tag.endswith('email'):
                fill_to['email'] = sub_item.text.strip()

    def find_data_in_trading_platform(self, el):
        """Вспомогательный метод для поиска данных в элементе electronicPlaceInfo
           :param el: элемент
        """
        fill_to = self.data['trading_platform']
        for sub_item in el:
            if sub_item.tag.endswith('name'):
                fill_to['name'] = sub_item.text.strip()
            elif sub_item.tag.endswith('url'):
                fill_to['url'] = sub_item.text.strip()
            elif sub_item.tag.endswith('electronicPlaceId'):
                fill_to['electronicPlaceId'] = sub_item.text.strip()

    def find_data_in_placing_procedure(self, el):
        """Вспомогательный метод для поиска данных в элементе placingProcedure
           :param el: элемент
        """
        fill_to = self.data['placing_procedure']
        for sub_item in el:
            # summingup - подведение итогов
            if sub_item.tag.endswith('summingupDateTime'):
                fill_to['summingup_date_time'] = sub_item.text.strip()
            elif sub_item.tag.endswith('summingupPlace'):
                fill_to['summingup_place'] = sub_item.text.strip()

    def find_data_in_common_el(self, el, fill_to):
        """Вспомогательный метод для поиска данных в типовом элементе с кодом, названием
           :param el: элемент
           :param fill_to: куда дополняем данные
        """
        for sub_el in el:
            if sub_el.tag.endswith('code'):
                fill_to['code'] = sub_el.text.strip()
            elif sub_el.tag.endswith('name'):
                fill_to['name'] = sub_el.text.strip()

    def find_data_in_lot_items(self, el, fill_to):
        """Вспомогательный метод для поиска данных в элементе lot->lotItems
           :param el: элемент
           :param fill_to: куда дополняем данные
        """
        items = []
        for sub_el in el:
            if sub_el.tag.endswith('lotItem'):
                items.append(sub_el)
        for sub_el in items:
            lot_item = {}
            fill_to.append(lot_item)
            for lot_el in sub_el:
                if lot_el.tag.endswith('ordinalNumber'):
                    lot_item['ordinal_number'] = lot_el.text.strip()
                elif lot_el.tag.endswith('okpd2'):
                    lot_item['okpd2'] = {}
                    self.find_data_in_common_el(el=lot_el, fill_to=lot_item['okpd2'])
                elif lot_el.tag.endswith('okved2'):
                    lot_item['okved2'] = {}
                    self.find_data_in_common_el(el=lot_el, fill_to=lot_item['okved2'])
                elif lot_el.tag.endswith('okei'):
                    lot_item['okei'] = {}
                    self.find_data_in_common_el(el=lot_el, fill_to=lot_item['okei'])
                elif lot_el.tag.endswith('qty'):
                    lot_item['qty'] = lot_el.text.strip()

    def find_data_in_lots(self, el):
        """Вспомогательный метод для поиска данных в элементе lots
           :param el: элемент
        """
        items = []
        for sub_el in el:
            if sub_el.tag.endswith('lot'):
                items.append(sub_el)
        for sub_el in items:
            new_lot = {}
            self.data['lots'].append(new_lot)
            fill_to = self.data['lots'][-1]

            for sub_item in sub_el:
                if sub_item.tag.endswith('ordinalNumber'):
                    fill_to['ordinal_number'] = sub_item.text.strip()
                elif sub_item.tag.endswith('lotEditEnabled'):
                    fill_to['lot_edit_enabled'] = sub_item.text.strip()
                elif sub_item.tag.endswith('lotData'):
                    fill_to['lot_data'] = {}
                    for el in sub_item:
                        if el.tag.endswith('subject'):
                            fill_to['lot_data']['subject'] = el.text.strip()
                        elif el.tag.endswith('currency'):
                            fill_to['lot_data']['currency'] = {}
                            for sub_el in el:
                                if sub_el.tag.endswith('code'):
                                    fill_to['lot_data']['currency']['code'] = sub_el.text.strip()
                                elif sub_el.tag.endswith('digitalCode'):
                                    fill_to['lot_data']['currency']['digital_code'] = sub_el.text.strip()
                                elif sub_el.tag.endswith('name'):
                                    fill_to['lot_data']['currency']['name'] = sub_el.text.strip()
                        elif el.tag.endswith('initialSum'):
                            fill_to['initial_sum'] = el.text.strip()
                        elif el.tag.endswith('deliveryPlace'):
                            fill_to['lot_data']['delivery_place'] = {}
                            for sub_el in el:
                                if sub_el.tag.endswith('address'):
                                    fill_to['lot_data']['delivery_place']['address'] = sub_el.text.strip()
                        elif el.tag.endswith('lotItems'):
                            fill_to['lot_data']['lot_items'] = []
                            self.find_data_in_lot_items(el=el, fill_to=fill_to['lot_data']['lot_items'])
                        elif el.tag.endswith('forSmallOrMiddle'):
                            fill_to['for_small_or_middle'] = el.text.strip()

    def find_data(self, body_html):
        """Находим данные по 223ФЗ
        """
        self.data = {
            'main': {},
            'customer': {},
            'placer': {},
            'contact': {},
            'trading_platform': {},
            'placing_procedure': {},
            'lots': [],
        }
        bodies = []
        for el in body_html:
            if el.tag.endswith('body'):
                bodies.append(el)
        for body in bodies:
            items = []
            for el in body:
                if el.tag.endswith('item'):
                    items.append(el)
            for item in items:
                purchases = []
                for el in item:
                    if el.tag.endswith('purchaseNoticeEPData') or el.tag.endswith('purchaseNoticeData'):
                        purchases.append(el)
                
                for purchase in purchases:
                    for el in purchase:
                        print(el.tag, el.text)
                        if el.tag.endswith('registrationNumber'):
                            self.data['main']['registrationNumber'] = el.text.strip()
                        elif el.tag.endswith('name'):
                            self.data['main']['name'] = el.text.strip()
                        elif el.tag.endswith('customer'):
                            self.find_data_in_customer(el=el)
                        elif el.tag.endswith('placer'):
                            self.find_data_in_customer(el=el, key='placer')
                        elif el.tag.endswith('contact'):
                            self.find_data_in_contact(el=el)
                        elif el.tag.endswith('publicationDateTime'):
                            self.data['main']['publication_date_time'] = el.text.strip()
                        elif el.tag.endswith('electronicPlaceInfo'):
                            self.find_data_in_trading_platform(el=el)
                        elif el.tag.endswith('placingProcedure'):
                            self.find_data_in_placing_procedure(el=el)
                        elif el.tag.endswith('submissionCloseDateTime'):
                            self.data['main']['submission_close_date_time'] = el.text.strip()
                        elif el.tag.endswith('publicationPlannedDate'):
                            self.data['main']['publication_planned_date'] = el.text.strip()
                        elif el.tag.endswith('lots'):
                            self.find_data_in_lots(el=el)

    def fill_result(self):
        """Заполнение данных по 44ФЗ
        """
        print(json_pretty_print(self.data))

        self.result = {
            'auction_number': self.data['main'].get('registrationNumber'),
            #'code': misc.get('Идентификационный код закупки'),
            'name': self.data['main'].get('name'),
            'federal_law': self.name,
            'lots_сount': len(self.data['lots']),
            #'amount': self.get_money(cond_info.get('Начальная (максимальная) цена контракта')),
            #'guarantee_amount': self.get_money(provision_info.get('Размер обеспечения заявки')),
            #'guarantee_execution_amount': self.get_money(provision_execution_info.get('Размер обеспечения исполнения контракта')),
            #'guarantee_warranty_amount': None, # TODO: найти
            #'advance': None, # TODO: найти
            #'execution_period': terms_and_funding_info.get('Срок исполнения контракта'),
            'execution_dates': [
                self.data['placing_procedure'].get('summingup_date_time'),
                ###terms_and_funding_info.get('Срок исполнения контракта'),
            ],
            'end_order_date_at': self.data['main'].get('submission_close_date_time'),
            'trading_platform': {
                'name': self.data['trading_platform'].get('name'),
                'url': self.data['trading_platform'].get('url'),
            },
            'customer': {
                'full_name': self.data['customer'].get('full_name'),
                'short_name': self.data['customer'].get('short_name'),
            },
            'lots': [{
                'number': lot.get('ordinal_number'),
                #'planingStart': None,
                #'planingEnd': None,
                'name': lot.get('lot_data', {}).get('subject'),
                #'description': None,
                #'lotAmountType': None,
                'lot_amount': lot.get('initial_sum'),
                #'lotAmountDescription': None,
                #'lotGuaranteeAmount': None,
                #'lotGuaranteeDescription': None,
                #'lotGuaranteeExecutionAmount': None,
                #'lotGuaranteeExecutionDescription': None,
                #'addressSubject': None,
                'address': lot.get('lot_data', {}).get('delivery_place', {}).get('address'),
                'is_only_for_small_medium_business': lot.get('for_small_or_middle'),
            } for lot in self.data['lots']]
        }

