import click


@click.group()
def cli():
    """Example script."""
    click.echo("Hello World!")


@cli.command()  # @cli, not @click!
def web():
    click.echo("Syncing")
