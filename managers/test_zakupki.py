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