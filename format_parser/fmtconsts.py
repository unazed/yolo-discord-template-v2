import enum
from .fmtregexp import interpret

COMMENT_IDENT       = interpret("--[.+whitespace]*")
NAMESPACE_IDENT     = interpret("[alphanum+underscore]*:[whitespace]*")
ASSIGNMENT_IDENT    = interpret("[nest]*[whitespace]*[alphanum+underscore]*[whitespace]*->[whitespace]*[.+whitespace]*")
STRING_ASSN_IDENT   = interpret('[nest]*[whitespace]*"[string]*"[whitespace]*->[whitespace]*[.+whitespace]*')


class ParseState(enum.Enum):
    INITIAL_STATE   = 0
    IN_NAMESPACE    = 1
