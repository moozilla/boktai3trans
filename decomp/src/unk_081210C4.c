#include "global.h"

void sub_08120DAC(u8 *);

void sub_081210C4(u8 *obj)
{
    *(u16 *)(obj + 0x8BA) = 0;
    sub_08120DAC(obj);
}
