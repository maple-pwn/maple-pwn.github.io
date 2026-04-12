# 做题技巧


## `_IO_do_write`

题目中使用到了`puts`函数，会最终调用到`IO_new_file_overflow`，该函数会最终使用`_IO_do_write`进行真正的输出。在输出的时候如果有缓冲区，会输出`_IO_write_base`开始的缓冲区内容，直到`_IO_write_ptr`（也就是将`IO_write_base`一直到`_IO_write_ptr`部分的值当作缓冲区，在无缓冲区时，两个指针指向同一位置，位于该结构体附近，也就是libc中），但是在`setbuf`后，理论上会不使用缓冲区，然而如果能修改`_IO_2_1_stdout_`结构体的 flags 部分，使得其认为 stdout 有缓冲区，再将`_IO_write_base`处的值进行 `partiwal overwrite`，就可以泄露出 libc 了

涉及到的相关代码：

`puts`函数最终会调用到该函数，我们需要满足部分 flag 要求使其能够进入`_IO_do_write`


```

int

_IO_new_file_overflow

(
_IO_FILE

*
f
,

int

ch
)

{


if

(
f
->
_flags

&

_IO_NO_WRITES
)



{


f
->
_flags

|=

_IO_ERR_SEEN
;


__set_errno

(
EBADF
);


return

EOF
;


}


/* If currently reading or no buffer allocated. */


if

((
f
->
_flags

&

_IO_CURRENTLY_PUTTING
)

==

0

||

f
->
_IO_write_base

==

NULL
)



{


:


:


}


if

(
ch

==

EOF
)


return

_IO_do_write

(
f
,

f
->
_IO_write_base
,

f
->
_IO_write_ptr

-

f
->
_IO_write_base
);


// 第二个参数为需要调用的目标，如果使得_IO_write_base < _IO_write_ptr，且 _IO_write_base 处存在有价值的地址 （libc 地址）则可进行泄露


// 在正常情况下，_IO_write_base == _IO_write_ptr 且位于 libc 中，所以可进行部分写

```

进入后的部分


```

static

_IO_size_t

new_do_write

(
_IO_FILE

*
fp
,

const

char

*
data
,

_IO_size_t

to_do
)

{


_IO_size_t

count
;


if

(
fp
->
_flags

&

_IO_IS_APPENDING
)

/* 需要满足 */


/* 在没有正确实现 O_APPEND 的系统上，

    你需要在这里调用 sys_seek(0, SEEK_END)，

    但在类 Unix 或类 Posix 系统上，这是不需要的，也不推荐这样做。

    相反，只需表明偏移量（前后）是不可预测的。 */


fp
->
_offset

=

_IO_pos_BAD
;


else

if

(
fp
->
_IO_read_end

!=

fp
->
_IO_write_base
)


{


............


}


count

=

_IO_SYSWRITE

(
fp
,

data
,

to_do
);

// 这里真正进行 write

```

也就是说，为调用到目标函数地址，需要满足部分flags的需求，具体需要满足的flags：


```

_flags

=

0xfbad0000

//Magic Number

_flags

&=

~
_IO_NO_WRITES

//_flags = 0xfbad0000

_flags

|=

_IO_CURRENTLY_PUTTING

//_flags = 0xfbad0800

_flags

|=

_IO_IS_APPENDING

//_flags = 0xfbad1800

```
