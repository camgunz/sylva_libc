from cdump import cdefs as CDefs

from .definitions import Definitions

###
# carray
# cpointer
# cfn
# cfntype
# cstruct
# cenum
# cunion
# cvoid
###

_BUILTIN_TYPES = {
    'char': 'cchar',
    'signed char': 'scchar',
    'unsigned char': 'ucchar',
    ('short', 'short int', 'signed short', 'signed short int'): 'cshort',
    ('unsigned short', 'unsigned short int'): 'cushort',
    ('int', 'signed', 'signed int'): 'cint',
    ('unsigned', 'unsigned int'): 'cuint',
    ('long', 'long int', 'signed long', 'signed long int'): 'clong',
    ('unsigned long', 'unsigned long int'): 'culong',
    ('long long', 'long long int', 'signed long long',
     'signed long long int'): 'clonglong',
    ('unsigned long long', 'unsigned long long int'): 'culonglong',
    'float': 'cfloat',
    'double': 'cdouble',
    'long double': 'clongdouble',
    'float_t': 'cfloat_t',
    'double_t': 'cdouble_t',
    'float _Complex': 'cfloati',
    'double _Complex': 'cdoublei',
    'long double _Complex': 'clongdoublei',
    '_Bool': 'cbool',
    'void': 'cvoid'
}

class StdLib:

    def __init__(self, libc_files, libclang=None):
        self.definitions = Definitions.FromLibcFiles(libc_files, libclang)

    @property
    def builtins(self):
        for cdef in self.definitions:
            if not isinstance(cdef, CDefs.Typedef):
                continue
            if not isinstance(cdef.type, CDefs.Builtin):
                continue
            yield cdef.type
