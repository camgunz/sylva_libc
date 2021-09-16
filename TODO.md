# To Do

## Features

- Opaque types (dangling references)
- Warn when alignments of base types don't match

## Bugs

```
typedef struct {
  union {
    int __i[sizeof(long)==8?14:9];
    volatile int __vi[sizeof(long)==8?14:9];
    unsigned long __s[sizeof(long)==8?7:9];
  } __u;
} pthread_attr_t;

cstruct struct_pthread_attr_t {
  : cunion {
  __i: i32[14],
  __vi: i32[14],
  __s: u64[7]
},
  __u: union_(anonymous_union_at_/usr/lib/musl/include/bits/alltypes.h:372:18)
}
```

```
struct timespec {
  time_t tv_sec;
  int :8*(sizeof(time_t)-sizeof(long))*(__BYTE_ORDER==4321);
  long tv_nsec;
  int :8*(sizeof(time_t)-sizeof(long))*(__BYTE_ORDER!=4321);
};

cstruct struct_timespec {
  tv_sec: time_t,
  : i32,
  tv_nsec: i64
}
```

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
