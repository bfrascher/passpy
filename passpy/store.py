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
# along with this program.  If not, see <http://www.gnu.org/licenses/>._

import os
import re
import shutil

from passpy.git import (
    get_git_repository,
    git_add_path,
    git_remove_path,
    git_init,
    git_config
)

from passpy.gpg import (
    reencrypt_path,
    read_key,
    write_key
)

from passpy.util import (
    trap,
    initialised,
    gen_password,
    copy_move
)


class Store():
    """Python implementation of ZX2C4's password store.
    """
    def __init__(self, gpg_bin='gpg2', git_bin='git',
                 store_dir=os.getenv('PASSWORD_STORE_DIR', '~/.password-store'),
                 use_agent=True, interactive=False, verbose=False):
        """Creates a new Store object.

        :param str gpg_bin: (optional) The path to the gpg
            binary.

        :param str git_bin: (optional) The path to the git binary.
            CURRENTLY DOES NOTHING You will need to set the
            environmental variable GIT_PYTHON_GIT_EXECUTABLE to your
            path to git binary if your git binary not in your PATH
            already.

        :param str store_dir: (optional) The path to the password store.  Will
            use the value of the PASSWORD_STORE_DIR environment variable by
            default, or `~/.password-store`, if not set.

        :param bool use_agent: (optional) Set to ``True`` if you are
            using a gpg agent.

        :param bool interactive: (optional) If ``True`` the user will
            be prompted before overwriting/deleting files.

        :param bool verbose: (optional) If ``True`` additional
            information will be printed to the standard out.

        """
        self.gpg_bin = gpg_bin
        self.git_bin = git_bin

        self.gpg_opts = ['--quiet', '--yes', '--compress-algo=none',
                         '--no-encrypt-to']
        if use_agent:
            self.gpg_opts += ['--batch', '--use-agent']

        self.store_dir = os.path.normpath(os.path.expanduser(store_dir))
        self.repo = get_git_repository(self.store_dir)

        self.interactive = interactive
        self.verbose = verbose

    def __iter__(self):
        return self.iter_dir('')

    def _get_store_name(self, path):
        """Returns the path relative to the store.

        :param str path: The absolute path to an entry in the store.

        :rtype: str
        :returns: `path` relative to
            :attr:`passpy.store.Store.store_dir` without a leading '/'
            and trailing '.gpg' if any.

        """
        path = os.path.relpath(path, self.store_dir)
        # Keys are identified without their file ending.
        if path.endswith('.gpg'):
            path = path[:-4]
        return path

    def is_init(self):
        gpg_id_path = os.path.join(self.store_dir, '.gpg-id')
        if os.path.isfile(gpg_id_path):
            return True
        return False

    @trap('path')
    def init_store(self, gpg_ids, path=None):
        """Initialise the password store or a subdirectory with the gpg ids.

        :param list gpg_ids: The list of gpg ids to encrypt the
            password store with.  If the list is empty, the current
            gpg id will be removed from the directory in path or root,
            if path is None.

        :param str path: (optional) If given, the gpg ids will only be
            set for the given directory.  The path is relative to
            :attr:`passpy.store.Store.store_dir`.

        :raises ValueError: if the there is a problem with `path`.

        :raises FileExistsError: if
            :attr:`passpy.store.Store.store_dir` already exists and is
            a file.

        :raises FileNotFoundError: if the current gpg id should be
            deleted, but none exists.

        :raises OSError: if the directories in path do not exist and
            can't be created.

        """
        if path is None:
            path = self.store_dir
        else:
            path = os.path.normpath(os.path.join(self.store_dir, path))

        if os.path.exists(path):
            if not os.path.isdir(path):
                raise FileExistsError('{0} exists but is not a directory.'.format(path))

        # Ensure that gpg_ids is a list so that the later .join does
        # not accidentally join single letters of a string.
        if gpg_ids is not None and not isinstance(gpg_ids, list):
            gpg_ids = [gpg_ids]

        gpg_id_path = os.path.join(path, '.gpg-id')

        # Delete current gpg id.
        if gpg_ids is None or len(gpg_ids) == 0:
            if not os.path.isfile(gpg_id_path):
                raise FileNotFoundError(('{0} does not exist and so'
                                         'cannot be removed.')
                                        .format(gpg_id_path))
            os.remove(gpg_id_path)
            git_remove_path(self.repo, [gpg_id_path],
                            'Deinitialize {0}.'.format(gpg_id_path),
                            recursive=True, verbose=self.verbose)
            # The password store should not contain any empty directories,
            # so we try to remove as many directories as we can.  Any
            # nonempty ones will throw an error and will not be
            # removed.
            shutil.rmtree(path, ignore_errors=True)
        else:
            os.makedirs(path)
            # pass needs the gpg id file to be newline terminated.
            with open(gpg_id_path, 'w') as gpg_id_file:
                gpg_id_file.write('\n'.join(gpg_ids))
                gpg_id_file.write('\n')
            git_add_path(self.repo, gpg_id_path, 'Set GPG id to {0}.'
                         .format(', '.join(gpg_ids)), verbose=self.verbose)

        reencrypt_path(path, gpg_bin=self.gpg_bin,
                       gpg_opts=self.gpg_opts)
        git_add_path(self.repo, path,
                     'Reencrypt password store using new GPG id {0}.'
                     .format(', '.join(gpg_ids)), verbose=self.verbose)

    @initialised
    def init_git(self):
        """Initialise git for the password store.

        Silently fails if :attr:`passpy.store.Store.repo` is not
        ``None``.

        """
        if self.repo is not None:
            return
        self.repo = git_init(self.store_dir)
        git_add_path(self.repo, self.store_dir,
                     'Add current contents of password store.',
                     verbose=self.verbose)
        attributes_path = os.path.join(self.store_dir, '.gitattributes')
        with open(attributes_path, 'w') as attributes_file:
            attributes_file.write('*.gpg diff=gpg\n')
        git_add_path(self.repo, attributes_path,
                     'Configure git repository for gpg file diff.',
                     verbose=self.verbose)
        git_config(self.repo, '--local', 'diff.gpg.binary', 'true')
        git_config(self.repo, '--local', 'diff.gpg.textconf',
                   '"' + self.gpg_bin + ' -d ' + ' '.join(self.gpg_opts) + '"')

    @initialised
    def git(self, method, *args, **kwargs):
        if method == 'init':
            self.init_git()
        else:
            res = self.repo.git._call_process(method, *args, **kwargs)
            if self.verbose:
                print(res)

    @initialised
    @trap(1)
    def get_key(self, path):
        """Reads the data of the key at path.

        :param str path: The path to the key (without '.gpg' ending)
            relative to :attr:`passpy.store.Store.store_dir`.

        :rtype: str
        :returns: The key data as a string or ``None``, if the key
            does not exist.

        :raises FileNotFoundError: if `path` is not a file.

        """
        if path is None or path == '':
            return None
        path = os.path.normpath(path)

        key_path = os.path.join(self.store_dir, path + '.gpg')
        if os.path.isfile(key_path):
            return read_key(key_path, self.gpg_bin, self.gpg_opts)
        raise FileNotFoundError('{0} is not in the password store.'
                                .format(path))

    @initialised
    @trap(1)
    def set_key(self, path, key_data, force=False):
        """Add a key to the store or update an existing one.

        :param str path: The key to write.

        :param str key_data: The data of the key.

        :param bool foce: (optional) If ``True`` path will be
            overwritten if it exists.

        :raises FileExistsError: if a key already exists for path and
            overwrite is ``False``.

        """
        if path is None or path == '':
            return
        path = os.path.normpath(path)

        key_path = os.path.join(self.store_dir, path + '.gpg')
        key_dir = os.path.dirname(key_path)
        if os.path.exists(key_path) and not force:
            raise FileExistsError('An entry already exists for {0}.'
                                  .format(path))

        os.makedirs(os.path.join(self.store_dir, key_dir), exist_ok=True)
        write_key(key_path, key_data, self.gpg_bin, self.gpg_opts)

        git_add_path(self.repo, key_path,
                     'Add given password for {0} to store.'.format(path),
                     verbose=self.verbose)

    @initialised
    @trap(1)
    def remove_path(self, path, recursive=False, force=False):
        """Removes the given key or directory from the store.

        :param str path: The key or directory to remove.  Use '' to
            delete the whole store.

        :param bool recursive: (optional) Set to ``True`` if nonempty
            directories should be removed.

        :param bool force: (optional) If ``True`` the user will never
            be prompted for deleting a file or directory, even if
            :attr:`passpy.store.Store.interactive` is set.

        """
        key_path = os.path.join(self.store_dir, path)
        key_path = os.path.normpath(key_path)
        if os.path.isdir(key_path):
            if self.interactive and not force:
                answer = input('Really delete {0}? [y/N] '.format(path))
                if answer.lower() != 'y':
                    return
            if recursive:
                shutil.rmtree(key_path)
            else:
                os.rmdir(key_path)
        else:
            key_path += '.gpg'
            if not os.path.isfile(key_path):
                raise FileNotFoundError('{0} is not in the password store.'
                                        .format(path))
            if self.interactive and not force:
                answer = input('Really delete {0}? [y/N] '.format(path))
                if answer.lower() != 'y':
                    return
            os.remove(key_path)

        if self.verbose:
            print('removed {0}'.format(path))

        if not os.path.exists(key_path):
            git_remove_path(self.repo, key_path,
                            'Remove {0} from store.'.format(path),
                            recursive=recursive, verbose=self.verbose)

    @initialised
    @trap(1)
    def gen_key(self, path, length, symbols=True, force=False,
                inplace=False):
        """Generate a new password for a key.

        :param str path: The path of the key.

        :param int length: The length of the new password.

        :param bool symbols: (optional) If ``True`` non alphanumeric
            characters will also be used in the new password.

        :param bool force: (optional) If ``True`` an existing key at
            `path` will be overwritten.

        :param bool inplace: (optional) If ``True`` only the first
            line of an existing key at `path` will be overwritten with
            the new password.

        """
        if path is None or path == '':
            return None
        path = os.path.normpath(path)
        key_path = os.path.join(self.store_dir, path + '.gpg')
        key_dir = os.path.dirname(key_path)
        if os.path.exists(key_path) and not (force or inplace):
            if self.interactive:
                answer = input('An entry already exists for {0}. '
                               'Overwrite it? [y/N] '.format(path))
                if answer.lower() != 'y':
                    return None
            else:
                raise FileExistsError('An entry already exists for {0}.'
                                      .format(path))

        os.makedirs(os.path.join(self.store_dir, key_dir), exist_ok=True)

        password = gen_password(length, symbols=symbols)
        action = 'Add'
        if not inplace:
            write_key(key_path, password, self.gpg_bin, self.gpg_opts)
            action = 'Add'
        else:
            action = 'Replace'
            key_data = read_key(key_path, gpg_bin=self.gpg_bin,
                                gpg_opts=self.gpg_opts)
            lines = key_data.split('\n')
            lines[0] = password
            write_key(key_path, '\n'.join(lines), gpg_bin=self.gpg_bin,
                      gpg_opts=self.gpg_opts)

        git_add_path(self.repo, key_path,
                     '{0} generated password for {1}.'.format(action, path),
                     verbose=self.verbose)
        return password

    @initialised
    @trap(1)
    @trap(2)
    def _copy_move_path(self, old_path, new_path, force=False,
                        move=False):
        """Copies or moves a key or directory within the password store.

        :param str old_path: The current path of the key or directory.

        :param str new_path: The new path of the key or directory.  If
            `new_path` ends in a trailing '/' it will always be
            treated as a directory.

        :param bool force: If ``True`` any existing key or directory at
            `new_path` will be overwritten.

        :param bool move: If ``True`` the key or directory will be
            moved.  If ``False`` the key or directory will be copied
            instead.

        """
        old_path = os.path.normpath(old_path)
        new_path = os.path.normpath(new_path)
        old_path_full = os.path.join(self.store_dir, old_path)
        new_path_full = os.path.join(self.store_dir, new_path)

        if not os.path.isdir(old_path_full):
            old_path_full += '.gpg'
            if not (os.path.isdir(new_path_full)
                    or new_path_full.endswith('/')):
                new_path_full += '.gpg'

        new_path_full = copy_move(old_path_full, new_path_full, force,
                                  move, self.interactive,
                                  self.verbose)
        if new_path_full is None:
            return

        if os.path.exists(new_path_full):
            reencrypt_path(new_path_full, gpg_bin=self.gpg_bin,
                           gpg_opts=self.gpg_opts)

        action = 'Copy'
        if move:
            action = 'Rename'
            shutil.rmtree(old_path_full, ignore_errors=True)
            if not os.path.exists(old_path_full):
                git_remove_path(self.repo, old_path_full, '',
                                recursive=True, commit=False)

        git_add_path(self.repo, new_path_full, '{0} {1} to {2}.'
                     .format(action, old_path, new_path),
                     verbose=self.verbose)


    def copy_path(self, old_path, new_path, force=False):
        """Copies a key or directory within the password store.

        :param str old_path: The current path of the key or directory.

        :param str new_path: The new path of the key or directory.  If
            `new_path` ends in a trailing '/' it will always be
            treated as a directory.

        :param bool force: If ``True`` any existing key or directory at
            `new_path` will be overwritten.

        """
        self._copy_move_path(old_path, new_path, force, False)

    def move_path(self, old_path, new_path, force=False):
        """Moves a key or directory within the password store.

        :param str old_path: The current path of the key or directory.

        :param str new_path: The new path of the key or directory.  If
            `new_path` ends in a trailing '/' it will always be
            treated as a directory.

        :param bool force: If ``True`` any existing key or directory at
            `new_path` will be overwritten.

        """
        self._copy_move_path(old_path, new_path, force, True)

    @initialised
    @trap(1)
    def list_dir(self, path):
        """Returns all directory and key entries for the given path.

        :param str path: The directory to list relative to
            :attr:`passpy.store.Store.store_dir`

        :rtype: (list, list)
        :returns: Two lists, the first for directories, the second for
            keys.  ``None`` if `path` is not a directory.

        :raises FileNotFoundError: if `path` is not a directory in the
            password store.

        """
        path = os.path.normpath(path)
        path_dir = os.path.join(self.store_dir, path)
        if path is None or not os.path.isdir(path_dir):
            raise FileNotFoundError('{0} is not a directory in the '
                                    'password store.'.format(path))

        dirs = []
        keys = []

        # We want to return the entries alphabetically sorted.
        for entry in sorted(os.listdir(path_dir), key=str.lower):
            if entry.startswith('.'):
                continue
            entry_path = os.path.join(path_dir, entry)
            if os.path.isdir(entry_path):
                dirs.append(self._get_store_name(entry_path))
            elif os.path.isfile(entry_path) and entry.endswith('.gpg'):
                # Keys are named without their ending.
                keys.append(self._get_store_name(entry_path))

        return dirs, keys

    @initialised
    @trap(1)
    def iter_dir(self, path):
        path = os.path.normpath(path)
        path_dir = os.path.join(self.store_dir, path)
        if path is None or not os.path.isdir(path_dir):
            raise FileNotFoundError('{0} is not a directory in the '
                                    'password store.'.format(path))

        # List keys in lexicographical order.
        entries = sorted(os.listdir(path_dir), key=str.lower)
        for entry in entries:
            # Ignore hidden files and directories as pass does the same.
            if entry.startswith('.'):
                continue
            entry_path = os.path.join(path_dir, entry)
            entry_path_rel = os.path.relpath(entry_path, self.store_dir)
            if os.path.isdir(entry_path):
                yield from self.iter_dir(entry_path_rel)
            # pass also shows files that do not end on .gpg in
            # it's overview, but will throw an error if trying to
            # access these files.  As this would make it harder to
            # automatically iterate over the keys in the store, we
            # just show files, that (probably) are in the store.
            elif entry.endswith('.gpg'):
                yield entry_path_rel[:-4]

    @initialised
    def find(self, names):
        """Find keys by name.

        Finds any keys in the password store that contain any one
        entry in `names`.

        :param names: The name or names to find keys for.
        :type names: str or list

        :rtype: list
        :returns: A list of keys whose name contain any one entry in
            `names`.

        """
        if names is None:
            return []
        if not isinstance(names, list):
            names = [names]

        keys = []
        for key in self:
            for name in names:
                if key.find(name) != -1:
                    keys.append(key)
                    # No need to append a key twice.
                    break
        return keys

    @initialised
    def search(self, term):
        """Search through all keys.

        :param str term: The term to search for.  The term will be
            compiled as a regular expression.

        :rtype: dict
        :returns: The dictionary has an entry for each key, that
            matched the given term.  The entry for that key then
            contains a list of tuples with the line the term was found
            on and the match object.

        """
        if term is None:
            return {}

        regex = re.compile(term)
        results = {}
        for key in self:
            data = self.get_key(key)
            for line in data.split('\n'):
                match = regex.search(line)
                if match is not None:
                    if key in results:
                        results[key].append((line, match))
                    else:
                        results[key] = [(line, match)]

        return results
