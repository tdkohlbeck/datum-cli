import click

@click.command()
@click.argument('cmd',
                required=False)
def cli(cmd):
    '''this program kills fascists'''
    click.echo('yey!')
