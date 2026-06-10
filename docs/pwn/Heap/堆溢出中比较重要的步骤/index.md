# 堆溢出要点


### 寻找堆分配函数

通常来说堆是通过调用 glibc 函数 malloc 进行分配的，在某些情况下会使用 calloc 分配。calloc 与 malloc 的区别是 **calloc 在分配后会自动进行清空，这对于某些信息泄露漏洞的利用来说是致命的**。


```
calloc(0x20);
//等同于
ptr=malloc(0x20);
memset(ptr,0,0x20);
```

除此之外，还有一种分配是经由 realloc 进行的，realloc 函数可以身兼 malloc 和 free 两个函数的功能。


```asm
#include <stdio.h>

int main(void) 
{
  char *chunk,*chunk1;
  chunk=malloc(16);
  chunk1=realloc(chunk,32);
  return 0;
}
```

realloc 的操作并不是像字面意义上那么简单，其内部会根据不同的情况进行不同操作

- 当 realloc(ptr,size) 的 size 不等于 ptr 的 size 时
  - 如果申请 size > 原来 size
    - 如果 chunk 与 top chunk 相邻，直接扩展这个 chunk 到新 size 大小
    - 如果 chunk 与 top chunk 不相邻，相当于 free(ptr),malloc(new\_size)
  - 如果申请 size < 原来 size
    - 如果相差不足以容得下一个最小 chunk(64 位下 32 个字节，32 位下 16 个字节)，则保持不变
    - 如果相差可以容得下一个最小 chunk，则切割原 chunk 为两部分，free 掉后一部分
- 当 realloc(ptr,size) 的 size 等于 0 时，相当于 free(ptr)
- 当 realloc(ptr,size) 的 size 等于 ptr 的 size，不进行任何操作


### 寻找危险函数

通过寻找危险函数，我们快速确定程序是否可能有堆溢出，以及有的话，堆溢出的位置在哪里。

常见的危险函数如下

- 输入
  - gets，直接读取一行，忽略 `'\x00'`
  - scanf
  - vscanf
- 输出
  - sprintf
- 字符串
  - strcpy，字符串复制，遇到 `'\x00'` 停止
  - strcat，字符串拼接，遇到 `'\x00'` 停止
  - bcopy


### 确定填充长度

这一部分主要是计算\*\*我们开始写入的地址与我们所要覆盖的地址之间的距离\*\*。 一个常见的误区是 malloc 的参数等于实际分配堆块的大小，但是事实上 ptmalloc 分配出来的大小是对齐的。这个长度一般是字长的 2 倍，比如 32 位系统是 8 个字节，64 位系统是 16 个字节。但是对于不大于 2 倍字长的请求，malloc 会直接返回 2 倍字长的块也就是最小 chunk，比如 64 位系统执行`malloc(0)`会返回用户区域为 16 字节的块。


```asm
#include <stdio.h>

int main(void) 
{
  char *chunk;
  chunk=malloc(0);
  puts("Get input:");
  gets(chunk);
  return 0;
}
```


```
//根据系统的位数，malloc会分配8或16字节的用户空间
0x602000:   0x0000000000000000  0x0000000000000021
0x602010:   0x0000000000000000  0x0000000000000000
0x602020:   0x0000000000000000  0x0000000000020fe1
0x602030:   0x0000000000000000  0x0000000000000000
```

注意用户区域的大小不等于 chunk\_head.size，chunk\_head.size = 用户区域大小 + 2 \* 字长

还有一点是之前所说的用户申请的内存大小会被修改，其有可能会使用与其物理相邻的下一个 chunk 的 prev\_size 字段储存内容。回头再来看下之前的示例代码


```asm
#include <stdio.h>

int main(void) 
{
  char *chunk;
  chunk=malloc(24);
  puts("Get input:");
  gets(chunk);
  return 0;
}
```

观察如上代码，我们申请的 chunk 大小是 24 个字节。但是我们将其编译为 64 位可执行程序时，实际上分配的内存会是 16 个字节而不是 24 个。


```
0x602000:   0x0000000000000000  0x0000000000000021
0x602010:   0x0000000000000000  0x0000000000000000
0x602020:   0x0000000000000000  0x0000000000020fe1
```

16 个字节的空间是如何装得下 24 个字节的内容呢？答案是借用了下一个块的 pre\_size 域。我们可来看一下用户申请的内存大小与 glibc 中实际分配的内存大小之间的转换。


```
/* pad request bytes into a usable size -- internal version */
//MALLOC_ALIGN_MASK = 2 * SIZE_SZ -1
#define request2size(req)                                                \
    (((req) + SIZE_SZ + MALLOC_ALIGN_MASK < MINSIZE)                           \
         ? MINSIZE                                                             \
         : ((req) + SIZE_SZ + MALLOC_ALIGN_MASK) & ~MALLOC_ALIGN_MASK)
```

当 req=24 时，request2size(24)=32。而除去 chunk 头部的 16 个字节。实际上用户可用 chunk 的字节数为 16。而根据我们前面学到的知识可以知道 chunk 的 pre\_size 仅当它的前一块处于释放状态时才起作用。所以用户这时候其实还可以使用下一个 chunk 的 prev\_size 字段，正好 24 个字节。**实际上 ptmalloc 分配内存是以双字为基本单位，以 64 位系统为例，分配出来的空间是 16 的整数倍，即用户申请的 chunk 都是 16 字节对齐的。**
