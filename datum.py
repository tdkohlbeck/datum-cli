import click
import pymysql.cursors
from datetime import datetime
from pprint import pprint

connection = pymysql.connect(
    host='localhost',
    user='root',
    db='datum',
    cursorclass=pymysql.cursors.DictCursor
)

@click.group()
def main():
    pass

@main.command()
@click.argument('datum', nargs=-1)
def add(datum):
    '''Add a new datum'''
    try:
        with connection.cursor() as cursor:
            sql = 'insert into datums (time) values (%s)'
            cursor.execute(sql, datetime.now())
        connection.commit()
    finally:
        connection.close()

    click.echo(datum)

@main.command()
def ls():
    '''List all datums'''
    try:
        with connection.cursor() as cursor:
            sql = 'select * from datums'
            cursor.execute(sql)
            click.echo(pprint(cursor.fetchall()))
    finally:
        connection.close()


@main.command()
def edit():
    '''Edit an existing datum'''
    pass

@main.command()
def rm():
    '''Remove an existing datum'''
    pass
