# pypass -- A Python implementation of ZX2C4's pass.
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

import logging
import os
import shutil

from pypass.git import (
    _get_git_repository,
    _git_add_file,
    _git_remove_path,
    _git_init,
    _git_config
)

from pypass.gpg import (
    _reencrypt_path,
    _read_key,
    _write_key
)

from pypass.util import (
    trap,
    _get_parent_dir
)


class StoreEntry():
    """Represents a folder or file in the password store.
    """
    def __init__(self, name, path, is_key):
        """Creates a new StoreEntry object.

        :param str name: Name of the folder or file.
        :param str path: The path to the file or folder relative to `store_dir`.
        :param bool is_key: Indicates, whether the entry is a key or a folder.
        """
        self.name = name
        self.path = path
        self.is_key_ = is_key

    def is_dir(self):
        return not self.is_key_

    def is_key(self):
        return self.is_key_

    def get_name(self):
        return self.name

    def get_path(self):
        return self.path


class Store():
    """Python implementation of ZX2C4's password store.
    """
    def __init__(self, gpg_bin='gpg', git_bin='git', **kwargs):
        """Creates a new Store object.

        :param str gpg_bin: (optional) The path to the gpg
            binary. Default: 'gpg'

        :param str git_bin: (optional) The path to the git
            binary. Default: 'git'

        :param str store_dir: (optional) The path to the password
            store. Assumes '~/.password-store' if no value is given.

        :param bool debug: (optional) Set to ``True`` to enable
            debugging information in logs.

        :param bool use_agent: (optional) Set to ``True`` if you are
            using a gpg agent.

        """
        if 'debug' in kwargs:
            lvl = logging.DEBUG
        else:
            lvl = logging.WARNING
        logging.basicConfig(filename='pass.log', level=lvl)

        self.gpg_bin = gpg_bin
        self.git_bin = git_bin

        self.gpg_opts = ['--quiet', '--yes', '--compress-algo=none',
                         '--no-encrypt-to']
        if 'use_agent' in kwargs:
            self.gpg_opts += ['--batch', '--use-agent']

        if 'store_dir' in kwargs:
            self.store_dir = kwargs['store_dir']
        else:
            self.store_dir = os.path.join(os.path.expanduser('~'),
                                          '.password-store')

        self.repo = _get_git_repository(self.store_dir)

    def __iter__(self):
        for root, dirs, keys in os.walk(self.store_dir):
            # Ensure we walk through the folders and keys in
            # lexicographic order.
            dirs.sort()
            keys.sort()
            for key in keys:
                if key.endswith('.gpg'):
                    # Keys are always identified without the '.gpg'
                    # ending and are relative to the `store_dir`.
                    relative_root = root.replace(self.store_dir, '', 1)
                    if relative_root.startswith('/'):
                        relative_root = relative_root[1:]
                    yield os.path.join(relative_root, key[:-4])

    @trap('path')
    def init_store(self, gpg_ids, path=None):
        """Initialise the password store or a subfolder with the gpg ids.

        :param list gpg_ids: The list of gpg ids to encrypt the
            password store with.  If the list is empty, the current
            gpg id will be removed from the folder in path or root, if
            path is None.

        :param str path: (optional) If given, the gpg ids will only be
            set for the given folder.  The path is relative to
            ``store_dir``.

        :raises: A :exc:`ValueError` if the there is a problem with
            ``path``.

        :raises: :exc:`FileExistsError` if ``store_dir`` already
            exists and is a file.

        :raises: A :exc:`FileNotFoundError` if the current gpg id
            should be deleted, but none exists.

        :raises: A :exc:`os.OSError` if the directories in path do not
            exist and can't be created.

        """
        if path is not None:
            if not os.path.isdir(path) and os.path.exists(path):
                raise FileExistsError('{}/{} exists but is not a directory.'
                                      .format(self.store_dir, path))
        else:
            path = self.store_dir

        gpg_id_dir = os.join(self.store_dir, path)
        gpg_id_path = os.join(gpg_id_dir, '.gpg-id')

        # Delete current gpg id.
        if gpg_ids is None or len(gpg_ids) == 0:
            if not os.path.isfile(gpg_id_path):
                raise FileNotFoundError(('{} does not exist and so'
                                         'cannot be removed.')
                                        .format(gpg_id_path))
            os.remove(gpg_id_path)
            _git_remove_path(self.repo, [gpg_id_path],
                             'Deinitialize {}.'.format(gpg_id_path),
                             recursive=True)
            # The password store should not contain any empty folders,
            # so we try to remove as many folders as we can.  Any
            # nonempty ones will throw an error and will not be
            # removed.
            shutil.rmtree(gpg_id_dir, ignore_errors=True)
        else:
            os.makedirs(gpg_id_dir)
            with open(gpg_id_path, 'w') as gpg_id_file:
                gpg_id_file.writelines(gpg_ids)
            _git_add_file(self.repo, gpg_id_file, 'Set GPG id to {}.'
                          .format(', '.join(gpg_ids)))

        _reencrypt_path(gpg_id_dir)
        _git_add_file(self.repo, gpg_id_path,
                      'Reencrypt password store using new GPG id {}.'
                      .format(', '.join(gpg_ids)))

    def init_git(self):
        """Initialise git for ``store_dir``.

        Silently fails if ``repo`` is not None.
        """
        if self.repo is not None:
            return
        self.repo = _git_init(self.store_dir)
        _git_add_file(self.repo, self.store_dir,
                      'Add current contents of password store.')
        attributes_path = os.path.join(self.store_dir, '.gitattributes')
        with open(attributes_path) as attributes_file:
            attributes_file.write('*.gpg diff=gpg')
        _git_add_file(self.repo, attributes_path,
                      'Configure git repository for gpg file diff.')
        _git_config(self.repo, '--local', 'diff.gpg.binary', 'true')
        _git_config(self.repo, '--local', 'diff.gpg.textconf',
                   '"' + self.gpg_bin + ' -d ' + ' '.join(self.gpg_opts) + '"')

    @trap(1)
    def get_key(self, path):
        """Reads the data of the key at path.

        :param str path: The path to the key (without '.gpg'
            ending) relative to ``store_dir``.

        :rtype: str
        :returns: The key data as a string or None, if the key
            does not exist.

        :raises: :exc:`FileNotFoundError` if path is not a file.

        :raises: :exc:`pypass.util.OutsideStoreError` if path points
            outside of ``store_dir``.

        """
        if path is None:
            return None

        key_path = os.path.join(self.store_dir, path + '.gpg')
        if os.path.isfile(key_path):
            return _read_key(key_path, self.gpg_bin, self.gpg_opts)
        raise FileNotFoundError('{} is not in the password store.'
                                .format(path))

    @trap(1)
    def set_key(self, path, key_data, overwrite=False):
        """Add a key to the store or update an existing one.

        :param str path: The key to write.

        :param str key_data: The data of the key.

        :param bool overwrite: (optional) If `True` path will be
            overwritten if it exists.  Default: `False`.

        :raises: :exc:`FileExistsError` if a key already exists for
            path and overwrite is `False`.

        """
        if path is None:
            return

        key_path = os.path.join(self.store_dir, path + '.gpg')
        key_dir = _get_parent_dir(path)
        if os.path.exists(key_path) and not overwrite:
            raise FileExistsError('An entry already exists for {}.'
                                  .format(path))

        os.makedirs(os.path.join(self.store_dir, key_dir), exist_ok=True)
        _write_key(key_path, key_data, self.gpg_bin, self.gpg_opts)

        _git_add_file(self.repo, key_path,
                      'Add given password for {} to store.'.format(path))

    @trap(1)
    def remove_path(self, path, recursive=False):
        """Removes the given key or folder from the store.

        :param str path: The key or folder to remove.  Use `None` or
            '' to delete the whole store.

        :param bool recursive: (optional) Set to `True` if nonempty
            directories should be removed.

        """
        key_path = os.path.join(self.store_dir, path)
        if os.path.isdir(key_path):
            if recursive:
                shutil.rmtree(key_path)
            else:
                os.rmdir(key_path)
        else:
            key_path += '.gpg'
            if not os.path.isfile(key_path):
                raise FileNotFoundError('{} is not in the password store.'
                                        .format(path))
            os.remove(key_path)

        if not os.exists(key_path):
            _git_remove_path(self.repo, [key_path],
                             'Remove {} from store.'.format(path),
                             recursive=recursive)

    @trap(1)
    def gen_key(self, path):
        pass

    @trap(1)
    def list_dir(self, path):
        pass
