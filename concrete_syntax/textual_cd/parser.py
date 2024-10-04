grammar = r"""
%import common.WS_INLINE
%ignore WS_INLINE
%ignore COMMENT

%declare _INDENT _DEDENT

?start: (_NL | object )*

IDENTIFIER: /[A-Za-z_][A-Za-z_0-9]*/
COMMENT: /#.*/

# newline
_NL: /(\r?\n[\t ]*)+/

literal: INT
       | STR
       | BOOL

INT: /[0-9]+/
STR: /"[^"]*"/
   | /'[^']*'/
BOOL: "True" | "False"

object: [IDENTIFIER] ":" IDENTIFIER [link] _NL [_INDENT slot+ _DEDENT]
link: "(" IDENTIFIER "->" IDENTIFIER ")"
slot: IDENTIFIER "=" literal _NL
"""
