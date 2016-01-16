import click

from pypass import (
    Store,
    StoreNotInitialisedError
)


MSG_STORE_NOT_INITIALISED_ERROR = ('You need to call {} init first.'
                                   .format(__name__))
MSG_PERMISSION_ERROR = 'Nah-ah!'


class PassGroup(click.Group):
    def get_command(self, ctx, cmd_name):
        if cmd_name == 'list':
            cmd_name = 'ls'
        elif cmd_name == 'search':
            cmd_name = 'find'
        elif cmd_name == 'gen':
            cmd_name = 'generate'
        elif cmd_name == 'add':
            cmd_name = 'insert'
        elif cmd_name == 'remove' or cmd_name == 'delete':
            cmd_name = 'rm'
        elif cmd_name == 'rename':
            cmd_name = 'mv'
        elif cmd_name == 'copy':
            cmd_name = 'cp'

        # TODO(benedikt) Figure out how to make 'show' the dfault
        # command and pass cmd_name as the first argument.
        rv = click.Group.get_command(self, ctx, cmd_name)
        if rv is not None:
            return rv


@click.group(cls=PassGroup)
@click.pass_context
def cli(ctx):
    ctx.obj = Store()


@cli.command(options_metavar='[ --path,-p ]')
@click.option('-p', '--path', type=str,
              help='Only set the gpg-ids for the given subfolder.')
@click.argument('gpg_ids', nargs=-1, metavar='gpg-id')
@click.pass_context
def init(ctx, gpg_ids, path):
    """Initialize new password storage and use `gpg-id` for encryption.
    Selectively reencrypts existing passwords using new `gpg-id`.

    """
    try:
        ctx.obj.init_store(list(gpg_ids), path=path)
    except PermissionError:
        click.echo(MSG_PERMISSION_ERROR)


@cli.command()
@click.argument('subfolder', type=str)
@click.pass_context
def ls(ctx, subfolder):
    # TODO(benedikt) Generate pretty output
    try:
        for key in ctx.obj.iter_dir(subfolder):
            click.echo(key)
    # If subfolder is actually a key in the password store pass shows
    # the contents of that key.
    except FileNotFoundError:
        show(ctx, subfolder, False)
    except StoreNotInitialisedError:
        click.echo(MSG_STORE_NOT_INITIALISED_ERROR)
        return 1


@cli.command()
@click.argument('search_string', type=str, metavar='search-string')
@click.pass_context
def grep(ctx, search_string):
    try:
        results = ctx.obj.search(search_string)
    except StoreNotInitialisedError:
        click.echo(MSG_STORE_NOT_INITIALISED_ERROR)
        return 1

    for key in results:
        # TODO(benedikt) Color this line
        click.echo(key + ':')
        for line, match in results[key]:
            # TODO(benedikt) Color the matched part of the line
            click.echo(line)


@cli.command()
@click.argument('pass_names', type=str, nargs=-1, metavar='pass-name')
@click.pass_context
def find(ctx, pass_names):
    try:
        keys = ctx.obj.find(list(pass_names))
    except StoreNotInitialisedError:
        click.echo(MSG_STORE_NOT_INITIALISED_ERROR)
        return 1

    # TODO(benedikt) Pretty up the output (tree-like?)
    for key in keys:
        click.echo(key)


@cli.command(options_metavar='[ --clip,-c ]')
@click.option('-c', '--clip', is_flag=True,
              help='Copy the password to the clipboard instead of '
              'printing it to the command line.')
@click.argument('pass_name', type=str, metavar='pass-name')
@click.pass_context
def show(ctx, pass_name, clip):
    try:
        data = ctx.obj.get_key(pass_name)
    except StoreNotInitialisedError:
        click.echo(MSG_STORE_NOT_INITIALISED_ERROR)
        return 1
    except PermissionError:
        click.echo(MSG_PERMISSION_ERROR)
        return 1

    if clip:
        # TODO(benedikt) Copy to clipboard
        pass
    else:
        clip.echo(data)


@cli.command(options_metavar='[ --echo,-e | --multiline,-m ] [ --force,-f ]')
@click.option('-e', '--echo', 'input_method', flag_value='echo',
              help='Don\'t ask to repeat the password.')
@click.option('-m', '--multiline', 'input_method', flag_value='multiline',
              help='Allows entering multiple lines of text for the key.')
@click.option('-f', '--force', is_flag=True,
              help='Any existing key at pass-name will be '
              'silently overwritten.')
@click.argument('pass_name', type=str, metavar='pass-name')
@click.pass_context
def insert(ctx, pass_name, input_method, force):
    if input_method is None:
        input_method = 'neither'
    if input_method == 'multiline':
        click.echo('Enter contents of {} and press Ctrl+D on an empty '
                    'line when finished:'.format(pass_name))
        lines = []
        while True:
            try:
                line = input('> ')
                lines.append(line)
            except EOFError:
                break
        data = '\n'.join(lines)
    else:
        echo = (input_method == 'echo')
        data = click.prompt('Enter password for {}: '.format(pass_name),
                            hide_input=True, confirmation_prompt=echo,
                            type=str)

    try:
        ctx.obj.set_key(pass_name, data, force=force)
    except StoreNotInitialisedError:
        click.echo(MSG_STORE_NOT_INITIALISED_ERROR)
        return 1
    except PermissionError:
        click.echo(MSG_PERMISSION_ERROR)
        return 1


@cli.command()
@click.argument('pass_name', type=str, metavar='pass-name')
@click.pass_context
def edit(ctx, pass_name):
    pass


@cli.command(options_metavar='[ --no-symbols,-n ] [ --clip,-c ] '
             '[ --in-place,-i ] [ --force,-f ]')
@click.option('-n', '--no-symbols', is_flag=True,
              help='If specified the password will only consist '
              'of alphanumeric characters.')
@click.option('-c', '--clip', is_flag=True,
              help='Copy the password to the clipboard instead of '
              'printing it on the command line.')
@click.option('-i', '--in-place', is_flag=True,
              help='Replace the first line of an existing key at '
              'path-name with the newly generated password.')
@click.option('-f', '--force', is_flag=True,
              help='Overwrite an existing key at pass-name without '
              'prompting the user first.')
@click.argument('pass_name', type=str, metavar='pass-name')
@click.argument('pass_length', type=int, metavar='pass-length')
@click.pass_context
def generate(ctx, pass_name, pass_length, no_symbols, clip, in_place, force):
    symbols = not no_symbols
    try:
        password = ctx.obj.gen_key(pass_name, pass_length, symbols, force, in_place)
    except StoreNotInitialisedError:
        click.echo(MSG_STORE_NOT_INITIALISED_ERROR)
        return 1
    except PermissionError:
        click.echo(MSG_PERMISSION_ERROR)
        return 1

    if clip:
        # TODO(benedikt) Copy password to the clipboard
        pass
    else:
        click.echo(password)


@cli.command(options_metavar='[ --recursive,-r ] [ --force,-f ]')
@click.option('-r', '--recursive', is_flag=True,
              help='If pass-name is a directory, also remove all '
              'it\'s contents.')
@click.option('-f', '--force', is_flag=True,
              help='Don\'t prompt for confirmation when removing a key.')
@click.argument('pass_name', type=str, metavar='pass-name')
@click.pass_context
def rm(ctx, pass_name, recursive, force):
    # TODO(benedikt) Use force option when implemented
    try:
        ctx.obj.remove_path(pass_name, recursive)
    except StoreNotInitialisedError:
        click.echo(MSG_STORE_NOT_INITIALISED_ERROR)
        return 1
    except FileNotFoundError:
        click.echo('{} is not in the password store.'.format(pass_name))
        return 1
    except PermissionError:
        click.echo(MSG_PERMISSION_ERROR)
        return 1


@cli.command(options_metavar='[ --force,-f ]')
@click.option('-f', '--force', is_flag=True,
              help='If specified existing files at `new-path` '
              'will be silently overwritten.')
@click.argument('old_path', type=str, metavar='old-path')
@click.argument('new_path', type=str, metavar='old-path')
@click.pass_context
def mv(ctx, old_path, new_path, force):
    try:
        ctx.obj.move_path(old_path, new_path, force)
    except StoreNotInitialisedError:
        click.echo(MSG_STORE_NOT_INITIALISED_ERROR)
        return 1
    except FileNotFoundError:
        click.echo('{} is not in the password store.'.format(old_path))
        return 1
    except PermissionError:
        click.echo(MSG_PERMISSION_ERROR)
        return 1


@cli.command(options_metavar='[ --force,-f ]')
@click.option('-f', '--force', is_flag=True,
              help='If specified existing files at `new-path` '
              'will be silently overwritten.')
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
    try:
        ctx.obj.copy_path(old_path, new_path, force)
    except StoreNotInitialisedError:
        click.echo(MSG_STORE_NOT_INITIALISED_ERROR)
        return 1
    except FileNotFoundError:
        click.echo('{} is not in the password store.'.format(old_path))
        return 1
    except PermissionError:
        click.echo(MSG_PERMISSION_ERROR)
        return 1


@cli.command()
@click.pass_context
def git(ctx):
    pass


if __name__ == '__main__':
    cli()
