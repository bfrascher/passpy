import pytest

from passpy.__main__ import (
    MSG_STORE_NOT_INITIALISED_ERROR,
    MSG_PERMISSION_ERROR,
    MSG_FILE_NOT_FOUND,
    MSG_RECURSIVE_COPY_MOVE_ERROR,
    _gen_tree,
    _print_name,
    _print_tree,
    cli,
    init,
    ls,
    grep,
    find,
    show,
    insert,
    edit,
    generate,
    rm,
    mv,
    cp,
    git,
)


def run(r, d, *args, **kwargs):
    return r.invoke(cli, ['--store-dir', str(d)] + list(args), **kwargs)


@pytest.fixture(scope='module')
def runner():
    from click.testing import CliRunner
    return CliRunner()


@pytest.fixture
def store(runner, tmpdir):
    run(runner, tmpdir, 'init', 'passpy_test1')
    return tmpdir


class TestStoreNotInitialisedError:
    def test_ls(self, runner, tmpdir):
        result = run(runner, tmpdir, 'ls', 'not-init')
        assert result.output == MSG_STORE_NOT_INITIALISED_ERROR + '\n'

    def test_grep(self, runner, tmpdir):
        result = run(runner, tmpdir, 'grep', 'not-init')
        assert result.output == MSG_STORE_NOT_INITIALISED_ERROR + '\n'

    def test_find(self, runner, tmpdir):
        result = run(runner, tmpdir, 'find', 'not-init')
        assert result.output == MSG_STORE_NOT_INITIALISED_ERROR + '\n'

    def test_show(self, runner, tmpdir):
        result = run(runner, tmpdir, 'show', 'not-init')
        assert result.output == MSG_STORE_NOT_INITIALISED_ERROR + '\n'

    def test_insert(self, runner, tmpdir):
        result = run(runner, tmpdir, 'insert', '--echo', 'not-init',
                     input='pw\n')
        lines = result.output.split('\n')
        assert len(lines) == 3
        assert lines[0] == 'Enter password for not-init: pw'
        assert lines[1] == MSG_STORE_NOT_INITIALISED_ERROR
        assert lines[2] == ''

    # Can't test since we can't open an editor.
    # def test_edit(self, runner, tmpdir):
    #     result = run(runner, tmpdir, ['edit', 'not-init'])
    #     assert result.output == MSG_STORE_NOT_INITIALISED_ERROR + '\n'

    def test_generate(self, runner, tmpdir):
        result = run(runner, tmpdir, 'generate', 'not-init', '16')
        assert result.output == MSG_STORE_NOT_INITIALISED_ERROR + '\n'

    def test_rm(self, runner, tmpdir):
        result = run(runner, tmpdir, 'rm', 'not-init')
        assert result.output == MSG_STORE_NOT_INITIALISED_ERROR + '\n'

    def test_mv(self, runner, tmpdir):
        result = run(runner, tmpdir, 'mv', 'not-init', 'also-not-init')
        assert result.output == MSG_STORE_NOT_INITIALISED_ERROR + '\n'

    def test_cp(self, runner, tmpdir):
        result = run(runner, tmpdir, 'cp', 'not-init', 'also-not-init')
        assert result.output == MSG_STORE_NOT_INITIALISED_ERROR + '\n'

    def test_git(self, runner, tmpdir):
        result = run(runner, tmpdir, 'cp', 'not-init', 'also-not-init')
        assert result.output == MSG_STORE_NOT_INITIALISED_ERROR + '\n'


class TestInsert:
    def test_permission_error(self, runner, store):
        result = run(runner, store, 'insert', '--echo', '../no-permission',
                     input='pw\n')
        lines = result.output.split('\n')
        assert len(lines) == 3
        assert lines[0] == 'Enter password for ../no-permission: pw'
        assert lines[1] == MSG_PERMISSION_ERROR
        assert lines[2] == ''

    def test_insert(self, runner, store):
        key_data = 'This is a password for key'
        result = run(runner, store, 'insert', '--echo', 'key',
                     input=key_data + '\n')
        lines = result.output.split('\n')
        assert len(lines) == 2
        assert lines[0] == 'Enter password for key: ' + key_data
        assert lines[1] == ''

        result = run(runner, store, 'show', 'key')
        assert result.output == key_data + '\n'

        key_data = 'Another password for a key'
        result = run(runner, store, 'insert', 'dir/key',
                     input=key_data + '\n' + key_data + '\n')
        result = run(runner, store, 'show', 'dir/key')
        assert result.output == key_data + '\n'

        key_data = 'Final password'
        result = run(runner, store, 'insert', '--echo', 'dir/final',
                     input=key_data + '\n')
        result = run(runner, store, 'show', 'dir/final')
        assert result.output == key_data + '\n'

    def test_force(self, runner, store):
        key_data = 'This is a password for key'
        run(runner, store, 'insert', '--echo', 'key',
            input=key_data + '\n')

        key_data = 'This is the new password'
        result = run(runner, store, 'insert', '--echo', 'key',
                     input=key_data + '\n' + 'n\n')
        lines = result.output.split('\n')
        assert len(lines) == 2
        assert lines[1] == 'Really overwrite {0}? [y/N] '.format(
            str(store.join('key')))

        result = run(runner, store, 'show', 'key')
        assert result.output != key_data + '\n'

        run(runner, store, 'insert', '--echo', '--force', 'key',
            input=key_data + '\n')
        result = run(runner, store, 'show', 'key')
        assert result.output == key_data + '\n'

    def test_multiline(self, runner, store):
        key_data = 'This is\na multiline\n password for\nkey'
        run(runner, store, 'insert', 'key', '--multiline', input=key_data)

        result = run(runner, store, 'show', 'key')
        assert result.output == key_data + '\n'

    def test_alias(self, runner, store):
        result = run(runner, store, 'add')
        lines = result.output.split('\n')
        # As we call __main__.cli directly it's name will be used
        # instead of passpy.
        assert lines[0] == ('Usage: cli add [ --echo,-e | --multiline,-m ]'
                            ' [ --force,-f ] pass-name')
