/* Diagnostic hooks for Blood Omen 2 (bo2.exe, image base 0x400000), used to reverse engineer the caption
 * pipeline. NOT part of the shipped patch. Build with tools/build_diag.py; it adds these hooks plus the
 * loose-file fallback (hookC) to a copy of bo2.exe, which logs to C:\bo2_diag.log (inside the Wine prefix:
 * drive_c/bo2_diag.log). Log lines are "<tag> <hex dword> ...":
 *   E  PhraseStart entry: this, message*                (followed by a line with the phrase name)
 *   P  just before the caption section of PhraseStart:   this, name string, its first dword (0 = empty),
 *      phrase record (0 = not in the phrase table), controller type
 *   A  AddCaption entry: manager, 3 args (text*, label*, lifetime), manager fields +0,+4,+0xc,+0x10,+0x14,+0x18
 *   D  caption draw entry, only while the manager's caption list is non-empty: manager fields, first record fields
 *   C  hookC loaded a .cnv from disk: file object, size, buffer, first dword
 *   LOAD <path>  the path the phrase table loader asks the virtual file system for
 * See docs/captions.md for what the values mean.
 */
    .intel_syntax noprefix
    .set CreateFileA, 0x83f0c0
    .set WriteFile,   0x83f190
    .set CloseHandle, 0x83f1fc
    .set GetFileSize, 0x83f064
    .set ReadFile,    0x83f094
    .set STR_FROM_C,  0x68e940
    .set STR_ASSIGN,  0x68ea80
    .set STR_FREE,    0x68e7c0
    .set PARSE,       0x4b6c50

    .text
    .globl _start
_start:

/* ---- logfn: dl = tag, esi = dword array, ecx = count; clobbers everything ---- */
logfn:
    push ebp
    mov ebp, esp
    sub esp, 0x200
    mov edi, esp
    mov byte ptr [edi], dl
    inc edi
lf_item:
    mov byte ptr [edi], 0x20
    inc edi
    mov eax, dword ptr [esi]
    add esi, 4
    mov ebx, 8
lf_digit:
    rol eax, 4
    mov edx, eax
    and edx, 15
    add dl, 0x30
    cmp dl, 0x39
    jbe lf_ok
    add dl, 7
lf_ok:
    mov byte ptr [edi], dl
    inc edi
    dec ebx
    jnz lf_digit
    dec ecx
    jnz lf_item
    mov word ptr [edi], 0x0a0d
    add edi, 2
    sub edi, esp
    mov ebx, edi                   /* length */
    lea esi, [ebp-0x200]           /* buffer */
    push 0
    push 0x80
    push 4
    push 0
    push 3
    push 4
    push offset diagpath
    call dword ptr ds:[CreateFileA]
    cmp eax, -1
    je lf_out
    mov edi, eax
    sub esp, 4
    push 0
    lea edx, [esp+4]
    push edx
    push ebx
    push esi
    push edi
    call dword ptr ds:[WriteFile]
    add esp, 4
    push edi
    call dword ptr ds:[CloseHandle]
lf_out:
    leave
    ret

/* ---- hook D: caption draw 0x5205b0 (relocates sub esp,0x14; push ebx; push ebp) ---- */
    .globl hookD
hookD:
    pushad
    pushfd
    mov eax, dword ptr [ecx+0x20]
    mov edx, dword ptr [eax]
    cmp edx, eax
    je hd_skip
    sub esp, 0x48
    mov dword ptr [esp+0], ecx
    mov eax, dword ptr [ecx]
    mov dword ptr [esp+4], eax
    mov eax, dword ptr [ecx+4]
    mov dword ptr [esp+8], eax
    mov eax, dword ptr [ecx+0xc]
    mov dword ptr [esp+12], eax
    mov eax, dword ptr [ecx+0x10]
    mov dword ptr [esp+16], eax
    mov eax, dword ptr [ecx+0x14]
    mov dword ptr [esp+20], eax
    mov eax, dword ptr [ecx+0x18]
    mov dword ptr [esp+24], eax
    mov eax, dword ptr [ecx+0x1c]
    mov dword ptr [esp+28], eax
    mov ebx, dword ptr [edx+8]
    mov dword ptr [esp+32], ebx
    mov eax, dword ptr [ebx+0x18]
    mov dword ptr [esp+36], eax
    mov eax, dword ptr [ebx+0x1c]
    mov dword ptr [esp+40], eax
    mov eax, dword ptr [ebx+0x28]
    mov dword ptr [esp+44], eax
    test eax, eax
    jz hd_z
    mov eax, dword ptr [eax]
hd_z:
    mov dword ptr [esp+48], eax
    mov eax, dword ptr [ebx+0x38]
    mov dword ptr [esp+52], eax
    mov eax, dword ptr [ebx+0x40]
    mov dword ptr [esp+56], eax
    mov eax, dword ptr [ebx+0x44]
    mov dword ptr [esp+60], eax
    mov esi, esp
    mov ecx, 16
    mov dl, 0x44
    call logfn
    add esp, 0x48
hd_skip:
    popfd
    popad
    sub esp, 0x14
    push ebx
    push ebp
    jmp 0x5205b5

/* ---- hook A: AddCaption 0x520470 (relocates push -1; push 0x811e5b) ---- */
    .globl hookA
hookA:
    push -1
    push 0x811e5b
    pushad
    pushfd
    sub esp, 0x28
    /* original [esp+4] was ret addr slot ... after our two pushes the args sit +8 further */
    mov dword ptr [esp+0], ecx
    mov eax, dword ptr [esp+0x28+0x24+8+4]
    mov dword ptr [esp+4], eax
    mov eax, dword ptr [esp+0x28+0x24+8+8]
    mov dword ptr [esp+8], eax
    mov eax, dword ptr [esp+0x28+0x24+8+12]
    mov dword ptr [esp+12], eax
    mov eax, dword ptr [ecx]
    mov dword ptr [esp+16], eax
    mov eax, dword ptr [ecx+4]
    mov dword ptr [esp+20], eax
    mov eax, dword ptr [ecx+0xc]
    mov dword ptr [esp+24], eax
    mov eax, dword ptr [ecx+0x10]
    mov dword ptr [esp+28], eax
    mov eax, dword ptr [ecx+0x14]
    mov dword ptr [esp+32], eax
    mov eax, dword ptr [ecx+0x18]
    mov dword ptr [esp+36], eax
    mov esi, esp
    mov ecx, 10
    mov dl, 0x41
    call logfn
    add esp, 0x28
    popfd
    popad
    jmp 0x520477

/* ---- hook 0: PhraseStart entry 0x4b6420 (relocates mov eax, fs:[0]); logs phrase name ---- */
    .globl hook0
hook0:
    mov eax, dword ptr fs:[0]
    pushad
    pushfd
    sub esp, 0x10
    mov dword ptr [esp+0], ecx
    mov eax, dword ptr [esp+0x38]
    mov dword ptr [esp+4], eax
    mov esi, esp
    mov ecx, 2
    mov dl, 0x45
    call logfn
    add esp, 0x10
    mov eax, dword ptr [esp+0x28]
    test eax, eax
    jz h0_done
    mov esi, dword ptr [eax+8]
    test esi, esi
    jz h0_done
    add esi, 6
    xor ebx, ebx
h0_len:
    cmp byte ptr [esi+ebx], 0
    je h0_have
    inc ebx
    cmp ebx, 200
    jb h0_len
h0_have:
    push 0
    push 0x80
    push 4
    push 0
    push 3
    push 4
    push offset diagpath
    call dword ptr ds:[CreateFileA]
    cmp eax, -1
    je h0_done
    mov ebp, eax
    sub esp, 4
    push 0
    lea edx, [esp+4]
    push edx
    push ebx
    push esi
    push ebp
    call dword ptr ds:[WriteFile]
    push 0
    lea edx, [esp+4]
    push edx
    push 2
    push offset crlf
    push ebp
    call dword ptr ds:[WriteFile]
    add esp, 4
    push ebp
    call dword ptr ds:[CloseHandle]
h0_done:
    popfd
    popad
    jmp 0x4b6426
crlf:
    .ascii "\r\n"

/* ---- probe P: 0x4b6756 (relocates mov ecx,[ebp]; cmp dword ptr [ecx],0), returns to 0x4b675c ---- */
    .globl hookP
hookP:
    mov ecx, dword ptr [ebp]
    cmp dword ptr [ecx], 0
    pushad
    pushfd
    sub esp, 0x14
    mov dword ptr [esp+0], esi
    mov dword ptr [esp+4], ecx
    mov eax, dword ptr [ecx]
    mov dword ptr [esp+8], eax
    mov eax, dword ptr [esi+0x24]
    mov dword ptr [esp+12], eax
    mov eax, dword ptr [esi+0xc]
    mov dword ptr [esp+16], eax
    mov esi, esp
    mov ecx, 5
    mov dl, 0x50
    call logfn
    add esp, 0x14
    popfd
    popad
    jmp 0x4b675c

/* ---- hook L: PhraseTable::Load 0x75aaa6, right after the path builder returns; eax -> path string handle ---- */
    .globl hookL
hookL:
    mov ecx, dword ptr ds:[0xa83ca0]   /* relocated original instruction */
    pushad
    pushfd
    test eax, eax
    jz hl_done
    mov esi, dword ptr [eax]
    test esi, esi
    jz hl_done
    add esi, 6
    xor ebx, ebx
hl_len:
    cmp byte ptr [esi+ebx], 0
    je hl_have
    inc ebx
    cmp ebx, 200
    jb hl_len
hl_have:
    push 0
    push 0x80
    push 4
    push 0
    push 3
    push 4
    push offset diagpath
    call dword ptr ds:[CreateFileA]
    cmp eax, -1
    je hl_done
    mov ebp, eax
    sub esp, 4
    push 0
    lea edx, [esp+4]
    push edx
    push 5
    push offset ltag
    push ebp
    call dword ptr ds:[WriteFile]
    push 0
    lea edx, [esp+4]
    push edx
    push ebx
    push esi
    push ebp
    call dword ptr ds:[WriteFile]
    push 0
    lea edx, [esp+4]
    push edx
    push 2
    push offset crlf
    push ebp
    call dword ptr ds:[WriteFile]
    add esp, 4
    push ebp
    call dword ptr ds:[CloseHandle]
hl_done:
    popfd
    popad
    jmp 0x75aaac
ltag:
    .ascii "LOAD "

/* ---- hook C: loose-file fallback inside FUN_00758e60 (whole-file reader) ----
 * Entered from the retargeted "je 0x758efd" at 0x758e76 (archive lookup failed).
 * edi = path handle*, stack: [esp]=saved edi [esp+4]=saved esi [esp+8]=ret [esp+0xc]=arg1 [esp+0x10]=obj
 * For paths ending in ".cnv" reads .\data\texts\<basename> into engine-allocated memory,
 * sets obj+8 = size, obj+0xc = buffer. Always finishes by jumping to 0x758efd.
 */
    .globl hookC
hookC:
    pushad
    pushfd
    sub esp, 0x240
    mov eax, dword ptr [edi]
    test eax, eax
    jz c_done
    lea esi, [eax+6]
    xor ebx, ebx
c_len:
    cmp byte ptr [esi+ebx], 0
    je c_have
    inc ebx
    cmp ebx, 400
    jb c_len
c_have:
    cmp ebx, 5
    jb c_done
    cmp dword ptr [esi+ebx-4], 0x766e632e
    jne c_done
    mov ecx, ebx
c_back:
    test ecx, ecx
    jz c_found
    mov al, byte ptr [esi+ecx-1]
    cmp al, 0x2f
    je c_found
    cmp al, 0x5c
    je c_found
    dec ecx
    jmp c_back
c_found:
    lea edi, [esp]
    mov edx, offset cnvprefix
c_pre:
    mov al, byte ptr [edx]
    test al, al
    jz c_pre_done
    mov byte ptr [edi], al
    inc edi
    inc edx
    jmp c_pre
c_pre_done:
    lea edx, [esi+ecx]
c_cp:
    mov al, byte ptr [edx]
    mov byte ptr [edi], al
    inc edx
    inc edi
    test al, al
    jnz c_cp
    lea eax, [esp]
    push 0
    push 0x80
    push 3
    push 0
    push 1
    push 0x80000000
    push eax
    call dword ptr ds:[CreateFileA]
    cmp eax, -1
    je c_done
    mov ebp, eax
    push 0
    push ebp
    call dword ptr ds:[GetFileSize]
    cmp eax, -1
    je c_close
    test eax, eax
    jz c_close
    cmp eax, 0x4000000
    ja c_close
    mov ebx, eax
    mov dword ptr [esp+0x200], 0x4b
    mov ecx, dword ptr ds:[0xa74590]
    mov edx, dword ptr [ecx]
    lea eax, [esp+0x200]
    push eax
    push ebx
    call dword ptr [edx+0x2c]
    test eax, eax
    jz c_close
    mov esi, eax
    mov edi, esi
    mov ecx, ebx
    xor eax, eax
    rep stosb
    lea edx, [esp+0x204]
    push 0
    push edx
    push ebx
    push esi
    push ebp
    call dword ptr ds:[ReadFile]
    mov eax, dword ptr [esp+0x274]
    mov dword ptr [eax+8], ebx
    mov dword ptr [eax+0xc], esi
    sub esp, 0x10
    mov dword ptr [esp+0], eax
    mov dword ptr [esp+4], ebx
    mov dword ptr [esp+8], esi
    mov eax, dword ptr [esi]
    mov dword ptr [esp+12], eax
    mov esi, esp
    mov ecx, 4
    mov dl, 0x43
    call logfn
    add esp, 0x10
c_close:
    push ebp
    call dword ptr ds:[CloseHandle]
c_done:
    add esp, 0x240
    popfd
    popad
    jmp 0x758efd
cnvprefix:
    .asciz ".\\data\\texts\\"
    .balign 4

diagpath:
    .asciz "C:\\bo2_diag.log"
    .balign 4
