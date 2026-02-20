import re
from managers.simple_logger import json_pretty_print, logger


rega_body = re.compile('<body>(.+)</body>', re.I+re.U+re.DOTALL)


class FZ44:
    fz_id = 44
    name = '44-ФЗ'
    # не всегда страничка для печати с таким адресом
    #url = '%s/epz/order/notice/printForm/view.html?regNumber=%s'
    url = '%s/epz/order/notice/zk20/view/common-info.html?regNumber=%s'
    rega_org_id = re.compile("/epz/organization/view/info.html.organizationId=([0-9]+)", re.I+re.U+re.DOTALL)

    def __init__(self):
        self.data = {}
        self.result = {}

    def find_body(self, text: str):
        """Найти тело документа 44ФЗ
           :param text: текст, в котором ищем <body></body>
        """
        body = rega_body.search(text)
        if body:
            body = body[0].replace('<br>', '<br/>').replace('<hr>', '</hr>')
            #logger.info(body)
            return body

    def find_data(self, body_html):
        """Находим данные по 44ФЗ
           например,
            <td>
               <p class="parameter">Номер извещения</p>
            </td>
            <td>
               <p class="parameterValue">0338200009826000065</p>
            </td>
           Номер извещения (аукциона)
        """
        self.data = {
            'misc': {},
        }
        caption = 'misc' # Раздел который заполняем параметрами
        tables = []
        for el in body_html:
            if el.tag == 'table':
                tables.append(el)
        for table in tables:
            trs = []
            for el in table:
                if el.tag == 'tr':
                    trs.append(el)
            for tr in trs:
                tds = []
                for el in tr:
                    if el.tag == 'td':
                        tds.append(el)
                parameter = parameter_value = None
                for td in tds:
                    for el in td:
                        if el.tag == 'p':
                            class_attibute = el.attrib.get('class')
                            if class_attibute == 'parameter':
                                # <p class="parameter">Номер извещения</p>
                                parameter = el.text.strip() if el.text else '-'
                            elif class_attibute == 'parameterValue':
                                # <p class="parameterValue">0338200009826000065</p>
                                parameter_value = el.text.strip() if el.text else '-'
                            elif class_attibute == 'caption':
                                # <p class="caption"><b>Общая информация</b></p>
                                caption = el[0].text.strip() if len(el) and el[0].text else 'misc'
                                self.data[caption] = {}
                if caption and parameter and parameter_value:
                    self.data[caption][parameter] = parameter_value

    def get_money(self, text):
        """Получить сумму,
           например, text = "104880.00 РОССИЙСКИЙ РУБЛЬ"
        """
        if not text:
            return text
        return text.split(' ')[0]

    def fill_result(self):
        """Заполнение данных по 44ФЗ
        """
        main_info = self.data.get('Общая информация', {})
        misc = self.data.get('misc', {})
        cond_info = self.data.get('Условия контракта', {})
        provision_info = self.data.get('Обеспечение заявки', {})
        provision_execution_info = self.data.get('Обеспечение исполнения контракта', {})
        terms_and_funding_info = self.data.get('Информация о сроках исполнения контракта и источниках финансирования', {})
        buy_process_info = self.data.get('Информация о процедуре закупки', {})
        contact_info = self.data.get('Контактная информация', {})

        print(json_pretty_print(self.data))

        self.result = {
            'auction_number': main_info.get('Номер извещения'),
            'code': misc.get('Идентификационный код закупки'),
            'name': main_info.get('Наименование объекта закупки'),
            'federal_law': self.name,
            'lots_сount': None, # не нашел c лотами
            'amount': self.get_money(cond_info.get('Начальная (максимальная) цена контракта')),
            'guarantee_amount': self.get_money(provision_info.get('Размер обеспечения заявки')),
            'guarantee_execution_amount': self.get_money(provision_execution_info.get('Размер обеспечения исполнения контракта')),
            'guarantee_warranty_amount': None, # TODO: найти
            'advance': None, # TODO: найти
            'execution_period': terms_and_funding_info.get('Срок исполнения контракта'),
            'execution_dates': [
                buy_process_info.get('Дата подведения итогов определения поставщика (подрядчика, исполнителя)'),
                terms_and_funding_info.get('Срок исполнения контракта'),
            ],
            'end_order_date_at': buy_process_info.get('Дата и время окончания срока подачи заявок'),
            'trading_platform': {
                'name': main_info.get('Наименование электронной площадки в информационно-телекоммуникационной сети «Интернет»'),
                'url': main_info.get('Адрес электронной площадки в информационно-телекоммуникационной сети «Интернет»'),
            },
            'customer': {
                'full_name': contact_info.get('Организация, осуществляющая размещение'),
            },
            'lots': None, # TODO: поискать с лотами
        }

