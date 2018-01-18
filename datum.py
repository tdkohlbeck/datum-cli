import click
import pymysql.cursors
from datetime import datetime
from pprint import pprint

connection = pymysql.connect(
    host='localhost',
    user='root',
    db='datum',
    charset='utf8mb4',
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
    if len(datum) % 2:
        click.echo('each tag requires a value!')
        return
    # TODO parse datum tuple

    try:
        with connection.cursor() as c:
            # check if column exists, create if not
            sql = 'show columns from datums like %s'
            if not c.execute(sql, datum[0]):
                sql = 'alter table datums add ' + datum[0] + ' varchar(32)'
                c.execute(sql)
            sql = 'insert into datums (' + datum[0] + ', time) values (%s, %s)'
            c.execute(sql, (datum[1], datetime.now()))
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
