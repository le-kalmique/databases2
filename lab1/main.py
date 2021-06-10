from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from lxml import etree
import os
import webbrowser


def task1():
    print_delimeter()
    print("Task 1 - football.ua")
    root = etree.parse("task1.xml")
    pages = root.xpath("//page")

    print("Number of images for scrapped pages:")
    for page in pages:
        url = page.xpath("@url")[0]
        imgs_count = page.xpath("count(fragment[@type='image'])")
        print(f"{url}: {imgs_count} img(s)")


def task2():
    print_delimeter()
    print("Task 2 - moyo.ua")

    transform = etree.XSLT(etree.parse("task2.xsl"))
    result = transform(etree.parse("task2.xml"))
    result.write("task2.xhtml", pretty_print=True, encoding="UTF-8")

    print("- Opening XHTML page")
    webbrowser.open('file://' + os.path.realpath("task2.xhtml"))


def clean_files():
    try:
        os.remove("task1.xml")
        os.remove("task2.xml")
        os.remove("task2.xhtml")
    except OSError:
        pass


def scrap_data():
    process = CrawlerProcess(get_project_settings())
    process.crawl('football')
    process.crawl('moyo')
    process.start()


def print_delimeter():
    print("=-" * 30, end="=\n")

if __name__ == '__main__':
    print("Lab #1 - Dzherhalova Renata - KP82")
    print_delimeter()
    print("- Scrapping data")
    clean_files()
    scrap_data()
    print("- Scraping finished", end="\n")

    while True:
        print_delimeter()
        print("Choose the task")
        print("1. Task #1")
        print("2. Task #2")
        print("0. Quit")
        print(":: ", end='', flush=True)
        number = input()
        if number == "1":
            task1()
        elif number == "2":
            task2()
        elif number == "0":
            break

    print("Quiting...")
