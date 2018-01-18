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
    # make sure each tag has a value
    if len(datum)%2:
        click.echo('each tag requires a value!')
        return
    # TODO parse datum tuple


    try:
        with connection.cursor() as c:
            sql = 'show columns from datums like %s'
            # check if column exists, create if not
            if not c.execute(sql, datum[0]):
                click.echo('tag not found...')
                sql = 'alter table datums add %s varchar(32)'

            sql = 'insert into datums (time) values (%s)'
            c.execute(sql, datetime.now())
        connection.commit()
    finally:
        connection.close()

@main.command()
def ls():
    '''List all datums'''
    try:
        with connection.cursor() as c:
            sql = 'select * from datums'
            c.execute(sql)
            click.echo(pprint(c.fetchall()))
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
