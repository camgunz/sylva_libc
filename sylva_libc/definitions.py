from collections import OrderedDict

from cdump import cdefs as CDefs
from cdump.parser import Parser


class Definitions:

    @staticmethod
    def CPointer(name, target):
        pass

    @staticmethod
    def Alias(name, target):
        pass

    @staticmethod
    def ConvertCDef(cdefs, cdef):
        if isinstance(cdef, CDefs.Array):
            return None
        if isinstance(cdef, CDefs.Enum):
            return None
        if isinstance(cdef, CDefs.Function):
            return None
        if isinstance(cdef, CDefs.FunctionPointer):
            return None
        if isinstance(cdef, CDefs.BlockFunctionPointer):
            return None
        if isinstance(cdef, CDefs.Struct):
            return None
        if isinstance(cdef, CDefs.Union):
            return None
        if isinstance(cdef, CDefs.Void):
            print(f'Void: {cdef}')
            return None
        if isinstance(cdef, CDefs.Bool):
            return None
        if isinstance(cdef, CDefs.Integer):
            return None
        if isinstance(cdef, CDefs.FloatingPoint):
            return None
        if isinstance(cdef, CDefs.Pointer):
            print(f'Pointer: {cdef}')
            return None
        if isinstance(cdef, CDefs.Reference):
            try:
                target = cdefs[cdef.target]
            except KeyError:
                print(f'Found builtin: {cdef.target}')
                return None
            return Definitions.ConvertCDef(cdefs, target)
        if isinstance(cdef, CDefs.Typedef):
            if isinstance(cdef.type, CDefs.Pointer):
                return Definitions.CPointer(
                    cdef.name,
                    Definitions.ConvertCDef(cdefs, cdef.type)
                )
            return Definitions.Alias(
                cdef.name,
                Definitions.ConvertCDef(cdefs, cdef.type)
            )
        raise Exception(f'Unknown C definition: {cdef} ({type(cdef)})')

    @staticmethod
    def FromLibcFiles(libc_files, libclang=None):
        parser = Parser(libclang)
        cdefs = OrderedDict([
            (cdef.name, cdef)
            for libc_file in libc_files
            for cdef in parser.parse(libc_file)
            if hasattr(cdef, 'name')
        ])
        return filter(None, [
            Definitions.ConvertCDef(cdefs, cdef)
            for cdef in cdefs.values()
        ])
