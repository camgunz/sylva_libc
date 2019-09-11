from collections import OrderedDict

from cdump.parser import Parser


class Definitions:

    @staticmethod
    def SylvaDef(cdefs, cdef):
        if isinstance(cdef, CDefs.Void):
            pass
        if isinstance(cdef, CDefs.Boolean):
            pass
        if isinstance(cdef, CDefs.Integer):
            pass
        if isinstance(cdef, CDefs.FloatingPoint):
            pass
        if isinstance(cdef, CDefs.Array):
            pass
        if isinstance(cdef, CDefs.Reference):
            return SylvaDef(cdefs, cdef.target)
        if isinstance(cdef, CDefs.Pointer):
            pass
        if isinstance(cdef, CDefs.FunctionPointer):
            pass
        if ctype.kind == TypeKind.BLOCKPOINTER:
            return None
        if ctype.kind == TypeKind.INCOMPLETEARRAY:
            pass

    @staticmethod
    def FromLibcFiles(libc_files, libclang=None):
        parser = Parser(libclang)
        cdefs = OrderedDict([
            (cdef.name, cdef)
            for libc_file in libc_files
            for cdef in parser.parse(libc_file)
            if getattr(cdef, 'name')
        ])
        return [SylvaDef(cdefs, cdef) for cdef in cdefs.values()]
