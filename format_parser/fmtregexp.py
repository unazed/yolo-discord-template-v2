from warnings import warn
from string import (ascii_letters, printable,
                    digits, whitespace)


OPEN_GROUP       = "["
END_GROUP        = "]"
CONCAT_GROUP     = "+"
GROUP_SUFFIX_AST = "*"

GROUP_CATEGORIES = {
        "alpha": ascii_letters,
        "alphanum": ascii_letters + digits,
        "digits": digits,
        "underscore": "_",
        "whitespace": whitespace.replace("\n", ""),
        ".": printable.strip(),
        "string": printable.replace('"', ""),
        "nest": "|"
        }


def parse_error(idx, string):
    raise SyntaxError(f"{idx+1}: {string}")


def category_error(category):
    raise ValueError(f"category {category!r} doesn't exist")


def internal_error(string):
    state_concatenating = False
    raise RuntimeError(string)


def validate_groups(token_list):
    validated_groups = []

    for token in token_list:
        if not isinstance(token, list):
            validated_groups.append(token)
            continue
        elif not token[1:]:
            if not token or isinstance(token[0], tuple):
                warn("empty groups are entirely pointless")
                continue

        token = token.copy()

        current_group = [""]
        for idx, category in enumerate(token):
            if isinstance(category, tuple):
                current_group.insert(0, category)
                continue
            elif (mapped := GROUP_CATEGORIES.get(category, None)) is None:
                category_error(category)
            current_group[-1] += mapped
        validated_groups.append(current_group)

    return validated_groups


def interpret(regexp):
    token_list = []
    current_group = [""]

    state_neutral = True
    state_expecting_group = False
    state_accept_suffix = False
    state_concatenating = False

    current_literal = ""

    for idx, char in enumerate(regexp):
        if state_expecting_group:
            if char == CONCAT_GROUP:
                if not current_group[-1]:
                    parse_error(idx, "can't concatenate with empty category")
                current_group.append("")
                state_concatenating = True
            elif char == END_GROUP:
                if state_concatenating and len(current_group) % 2 != 0:
                    parse_error(idx, "expected category with which to concatenate")
                elif current_group == [""]:
                    current_group = []
                token_list.append(current_group.copy())
                current_group = [""]
                state_expecting_group = False
                state_concatenating = False
                state_accept_suffix = True
                state_neutral = True
            else:
                current_group[-1] += char
            continue
        elif state_accept_suffix:
            state_accept_suffix = False
            if char == GROUP_SUFFIX_AST:
                token_list[-1].insert(0, (char,))
                continue

        if not state_neutral:
            internal_error("expected neutral state")
        elif state_accept_suffix:
            internal_error("accept-suffix state leaked")

        if char == OPEN_GROUP:
            if current_group != [""]:
                parse_error(idx, "nesting groups unimplemented")
            elif current_literal:
                token_list.append(current_literal)
                current_literal = ""
            state_expecting_group = True
        else:
            current_literal += char

    if current_literal:
        token_list.append(current_literal)

    return validate_groups(token_list)


def filter_whitespace(match):
    return [*filter(lambda k: not all(c in whitespace for c in k), match)]


def matches(regexp, expr):
    if not expr or not regexp:
        return (False, "")
    regexp_idx = 0
    regexp_str_idx = 0

    expr_idx = 0

    captured_groups = [""]

    while expr_idx != len(expr):
        char = expr[expr_idx]
        if regexp_idx == len(regexp):
            return (True, filter_whitespace(captured_groups))

        regexp_pattern = regexp[regexp_idx]
        if regexp_str_idx and regexp_str_idx == len(regexp_pattern):
            regexp_idx += 1
            regexp_str_idx = 0
            if regexp_idx == len(regexp):
                return (True, filter_whitespace(captured_groups))
            regexp_pattern = regexp[regexp_idx]

        if isinstance(regexp_pattern, list):
            *suffix, pattern = regexp_pattern
            if suffix and suffix[0] == (GROUP_SUFFIX_AST,):
                if char in pattern:
                    captured_groups[-1] += char
                else:
                    if captured_groups != [""]:
                        captured_groups.append("")
                    expr_idx -= 1
                    regexp_idx += 1
            elif not suffix:
                if char not in pattern:
                    return (False, captured_groups)
                captured_groups[-1] += char
                captured_groups.append("")
                regexp_idx += 1
        elif isinstance(regexp_pattern, str):
            if char != regexp_pattern[regexp_str_idx]:
                return (False, captured_groups)
            regexp_str_idx += 1
        expr_idx += 1
    
    if regexp_str_idx == len(regexp_pattern):
        regexp_idx += 1

    if regexp_idx < len(regexp) - 1:
        return (False, captured_groups)
    return (True, filter_whitespace(captured_groups))
