
function! Bufferlist()
let i = 0
    let max = bufnr('$')
    let lis = ""
    while i < max
        if bufexists(i)
            let lis = lis.";".i.":".bufname(i)
        endif
        let i = i + 1
    endwhile
    return lis
endfunction

function! Au_bufferchange()
    let @e="'bufferchange,".bufnr('%').",".bufname('%')."'"
    call Async_event(@e)
endfunction

function! Async_event(e)
    try
        exec "call server2client('".expand('<client>')."', ".@e.")"
    catch /.*/
    endtry
endfunction

au! BufEnter *
au BufEnter *  call Au_bufferchange()
