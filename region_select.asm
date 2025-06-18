; Region select patch for the Boktai 3 translation
; This does the following things:
; * Loads time zone offsets from the region data (Boktai 3 (J) skips this, because there is only
;   a single time zone in Japan)
; * Patches the time zone calculation to support minute precision (the existing time zone code
;   only supports full hours)
; * Increases the number of pages in the region selection screen
; * Increases the maximum total number of regions in the region selection screen
; * Changes the default region (from 6=Tokyo)
; To build the US patch: `armips region_select.asm`
; To build the EU patch: `armips region_select.asm -definelabel europe 1`

.gba
.open "scriptEd/shinbok-edit.gba", \
	"region_select_" + (defined(europe) ? "eu" : "us") + ".gba", \
	0x08000000

RegionPageCount equ (defined(europe) ? 21 : 20)
RegionNameOffset equ (defined(europe) ? 20 : 0)
DefaultRegionId equ (defined(europe) ? 1 : 15)
RegionListKeyword equ (defined(europe) ? 'P' : 'E')


; =================================================================================================
; Functions and global variables we need
; =================================================================================================
; Pointer to global save data
g_ptrGlobalSaveData equ 0x030053f8
; void Video_GetBackgroundMap(int bg) - Returns pointer to buffer containing a BG map *in EWRAM*
Video_GetBackgroundMap equ 0x08215698
; void Menu_EraseRect(u32 x, u32 y, i32 width, i32 height) - Erases a rectangle in the UI
Menu_EraseRect equ 0x081dc02c
; void Menu_DrawText(u32 x, u32 y, char* text) - Draws some text in the UI
Menu_DrawText equ 0x081dc054
; void Time_CalculateSunriseSunset(i32 latitude, i32 longitude, i32 tz_offset)
; Calculates & stores the result of the sunrise/sunset calculation. Also stores the parameters
; for future use.
Time_CalculateSunriseSunset equ 0x0822ae00
; char* Text_FindChar(char* s, char ch) - strchr with a subtle change this margin is too small for
Text_FindChar equ 0x0803223c
; char* Text_LookupString(i32 id) - Returns the pointer to a string in the script directory
Text_LookupString equ 0x0821add4

; === Bytecode interpreter ===
; (PC = program counter of the bytecode interpreter), returns pc
; void* Script_SetPc(void* pc)
Script_SetPc equ 0x821a960
; void* Script_SeekToKeyword(char kw) - Advances the PC until the next keyword instruction with
; the specified keyword
Script_SeekToKeyword equ 0x0821a96c
; void Script_PushCtrlNextKeyword(void* pc)
; Maintenance for Script_SeekToKeyword
Script_PushCtrlNextKeyword equ 0x0821a940
; void Script_PopCtrlNextKeyword()
Script_PopCtrlNextKeyword equ 0x0821a950
; void* Script_GetPc()
Script_GetPc equ 0x0821ab18
; i32 Script_GetValue() - Evaluates a value at the current PC (always an integer)
Script_GetValue equ 0x0821ab40
; i32 Script_GetValueSafe() - Like Script_GetValue() but with null checks on the PC
Script_GetValueSafe equ 0x0821ab88
; u16 Script_ParseStringRef(void* pc) - Returns the parameter of the current string-ref insn
Script_ParseStringRef equ 0x0821aabc


; =================================================================================================
; Update page count. This is unfortunately hardcoded.
; The game also has an u32[page_count] array where to keep track of the 1st region ID of each page.
; There's data after this array, so we cannot grow it.
; We can however change it to an u8[page_count] array, to store more data in the same space.
; Since we support 0xff regions at most, this is not an issue.
; =================================================================================================
; Patch u32[page_count] accesses to u8[page_count] accesses
.org 0x081dc884 :: nop
.org 0x081dc88c :: ldrb r0, [r0, #0]
.org 0x081dc8d2 :: nop
.org 0x081dc8da :: ldrb r0, [r0, #0]
.org 0x081dcb9c :: mov r1, r6
.org 0x081dcba6 :: strb r1, [r0, #0]

; Patch menu cursor boundaries (LanHikariDS)
.org 0x081dc876 :: db RegionPageCount
.org 0x081dc8c6 :: db RegionPageCount


; =================================================================================================
; Change data type of cursor in the menu (=ID of hovered region) from i8 to u8.
; Because we have more than 127 regions now.
; =================================================================================================
.org 0x081dc75e :: ldrb r0, [r4, r0]
.org 0x081dc910 :: ldrb r1, [r5, r1]
.org 0x081dc94e :: ldrb r1, [r5, r1]
.org 0x081dc980 :: ldrb r0, [r5, r0]
.org 0x081dcad6 :: ldrb r0, [r1, r0]
.org 0x081dcd2a :: ldrb r0, [r3, r0]
.org 0x081dcc24 :: ldrb r1, [r2, r1]


; =================================================================================================
; void Time_ShowRegionMenu(region_menu* menu) // @ 0x081dc6d0
; This function renders the entries in the region menu. We are rewriting this for two reasons:
; * To support more regions, by changing how the region names are accessed
; * To convert the page names from a sprite to a plain text (because we currently lack the
;   technology to insert new sprites for the new pages)
; =================================================================================================
.org 0x081dc6d0
.area 132
push {r4, lr}

; Set "1st region index of current page"
; r4 = page number = *(menu + 0x1c)
ldr r4, [r0, 0x1c]
; *(menu + 0xeb4) = (menu + 0x28)[page_number]
ldr r1, =0xeb4
add r1, r0
mov r2, r0
add r2, 0x28
add r2, r4
ldrb r2, [r2]
str r2, [r1]

; Erase space for the page name
mov r0, #5
mov r1, #4
mov r2, #20
mov r3, #2
bl Menu_EraseRect
; Erase space for the region names
mov r0, #4
mov r1, #7
mov r2, #20
mov r3, #10
bl Menu_EraseRect

; set r4 = string ID for current page
ldr r0, =0x02000310
ldr r0, [r0]
bl Script_ParseStringRef
add r0, RegionNameOffset
add r0, r4
; set r4 = string for current page
bl Text_LookupString
mov r4, r0

; Draw page name
mov r0, #5
mov r1, #4
mov r2, r4
bl Menu_DrawText

; Advance @@StringPtr past the null terminator - this is where the region names themselves start
mov r0, r4
mov r1, #0
bl Text_FindChar
add r2, r0, #1

; Draw region names - we only need 1 call for all region names in one page, since the string
; we are drawing contains newline characters.
mov r0, #4
mov r1, #7
bl Menu_DrawText

; HACK: Manually change palette of the page name. Menu_DrawChar (called by Menu_DrawText)
; will hardcode the palette to 0xf, we want 0x3 to make the page name stand out more
; Set r0 = pointer to high byte of BG map entry row 4 column 5
;     r1 = pointer to high byte of BG map entry row 5 column 5
;          high byte because that's where the palette index is stored.
;     r2 = column byte offset/loop variable (38)
mov r0, #0
bl Video_GetBackgroundMap ; returns a pointer to EWRAM, not VRAM!
add r0, 0xff
add r0, #12
mov r1, r0
add r1, 0x40
mov r2, #38

@@loop:
; Transform row 4
ldrb r3, [r0, r2]
sub r3, 0xc0 ; adjust palette
strb r3, [r0, r2]
; Transform row 5
ldrb r3, [r1, r2]
sub r3, 0xc0 ; adjust palette
strb r3, [r1, r2]
sub r2, #2
bge @@loop

pop {r4, pc}
.pool
.endarea

; =================================================================================================
; void Time_CalculateSunriseSunsetCore(...) // @ 0x0822a7a8
;
; In Boktai 3, this function only supports whole-hour time zone offsets. We need to patch in
; support for 30min/15min time zone offsets here. We'll re-use the code from Boktai 2 for this.
; =================================================================================================
.org 0x0822ac3e
.area 20
; r1 = minutes, r6 = hours, sp+0xdc = tz_offset
; We need to add tz_offset to minutes and hours.
mov r0, r6
ldr r2, [sp, #0xdc]
bl Time_AddOffset
b 0x0822ac52
.endarea

.org 0x0822ad62
.area 20
; Same as above
mov r0, r6
ldr r2, [sp, #0xdc]
bl Time_AddOffset
b 0x0822ad76
.endarea


; =================================================================================================
; void Time_LoadRegionList(region_menu* menu) // @ 0x081dca9c
;
; This function is responsible for filling the region menu with the region data in the string list.
; In vanilla Boktai 3, each region entry looks like this:
;   struct region { i16 page; u16 id; i32 longitude; i32 latitude };
; However, we also need some space to store the time zone offset for each region. In Japan, this is
; implied to be zero, but in the US/European releases, this can vary. Therefore, we must load the
; time zone offset from the region data, and then squeeze it into the region struct.
; Luckily for us, the game doesn't actually use the "id" field of the struct, so we can just store
; the time zone offset in there!
;   struct region { i16 page; i16 tz_offset; i32 longitude; i32 latitude };
; =================================================================================================
.org 0x081dcc02
; Increase max region count from 0x40 to 0xff
cmp r0, #0xff

.org 0x081dcab6 :: db DefaultRegionId
.org 0x081dcb62 :: bl Time_SeekToRegionBytecode

.org 0x081dcbc6
.area 46, 0
; Store page number
strh r6, [r5, #0]
; Ignore region ID
bl Script_GetValue
; Load & store time zone offset
bl Script_GetValue
strh r0, [r5, #2]
; Load & store longitude
bl Script_GetValue
str r0, [r5, #4]
; Load & store latitude
bl Script_GetValue
str r0, [r5, #8]
; Maintain loop variables
add r5, #12
mov r0, #1
add r8, r0
add r9, r0
.endarea

; Don't create a sprite for the page name - pages names are now plain text, not a sprite.
.org 0x081dcc88
nop :: nop


; =================================================================================================
; void Time_DestroyRegionMenu(region_menu* menu) // @ 0x081dca6c
;
; Called when exiting the region menu. Since we skipped creating a sprite for the page name above,
; we must also skip destroying it here.
; =================================================================================================
.org 0x081dca88
nop :: nop


; =================================================================================================
; void Time_HandleRegionKeypad(region_menu* menu) // @ 0x081dc7a0
;
; Called every frame to update the region menu. Processes keypad input, amongst other things.
; =================================================================================================
; Skip updating the page name sprite here, we are moving this logic to Time_ShowRegionMenu.
.org 0x081dc8a4
nop :: nop

.org 0x081dc8f2
nop :: nop


; =================================================================================================
; void Time_OnRegionListSelect(region_menu* menu) // @ 0x081dc754
;
; This function is called when selecting an entry in the region list, and it will call
; Time_CalculateSunriseSunset(latitude, longitude, tz_offset) for the selected region. In vanilla
; Boktai 3, the tz_offset is hardcoded to 0. This patch loads it from the region menu instead (just
; like the latitude/longitude).
; =================================================================================================
.org 0x081dc76e
; At this point, r0 points to the "latitude" field in the region entry struct (see above). We now
; must set up the call such that r0 = latitude, r1 = longitude, r2 = tz_offset.
.area 12, 0
sub r0, #8         ; Make r0 point to the start of the region struct
mov r1, #2
ldrsh r2, [r0, r1] ; Load tz_offset
ldr r1, [r0, #4]   ; Load longitude
ldr r0, [r0, #8]   ; Load latitude
.endarea

; =================================================================================================
; void Time_OnLoadSave() // @ 0x081dce34
;
; This function is called when loading a save in the main menu. This function checks the region ID
; in the save data, finds the matching region in the bytecode,
; and then calls Time_CalculateSunriseSunset as above. And just like above, the tz_offset is
; hardcoded to 0 here. We must patch it so it's loaded from the bytecode instead.
; The easiest way to do this is just to rewrite the entire function from scratch.
; =================================================================================================
.org 0x081dce34
@@SelectedRegionId equ r4
@@RemainingRegionsOnPage equ r5
@@SelectedRegionFound equ r6
@@GlobalSaveData equ r7
@@StackSize equ #12

.area 236
push {r4-r7, lr}
sub sp, @@stackSize

mov r0, 'd'
bl Script_SeekToKeyword
; Should put a if (!r0) { return; } here, but we don't have enough space :(
; cmp r0, #0 :: beq @@ret
; Move PC to the region data bytecode
bl Script_GetValueSafe
bl Time_SeekToRegionBytecode
; Load selected region ID
ldr r0, =g_ptrGlobalSaveData
ldr @@GlobalSaveData, [r0]
ldrb @@SelectedRegionId, [@@GlobalSaveData, #0x18]
mov @@SelectedRegionFound, #0

@@pages_loop:
bl Script_GetPc
cmp r0, #0
beq @@pages_done
bl Script_GetValue ; r0 = page number
cmp r0, #0
blt @@pages_done
; Parse this page
bl Script_GetValue
mov @@RemainingRegionsOnPage, r0

@@region_loop:
cmp @@RemainingRegionsOnPage, #0
beq @@pages_loop
bl Script_GetPc
cmp r0, #0
beq @@pages_loop
bl Script_GetValue ; Load region ID
cmp r0, @@SelectedRegionId ; Is it the selected region?
beq @@found_selected_region
cmp r0, DefaultRegionId ; Is it the fallback region?
beq @@region_found

bl Script_GetValue ; discard tz_offset
bl Script_GetValue ; discard longitude
bl Script_GetValue ; discard latitude
b @@region_next

@@found_selected_region:
mov @@SelectedRegionFound, #1

@@region_found:
bl Script_GetValue ; Load tz_offset
str r0, [sp, #8]
bl Script_GetValue ; Load longitude
str r0, [sp, #4]
bl Script_GetValue ; Load latitude
str r0, [sp, #0]
; Can we stop now?
cmp @@SelectedRegionFound, #1
beq @@exit_search

@@region_next:
sub @@RemainingRegionsOnPage, #1
b @@region_loop

@@pages_done:
; Didn't find the selected region :(
mov @@SelectedRegionId, DefaultRegionId
strb @@SelectedRegionId, [@@GlobalSaveData, #0x18]

@@exit_search:
ldr r0, [sp, #0]
ldr r1, [sp, #4]
ldr r2, [sp, #8]
bl Time_CalculateSunriseSunset
; *0x03005439 = 0, reusing g_ptrGlobalSaveData for address calculation to not waste more literal
; pool space than we have available
mov r0, #0
ldr r1, =g_ptrGlobalSaveData
add r1, #65
strb r0, [r1]

@@ret:
add sp, @@stackSize
pop {r4-r7, pc}

; =================================================================================================
; u32[2] Time_AddOffset(hours, minutes, offset)
;
; There's now some space here for Time_AddOffset function (adapted code from Boktai 2 (U))
; Returns adjusted hours in r0, and adjusted minutes in r1, since that's what the code at
; the call site expect.
; =================================================================================================
Time_AddOffset:
push {r4, r5, lr}
mov r4, #0
cmp r2, #0
bge @@offset_positive
neg r2, r2
mov r4, #1
@@offset_positive:

; Extract minutes from tz_offset
mov r3, r2
mov r5, #0x3f
and r3, r5
mov r5, #60
mul r3, r5
asr r3, #6
asr r2, #6
; Now: r2 = tz_offset hours, r3 = tz_offset minutes

cmp r4, #0
bne @@calc_negative

; tz_offset is positive
; add minutes
add r1, r3
cmp r1, #60
blt @@positive_no_mins_overflow
sub r1, #60
add r0, #1
@@positive_no_mins_overflow:
; add hours
add r0, r2
cmp r0, #24
blt @@positive_no_hours_overflow
sub r0, #24
@@positive_no_hours_overflow:
b @@calc_ret

@@calc_negative:
; tz_offset is negative
; subtract minutes
sub r1, r3
cmp r1, #0
bge @@negative_no_mins_underflow
add r1, #60
sub r0, #1
@@negative_no_mins_underflow:
; subtract hours
sub r0, r2
cmp r0, #0
bge @@calc_ret
add r0, #24

@@calc_ret:
pop {r4, r5, pc}


Time_SeekToRegionBytecode:
; Precondition: r0 = pointer to start of region bytecode
push {lr}
bl Script_SetPc
bl Script_PushCtrlNextKeyword
mov r0, RegionListKeyword
bl Script_SeekToKeyword
bl Script_PopCtrlNextKeyword
pop {pc}

.pool

.endarea

; =================================================================================================
; Enlarge region menu size. Vanilla, this can accommodate 64 entries. Let's bump it to 256 entries.
; Unfortunately, there is 0x38 further bytes after that array... So we have to patch all accesses
; to that data as well...
; =================================================================================================
.macro patch_580,reg
	; patch 0x580 -> 0xe80
	mov reg, 0xe8
	lsl reg, reg, #4
.endmacro
.macro patch_584
	dw 0xe84
.endmacro
.macro patch_59c
	dw 0xe9c
.endmacro
.macro patch_5a4
	dw 0xea4
.endmacro
.macro patch_5a8,reg
	dw 0xeb4
.endmacro
.macro patch_5ac
	dw 0xeac
.endmacro
.macro patch_5b0,reg
	; patch 0x5b0 -> 0xeb0
	mov reg, 0xeb
	lsl reg, reg, #4
.endmacro
.macro patch_5b4
	dw 0xeb4
.endmacro
.macro patch_600,reg
	mov reg, 0xf
	lsl reg, #8
.endmacro

; Set r1 = 0xeb8 (new menu struct size) - This gets passed to malloc()
.org 0x081dcdf8 :: ldr r1, [FUN_081dcdf4_const_5b8]
.org 0x081dce2e
pop {r4, lr}
FUN_081dcdf4_const_5b8: dw 0xeb8

.org 0x081dc7ee :: patch_5b0 r2
.org 0x081dc800 :: patch_5a4
.org 0x081dc80c :: patch_5b0 r3
.org 0x081dc81a :: patch_5b0 r1
.org 0x081dc830 :: ldr r3, [FUN_081dc7a0_const_5a8]
.org 0x081dc838 :: patch_5a4
.org 0x081dc84a :: patch_5b0 r1
.org 0x081dc85a :: ldr r2, [FUN_081dc7a0_const_5a8]
.org 0x081dc9c8 :: patch_5b4
.org 0x081dc9cc :: patch_59c
.org 0x081dc9d4 :: patch_5b0 r1
.org 0x081dca1c :: ldr r1, [FUN_081dc7a0_const_5a8]
.org 0x081dca34 :: patch_5ac
.org 0x081dca68 :: patch_5ac
.org 0x081dca5c
pop {r4-r7, pc}
nop
FUN_081dc7a0_const_5a8: dw 0xea8

.org 0x081dcae0 :: patch_5b0 r2
.org 0x081dccbc :: patch_600 r2
.org 0x081dccfa :: patch_580 r3
.org 0x081dcd00 :: patch_580 r3
.org 0x081dcd58 :: patch_5b0 r1
.org 0x081dcd84 :: patch_584
.org 0x081dcd8c :: patch_5b4

.close
