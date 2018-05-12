import click
import json as jayson
import pymysql.cursors
from datetime import datetime
from pprint import pprint
from personal_config import mysql_password

import sys
sys.path.append('../datum-cli/')

datums_db = {
    'host': 'localhost',
    'user': 'root',
    'password': mysql_password(),
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

class Config(object):
    def __init__(self):
        self.json = False
        self.last = False

    def lineout(self, sql_results):
        for datum in sql_results:
            datum['_time'] =  datum['_time'].strftime(
            '%Y-%m-%d %H:%M:%S'
            )
        if self.json:
            click.echo(jayson.dumps(sql_results))
            return
        output = ''
        for datum in sql_results:
            output += str(datum['id']) + ' '
            output += str(datum['_time']) + ' '
            for tag, value in datum.iteritems():
                if tag == '_time' or tag == 'id':
                    continue
                if not value:
                    continue
                if value == u'True':
                    output += str(tag) + ', '
                else:
                    output += str(tag) + ': ' + str(value) + ', '
            output = output[:-2] # remove last comma
            output += '\n'
        output = output[:-1] # remove last newline
        click.echo(output)


pass_config = click.make_pass_decorator(Config, ensure=True) # auto make instance

@click.group()
@click.option(
    '--json',
    '-j',
    is_flag=True,
    help='output data in json format',
)
@click.option(
    '--last',
    '-l',
    default=1,
    help='output last N datum entries only',
)
@pass_config
def main(config, json, last):
    '''A personal metrics management platform'''
    if json:
        config.json = True
    if last:
        config.last = last

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
            click.echo('new tag! adding db column ' + tag)
            # TODO change types based on tag values
            db('alter table datums add {} varchar(32)'.format(tag))

    # update tag metadata
    for tag, value in datum_dict.items():

        # look for tag, add if not found
        sql = 'select tag_name from tags where tag_name=\'{}\''
        row_count, row = db(sql.format(tag))
        if not row:
            sql = 'insert into tags (tag_name, count) value (\'{}\', 0)'
            db(sql.format(tag))

        # pull out tag count
        sql = 'select count from tags where tag_name=\'{}\''
        _, tag_count = db(sql.format(tag))
        # put in tag count + 1
        sql = 'update tags set count={} where tag_name=\'{}\''
        # TODO clean up this mess! vvv
        db(sql.format(tag_count[0]['count'] + 1, tag))

        # TODO value set
        # pull out value_set
        # append value to set
        # put updated set in its place

    # build tag and value tuples for sql command
    tags = tuple(
        [ str(tag) for tag in datum_dict.keys() ] +
        ['_time']
    )
    values = tuple(
        [ str(val) for val in datum_dict.values() ] +
        [ str(datetime.now()) ]
    )

    # remove quotes from tag tuple for sql command
    tags = str(tags).replace('\'', '')

    sql = 'insert into datums {} values {}'
    db(sql.format(tags, values))

@main.command()
@click.argument('args', nargs=-1)
@pass_config
def ls(config, args):
    '''List all datums'''

    # to see a list of tags
    if args and args[0] == 'tags':
        tag_list_count, tag_list = db('select tag_name from tags')
        config.lineout(tag_list)

    # to see a list of datums with a specific tag
    elif args:
        try:
            sql = 'select * from datums where {} like "%"'
            datum_count, datum_list = db(sql.format(args[0]))
        except:
            click.echo(
                'no datums found with tag ' + str( args[0] )
            )
            return
        config.lineout(datum_list)

    # to see all datums
    else:
        datum_count, datum_list = db('select * from datums')
        if not datum_list:
            click.echo('no datums found!')
            return
        config.lineout(datum_list)


@main.command()
def edit():
    '''Edit an existing datum'''
    pass

@main.command()
@click.argument('datum_ids', nargs=-1)
def rm(datum_ids):
    '''Removes existing datum(s)'''

    # tally up all the tags being deleted
    tag_dict = {}
    for datum_id in datum_ids:
        sql = 'select * from datums where id={}'
        _, datum = db(sql.format(datum_id))

        if not datum:
            click.echo('datum doesn\'t exist!')
            return

        datum = datum[0] # escape list
        for tag, count in datum.items():
            if not (tag == 'id' or tag == '_time') and datum[tag] != None:
                if not tag in tag_dict:
                    tag_dict[tag] = 1
                else:
                    tag_dict[tag] += 1

    # update tag counts in tag table
    for tag, count in tag_dict.items():
        sql = 'select * from tags where tag_name=\'{}\''
        _, records = db(sql.format(tag))
        old_count = records[0]['count']
        sql = 'update tags set count={} where tag_name=\'{}\''
        db(sql.format(old_count - count, tag))

        # remove tag column if 0
        if old_count - count == 0:
            sql='alter table datums drop column {}'
            db(sql.format(tag))

    # remove the datums
    for datum_id in datum_ids:
        if datum_id == 'all':
            db('delete from datums')
            click.echo('all datums deleted!')
        else:
            db('delete from datums where id={}'.format(datum_id))
            click.echo('deleted datum ' + str(datum_id))

import dateparser
@main.command()
@click.argument('args', nargs=-1)
@pass_config
def time(config, args):
    '''View start/stop activities'''

    # get the time interval and activities
    day = 0
    activities = []
    for arg in args:
        if dateparser.parse(arg):
            day = dateparser.parse(arg)
        else:
            activities.append(arg)
    if not day:
        click.echo('please specify a date')
        return

    sql = 'select * from datums where convert(_time,date)=\'{}\''
    count, datums_with_date = db(sql.format(day.date()))
    if not count:
        click.echo('no datums added on ' + str(day.date()))
        return

    def time_of(datum):
        if 'time' in datum:
            return datum['time']
        return datum['_time']

    def stop_time_for(activity, datums):
        start_datum = {}
        next_start_datum = {}
        stop_datum = {}
        #pprint(datums)
        for datum in datums:
            if not start_datum and 'start' in datum and datum['start'] == activity:
                #click.echo('found start datum')
                start_datum = datum
            if start_datum and not next_start_datum and 'start' in datum and datum['start'] != activity:
                #click.echo('found next start datum')
                next_start_datum = datum
            if 'stop' in datum and datum['stop'] == activity:
                #click.echo('found stop datum')
                stop_datum = datum
        #pprint('start ' + str(start_datum['start']))
        #pprint('stop  ' + str(start_datum['stop']))
        #pprint(stop_datum)
        if not start_datum:
            return 'stop time for ' + activity + ' not found'
        if not stop_datum:
            if not next_start_datum:
                return datetime.now()
            return time_of(next_start_datum)
        return time_of(stop_datum)

    time_app_rows = []
    for datum in datums_with_date:
        if 'start' in datum and datum['start']:
            activity = datum['start']
            start_time = time_of(datum)
            stop_time = stop_time_for(activity, datums_with_date)
            duration = int((stop_time - start_time).total_seconds() / 60)
            time_app_rows.append(
                [str(activity), str(duration), start_time.strftime('%H:%M'), stop_time.strftime('%H:%M')]
            )

    for row in time_app_rows:
        for col in row:
            click.echo(col + '  ', nl=False)
        click.echo()

    #click.echo(stop_time_for('two', datums_with_date))
@main.command()
def reset():
    '''clears all data'''
    db('drop table if exists datums, tags')
    db('create table datums (id int(11) not null auto_increment primary key, _time datetime)')
    db('create table tags (id int(11) not null auto_increment primary key, tag_name varchar(32), count int(11))')
