# 小技巧

64位情况下，各个bins的分配方案

- tcachebins：大小小于0x420，里面没有被填满（7个）
- fastbins：tcachebins被填满，大小小于等于0x80
- 上述都不符合，填入unsortedbins中

当寄存器都是0的时候，执行syscall，rcx会被赋值，从而泄漏libc

在不加入tcachebins和fastbins的情况下直接加入到ub中

- 一般直接申请一个0x420更大的就行了，不过有的题会限制大小，那么采用下面的方法
- 在堆上构造一个`0x420`或以上的堆块，然后利用`UAF`让`chunk`指向这个伪造的堆块，最后进行`delete`把这个堆块`free`掉，就可以到`unsortedbin`，[这里](https://tover.xyz/p/PWN-Note-1-Tcache-and-Setcontext/index.html#%E6%96%B9%E6%B3%95-1-%E6%9E%84%E9%80%A0%E5%81%87%E7%9A%84chunk)
- 通过改tcache\_perthread\_struct然后把tcache\_perthread\_struct给free掉
