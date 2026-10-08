#include "global.h"

void sub_08121EE0(void);
extern s32 gUnk_02000138;

s32 sub_08121F0C(s32 value)
{
    sub_08121EE0();
    gUnk_02000138 = value;
    return 0;
}
