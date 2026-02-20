Описание
-----------
Менеджер для работы с zakuplki.gov.ru

Установка пакетом
-----------
Для локальной разработки::
    pip install -e packages/zakupki_gov_ru_manager

Импорт
-----------
Проверка::
    import sys
    from managers.simple_logger import json_pretty_print, logger
    from managers.zakupki_gov_ru_manager import ZakupkiGovRuManager
    number = '0338200009826000065'
    if len(sys.argv) > 1:
        number = sys.argv[1]
    def main():
        zm = ZakupkiGovRuManager()
        zm.get_by_number(number=number)
        print(json_pretty_print(zm.fz.result))
    if __name__ == '__main__':
        main()


Удаление
-----------
Удалить пакет::
    pip uninstall zakupki_gov_ru_manager

Для создания пакета
https://docs.python.org/3.10/distutils/introduction.html#distutils-simple-example
https://docs.python.org/3.10/distutils/sourcedist.html
::
    python setup.py sdist




