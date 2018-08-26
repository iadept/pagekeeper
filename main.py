# coding: utf-8
from typing import Optional

from hnmp import SNMP, SNMPError
import sqlite3
import argparse
import json
from datetime import date


def intbit(number):
    i = 0
    out = ''
    for c in str(number)[::-1]:
        if i == 3:
            i = 0
            out = out + " "
        out = out + c
        i = i + 1
    return out[::-1]


class Printer:

    def __init__(self, configuration):
        self.title: str = configuration['title']
        self.description: str = configuration['description']
        self.oid: str = configuration.get('oid', "1.3.6.1.2.1.43.10.2.1.4.1.1")
        self.ip: str = configuration['ip']
        self.groups: [str] = configuration['groups']

    def get_page_count(self) -> Optional[int]:
        try:
            snmp = SNMP(self.ip, community="public")
            return snmp.get(self.oid)
        except SNMPError as error:
            print(error)
            return None


class Configuration:

    def __init__(self, data):
        self.database: str = data['database']
        self.printers = {}
        for printer_data in data['printers']:
            printer = Printer(printer_data)
            self.printers[printer.title] = printer


class Database:

    def __init__(self, filename):
        self.connection = sqlite3.connect(filename)
        self.cursor = self.connection.cursor()
        self.__create_table("archive", "created DATE, name TEXT, pages INT")

    def __create_table(self, name, fields):
        try:
            self.cursor.execute("CREATE TABLE %s (%s)" % (name, fields))
        except Exception:
            pass

    def __insert(self, name, value):
        self.cursor.execute("INSERT INTO archive VALUES (?,?,?)", (date.today(), name, value))

    def __update(self, name, value, created=date.today()):
        self.cursor.execute("UPDATE archive SET pages = ? WHERE created = ? AND name = ?", (value, created, name))

    def add(self, name, value, refresh=False):
        if self.get(name):
            if refresh:
                self.__update(name, value)
        else:
            self.__insert(name, value)
        self.connection.commit()

    def get(self, name, created=date.today()):
        result = self.cursor.execute("SELECT pages FROM archive WHERE created = ? AND name = ?", (created, name)).fetchone()
        if result:
            return result[0]
        return None

    def select(self, created):
        result = []
        for row in self.cursor.execute("SELECT name, pages FROM archive WHERE created = ?", (created,)):
            result.append((row[0], row[1]))
        return result


    def clear(self):
        self.cursor.execute("DELETE FROM archive")
        self.connection.commit()

def main():
    parser = argparse.ArgumentParser(description="Collect and analyze count of printed pages")
    parser.add_argument('start', type=str, nargs="?", help="Start date to analyze")
    parser.add_argument('end', type=str, nargs="?", help="End date of analyze")
    parser.add_argument('--conf', action='store', dest="conf", default="conf.json", help="Configuration file (default=conf.json)")

    parser.add_argument('-c', '--collect', action='store_const', const='value-to-store', dest="collect", help="Collect page counts")
    parser.add_argument('-r', '--refresh', action='store_const', const='value-to-store', dest="refresh", help="Refresh data when collect page")
    parser.add_argument('--clear', action='store_const', const='value-to-store', dest="clear", help="Clear database")
    args = parser.parse_args()

    with open(args.conf) as f:
        try:
            data = json.load(f)
            configuration = Configuration(data)
        except Exception as error:
            print('ERROR: Corrupt configuration file')
            print(error)
            return

        database = Database(configuration.database)
        if args.clear:
            print("Clear database!")
            database.clear()

        if args.collect:
            print("Scan printer:")
            for printer in configuration.printers.values():
                count = printer.get_page_count()
                if count:
                    database.add(printer.title, count, args.refresh)
                    print("%20s : %10s %s" % (printer.title, intbit(count), printer.description))
                else:
                    print("%20s : No answer" % (printer.title))

        if args.start:
            print("Report:")

            archive = {}
            groups_start = {}
            groups_end = {}

            archive_start = database.select(created=args.start)
            for name, value in archive_start:
                printer = configuration.printers[name]
                archive[name] = value
                for group in printer.groups:
                    if group not in groups_start:
                        groups_start[group] = 0
                    groups_start[group] = groups_start[group] + value

            if args.end:
                archive_end = database.select(created=args.end)
            else:
                archive_end = database.select(created=date.today())


            total_start = 0
            total_end = 0

            for name, value in archive_end:
                total_start = total_start + archive[name]
                total_end = total_end + value
                diff = value - archive[name]
                if diff > 0:
                    print("%20s: %10s (+%i)" % (name, intbit(value), diff))
                else:
                    print("%20s: %10s" % (name, intbit(value)))
                printer = configuration.printers[name]
                for group in printer.groups:
                    if group not in groups_end:
                        groups_end[group] = 0
                        groups_end[group] = groups_end[group] + value

            total_diff = total_end - total_start

            if total_diff > 0:
                print("Total page: %s (+%i)" % (intbit(total_end), total_diff))
            else:
                print("Total page: %s" % intbit(total_end))
            print("Groups:")

            for group in groups_end:
                diff = groups_end[group] - groups_start[group]
                if diff > 0:
                    print("%20s: %10s (+%i)" %(group, intbit(groups_end[group]), diff))
                else:
                    print("%20s: %10s" % (group, intbit(groups_end[group])))


if __name__ == '__main__':
    main()