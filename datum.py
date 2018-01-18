import click
import pymysql.cursors
import datetime

connection = pymysql.connect(
    host='localhost',
    user='root',
    db='datum',
    cursorclass=pymysql.cursors.DictCursor
)

try:
    with connection.cursor() as cursor:
        sql = 'insert into datums (time) values (%s)'
        cursor.execute(sql, '2018-01-18 11:11:44')
    connection.commit()
finally:
    connection.close()

@click.group()
def main():
    pass

@main.command()
@click.argument('command')
def test(command):
    '''A personal data management platform--for humans!'''
    click.echo(command)

@main.command()
@click.argument('datum', nargs=-1)
def add(datum):
    '''Add a new datum'''
    click.echo(datum)

@main.command()
def ls():
    '''List all datums'''
    pass

@main.command()
def edit():
    '''Edit an existing datum'''
    pass

@main.command()
def rm():
    '''Remove an existing datum'''
    pass
