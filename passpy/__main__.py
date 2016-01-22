# coding: utf-8

# passpy --  ZX2C4's pass compatible library and cli
# Copyright (C) 2016 Benedikt Rascher-Friesenhausen <benediktrascherfriesenhausen@gmail.com>

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


import locale
import os

import click
import pyperclip

from git import (
    GitCommandError
)

from passpy import (
    Store,
    StoreNotInitialisedError,
    RecursiveCopyMoveError
)


# Message constants
MSG_STORE_NOT_INITIALISED_ERROR = ('You need to call {0} init first.'
                                   .format(__name__))
MSG_PERMISSION_ERROR = 'Nah-ah!'
MSG_FILE_NOT_FOUND = 'Error: {0} is not in the password store.'
MSG_RECURSIVE_COPY_MOVE_ERROR = 'Error: Can\'t {0} a directory into itself.'

# Tree constants
if locale.getdefaultlocale()[1].startswith('UTF'):
    SPACES = '    '
    BRIDGE = '│   '
    BRANCH = '├── '
    ENDING = '└── '
else:
    SPACES = '    '
    BRIDGE = '|   '
    BRANCH = '|-- '
    ENDING = '`-- '


def _gen_tree(lines):
    """Create hierarchical file tree from key names.

    :param list lines: A list of key names from the password store.

    :rtype: dict
    :returns: A nested dictionary with directories and key names as
        it's keys.

    """
    tree = {}
    for line in lines:
        ctree = tree
        for segment in line.split(os.sep):
            if segment not in ctree:
                ctree[segment] = {}
            ctree = ctree[segment]

    return tree


def _print_name(name, num_children):
    """Print a name with added styles.

    If `num_children` is larger than nil, `name` will be printed in
    bold face and in blue, to differentiate it as a directory and not
    a key.

    :param str name: The name to be printed.

    :param int num_children: The number of children the leaf has.

    """
    # pass colors folders blue, so we do too.
    if num_children > 0:
        click.secho(name, bold=True, fg='blue')
    else:
        click.echo(name)


def _print_tree(tree, seperators=None):
    """Print a depth indented listing.

    The algorithm for printing the tree has been taken from `doctree`_
    written by Mihai Ciumeică and licensed under the MIT licence.  The
    code has been adapted to fit our needs.

    .. _doctree: https://github.com/cmihai/docktree

    :param dict tree: A dictionary created by
        :func:`passpy.__main__._gen_tree`.

    :param list seperators: (optional) The seperators to print before
       the leaf name.  Leave empty when calling this function.

    """
    if seperators is None:
        seperators = []

    length = len(tree)
    for i, entry in enumerate(sorted(tree, key=str.lower)):
        num_children = len(tree[entry])
        for seperator in seperators:
            if seperator:
                click.echo(BRIDGE, nl=False)
            else:
                click.echo(SPACES, nl=False)
        if i < length - 1:
            click.echo(BRANCH, nl=False)
            _print_name(entry, num_children)
            _print_tree(tree[entry], seperators + [1])
        else:
            click.echo(ENDING, nl=False)
            _print_name(entry, num_children)
            _print_tree(tree[entry], seperators + [0])


class PassGroup(click.Group):
    """Custom group for command name aliases.
    """
    def get_command(self, ctx, cmd_name):
        """Allow aliases for commands.
        """
        if cmd_name == 'list':
            cmd_name = 'ls'
        elif cmd_name == 'search':
            cmd_name = 'find'
        elif cmd_name == 'gen':
            cmd_name = 'generate'
        elif cmd_name == 'add':
            cmd_name = 'insert'
        elif cmd_name in ['remove', 'delete']:
            cmd_name = 'rm'
        elif cmd_name == 'rename':
            cmd_name = 'mv'
        elif cmd_name == 'copy':
            cmd_name = 'cp'

        # TODO(benedikt) Figure out how to make 'show' the default
        # command and pass cmd_name as the first argument.
        rv = click.Group.get_command(self, ctx, cmd_name)
        if rv is not None:
            return rv


@click.group(cls=PassGroup)
@click.option('--gpg-bin', envvar='PYPASS_GPG_BIN', default='gpg2',
              help='The path to your gpg2 binary.  Only necessary '
              'if gpg2 is not already in your PATH.  Alternatively '
              'you can set the PYPASS_GPG_BIN environment variable '
              'with the path.')
@click.option('--git-bin', envvar='PYPASS_GIT_BIN', default='git',
              help='The path to your git binary.  Only necessary '
              'if git is not already in your PATH.  Alternatively '
              'you can set the PYPASS_GIT_BIN environment variable '
              'with the path.')
@click.option('--store-dir', envvar='PYPASS_STORE_DIR',
              default='~/.password-store',
              help='The path to the directory to use for the '
              'password store.  Alternatively you can set the '
              'PYPASS_STORE_DIR environment variable with the path.')
@click.option('--no-agent', envvar='PYPASS_NO_AGENT', is_flag=True,
              help='Pass this along if you don\'t have an ssh agent '
              'running.  Alternatively you can set the PYPASS_NO_AGENT '
              'environment variable.', default=False)
@click.pass_context
def cli(ctx, gpg_bin, git_bin, store_dir, no_agent):
    """passpy is a password manager compatible with ZX2C4's pass written
    in Python.

    """
    if no_agent:
        use_agent = False
    else:
        use_agent = True
    ctx.obj = Store(gpg_bin, git_bin, store_dir, use_agent, True, True)


@cli.command(options_metavar='[ --path,-p ]')
@click.option('-p', '--path', type=str,
              help='Only set the gpg-ids for the given subfolder.')
@click.argument('gpg_ids', nargs=-1, metavar='gpg-id')
@click.pass_context
def init(ctx, gpg_ids, path):
    """Initialize new password storage and use `gpg-id` for encryption.
    Mutliple gpg-ids may be specified, in order to encrypt each
    password with multiple ids.  This command must be run first before
    a password store can be used.  If the specified `gpg-id` is
    different from the ye used in any existing files, these files will
    be reencrypted to use the new id.  Note that use of an gpg agent
    is recommended so that the batch decryption does not require as
    much user intervention.  If `--path` or `-p` is specified, along
    with an argument, a specific gpg-id or a set of gpg-ids is
    assigned for that specific sub folder of the password store.  If
    only the gpg-id is given, and it is an empty string then the
    current `.gpg-id` file for the specfified `sub-folder` (or root if
    unspecified) is removed.

    """
    try:
        ctx.obj.init_store(list(gpg_ids), path=path)
    except PermissionError:
        click.echo(MSG_PERMISSION_ERROR)
        return 1

    click.echo('Password store initialised for {0}.'
               .format(','.join(gpg_ids)))


@cli.command()
@click.argument('subfolder', type=str, default='.')
@click.pass_context
def ls(ctx, subfolder, passthrough=False):
    """List names of passwords inside the tree at `subfolder`.  This
    command is alternatively names `list`.

    """
    # TODO(benedikt) Generate pretty output
    try:
        keys = list(ctx.obj.iter_dir(subfolder))
    # If subfolder is actually a key in the password store pass shows
    # the contents of that key.
    except FileNotFoundError:
        if not passthrough:
            return ctx.invoke(show, pass_name=subfolder, clip=False,
                              passthrough=True)
        else:
            click.echo(MSG_FILE_NOT_FOUND.format(subfolder))
            return 1
    except StoreNotInitialisedError:
        click.echo(MSG_STORE_NOT_INITIALISED_ERROR)
        return 1

    click.echo('Password Store')
    tree = _gen_tree(keys)
    _print_tree(tree)


@cli.command()
@click.argument('search_string', type=str, metavar='search-string')
@click.pass_context
def grep(ctx, search_string):
    """Searches inside each decrypted password file for `search-string`,
    and displays line containing matched string along with filename.
    `search-string` can be a regular expression.

    """
    try:
        results = ctx.obj.search(search_string)
    except StoreNotInitialisedError:
        click.echo(MSG_STORE_NOT_INITIALISED_ERROR)
        return 1

    for key in results:
        if os.path.dirname(key) != '':
            click.secho(os.path.dirname(key) + os.sep, fg='blue', nl=False)
        click.secho(os.path.basename(key), fg='blue', bold=True, nl=False)
        click.secho(':')
        for line, match in results[key]:
            start = match.start()
            end = match.end()
            click.echo(line[:start], nl=False)
            click.secho(line[start:end], nl=False, fg='red', bold=True)
            click.echo(line[end:])


@cli.command()
@click.argument('pass_names', type=str, nargs=-1, metavar='pass-name')
@click.pass_context
def find(ctx, pass_names):
    """List names of passwords inside the tree that match `pass-names` and
    print them to the command line.  This command is alternatively
    named `search`.

    """
    try:
        keys = ctx.obj.find(list(pass_names))
    except StoreNotInitialisedError:
        click.echo(MSG_STORE_NOT_INITIALISED_ERROR)
        return 1

    click.echo('Search Terms: {0}'.format(','.join(pass_names)))
    tree = _gen_tree(keys)
    _print_tree(tree)


@cli.command(options_metavar='[ --clip,-c ]')
@click.option('-c', '--clip', is_flag=True,
              help='Copy the password to the clipboard instead of '
              'printing it to the command line.')
@click.argument('pass_name', type=str, metavar='pass-name', default='.')
@click.pass_context
def show(ctx, pass_name, clip, passthrough=False):
    """Decrypt and print a password named `pass-name`.  If `--clip` or
    `-c` is specified, do not print the password but instead copy the
    first line to the clipboard using pyperclip.  On Linux you will
    need to have xclip/xsel and on OSX pbcopy/pbpaste installed.

    """
    try:
        data = ctx.obj.get_key(pass_name)
    # If pass_name is actually a folder in the password store pass
    # lists the folder instead.
    except FileNotFoundError:
        if not passthrough:
            return ctx.invoke(ls, subfolder=pass_name, passthrough=True)
        else:
            click.echo(MSG_FILE_NOT_FOUND.format(pass_name))
            return 1
    except StoreNotInitialisedError:
        click.echo(MSG_STORE_NOT_INITIALISED_ERROR)
        return 1
    except PermissionError:
        click.echo(MSG_PERMISSION_ERROR)
        return 1

    if clip:
        pyperclip.copy(data.split('\n')[0])
        click.echo('Copied {0} to the clipboard.'.format(pass_name))
    else:
        # The key data always ends with a newline.  So no need to add
        # another one.
        click.echo(data, nl=False)


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
    """Insert a new password into the password store called `pass-name`.
    This will read the new password from standard in.  If `--echo` or
    `-e` are NOT specified, disable keyboard echo when the password is
    entered and confirm the password by asking for it twice.  If
    `--multiline` or `-m` is specified, lines will be read until EOF
    or Ctrl+D is reached.  Otherwise, only a single line from standard
    in read.  Prompt before overwriting an existing password, unless
    `--force` or `-f` is specified.  This command is alternatively
    named `add`

    """
    if input_method is None:
        input_method = 'neither'
    if input_method == 'multiline':
        click.echo('Enter contents of {0} and press Ctrl+D on an empty '
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
        echo = (input_method != 'echo')
        data = click.prompt('Enter password for {0}'.format(pass_name),
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
    """Insert a new password or edit an existing one using the editor
    specified by either EDITOR or VISUAL or falling back on the
    platform default if both are not set.

    """
    try:
        data = ctx.obj.get_key(pass_name)
    except FileNotFoundError:
        data = ''
    except StoreNotInitialisedError:
        click.echo(MSG_STORE_NOT_INITIALISED_ERROR)
        return 1
    except PermissionError:
        click.echo(MSG_PERMISSION_ERROR)
        return 1

    if 'EDITOR' in os.environ:
        data = click.edit(text=data, editor=os.environ['EDITOR'])
    else:
        data = click.edit(text=data)

    if data is None:
        click.echo('Password unchanged.')
        return 1

    ctx.obj.set_key(pass_name, data, force=True)


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
    """Generate a new password of length `pass-length` and insert into
    `pass-name`.  If `--no-symbols` or `-n` is specified, do not use
    any non-alphanumeric characters in the generated password.  If
    `--clip` or `-c` is specified, do not print the password but
    instead copy it to the clipboard.  On Linux you will need to have
    xclip/xsel and on OSX pbcopy/pbpaste installed.  Prompt before
    overwriting an existing password, unless `--force` or `-f` is
    specified.  If `--in-place` or `-i` is specified, do not
    interactively prompt, and only replace the first line of the
    password file with the new generated password, keeping the
    remainder of the file intact.

    """
    symbols = not no_symbols
    try:
        password = ctx.obj.gen_key(pass_name, pass_length, symbols,
                                   force, in_place)
    except StoreNotInitialisedError:
        click.echo(MSG_STORE_NOT_INITIALISED_ERROR)
        return 1
    except PermissionError:
        click.echo(MSG_PERMISSION_ERROR)
        return 1
    except FileNotFoundError:
        click.echo(MSG_FILE_NOT_FOUND.format(pass_name))
        return 1

    if password is None:
        return 1

    if clip:
        pyperclip.copy(password)
        click.echo('Copied {0} to the clipboard.'.format(pass_name))
    else:
        click.echo('The generated password for {0} is:'.format(pass_name))
        click.echo(password)


@cli.command(options_metavar='[ --recursive,-r ] [ --force,-f ]')
@click.option('-r', '--recursive', is_flag=True,
              help='If pass-name is a directory, also remove all '
              'it\'s contents.')
@click.option('-f', '--force', is_flag=True, default=False,
              help='Don\'t prompt for confirmation when removing a key.')
@click.argument('pass_name', type=str, metavar='pass-name')
@click.pass_context
def rm(ctx, pass_name, recursive, force):
    """Remove the password names `pass-name` from the password store.
    This command is alternatively named `remove` or `delete`.  If
    `--recursive` or `-r` is specified, delete pass-name recursively
    if it is a directory.  If `--force` or `-f` is specified, do not
    interactively prompt before removal.

    """
    try:
        ctx.obj.remove_path(pass_name, recursive, force)
    except StoreNotInitialisedError:
        click.echo(MSG_STORE_NOT_INITIALISED_ERROR)
        return 1
    except FileNotFoundError:
        click.echo('{0} is not in the password store.'.format(pass_name))
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
    """Renames the password or directory named `old-path` to `new-path`.
    This command is alternatively named `rename`.  If `--force` or
    `-f` is specified, silently overwrite `new-path` if it exists.  If
    `new-path` ends in a trailing '/', it is always treated as a
    directory.  Passwords are selectively reencrypted to the
    corresponding keys of their new destination.

    """
    try:
        ctx.obj.move_path(old_path, new_path, force)
    except StoreNotInitialisedError:
        click.echo(MSG_STORE_NOT_INITIALISED_ERROR)
        return 1
    except FileNotFoundError:
        click.echo('{0} is not in the password store.'.format(old_path))
        return 1
    except PermissionError:
        click.echo(MSG_PERMISSION_ERROR)
        return 1
    except RecursiveCopyMoveError:
        click.echo(MSG_RECURSIVE_COPY_MOVE_ERROR.format('move'))
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
        click.echo('{0} is not in the password store.'.format(old_path))
        return 1
    except PermissionError:
        click.echo(MSG_PERMISSION_ERROR)
        return 1
    except RecursiveCopyMoveError:
        click.echo(MSG_RECURSIVE_COPY_MOVE_ERROR.format('copy'))
        return 1


@cli.command()
@click.argument('git_args', type=str, metavar='git-command-args', nargs=-1)
@click.pass_context
def git(ctx, git_args):
    """If the password store is a git repository, pass `args` as arguments
    to `git` using the password store as the git repository.  If
    `args` is `init`, in addition to initializing the git repository,
    add the current contents of the password store to the repository
    in an initial commit.

    """
    try:
        ctx.obj.git(*list(git_args))
    except GitCommandError as e:
        click.echo(e)
        return 1
