#include "global.h"

extern u8 *gUnk_020000E0;

s32 sub_08033568(void)
{
    s32 ret;

    if (gUnk_020000E0) {
        gUnk_020000E0[0x17D] = 1;
        ret = 0;
    } else {
        ret = -1;
    }
    return ret;
}
