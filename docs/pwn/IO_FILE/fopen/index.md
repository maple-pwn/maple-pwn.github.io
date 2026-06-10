# fopen


#### **demo如下**


```asm
#include<stdio.h>
#include<stdlib.h>
int main() {
    FILE *fp = fopen("test.txt","wb");
    char *ptr = malloc(0x20);
    return 0;
}
```

**汇编如下**


```
pwndbg> disass
Dump of assembler code for function fopen64:
=> 0x00007ffff7e11630 <+0>:     endbr64
   0x00007ffff7e11634 <+4>:     push   r13
   0x00007ffff7e11636 <+6>:     mov    r13,rsi
   0x00007ffff7e11639 <+9>:     push   r12
   0x00007ffff7e1163b <+11>:    push   rbp
   0x00007ffff7e1163c <+12>:    mov    rbp,rdi
   0x00007ffff7e1163f <+15>:    mov    edi,0x1d8
   0x00007ffff7e11644 <+20>:    push   rbx
   0x00007ffff7e11645 <+21>:    sub    rsp,0x8
   0x00007ffff7e11649 <+25>:    call   0x7ffff7dba380 <malloc@plt>
   0x00007ffff7e1164e <+30>:    test   rax,rax
   0x00007ffff7e11651 <+33>:    je     0x7ffff7e11721 <fopen64+241>
   0x00007ffff7e11657 <+39>:    mov    rbx,rax
   0x00007ffff7e1165a <+42>:    lea    rax,[rax+0xe0]
   0x00007ffff7e11661 <+49>:    xor    edx,edx
   0x00007ffff7e11663 <+51>:    xor    esi,esi
   0x00007ffff7e11665 <+53>:    mov    QWORD PTR [rbx+0x88],rax
   0x00007ffff7e1166c <+60>:    lea    rcx,[rbx+0xf0]
   0x00007ffff7e11673 <+67>:    mov    rdi,rbx
   0x00007ffff7e11676 <+70>:    mov    r12,rbx
   0x00007ffff7e11679 <+73>:    lea    r8,[rip+0x197a40]        # 0x7ffff7fa90c0 <_IO_wfile_jumps>
   0x00007ffff7e11680 <+80>:    call   0x7ffff7e20650
   0x00007ffff7e11685 <+85>:    lea    rax,[rip+0x197f74]        # 0x7ffff7fa9600 <_IO_file_jumps>
   0x00007ffff7e1168c <+92>:    mov    rdi,rbx
   0x00007ffff7e1168f <+95>:    mov    QWORD PTR [rbx+0xd8],rax
   0x00007ffff7e11696 <+102>:   call   0x7ffff7e1de10
   0x00007ffff7e1169b <+107>:   mov    ecx,0x1
   0x00007ffff7e116a0 <+112>:   mov    rdx,r13
   0x00007ffff7e116a3 <+115>:   mov    rsi,rbp
   0x00007ffff7e116a6 <+118>:   mov    rdi,rbx
   0x00007ffff7e116a9 <+121>:   call   0x7ffff7e1e180 <_IO_file_fopen>
   0x00007ffff7e116ae <+126>:   test   rax,rax
   0x00007ffff7e116b1 <+129>:   je     0x7ffff7e11700 <fopen64+208>
   0x00007ffff7e116b3 <+131>:   test   BYTE PTR [rbx+0x74],0x1
   0x00007ffff7e116b7 <+135>:   je     0x7ffff7e116ed <fopen64+189>
   0x00007ffff7e116b9 <+137>:   test   BYTE PTR [rbx],0x8
   0x00007ffff7e116bc <+140>:   je     0x7ffff7e116ed <fopen64+189>
   0x00007ffff7e116be <+142>:   mov    ecx,DWORD PTR [rbx+0xc0]
   0x00007ffff7e116c4 <+148>:   lea    rdx,[rip+0x197875]        # 0x7ffff7fa8f40
   0x00007ffff7e116cb <+155>:   lea    rax,[rip+0x197dae]        # 0x7ffff7fa9480
   0x00007ffff7e116d2 <+162>:   test   ecx,ecx
   0x00007ffff7e116d4 <+164>:   cmovg  rax,rdx
   0x00007ffff7e116d8 <+168>:   mov    QWORD PTR [rbx+0xd8],rax
   0x00007ffff7e116df <+175>:   mov    rax,QWORD PTR [rbx+0xa0]
   0x00007ffff7e116e6 <+182>:   mov    QWORD PTR [rax+0xe0],rdx
   0x00007ffff7e116ed <+189>:   add    rsp,0x8
   0x00007ffff7e116f1 <+193>:   mov    rax,r12
   0x00007ffff7e116f4 <+196>:   pop    rbx
   0x00007ffff7e116f5 <+197>:   pop    rbp
   0x00007ffff7e116f6 <+198>:   pop    r12
   0x00007ffff7e116f8 <+200>:   pop    r13
   0x00007ffff7e116fa <+202>:   ret
   0x00007ffff7e116fb <+203>:   nop    DWORD PTR [rax+rax*1+0x0]
   0x00007ffff7e11700 <+208>:   mov    rdi,rbx
   0x00007ffff7e11703 <+211>:   xor    r12d,r12d
   0x00007ffff7e11706 <+214>:   call   0x7ffff7e1f2b0 <_IO_un_link>
   0x00007ffff7e1170b <+219>:   mov    rdi,rbx
   0x00007ffff7e1170e <+222>:   call   0x7ffff7dba370 <free@plt>
   0x00007ffff7e11713 <+227>:   add    rsp,0x8
   0x00007ffff7e11717 <+231>:   mov    rax,r12
   0x00007ffff7e1171a <+234>:   pop    rbx
   0x00007ffff7e1171b <+235>:   pop    rbp
   0x00007ffff7e1171c <+236>:   pop    r12
   0x00007ffff7e1171e <+238>:   pop    r13
   0x00007ffff7e11720 <+240>:   ret
   0x00007ffff7e11721 <+241>:   xor    r12d,r12d
   0x00007ffff7e11724 <+244>:   jmp    0x7ffff7e116ed <fopen64+189>
End of assembler dump.
```


#### 流程

![Pasted image 20250926095709.png](../../images/Pasted%20image%2020250926095709.png)


##### 1. 申请\_IO\_FILE\_plus空间


```
   0x00007ffff7e11649 <+25>:    call   0x7ffff7dba380 <malloc@plt>
```

在处调用`malloc`来为`_IO_FILE_plus`来分配内存，此时看看chunk


```
pwndbg> heap
Allocated chunk | PREV_INUSE
Addr: 0x55555555b000
Size: 0x290 (with flag bits: 0x291)

Allocated chunk | PREV_INUSE
Addr: 0x55555555b290
Size: 0x1e0 (with flag bits: 0x1e1)

Top chunk | PREV_INUSE
Addr: 0x55555555b470
Size: 0x20b90 (with flag bits: 0x20b91)
```


##### 2. 初始化变量

**`_flags`的maigc初始化**：


```
   0x7f69440e0680 <fopen64+80>    call   _IO_no_init                 <_IO_no_init>
```

调用`_IO_no_init`函数和`_IO_old_inti`函数，实现 `_flag`的初始化


```
pwndbg> vis 1 0x55555555b290

0x55555555b290  0x0000000000000000      0x00000000000001e1      ................
0x55555555b2a0  0x00000000fbad0000      0x0000000000000000      ................
0x55555555b2b0  0x0000000000000000      0x0000000000000000      ................
0x55555555b2c0  0x0000000000000000      0x0000000000000000      ................
0x55555555b2d0  0x0000000000000000      0x0000000000000000      ................
0x55555555b2e0  0x0000000000000000      0x0000000000000000      ................
0x55555555b2f0  0x0000000000000000      0x0000000000000000      ................
0x55555555b300  0x0000000000000000      0x0000000000000000      ................
0x55555555b310  0x0000000000000000      0x0000000000000000      ................
0x55555555b320  0x0000000000000000      0x000055555555b380      ..........UUUU..
0x55555555b330  0x0000000000000000      0x0000000000000000      ................
0x55555555b340  0x000055555555b390      0x0000000000000000      ..UUUU..........
0x55555555b350  0x0000000000000000      0x0000000000000000      ................
0x55555555b360  0x0000000000000000      0x0000000000000000      ................
0x55555555b370  0x0000000000000000      0x0000000000000000      ................
0x55555555b380  0x0000000000000000      0x0000000000000000      ................
0x55555555b390  0x0000000000000000      0x0000000000000000      ................
0x55555555b3a0  0x0000000000000000      0x0000000000000000      ................
0x55555555b3b0  0x0000000000000000      0x0000000000000000      ................
0x55555555b3c0  0x0000000000000000      0x0000000000000000      ................
0x55555555b3d0  0x0000000000000000      0x0000000000000000      ................
0x55555555b3e0  0x0000000000000000      0x0000000000000000      ................
0x55555555b3f0  0x0000000000000000      0x0000000000000000      ................
0x55555555b400  0x0000000000000000      0x0000000000000000      ................
0x55555555b410  0x0000000000000000      0x0000000000000000      ................
0x55555555b420  0x0000000000000000      0x0000000000000000      ................
0x55555555b430  0x0000000000000000      0x0000000000000000      ................
0x55555555b440  0x0000000000000000      0x0000000000000000      ................
0x55555555b450  0x0000000000000000      0x0000000000000000      ................
0x55555555b460  0x0000000000000000      0x0000000000000000      ................
0x55555555b470  0x00007ffff7fa90c0      0x0000000000020b91      ................        <-- Top chunk
```

**一系列初始化**


```
   0x7ffff7e11685 <fopen64+85>     lea    rax, [rip + 0x197f74]           RAX => 0x7ffff7fa9600 (_IO_file_jumps) ◂— 0
   0x7ffff7e1168c <fopen64+92>     mov    rdi, rbx                        RDI => 0x55555555b2a0 ◂— 0xfbad0000
   0x7ffff7e1168f <fopen64+95>     mov    qword ptr [rbx + 0xd8], rax     [0x55555555b378] <= 0x7ffff7fa9600 (_IO_file_jumps) ◂— 0
   0x7ffff7e11696 <fopen64+102>    call   _IO_new_file_init_internal  <_IO_new_file_init_internal>
```

现在的`_IO_file_plus`:


```
pwndbg> p *(struct _IO_FILE_plus*)  0x55555555b2a0
$1 = {
  file = {
    _flags = -72538996,
    _IO_read_ptr = 0x0,
    _IO_read_end = 0x0,
    _IO_read_base = 0x0,
    _IO_write_base = 0x0,
    _IO_write_ptr = 0x0,
    _IO_write_end = 0x0,
    _IO_buf_base = 0x0,
    _IO_buf_end = 0x0,
    _IO_save_base = 0x0,
    _IO_backup_base = 0x0,
    _IO_save_end = 0x0,
    _markers = 0x0,
    _chain = 0x7ffff7fad6a0 <_IO_2_1_stderr_>,
    _fileno = -1,
    _flags2 = 0,
    _old_offset = 0,
    _cur_column = 0,
    _vtable_offset = 0 '\000',
    _shortbuf = "",
    _lock = 0x55555555b380,
    _offset = -1,
    _codecvt = 0x0,
    _wide_data = 0x55555555b390,
    _freeres_list = 0x0,
    _freeres_buf = 0x0,
    __pad5 = 0,
    _mode = 0,
    _unused2 = '\000' <repeats 19 times>
  },
  vtable = 0x7ffff7fa9600 <_IO_file_jumps>
}
```


##### 3. 加入`_IO_list_all`链表中


```
   0x7ffff7e1de1e <_IO_new_file_init_internal+14>    mov    qword ptr [rdi + 0x90], 0xffffffffffffffff     [0x55555555b330] <= 0xffffffffffffffff
   0x7ffff7e1de29 <_IO_new_file_init_internal+25>    call   _IO_link_in                 <_IO_link_in>
```

在`_IO_new_file_init_internal`函数中调用`_IO_link_in`函数实现链表内的注册

注册前：


```
pwndbg> p/x *(struct _IO_FILE_plus*)0x55555555b2a0
$2 = {
  file = {
    _flags = 0xfbad240c,
    _IO_read_ptr = 0x0,
    _IO_read_end = 0x0,
    _IO_read_base = 0x0,
    _IO_write_base = 0x0,
    _IO_write_ptr = 0x0,
    _IO_write_end = 0x0,
    _IO_buf_base = 0x0,
    _IO_buf_end = 0x0,
    _IO_save_base = 0x0,
    _IO_backup_base = 0x0,
    _IO_save_end = 0x0,
    _markers = 0x0,
    _chain = 0x0,
    _fileno = 0x0,
    _flags2 = 0x0,
    _old_offset = 0x0,
    _cur_column = 0x0,
    _vtable_offset = 0x0,
    _shortbuf = {0x0},
    _lock = 0x55555555b380,
    _offset = 0xffffffffffffffff,
    _codecvt = 0x0,
    _wide_data = 0x55555555b390,
    _freeres_list = 0x0,
    _freeres_buf = 0x0,
    __pad5 = 0x0,
    _mode = 0x0,
    _unused2 = {0x0 <repeats 20 times>}
  },
  vtable = 0x7ffff7fa9600
}
```

`_IO_list_all`链表内容


```
pwndbg> p _IO_list_all
$3 = (struct _IO_FILE_plus *) 0x7ffff7fad6a0 <_IO_2_1_stderr_>
```

**设置\_flag位为0xfbad248c**


```
   0x7ffff7e1f2f0 <_IO_link_in+32>    xor    eax, eax                        EAX => 0
   0x7ffff7e1f2f2 <_IO_link_in+34>    mov    ebp, edx                        EBP => 0xfbad240c
   0x7ffff7e1f2f4 <_IO_link_in+36>    and    ebp, 0x80                       EBP => 0 (0xfbad240c & 0x80)
```


```
#define _IO_LINKED 0x80                /* Set if linked (using _chain) to streambuf::_list_all. 链接到一个链表（使用 _chain 指针），用于 streambuf::_list_all */
```

**一系列清理等操作**


```
   0x7ffff7e1f330 <_IO_link_in+96>     mov    dword ptr [rdi], edx       [0x55555555b2a0] <= 0xfbad248c
   0x7ffff7e1f332 <_IO_link_in+98>     mov    rdi, r12                   RDI => 0x7fffffffd8a0 —▸ 0x555555556004 ◂— 0x2e74736574006277 /* 'wb' */
   0x7ffff7e1f335 <_IO_link_in+101>    lea    r13, [rip + 0x18f714]      R13 => 0x7ffff7faea50 (list_all_lock) ◂— 0
 ► 0x7ffff7e1f33c <_IO_link_in+108>    mov    qword ptr [rsp + 8], 0     [0x7fffffffd8a8] <= 0
   0x7ffff7e1f345 <_IO_link_in+117>    mov    qword ptr [rsp], rax       [0x7fffffffd8a0] <= 0x7ffff7e1efe0 (flush_cleanup) ◂— endbr64
   0x7ffff7e1f349 <_IO_link_in+121>    call   __libc_cleanup_push_defer   <__libc_cleanup_push_defer>
```

**回归\_IO\_new\_file\_init\_internal后的布局**


```
pwndbg> p *(struct _IO_FILE_plus*)0x55555555b2a0
$10 = {
  file = {
    _flags = -72538996,
    _IO_read_ptr = 0x0,
    _IO_read_end = 0x0,
    _IO_read_base = 0x0,
    _IO_write_base = 0x0,
    _IO_write_ptr = 0x0,
    _IO_write_end = 0x0,
    _IO_buf_base = 0x0,
    _IO_buf_end = 0x0,
    _IO_save_base = 0x0,
    _IO_backup_base = 0x0,
    _IO_save_end = 0x0,
    _markers = 0x0,
    _chain = 0x7ffff7fad6a0 <_IO_2_1_stderr_>,
    _fileno = 0,
    _flags2 = 0,
    _old_offset = 0,
    _cur_column = 0,
    _vtable_offset = 0 '\000',
    _shortbuf = "",
    _lock = 0x55555555b380,
    _offset = -1,
    _codecvt = 0x0,
    _wide_data = 0x55555555b390,
    _freeres_list = 0x0,
    _freeres_buf = 0x0,
    __pad5 = 0,
    _mode = 0,
    _unused2 = '\000' <repeats 19 times>
  },
  vtable = 0x7ffff7fa9600 <_IO_file_jumps>
}
pwndbg> p _IO_list_all
$11 = (struct _IO_FILE_plus *) 0x55555555b2a0
```

- 新建的\_IO\_FILE\_plus结构体目前指向了`_IO_2_1_stderr`
- `_IO_list_all`现在也指向了新建的结构体
**也就是实现了在IO链表前插一个新节点**

然后清理了`0x310-0x2a0=0x70`偏移的内容为$-1$，也就是`_fileno`为$-1$


```
   0x7ffff7e1de2e <_IO_new_file_init_internal+30>    mov    dword ptr [rbx + 0x70], 0xffffffff     [0x55555555b310] <= 0xffffffff
 ► 0x7ffff7e1de35 <_IO_new_file_init_internal+37>    pop    rbx                                    RBX => 0x55555555b2a0
```

**至此，完成了\_IO\_FILE\_plus结构体的创建**


##### 打开文件


```
 ► 0x7ffff7e116a3 <fopen64+115>                      mov    rsi, rbp     RSI => 0x555555556007 ◂— 'test.txt'
   0x7ffff7e116a6 <fopen64+118>                      mov    rdi, rbx     RDI => 0x55555555b2a0 ◂— 0xfbad248c
   0x7ffff7e116a9 <fopen64+121>                      call   _IO_file_fopen              <_IO_file_fopen>
```

调用`_IO_file_fopen`来真正打开文件


```
   0x7ffff7e1e400 <_IO_file_fopen+640>    mov    rbx, rcx       RBX => 0x555555556005 ◂— 0x742e747365740062 /* 'b' */
   0x7ffff7e1e403 <_IO_file_fopen+643>    or     edx, edi       EDX => 0x241 (0x240 | 0x1)
   0x7ffff7e1e405 <_IO_file_fopen+645>    mov    ecx, 0x1b6     ECX => 0x1b6
   0x7ffff7e1e40a <_IO_file_fopen+650>    mov    rdi, rbp       RDI => 0x55555555b2a0 ◂— 0xfbad248c
 ► 0x7ffff7e1e40d <_IO_file_fopen+653>    call   _IO_file_open               <_IO_file_open>
        rdi: 0x55555555b2a0 ◂— 0xfbad248c
        rsi: 0x555555556007 ◂— 'test.txt'
        rdx: 0x241
        rcx: 0x1b6
        r8: 4
        r9: 1
```

此时，`_fileno`被修改为fd


```
pwndbg> p *(struct _IO_FILE_plus*)0x55555555b2a0
$14 = {
  file = {
    _flags = -72539004,
    _IO_read_ptr = 0x0,
    _IO_read_end = 0x0,
    _IO_read_base = 0x0,
    _IO_write_base = 0x0,
    _IO_write_ptr = 0x0,
    _IO_write_end = 0x0,
    _IO_buf_base = 0x0,
    _IO_buf_end = 0x0,
    _IO_save_base = 0x0,
    _IO_backup_base = 0x0,
    _IO_save_end = 0x0,
    _markers = 0x0,
    _chain = 0x7ffff7fad6a0 <_IO_2_1_stderr_>,
    _fileno = 3,
    _flags2 = 0,
    _old_offset = 0,
    _cur_column = 0,
    _vtable_offset = 0 '\000',
    _shortbuf = "",
    _lock = 0x55555555b380,
    _offset = -1,
    _codecvt = 0x0,
    _wide_data = 0x55555555b390,
    _freeres_list = 0x0,
    _freeres_buf = 0x0,
    __pad5 = 0,
    _mode = 0,
    _unused2 = '\000' <repeats 19 times>
  },
  vtable = 0x7ffff7fa9600 <_IO_file_jumps>
}
```

至此，结束fopen函数的完整调用


```
pwndbg> p *(struct _IO_FILE_plus*)0x55555555b2a0
$14 = {
  file = {
    _flags = -72539004,
    _IO_read_ptr = 0x0,
    _IO_read_end = 0x0,
    _IO_read_base = 0x0,
    _IO_write_base = 0x0,
    _IO_write_ptr = 0x0,
    _IO_write_end = 0x0,
    _IO_buf_base = 0x0,
    _IO_buf_end = 0x0,
    _IO_save_base = 0x0,
    _IO_backup_base = 0x0,
    _IO_save_end = 0x0,
    _markers = 0x0,
    _chain = 0x7ffff7fad6a0 <_IO_2_1_stderr_>,
    _fileno = 3,
    _flags2 = 0,
    _old_offset = 0,
    _cur_column = 0,
    _vtable_offset = 0 '\000',
    _shortbuf = "",
    _lock = 0x55555555b380,
    _offset = -1,
    _codecvt = 0x0,
    _wide_data = 0x55555555b390,
    _freeres_list = 0x0,
    _freeres_buf = 0x0,
    __pad5 = 0,
    _mode = 0,
    _unused2 = '\000' <repeats 19 times>
  },
  vtable = 0x7ffff7fa9600 <_IO_file_jumps>
}
```
