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


class Alias(SylvaDef):

    __slots__ = ('name', 'target',)

    def __init__(self, name, target):
        self.name = name
        self.target = target

    def emit_def(self):
        return f'alias {self.name}: {self.target.emit_ref()}'


class Array(SylvaRef):

    __slots__ = ('element_type', 'element_count')

    def __init__(self, element_type, element_count):
        self.element_type = element_type
        self.element_count = element_count

    def emit_ref(self):
        if self.element_count is not None:
            return f'{self.element_type.emit_ref()}[{self.element_count}]'
        return f'{self.element_type.emit_ref()}[]'


class CPointer(SylvaRef):

    __slots__ = ('base_type', 'is_const')

    def __init__(self, base_type, is_const):
        self.base_type = base_type
        self.is_const = is_const

    def emit_ref(self):
        if self.base_type.is_const:
            return f'cptr({self.base_type.emit_ref()})'
        return f'cptr({self.base_type.emit_ref()}!)'


# [TODO] I think this should decompose into some vals earlier
class CEnum(SylvaDef):

    def __init__(self, type, values):
        self.type = type
        self.values = values

    def emit_def(self):
        return '\n'.join([
            'val {name} {type.emit_ref()}'
            for name, type in self.values.items()
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
            return (
                'cfn {}({})'.format(
                    self.name,
                    ', '.join([param.emit_def() for param in self.parameters])
                )
            )
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

    __slots__ = ('parameter_types', 'return_type')

    def __init__(self, parameter_types, return_type):
        self.parameter_types = parameter_types
        self.return_type = return_type

    def emit(self):
        if (isinstance(self.return_type, CScalarType) and
                self.return_type.type == CScalarType.BuiltinTypes.VOID):
            return (
                'cfntype({})'.format(
                    ', '.join([
                        param.emit_def() for param in self.parameter_types
                    ])
                )
            )
        return (
            'cfntype({}): {}'.format(
                ', '.join([
                    param.emit_def() for param in self.parameter_types
                ]),
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

    def __init__(self, type, size, is_signed, is_const, is_volatile):
        self.type = type
        self.size = size
        self.is_signed = is_signed
        self.is_const = is_const
        self.is_volatile = is_volatile

    def emit_ref(self):
        if self.type == self.BuiltinTypes.VOID:
            return 'void'
        if self.type == self.BuiltinTypes.BOOL:
            return 'bool'
        if self.type == self.BuiltinTypes.INTEGER:
            if self.is_signed:
                return f'i{self.size * 8}'
            return f'u{self.size * 8}'
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
            cdef.is_volatile
        )


class CAnonymousStruct(SylvaDef):

    __slots__ = ('fields',)

    def __init__(self, fields):
        self.fields = fields

    def emit_def(self):
        if self.fields:
            return '\n'.join([
                'cstruct {',
                ',\n'.join([
                    f'  {name}: {type.emit_ref()}'
                    for name, type in self.fields.items()
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
                'cstruct %s {' % (self.name.replace(' ', '_')),
                ',\n'.join([
                    f'  {name}: {type.emit_ref()}'
                    for name, type in self.fields.items()
                ]),
                '}'
            ])
        return f'cstruct {self.name.replace(" ", "_")}'

    def emit_ref(self):
        return self.name.replace(' ', '_')


class CAnonymousUnion(SylvaDef):

    __slots__ = ('fields',)

    def __init__(self, fields):
        self.fields = fields

    def emit_def(self):
        if self.fields:
            return '\n'.join([
                'cunion {',
                ',\n'.join([
                    f'  {name}: {type.emit_ref()}'
                    for name, type in self.fields.items()
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
                'cunion %s {' % (self.name.replace(' ', '_')),
                ',\n'.join([
                    f'  {name}: {type.emit_ref()}'
                    for name, type in self.fields.items()
                ]),
                '}'
            ])
        return f'cunion {self.name.replace(" ", "_")}'

    def emit_ref(self):
        return self.name.replace(' ', '_')


class Val(SylvaDef, SylvaRef):

    __slots__ = ('name', 'type', 'value')

    def __init__(self, name, type, value):
        self.name = name
        self.type = type
        self.value = value

    def emit_def(self):
        return f'val {self.name}: {self.value}{self.type.emit_ref()}'

    def emit_ref(self):
        return self.name


###
# cfn fputs(cptr(i8), cptr(FILE)!): i32
# cfn strtok_r(
#   str: cptr(i8)!,
#   delim: cptr(i8),
#   saveptr: cptr(cptr(i8)!)!
# ): cptr(i8)
# cfn __FLOAT_BITS(__f: f32): u32
###


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
            return Array(
                self._process_cdef(cdef.element_type),
                cdef.element_count
            )
        if isinstance(cdef, CDefs.Enum):
            vals = []
            for name, value in cdef.values.items():
                val = Val(name, self._process_cdef(cdef.type), value)
                self.defs[val.name] = val
                vals.append(val)
            return vals
        if isinstance(cdef, CDefs.Function):
            cfunction = CFunction(
                cdef.name,
                [
                    CFunctionParameter(name, self._process_cdef(type))
                    for name, type in cdef.parameters.items()
                ],
                self._process_cdef(cdef.return_type)
            )
            self.defs[cfunction.name] = cfunction
            return cfunction
        if isinstance(cdef, CDefs.FunctionPointer):
            return CFunctionType(
                [
                    CFunctionParameterType(self._process_cdef(type))
                    for type in cdef.parameter_types
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
            if cdef.name:
                struct = CStruct(
                    cdef.name,
                    {
                        name: self._process_cdef(type)
                        for name, type in cdef.fields.items()
                    }
                )
                self.defs[struct.name] = struct
            else:
                struct = CAnonymousStruct({
                    name: self._process_cdef(type)
                    for name, type in cdef.fields.items()
                })
            return struct
        if isinstance(cdef, CDefs.Typedef):
            alias = Alias(cdef.name, self._process_cdef(cdef.type))
            self.defs[alias.name] = alias
            return alias
        if isinstance(cdef, CDefs.Union):
            if cdef.name:
                union = CUnion(
                    cdef.name,
                    {
                        name: self._process_cdef(type)
                        for name, type in cdef.fields.items()
                    }
                )
                self.defs[union.name] = union
            else:
                union = CAnonymousUnion({
                    name: self._process_cdef(type)
                    for name, type in cdef.fields.items()
                })
            return union
        raise Exception(f'Unknown C definition: {cdef} ({type(cdef)})')

    @classmethod
    def FromLibcFiles(cls, libc_files, libclang=None):
        parser = Parser(libclang)
        return cls([
            cdef
            for libc_file in libc_files
            for cdef in parser.parse(libc_file)
        ])
