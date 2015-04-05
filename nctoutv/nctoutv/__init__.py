# version: major, minor, patch, status (may be absent)
_version = (0, 1, 0, 'dev')

__version__ = '{v[0]}.{v[1]}.{v[2]}'.format(v=_version)

if len(_version) == 4:
    __version__ += '-{}'.format(_version[3])
