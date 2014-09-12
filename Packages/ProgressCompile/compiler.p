define variable cFile as character no-undo.
define variable i as integer no-undo.

cFile = entry (2, session:icfparameter, '=').
cFile = entry (1, cFile).

output to value ('c:\temp\result.txt').
compile value (cFile) no-error.
repeat i = 1 to compiler:num-messages:
    message compiler:get-message (i).
end.
output close.
