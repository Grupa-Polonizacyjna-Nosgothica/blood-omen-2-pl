/* Loose-file fallback for Blood Omen 2's whole-file reader (bo2.exe, image base 0x400000).
 *
 * Why: when a level or UI screen loads, the engine asks its virtual file system for
 *   /gogames/bo2/resources/levels/<area>/<name>.cnv
 * and parses the result as a phrase file (subtitle text, see docs/captions.md). The shipped archives
 * contain no such files, so every lookup fails and no captions are ever created.
 *
 * What: FUN_00758e60 (the reader) jumps to its epilogue at 0x758efd when the archive lookup
 * fails: "je 0x758efd" at 0x758e76. tools/build_patch.py retargets that 6-byte branch to hookC.
 * hookC then, for paths ending in ".cnv", opens .\data\texts\<basename> from disk, allocates a
 * zeroed buffer with the engine's allocator (the same call the original uses), reads the file into
 * it and sets obj+8 = size, obj+0xc = buffer on the file object the caller passed in. Everything
 * after that is unmodified engine code. In every other case it falls straight through to 0x758efd,
 * i.e. behaves exactly like the original failure path.
 *
 * Build (GNU binutils): as --32 -o cave.o cave.s && ld -m elf_i386 -Ttext=0x83e780 -o cave.elf cave.o
 *                       && objcopy -O binary -j .text cave.elf cave.bin
 * It is placed at 0x83e780, the unused zero tail of the .text section (file offset 0x43e780).
 *
 * Imports used (IAT slots of the shipped exe): CreateFileA 0x83f0c0, GetFileSize 0x83f064,
 * ReadFile 0x83f094, CloseHandle 0x83f1fc. The allocator object is the global at 0xa74590 (vtable +0x2c).
 */
    .intel_syntax noprefix
    .set CreateFileA, 0x83f0c0
    .set WriteFile,   0x83f190
    .set CloseHandle, 0x83f1fc
    .set GetFileSize, 0x83f064
    .set ReadFile,    0x83f094

    .text
    .globl _start
_start:
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
