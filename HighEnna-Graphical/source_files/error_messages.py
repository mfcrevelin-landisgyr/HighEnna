def get_error_message(code):
    # ----------------------------------------------------------------------
    # Cache errors
    if code == "MULT_CACHE":
        return """
Error : Multiple cache blocks
This error happens when a second cache block is opened.
"""
    if code == "EOF_OPN_CACHE":
        return """
Error : Open cache block due to EOF
This error happens when a cache block is opened and never closed.
"""

    # ----------------------------------------------------------------------
    # Expression errors
    if code == "LB_OPN_EXP":
        return """
Error : Open expression due to line break
This error happens when an expression is opened and a line break occurs before it is closed.
"""
    if code == "EOF_OPN_EXP":
        return """
Error : Open expression due to EOF
This error happens when an expression is opened and never closed.
"""

    # ----------------------------------------------------------------------
    # Directive argument errors
    if code == "LB_OPN_ARG":
        return """
Error : Open directive argument due to line break
This error happens when a directive argument is opened and a line break occurs before it is closed.
"""
    if code == "EOF_OPN_ARG":
        return """
Error : Open directive argument due to EOF
This error happens when a directive argument is opened and never closed.
"""
    if code == "EMPTY_ARG":
        return """
Error : Empty directive argument
This error happens when a directive argument has no content.
"""
    if code == "INV_IDF":
        return """
Error : Invalid identifier
This error happens when the text immediately following "val_" or "var_" inside an expression is not a valid ASCII Python identifier.
"""

    # ----------------------------------------------------------------------
    # Block errors
    if code == "EOF_OPN_BLK":
        return """
Error : Open block due to EOF
This error happens when a block is opened  and never closed .
"""
    if code == "CLOSE_ROOT":
        return """
Error : Attempted close on ROOT block
This error happens when there is an attempt to close a block while no block is open .
"""

    # ----------------------------------------------------------------------
    # Directive format errors
    if code == "MULT_DIR":
        return """
Error : Multiple directives
This error happens when there is more than one directive in the same line.
"""
    if code == "INV_DIR_PRE":
        return """
Error : Invalid directive prefix
This error happens when the line containing a directive also contains code before it. The line must be clear.
"""
    if code == "INV_DIR_POS":
        return """
Error : Invalid directive postfix
This error happens when the line containing a directive also contains code after it. The line must be clear.
"""

    # ----------------------------------------------------------------------
    # ELSE / ELIF placement errors
    if code == "ELSE_ROOT":
        return """
Error : ELSE without IF
This error happens when there is an attempt to open an ELSE block without a parent IF block.
"""
    if code == "ELSE_OUT":
        return """
Error : ELSE without IF
This error happens when there is an attempt to open an ELSE block without a parent IF block.
"""
    if code == "ELIF_ROOT":
        return """
Error : ELIF without IF
This error happens when there is an attempt to open an ELIF block without a parent IF block.
"""
    if code == "ELIF_OUT":
        return """
Error : ELIF without IF
This error happens when there is an attempt to open an ELIF block without a parent IF block.
"""
    if code == "ELSE_ELIF":
        return """
Error : ELIF after ELSE
This error happens when there is an attempt to open an ELIF block after an ELSE block.
"""

    # ----------------------------------------------------------------------
    # Unknown
    return f"Unknown error code {code}."
