#!/usr/bin/env python3

from datetime import datetime

def main():
    with open("/var/www/html/cse30246/databased/distributorScraper/cronTest.txt", "a+") as outfile:
        outfile.write("Cron ran\n")


if __name__ == "__main__":
    main()
