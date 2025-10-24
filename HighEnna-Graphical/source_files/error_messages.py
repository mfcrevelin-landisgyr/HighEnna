def get_error_message(code):
    # ----------------------------------------------------------------------
    # Cache errors
    if code == "MULT_CACHE":
        return """\
Error : Multiple cache blocks
This error occurs when there is an attempt to open an extra cache block.
"""
    if code == "EOF_OPN_CACHE":
        return """\
Error : Open cache block due to EOF
This error occurs when a cache block is opened and the file ends before it is closed.
"""

    # ----------------------------------------------------------------------
    # Expression errors
    if code == "LB_OPN_EXP":
        return """\
Error : Open expression due to line break
This error occurs when an expression is opened and the line breaks before it is closed.
"""
    if code == "EOF_OPN_EXP":
        return """\
Error : Open expression due to EOF
This error occurs when an expression is opened and the file ends before it is closed.
"""

    # ----------------------------------------------------------------------
    # Directive argument errors
    if code == "LB_OPN_ARG":
        return """\
Error : Open directive argument due to line break
This error occurs when a directive argument is opened and the line breaks before it is closed.
"""
    if code == "EOF_OPN_ARG":
        return """\
Error : Open directive argument due to EOF
This error occurs when a directive argument is opened and the file ends before it is closed.
"""
    if code == "EMPTY_ARG":
        return """\
Error : Empty directive argument
This error occurs when a directive's argument has no content.
"""
    if code == "INV_IDF":
        return """\
Error : Invalid identifier
This error occurs when the text immediately following "val_" or "var_" inside an expression is not a valid Python start  identifier or is not ASCII.
"""

    # ----------------------------------------------------------------------
    # Block errors
    if code == "EOF_OPN_BLK":
        return """\
Error : Open block due to EOF
This error occurs when a block is opened and the file ends before it is closed.
"""
    if code == "CLOSE_ROOT":
        return """\
Error : Attempted close on ROOT block
This error occurs when there is an attempt to close a block while no block is open.
"""

    # ----------------------------------------------------------------------
    # Directive format errors
    if code == "INV_DIR_PRE":
        return """\
Error : Invalid directive prefix
This error occurs when a directive line contains code before the directive.
The line must be clear before and after the directive.
"""
    if code == "INV_DIR_POS":
        return """\
Error : Invalid directive postfix
This error occurs when a directive line contains code after the directive.
The line must be clear before and after the directive.
"""

    # ----------------------------------------------------------------------
    # ELSE / ELIF placement errors
    if code == "ELSE_ROOT":
        return """\
Error : ELSE on ROOT
This error occurs when there is an attempt to open an ELSE block without a parent IF block.
"""
    if code == "ELSE_OUT":
        return """\
Error : ELSE without IF
This error occurs when there is an attempt to open an ELSE block without a parent IF block.
"""
    if code == "ELIF_ROOT":
        return """\
Error : ELIF on ROOT
This error occurs when there is an attempt to open an ELIF block without a parent IF block.
"""
    if code == "ELIF_OUT":
        return """\
Error : ELIF without IF
This error occurs when there is an attempt to open an ELIF block without a parent IF block.
"""
    if code == "ELSE_ELIF":
        return """\
Error : ELIF after ELSE
This error occurs when there is an attempt to open an ELIF block after an ELSE block.
"""

    # ----------------------------------------------------------------------
    # Unknown
    return f"Unknown error code {code}."
