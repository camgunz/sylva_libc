import enum

from abc import ABC, abstractmethod

from cdump import cdefs as CDefs
from cdump.parser import Parser


class SylvaDef(ABC):

    @abstractmethod
    def emit_def(self):
        ...


class SylvaRef(ABC):

    @abstractmethod
    def emit_ref(self):
        ...


class AnonymousDef(SylvaDef, SylvaRef):

    def emit_ref(self):
        return self.emit_def()


class Alias(SylvaDef):

    __slots__ = (
        'name',
        'target',
    )

    def __init__(self, name, target):
        self.name = name
        self.target = target

    def emit_def(self):
        return f'alias {self.name}: {self.target.emit_ref()}'


class CAnonymousArray(AnonymousDef):

    __slots__ = ('element_type', 'element_count')

    def __init__(self, element_type, element_count):
        self.element_type = element_type
        self.element_count = element_count

    def emit_def(self):
        et = self.element_type
        ec = self.element_count
        if ec is None:
            return f'carray[{et.emit_ref()}...]'
        return f'carray[{et.emit_ref()} * {ec}]'


class CArray(SylvaDef, SylvaRef):

    __slots__ = ('name', 'element_type', 'element_count')

    def __init__(self, name, element_type, element_count):
        self.name = name
        self.element_type = element_type
        self.element_count = element_count

    def emit_def(self):
        name = self.name.replace(' ', '_')
        et = self.element_type
        ec = self.element_count
        if ec is None:
            return f'carray {name} [{et.emit_ref()}...]'
        return f'carray {name} [{et.emit_ref()} * {ec}]'

    def emit_ref(self):
        return self.name.replace(' ', '_')


class CPointer(SylvaRef):

    __slots__ = ('base_type', 'is_const')

    def __init__(self, base_type, is_const):
        self.base_type = base_type
        self.is_const = is_const

    def emit_ref(self):
        if self.base_type.is_const:
            return f'cptr({self.base_type.emit_ref()})'
        return f'cptr({self.base_type.emit_ref()}!)'


class CEnum(SylvaDef):

    def __init__(self, type, values):
        self.type = type
        self.values = values

    def emit_def(self):
        return '\n'.join([
            'const {name} {type.emit_ref()}' for name,
            type in self.values.items()
        ])


class CFunctionParameter(SylvaDef):

    __slots__ = ('name', 'type')

    def __init__(self, name, type):
        self.name = name
        self.type = type

    def emit_def(self):
        return f'{self.name}: {self.type.emit_ref()}'


class CFunctionParameterType(SylvaDef):

    __slots__ = ('type',)

    def __init__(self, type):
        self.type = type

    def emit_def(self):
        if self.type.is_const:
            return f'{self.type.emit_ref()}'
        return f'{self.type.emit_ref()}!'


class CFunction(SylvaDef, SylvaRef):

    __slots__ = ('name', 'parameters', 'return_type')

    def __init__(self, name, parameters, return_type):
        self.name = name
        self.parameters = parameters
        self.return_type = return_type

    def emit_def(self):
        if (isinstance(self.return_type, CScalarType) and
                self.return_type.type == CScalarType.BuiltinTypes.VOID):
            # pylint: disable=consider-using-f-string
            return (
                'cfn {}({})'.format(
                    self.name,
                    ', '.join([param.emit_def() for param in self.parameters])
                )
            )
        # pylint: disable=consider-using-f-string
        return (
            'cfn {}({}): {}'.format(
                self.name,
                ', '.join([param.emit_def() for param in self.parameters]),
                self.return_type.emit_ref()
            )
        )

    def emit_ref(self):
        return self.name


class CFunctionType(SylvaDef, SylvaRef):

    __slots__ = ('parameters', 'return_type')

    def __init__(self, parameters, return_type, is_block=False):
        self.parameters = parameters
        self.return_type = return_type
        self.is_block = is_block

    def emit(self):
        keyword = 'cblockfntype' if self.is_block else 'cfntype'
        if (isinstance(self.return_type, CScalarType) and
                self.return_type.type == CScalarType.BuiltinTypes.VOID):
            # pylint: disable=consider-using-f-string
            return (
                '{}({})'.format(
                    keyword,
                    ', '.join([param.emit_def() for param in self.parameters])
                )
            )
        # pylint: disable=consider-using-f-string
        return (
            '{}({}): {}'.format(
                keyword,
                ', '.join([param.emit_def() for param in self.parameters]),
                self.return_type.emit_ref()
            )
        )

    def emit_def(self):
        return self.emit()

    def emit_ref(self):
        return self.emit()


class Reference(SylvaRef):

    __slots__ = ('target', 'is_const')

    def __init__(self, target, is_const):
        self.target = target
        self.is_const = is_const

    def emit_ref(self):
        return self.target.replace(' ', '_')


class CScalarType(SylvaRef):

    __slots__ = ('name', 'size')

    class BuiltinTypes(enum.Enum):
        VOID = enum.auto()
        BOOL = enum.auto()
        INTEGER = enum.auto()
        FLOAT = enum.auto()
        COMPLEX = enum.auto()

    def __init__(
        self, type, size, is_signed, is_const, is_bitfield, bitfield_width
    ):
        self.type = type
        self.size = size
        self.is_signed = is_signed
        self.is_const = is_const
        self.is_bitfield = is_bitfield
        self.bitfield_width = bitfield_width

    def emit_ref(self):
        if self.type == self.BuiltinTypes.VOID:
            return 'cvoid'
        if self.type == self.BuiltinTypes.BOOL:
            return 'bool'
        if self.type == self.BuiltinTypes.INTEGER:
            if self.size is None:
                return 'int' if self.is_signed else 'uint'
            base = f'i{self.size*8}' if self.is_signed else f'u{self.size*8}'
            if not self.is_bitfield:
                return base
            return f'cbitfield({base}, {self.bitfield_width})'
        if self.type == self.BuiltinTypes.FLOAT:
            return f'f{self.size * 8}'
        if self.type == self.BuiltinTypes.COMPLEX:
            return f'c{self.size * 8}'
        raise Exception(f'Unsupported builtin type {self.type}')

    @classmethod
    def FromCDef(cls, cdef):
        if isinstance(cdef, CDefs.Void):
            builtin_type = cls.BuiltinTypes.VOID
        elif isinstance(cdef, CDefs.Bool):
            builtin_type = cls.BuiltinTypes.BOOL
        elif isinstance(cdef, CDefs.Integer):
            builtin_type = cls.BuiltinTypes.INTEGER
        elif isinstance(cdef, CDefs.FloatingPoint):
            builtin_type = cls.BuiltinTypes.FLOAT
        elif isinstance(cdef, CDefs.Complex):
            builtin_type = cls.BuiltinTypes.COMPLEX
        else:
            raise ValueError(f'Unsupported builtin type {type(cdef)}')
        return cls(
            builtin_type,
            cdef.size,
            cdef.is_signed,
            cdef.is_const,
            cdef.is_bitfield if hasattr(cdef, 'is_bitfield') else False,
            cdef.bitfield_width if hasattr(cdef, 'bitfield_width') else None
        )


class CAnonymousStruct(AnonymousDef):

    __slots__ = ('fields',)

    def __init__(self, fields):
        self.fields = fields

    def emit_def(self):
        if self.fields:
            return '\n'.join([
                'cstruct {',
                ',\n'.join([
                    f'  {name}: {type.emit_ref()}' for name,
                    type in self.fields.items()
                ]),
                '}'
            ])
        return 'cstruct {}'


class CStruct(SylvaDef, SylvaRef):

    __slots__ = ('name', 'fields')

    def __init__(self, name, fields):
        self.name = name
        self.fields = fields

    def emit_def(self):
        if self.fields:
            return '\n'.join([
                f'cstruct {self.name.replace(" ", "_")} {{',
                ',\n'.join([
                    f'  {name}: {type.emit_ref()}' for name,
                    type in self.fields.items()
                ]),
                '}'
            ])
        return f'cstruct {self.name.replace(" ", "_")} {{}}'

    def emit_ref(self):
        return self.name.replace(' ', '_')


class CAnonymousUnion(AnonymousDef):

    __slots__ = ('fields',)

    def __init__(self, fields):
        self.fields = fields

    def emit_def(self):
        if self.fields:
            return '\n'.join([
                'cunion {',
                ',\n'.join([
                    f'  {name}: {type.emit_ref()}' for name,
                    type in self.fields.items()
                ]),
                '}'
            ])
        return 'cunion {}'


class CUnion(SylvaDef, SylvaRef):

    __slots__ = ('name', 'fields')

    def __init__(self, name, fields):
        self.name = name
        self.fields = fields

    def emit_def(self):
        if self.fields:
            return '\n'.join([
                f'cunion {self.name.replace(" ", "_")} {{',
                ',\n'.join([
                    f'  {name}: {type.emit_ref()}' for name,
                    type in self.fields.items()
                ]),
                '}'
            ])
        return f'cunion {self.name.replace(" ", "_")}'

    def emit_ref(self):
        return self.name.replace(' ', '_')


class Const(SylvaDef, SylvaRef):

    __slots__ = ('name', 'type', 'value')

    def __init__(self, name, type, value):
        self.name = name
        self.type = type
        self.value = value

    def emit_def(self):
        return f'const {self.name}: {self.value}{self.type.emit_ref()}'

    def emit_ref(self):
        return self.name


class DefinitionBuilder:

    def __init__(self, cdefs):
        self._cdefs = cdefs
        self._defs = {}
        self._built = False

    @property
    def cdefs(self):
        return self._cdefs

    @cdefs.setter
    def cdefs(self, new_cdefs):
        self._cdefs = new_cdefs
        self._defs = {}
        self._built = False

    @property
    def built(self):
        return self._built

    @property
    def defs(self):
        return self._defs

    def build(self):
        if self._built:
            return
        for cdef in self.cdefs:
            self._process_cdef(cdef)
        self._built = True

    def _process_cdef(self, cdef):
        if isinstance(cdef, CDefs.Array):
            if cdef.name is None:
                return CAnonymousArray(
                    self._process_cdef(cdef.element_type), cdef.element_count
                )
            carray = CArray(
                cdef.name,
                self._process_cdef(cdef.element_type),
                cdef.element_count
            )
            self.defs[carray.name] = carray
            return carray
        if isinstance(cdef, CDefs.Enum):
            vals = []
            for name, value in cdef.values.items():
                val = Const(name, self._process_cdef(cdef.type), value)
                self.defs[val.name] = val
                vals.append(val)
            return vals
        if isinstance(cdef, CDefs.Function):
            cfunction = CFunction(
                cdef.name,
                [ # yapf: disable
                    CFunctionParameter(name, self._process_cdef(ctype))
                    for name, ctype in cdef.parameters.items()
                ],
                self._process_cdef(cdef.return_type)
            )
            self.defs[cfunction.name] = cfunction
            return cfunction
        if isinstance(cdef, CDefs.FunctionPointer):
            return CFunctionType( # yapf: disable
                [
                    CFunctionParameter(name, self._process_cdef(ctype))
                    for name, ctype in cdef.parameters.items()
                ],
                self._process_cdef(cdef.return_type)
            )
        if isinstance(cdef, CDefs.Pointer):
            return CPointer(
                self._process_cdef(cdef.base_type),
                cdef.is_const,
            )
        if isinstance(cdef, CDefs.Reference):
            return Reference(cdef.target, cdef.is_const)
        if isinstance(cdef, CDefs.ScalarType):
            return CScalarType.FromCDef(cdef)
        if isinstance(cdef, CDefs.Struct):
            if not cdef.name:
                return CAnonymousStruct({
                    name: self._process_cdef(ctype)
                    for name,
                    ctype in cdef.fields.items()
                })
            cstruct = CStruct(
                cdef.name,
                {
                    name: self._process_cdef(ctype)
                    for name,
                    ctype in cdef.fields.items()
                    if name != 'packed'
                }
            )
            self.defs[cstruct.name] = cstruct
            return cstruct
        if isinstance(cdef, CDefs.Typedef):
            underlying_type = self._process_cdef(cdef.type)
            if isinstance(underlying_type, Reference) and \
                    underlying_type.target.startswith('enum '):
                underlying_type = CScalarType(
                    type=CScalarType.BuiltinTypes.INTEGER,
                    size=None,
                    is_signed=True,
                    is_const=True,
                    is_bitfield=False,
                    bitfield_width=None
                )
            elif isinstance(underlying_type, CArray):
                underlying_type = CAnonymousArray(
                    underlying_type.element_type,
                    underlying_type.element_count
                )
            alias = Alias(cdef.name, underlying_type)
            self.defs[alias.name] = alias
            return alias
        if isinstance(cdef, CDefs.Union):
            if cdef.name:
                union = CUnion(
                    cdef.name,
                    {
                        name: self._process_cdef(ctype)
                        for name,
                        ctype in cdef.fields.items()
                    }
                )
                self.defs[union.name] = union
            else:
                union = CAnonymousUnion({
                    name: self._process_cdef(ctype)
                    for name,
                    ctype in cdef.fields.items()
                })
            return union
        if isinstance(cdef, CDefs.BlockFunctionPointer):
            return CFunctionType([
                CFunctionParameter(name, self._process_cdef(ctype)) for name,
                ctype in cdef.parameters.items()
            ],
                                 self._process_cdef(cdef.return_type),
                                 is_block=True)
        raise Exception(f'Unknown C definition: {cdef} ({type(cdef)})')

    @classmethod
    def FromLibcFiles(cls, libc_files, preprocessor, libclang=None):
        parser = Parser(preprocessor, libclang)
        return cls([
            cdef for libc_file in libc_files
            for cdef in parser.parse(libc_file)
        ])
