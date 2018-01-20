import click
import pymysql.cursors
from datetime import datetime
from pprint import pprint

datums_db = {
    'host': 'localhost',
    'user': 'root',
    'db': 'datum',
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor
}

def db(sql):
    connection = pymysql.connect(**datums_db)
    try:
        with connection.cursor() as cursor:
            affected_row_count = cursor.execute(sql)
        connection.commit()
        all_rows = cursor.fetchall()
    finally:
        connection.close()
    return (affected_row_count, all_rows)

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

    tag, value = datum
    sql = 'show columns from datums like \'{}\''.format(tag)
    column_exists, those_columns = db(sql)
    if not column_exists:
        print('new tag! adding db column...')
        db('alter table datums add {} varchar(32)'.format(tag))
    sql = 'insert into datums ({}, time) values (\'{}\', \'{}\')'
    db( sql.format(tag, value, datetime.now()) )

@main.command()
def ls():
    '''List all datums'''
    datum_list = db('select * from datums')
    click.echo(pprint(datum_list))


@main.command()
def edit():
    '''Edit an existing datum'''
    pass

@main.command()
def rm():
    '''Remove an existing datum'''
    pass
