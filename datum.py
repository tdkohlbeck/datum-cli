import click

@click.group()
def main():
    pass

@main.command()
@click.argument('command')
def test(command):
    '''A personal data management platform--for humans!'''
    click.echo(command)

@main.command()
def add():
    '''Add a new datum'''
    pass

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
