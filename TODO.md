# To Do

## Features

- Opaque types (dangling references)
- Warn when alignments of base types don't match

## Broadly

Eventually Sylva needs baseline C FFI support, which means defining base types
like `int8_t` and such.  Once that's in, we shouldn't generate duplicate
bindings.

Fix the semantic graveyard that is `SylvaDef` and `SylvaRef`

Would be nice to work the definitions into Sylva's AST properly.  Kind of gives
rise to the idea of doing this automatically; essentially provide a list of
headers and the name of the library to link with and we'll generate the
bindings in memory vs. in a file.  I'll have to think a little more about the
implications of that, but it does seem ideal.
