import click

from pypass import (
    Store,
    StoreNotInitialisedError
)


class PassGroup(click.Group):
    def get_command(self, ctx, cmd_name):
        if cmd_name == 'list':
            cmd_name = 'ls'
        elif cmd_name == 'search':
            cmd_name = 'find'
        elif cmd_name == 'add':
            cmd_name = 'insert'
        elif cmd_name == 'remove' or cmd_name == 'delete':
            cmd_name = 'rm'
        elif cmd_name == 'rename':
            cmd_name = 'mv'
        elif cmd_name == 'copy':
            cmd_name = 'cp'
        else:
            # TODO(benedikt) Use current cmd_name as first parameter
            cmd_name = 'show'

        click.echo('Command: {}'.format(cmd_name))



        rv = click.Group.get_command(self, ctx, cmd_name)
        if rv is not None:
            return rv


@click.group(cls=PassGroup)
@click.pass_context
def cli(ctx):
    ctx.obj = Store()


@cli.command()
@click.option('-p', '--path', type=str)
@click.argument('gpg_id', nargs=-1)
@click.pass_context
def init(ctx, path, gpg_id):
    ctx.obj.init_store(list(gpg_id), path=path)


@cli.command()
@click.argument('subfolder', type=str)
@click.pass_context
def ls(ctx, subfolder):
    # keys = ctx.obj.ls_dir(subfolder)
    # for key in keys:
    #     click.echo(entry)
    pass


@cli.command()
@click.argument('search_string', type=str, nargs=-1)
@click.pass_context
def grep(ctx, search_string):
    pass


@cli.command()
@click.argument('pass_names', type=str, nargs=-1)
@click.pass_context
def find(ctx, pass_names):
    keys = ctx.obj.find(list(pass_names))
    for key in keys:
        click.echo(key)


@cli.command()
@click.option('-c', '--clip', is_flag=True)
@click.argument('pass_name', type=str)
@click.pass_context
def show(ctx, pass_name, clip):
    data = ctx.obj.get_key(pass_name)
    if clip:
        # TODO(benedikt) Copy to clipboard
        pass
    else:
        clip.echo(data)


@cli.command()
@click.option('-e', '--echo', is_flag=True)
@click.option('-m', '--multiline', is_flag=True)
@click.option('-f', '--force', is_flag=True)
@click.argument('pass_name', type=str)
@click.pass_context
def insert(ctx, pass_name, echo, multiline, force):
    if multiline:
        pass
        # TODO(benedikt) implement
        # data = click.prompt('Enter contents of {} and press Ctrl+D when finished:'
        #                     .format(pass_name), type=str)
    else:
        data = click.prompt('Enter password for {}: '.format(pass_name),
                            hide_input=True, confirmation_prompt=echo,
                            type=str)
    ctx.obj.set_key(pass_name, data, force=force)


@cli.command()
@click.argument('pass_name', type=str)
@click.pass_context
def edit(ctx, pass_name):
    pass


@cli.command()
@click.option('-n', '--no-symbols', is_flag=True)
@click.option('-c', '--clip', is_flag=True)
@click.option('-i', '--in-place', is_flag=True)
@click.option('-f', '--force', is_flag=True)
@click.argument('pass_name', type=str)
@click.argument('pass_length', type=int)
@click.pass_context
def generate(ctx, pass_name, pass_length, no_symbols, clip, in_place, force):
    pass


@cli.command()
@click.option('-r', '--recursive', is_flag=True)
@click.option('-f', '--force', is_flag=True)
@click.argument('pass_name', type=str)
@click.pass_context
def rm(ctx, pass_name, recursive, force):
    pass


@cli.command()
@click.option('-f', '--force', is_flag=True)
@click.argument('old_path', type=str)
@click.argument('new_path', type=str)
@click.pass_context
def mv(ctx, old_path, new_path, force):
    pass


@cli.command(options_metavar='[ --force, -f ]')
@click.option('-f', '--force', is_flag=True,
              help='If specified existing files at `new-path` will be silently\
              overwritten.')
@click.argument('old_path', type=str, metavar='old-path')
@click.argument('new_path', type=str, metavar='new-path')
@click.pass_context
def cp(ctx, old_path, new_path, force):
    """Copies the password or directory names `old-path` to `new-path`.
    This command is alternatively named `copy`.  If `--force` is
    specified, silently overwrite `new_path` if it exists.  If
    `new-path` ends in a trailing `/`, it is always treated as a
    directory.  Passwords are selectively reencrypted to the
    corresponding keys of their new destination.

    """
    pass


if __name__ == '__main__':
    cli()
