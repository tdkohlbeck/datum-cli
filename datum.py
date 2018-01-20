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
    '''A personal data management platform--for humans!'''

@main.command()
@click.argument('datum', nargs=-1)
def add(datum):
    '''Add a new datum'''

    # TODO allow for runtime tag entry
    if not datum:
        click.echo('TODO: allow runtime tag entry')
        return

    # parse args and place in dict
    datum_dict = {}
    for tag in datum:
        split_point = tag.find(':')
        if split_point == -1:
            tag_name = tag
            tag_value = True
        else:
            tag_name = tag[:split_point]
            tag_value = tag[split_point+1:]
        datum_dict[tag_name] = tag_value

    # add db columns if there are new tags
    for tag in datum_dict.keys():
        sql = 'show columns from datums like \'{}\''.format(tag)
        column_exists, column = db(sql)
        if not column_exists:
            print('new tag! adding db column...')
            db('alter table datums add {} varchar(32)'.format(tag))

    # build tag and value tuples for sql command
    tags = tuple(
        [ tag for tag in datum_dict.keys() ] +
        ['time']
    )
    values = tuple(
        [ val for val in datum_dict.values() ] +
        [ str(datetime.now()) ]
    )

    # remove quotes from tag tuple for sql command
    tags = str(tags).replace('\'', '')

    sql = 'insert into datums {} values {}'
    db(sql.format(tags, values))

@main.command()
def ls():
    '''List all datums'''
    datum_count, datum_list = db('select * from datums')
    for datum in datum_list:
        click.echo(str(datum['id']) + ' ', nl=False)
        click.echo(str(datum['time']) + ': ', nl=False)
        for tag, value in datum.items():
            if tag not in ['time', 'id'] and value:
                click.echo(str(tag + ': ' + value) + ', ', nl=False)
        click.echo()


@main.command()
def edit():
    '''Edit an existing datum'''
    pass

@main.command()
@click.argument('datum_ids', nargs=-1)
def rm(datum_ids):
    '''Removes existing datum(s)'''
    for datum_id in datum_ids:
        if datum_id == 'all':
            db('delete from datums')
            click.echo('all datums deleted!')
        else:
            db('delete from datums where id={}'.format(datum_id))
            click.echo('deleted datum ' + str(datum_id))
