import click
import json as jayson
import pymysql.cursors
from datetime import datetime
from pprint import pprint
import dateparser
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
    if 'time' in datum_dict:
        datum_dict['time'] = dateparser.parse(datum_dict['time'])
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

@main.command()
@click.argument('date', nargs=1)
@pass_config
def time(config, date):
    '''View start/stop activities'''

    date = dateparser.parse(date)
    if not date:
        click.echo('please specify a valid date')
        return

    sql = 'select * from datums where convert(_time,date)=\'{}\''
    count, datums_with_date = db(sql.format(date.date()))
    if not count:
        click.echo('no datums added on ' + str(date.date()))
        return

    def filter_activities(datums):
        activity_datums = []
        for datum in datums:
            if 'start' in datum and datum['start']:
                activity_datums.append(datum)
            elif 'stop' in datum and datum['stop']:
                activity_datums.append(datum)
        return activity_datums

    datums = filter_activities(datums_with_date)

    def time_of(datum):
        if 'time' in datum and datum['time']:
            return dateparser.parse(datum['time'])
        return datum['_time']

    def find_stop_time_for(activity, starting_index):
        remaining_datums = range(starting_index + 1, len(datums))

        next_start_time = 0
        for i in remaining_datums:
            datum = datums[i]
            if 'stop' in datum and datum['stop'] == activity:
                return time_of(datum)
            if datum['start'] and not next_start_time:
                next_start_time = time_of(datum)

        stop_time = next_start_time if next_start_time else datetime.now()
        return stop_time

    def format_duration(seconds):
        hours = seconds / 60 / 60
        hours_remainder = hours - int(hours)
        minutes = int(hours_remainder * 60)
        hours = str(int(hours))
        minutes = str(minutes)
        if len(hours) == 1:
            hours = '0' + hours
        if len(minutes) == 1:
            minutes = '0' + minutes
        return hours + ':' + minutes

    rows = [ # TODO add total time and uncounted time
        ['activity', 'duration', 'started', 'stopped'],
        ['--------', '--------', '-------', '-------']
    ]
    for i in range(len(datums)):
        datum = datums[i]
        if datum['start']:
            activity = datum['start']
            start_time = time_of(datum)
            stop_time = find_stop_time_for(activity, i)
            duration = format_duration(
                (stop_time - start_time).total_seconds()
            )
            rows.append([
                activity,
                str(duration),
                start_time.strftime('%H:%M'),
                stop_time.strftime('%H:%M'),
            ])

    max_column_lengths = [0, 0, 0, 0]
    for row in rows:
        for i in range(len(row)):
            if len(row[i]) > max_column_lengths[i]:
                max_column_lengths[i]  = len(row[i])

    def padded(entry, column):
        space_count = max_column_lengths[column] - len(entry)
        spaces = ''
        for x in range(space_count):
            spaces += ' '
        return spaces + entry

    for row in rows:
        for col in range(len(row)):
            entry = padded(row[col], col)
            click.echo(entry + '  ', nl=False)
        click.echo()

@main.command()
def reset():
    '''clears all data'''
    db('drop table if exists datums, tags')
    db('create table datums (id int(11) not null auto_increment primary key, _time datetime)')
    db('create table tags (id int(11) not null auto_increment primary key, tag_name varchar(32), count int(11))')
