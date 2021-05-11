import os
import string
from .fmtconsts import *
from .fmtregexp import matches


def _type_rvalue(value):
    if value.startswith('"'):
        return value[1:value.index('"', 1)]
    return float(value)

def parse(data, global_):
    data = data.splitlines() 
    current_state = ParseState.INITIAL_STATE

    if global_:
        varspace = {"$global": {}}
        current_namespace = "$global"
    else:
        varspace = {}
        current_namespace = None

    for line in data:
        if (match := matches(COMMENT_IDENT, line))[0]:
            continue

        if current_state == ParseState.INITIAL_STATE:
            if (match := matches(NAMESPACE_IDENT, line))[0]:
                varspace[match[1][0]] = {}
                current_namespace = match[1][0]
                current_state = ParseState.IN_NAMESPACE
            elif (match := matches(ASSIGNMENT_IDENT, line))[0]:
                *indent, name, rval = match[1]
                if indent:
                    raise SyntaxError("assignment nested in namespace, but no namespace declared")
                varspace[current_namespace][name] = _type_rvalue(rval)
            elif (match := matches(STRING_ASSN_IDENT, line))[0]:
                *indent, name, rval = match[1]
                if indent:
                    raise SyntaxError("assignment nested in namespace, but no namespace declared")
                varspace[current_namespace][name] = _type_rvalue(rval)
        elif current_state == ParseState.IN_NAMESPACE:
            if (match := matches(ASSIGNMENT_IDENT, line))[0]:
                *indent, name, rval = match[1]
                if not indent:
                    current_state = ParseState.INITIAL_STATE
                    current_namespace = "$global"
                elif indent[0][1:]:
                    raise SyntaxError("multiple nesting unimplemented")
                varspace[current_namespace][name] = _type_rvalue(rval)
            elif (match := matches(STRING_ASSN_IDENT, line))[0]:
                *indent, name, rval = match[1]
                if not indent:
                    current_state = ParseState.INITIAL_STATE
                    current_namespace = "$global"
                elif indent[0][1:]:
                    raise SyntaxError("multiple nesting unimplemented")
                varspace[current_namespace][name] = _type_rvalue(rval)
            elif (match := matches(NAMESPACE_IDENT, line))[0]:
                varspace[match[1][0]] = {}
                current_namespace = match[1][0]
                current_state = ParseState.IN_NAMESPACE 

    return varspace


def loadfile(path, global_=True):
    if not os.path.isfile(path):
        raise IOError("path doesn't exist")
    with open(path) as config:
        config = config.read()
    return parse(config, global_)

