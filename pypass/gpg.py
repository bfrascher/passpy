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

import os

from gnupg import GPG

from pypass.util import _get_parent_dir


def _get_gpg_recipients(path):
    """Get the GPG recipients for the given path.

    :param str path: The folder to get the GPG recipients for.

    :raises: A :exc:`FileNotFoundError` if there is not valid .gpg-id
        file for path.

    :rtype: list
    :returns: The list of IDs of the GPG recipients for the given
        path.

    """
    while True:
        gpg_id_path = os.path.join(path, '.gpg-id')
        if os.path.isfile(gpg_id_path):
            break;
        path = _get_parent_dir(path)

    if path is None or path == '':
        raise FileNotFoundError(
                'You must initialise the password store first!')

    with open(gpg_id_path) as gpg_id_file:
        gpg_recipients = [line.rstrip('\n') for line in gpg_id_file]
    return gpg_recipients


def _read_key(path, gpg_bin, gpg_opts):
    gpg = GPG(gpgbinary=gpg_bin, options=gpg_opts)
    with open(path, 'rb') as key_file:
        return gpg.decrypt_file(key_file).data


def _write_key(path, key_data, gpg_bin, gpg_opts):
    gpg = GPG(gpgbinary=gpg_bin, options=gpg_opts)
    gpg_recipients = _get_gpg_recipients(path)
    key_data_enc = gpg.encrypt(key_data, gpg_recipients).data
    with open(path, 'wb') as key_file:
        key_file.write(key_data_enc)


def _reencrypt_key(path, gpg, gpg_recipients):
    """Reencrypts the key at path.

    :param str path: The path to a gpg encrypted file.

    """
    with open(path, 'rb') as key_file:
        key_data = gpg.decrypt_file(key_file).data
    key_data_enc = gpg.encrypt(key_data, gpg_recipients).data
    with open(path, 'wb') as key_file:
        key_file.write(key_data_enc)


def _reencrypt_path(path, gpg_bin, gpg_opts):
    """Reencrypts the key or keys at or in path.

    If path is a folder all keys inside that folder and it's
    subfolders will be reencrypted.

    :param str path: The key or folder to reencrypt.  If None the
        function will silently fail.

    :param str gpg_bin: The path to the gpg binary.

    :param list gpg_opts: The gpg options.

    :raises: :exc:``FileNotFoundError`` if path does not exist.

    """
    if path is None:
        return
    gpg = GPG(gpgbinary=gpg_bin, options=gpg_opts)
    if os.path.isfile(path):
        gpg_recipients = _get_gpg_recipients(path)
        _reencrypt_key(path, gpg)
    elif os.path.isdir(path):
        for root, dirs, keys in os.walk(path):
            gpg_recipients = _get_gpg_recipients(root)
            for key in keys:
                if not key.endswith('.gpg'):
                    continue
                key_path = os.path.join(root, key)
                _reencrypt_key(key_path, gpg, gpg_recipients)
    else:
        raise FileNotFoundError('{} does not exist.'.format(path))
