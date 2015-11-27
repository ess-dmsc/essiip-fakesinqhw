#!/usr/bin/env python
# Script Context Driver Generator
# Author: Douglas Clowes (douglas.clowes@ansto.gov.au) Jan/Feb 2014
# vim: ft=python ts=8 sts=4 sw=4 expandtab autoindent smartindent
#
# This program generates Script Context Driver TCL files.
#
# It takes one or more "Script Context Driver Description" files.
# Each file may contain one or more driver descriptions. Each driver
# description will result in one TCL file.
#
# The name of the file produced, the TCL namespace used and names within
# the file are based on the driver name givin in the driver description.
#
# TODO:
#   implement attributes and units on vars
#   - type part ???
#   - nxalias xxxxx
#   - sdsinfo
#   check simulation works
#   handle environmental monitoring (emon)
#   - figure out how to do it
#   - make nodes monitorable
#   - make it conditional
#   handle the driving settling time in checkstatus
# Questions:
#   what it the 'plain spy none' on hfactory
#   what is 'mugger' vs 'manager' - seems like alias?
#   should some hset commands be hupdate commands?
#

import os
import re
import ply.lex as lex
import ply.yacc as yacc

states = (
    ('tcl', 'exclusive'),
    )

FunctionTypes = [
    'read_function',
    'write_function',
    'fetch_function',
    'check_function',
    'pid_function',
    'checkrange_function',
    ]

DriveableFunctionTypes = [
    'halt_function',
    'checklimits_function',
    'checkstatus_function',
    ]

Verbose = False
DriverDump = False
CodeDump = False
PrintedFileName = -1
NumberOfLinesIn = 0
NumberOfLinesOut = 0
SourceFileList = []
SourceLineList = []

def PrintParseError(message):
    global PrintedFileName
    global lexer
    global SourceLineList, SourceData
    curr_line = lexer.lineno
    curr_file = SourceLineList[curr_line - 1][0]
    if curr_file != PrintedFileName:
        PrintedFileName = curr_file
        SourceFile = SourceFileList[curr_file]
        print "in", SourceFile
    print message
    print "%4d:" % SourceLineList[curr_line - 1][1], SourceData[curr_line - 1]

def PrintPostError(message):
    global PrintedFileName
    global SourceLineList
    curr_file = 0
    if curr_file != PrintedFileName:
        PrintedFileName = curr_file
        SourceFile = SourceFileList[curr_file]
        print "in", SourceFile
    print message

#
# Tokenizer: This recognizes the tokens which can be keywords, identifiers,
# numbers or strings plus the punctuation.
#

#
# Reserved words (keywords) in the form reserved['KEYWORD'] = 'TOKEN'
#

reserved = {
# Driver keywords
    'DRIVER' : 'DRIVER',
    'VENDOR' : 'VENDOR',
    'DEVICE' : 'DEVICE',
    'PROTOCOL' : 'PROTOCOL',
    'DRIVER_PROPERTY' : 'DRIVER_PROPERTY',
    'WRAPPER_PROPERTY' : 'WRAPPER_PROPERTY',
    'CLASS' : 'CLASS',
    'SIMULATION_GROUP' : 'SIMULATION_GROUP',
    'DEBUG_THRESHOLD' : 'DEBUG_THRESHOLD',
    'CODE' : 'CODE',
    'ADD_ARGS' : 'ADD_ARGS',
    'MAKE_ARGS' : 'MAKE_ARGS',
    'SOBJ_PRIV_TYPE' : 'SOBJ_PRIV_TYPE',
    'PROTOCOL_ARGS' : 'PROTOCOL_ARGS',
# Group keywords
    'GROUP' : 'GROUP',
    'GROUP_PROPERTY' : 'GROUP_PROPERTY',
# Variable keywords
    'VAR' : 'VAR',
    'PROPERTY' : 'PROPERTY',
    'CONTROL' : 'CONTROL',
    'CONDITIONAL' : 'CONDITIONAL',
    'DATA' : 'DATA',
    'NXSAVE' : 'NXSAVE',
    'MUTABLE' : 'MUTABLE',
    'READABLE' : 'READABLE',
    'WRITEABLE' : 'WRITEABLE',
    'DRIVEABLE' : 'DRIVEABLE',
    'PERMLINK' : 'PERMLINK',
    'TRUE' : 'TRUE',
    'FALSE' : 'FALSE',
# Data Types
    'TYPE' : 'TYPE',
    'FLOAT' : 'FLOAT',
    'INT' : 'INT',
    'TEXT' : 'TEXT',
    'NONE' : 'NONE',
# Privilege levels
    'PRIV' : 'PRIV',
    'SPY' : 'SPY',
    'USER' : 'USER',
    'MANAGER' : 'MANAGER',
    'READONLY' : 'READONLY',
    'INTERNAL' : 'INTERNAL',
# Functions and Commands
    'READ_COMMAND' : 'READ_COMMAND',
    'READ_FUNCTION' : 'READ_FUNCTION',
    'FETCH_FUNCTION' : 'FETCH_FUNCTION',
    'WRITE_COMMAND' : 'WRITE_COMMAND',
    'WRITE_FUNCTION' : 'WRITE_FUNCTION',
    'CHECK_FUNCTION' : 'CHECK_FUNCTION',
    'PID_FUNCTION' : 'PID_FUNCTION',
    'CHECKRANGE_FUNCTION' : 'CHECKRANGE_FUNCTION',
    'CHECKLIMITS_FUNCTION' : 'CHECKLIMITS_FUNCTION',
    'CHECKSTATUS_FUNCTION' : 'CHECKSTATUS_FUNCTION',
    'HALT_FUNCTION' : 'HALT_FUNCTION',
# Value setting
    'VALUE'  : 'VALUE',
    'ALLOWED'  : 'ALLOWED',
    'LOWERLIMIT' : 'LOWERLIMIT',
    'UPPERLIMIT' : 'UPPERLIMIT',
    'TOLERANCE' : 'TOLERANCE',
    'UNITS' : 'UNITS',
    }

#
# Tokens list with keyword tokens added at the end
#

tokens = [
    'LBRACE',
    'RBRACE',
    'SLASH',
    'INTEGER',
    'FLOATER',
    'CODE_STRING',
    'TEXT_STRING1',
    'TEXT_STRING2',
    'EQUALS',
    'ID',
    'TCL_BEG',
    'TCL_END',
    'AT_TCL',
    'AT_END',
    ] + list(reserved.values())

#
# Token rules
#

t_EQUALS = r'='
t_LBRACE = r'{'
t_RBRACE = r'}'
t_SLASH = r'/'

def t_AT_TCL(t):
    r'@TCL'
    if Verbose:
        print 'AT_TCL'
    t.lexer.begin('tcl')
    #return t

def t_tcl_AT_END(t):
    r'[ \t]*@END'
    if Verbose:
        print 'AT_END'
    t.lexer.begin('INITIAL')
    #return t

def t_TCL_BEG(t):
    r'{%%'
    if Verbose:
        print 'TCL_BEG'
    t.lexer.begin('tcl')
    return t

def t_tcl_TCL_END(t):
    r'.*%%}'
    if Verbose:
        print 'TCL_END'
    t.lexer.begin('INITIAL')
    return t

t_tcl_ignore = ""

def t_tcl_CODE_STRING(t):
    r'.+'
    if t.value[0] == '@':
        t.value = t.value[1:]
    if Verbose:
        print 'TCL:', t.value
    return t

def t_tcl_newline(t):
    r'\n+'
    t.lexer.lineno += t.value.count("\n")

def t_tcl_error(t):
    message = "Illegal tcl character '%s'" % t.value[0]
    PrintParseError(message)
    t.lexer.skip(1)

def t_TEXT_STRING1(t):
    r'\'[^\']*\''
    t.value = t.value[1:-1]
    return t

def t_TEXT_STRING2(t):
    r"\"[^\"]*\""
    t.value = t.value[1:-1]
    return t

def t_CODE_STRING(t):
    r'\@.*'
    t.value = t.value[1:]
    return t

def t_COMMENT(t):
    r'\#.*'
    pass
    # No Return Value. Token discarded

def t_FLOATER(t):
    r'-?\d+\.\d*([eE]\d+)?'
    try:
        t.value = float(t.value)
    except ValueError:
        message = "Floating value invalid: " + repr(t.value)
        PrintParseError(message)
        t.value = 0.0
    return t

def t_INTEGER(t):
    r'-?\d+'
    try:
        t.value = int(t.value)
    except ValueError:
        message = "Integer value too large: " + repr(t.value)
        PrintParseError(message)
        t.value = 0
    return t

def t_ID(t):
    r'[a-zA-Z_][a-zA-Z_0-9]*'
    t.type = reserved.get(t.value.upper(), 'ID')    # Check for reserved words
    # Force reserved words to lower case for map lookup and comparisson
    if t.value.upper() in reserved:
        t.type = reserved[t.value.upper()]
        t.value = t.value.lower()
    return t

# Ignored characters
t_ignore = " \t;"

def t_newline(t):
    r'\n+'
    t.lexer.lineno += t.value.count("\n")

def t_error(t):
    message = "Illegal character '%s' at line %d" % \
          (t.value[0], t.lexer.lineno)
    PrintParseError(message)
    t.lexer.skip(1)

#
# Parser
#

#
# Parsing rules
#

#
# We don't yet have a need for precedence so leave it empty here
#
precedence = (
    #('left','PLUS','MINUS'),
    #('left','TIMES','DIVIDE'),
    #('right','UMINUS'),
    )

#
# The head token - it all reduces to this
#
def p_driver(p):
    'driver : DRIVER id_or_str EQUALS driver_block'
    p[0] = [{ 'Driver' : {p[2] : p[4]}}]
    if Verbose:
        print "Driver:", p[0]
    global PathName
    global TheDrivers
    TheDrivers[p[2]] = p[4] + [{'PathName':PathName}]

def p_driver_block(p):
    'driver_block : LBRACE driver_statement_list RBRACE'
    p[0] = p[2]

def p_driver_statement_list(p):
    '''driver_statement_list : driver_statement
                      | driver_statement_list driver_statement
                      '''
    if len(p) == 2:
        p[0] = [p[1]]
    else:
        p[0] = p[1] + [p[2]]

def p_driver_statement(p):
    '''driver_statement : driver_assignment
                 | group
                 | code
                 | driver_property
                 | wrapper_property
    '''
    p[0] = p[1]

def p_driver_assignment(p):
    '''
    driver_assignment : VENDOR EQUALS id_or_str
                      | DEVICE EQUALS id_or_str
                      | PROTOCOL EQUALS id_or_str
                      | CLASS EQUALS id_or_str
                      | SIMULATION_GROUP EQUALS id_or_str
                      | ADD_ARGS EQUALS text_string
                      | MAKE_ARGS EQUALS text_string
                      | SOBJ_PRIV_TYPE EQUALS text_string
                      | PROTOCOL_ARGS EQUALS text_string
                      | DEBUG_THRESHOLD EQUALS value
    '''
    p[0] = { p[1] : p[3] }

#
# The GROUP block
#
def p_group(p):
    '''
    group : named_group
          | unnamed_group
    '''
    p[0] = p[1]

def p_named_group(p):
    '''
    named_group : GROUP group_id EQUALS LBRACE group_statement_list RBRACE
    '''
    p[0] = { 'Group' : [{'name': p[2]}] + p[5] }

def p_unnamed_group(p):
    '''
    unnamed_group : GROUP EQUALS LBRACE group_statement_list RBRACE
    '''
    p[0] = { 'Group' : [{'name': None}] + p[4] }

def p_group_id(p):
    '''
    group_id  : id_or_str
    '''
    p[0] = p[1]

def p_group_statement_list(p):
    '''
    group_statement_list : group_statement
                         | group_statement_list group_statement
    '''
    if len(p) == 2:
        p[0] = [p[1]]
    else:
        p[0] = p[1] + [p[2]]

def p_group_statement(p):
    '''group_statement : group_assignment
                       | variable
                       | group
                 '''
    p[0] = p[1]

def p_group_assignment(p):
    '''group_assignment : group_property
                        | var_typ_ass
                        | property
    '''
    p[0] = p[1]

#
# The VAR block
#
def p_variable(p):
    '''
    variable : VAR id_or_str EQUALS LBRACE variable_statement_list RBRACE
              | VAR id_or_str EQUALS LBRACE RBRACE
              | VAR id_or_str
    '''
    if len(p) > 6:
        p[0] = { 'Variable' : [{'name' : p[2]}] + p[5] }
    else:
        p[0] = { 'Variable' : [{'name' : p[2]}] }

def p_variable_statement_list(p):
    '''variable_statement_list : variable_statement
                      | variable_statement_list variable_statement
                      '''
    if len(p) == 2:
        p[0] = [p[1]]
    else:
        p[0] = p[1] + [p[2]]

def p_variable_statement(p):
    '''variable_statement : var_typ_ass
                          | var_val_ass
                          | property
                          | variable
                          | group
                 '''
    p[0] = p[1]

def p_var_typ_ass(p):
    '''
    var_typ_ass  : READABLE EQUALS INTEGER
                 | WRITEABLE EQUALS INTEGER
                 | READ_COMMAND EQUALS text_string
                 | READ_FUNCTION EQUALS id_or_str
                 | FETCH_FUNCTION EQUALS id_or_str
                 | WRITE_COMMAND EQUALS text_string
                 | WRITE_FUNCTION EQUALS id_or_str
                 | CHECK_FUNCTION EQUALS id_or_str
                 | PID_FUNCTION EQUALS id_or_str
                 | CHECKRANGE_FUNCTION EQUALS id_or_str
                 | CHECKLIMITS_FUNCTION EQUALS id_or_str
                 | CHECKSTATUS_FUNCTION EQUALS id_or_str
                 | HALT_FUNCTION EQUALS id_or_str
                 | TYPE EQUALS type_code
                 | PRIV EQUALS priv_code
                 | CONTROL EQUALS true_false
                 | DATA EQUALS true_false
                 | NXSAVE EQUALS true_false
                 | MUTABLE EQUALS true_false
                 | CONDITIONAL EQUALS text_string
    '''
    p[0] = { p[1] : p[3] }

def p_var_path(p):
    '''
    var_path  : id_or_str
              | var_path SLASH id_or_str
    '''
    if len(p) == 2:
        p[0] = p[1]
    else:
        p[0] = p[1] + '/' + p[3]

def p_var_val_ass(p):
    '''
    var_val_ass : VALUE EQUALS FLOATER
                | VALUE EQUALS text_string
                | VALUE EQUALS INTEGER
                | ALLOWED EQUALS text_string
                | UNITS EQUALS text_string
                | LOWERLIMIT EQUALS value
                | UPPERLIMIT EQUALS value
                | TOLERANCE EQUALS value
                | PERMLINK EQUALS text_string
                | DRIVEABLE EQUALS var_path
    '''
    p[0] = { p[1] : p[3] }

def p_driver_property(p):
    '''
    driver_property : DRIVER_PROPERTY id_or_str EQUALS value
    '''
    p[0] = { 'DriverProperty' : ( p[2], p[4] ) }

def p_wrapper_property(p):
    '''
    wrapper_property : WRAPPER_PROPERTY id_or_str EQUALS value
    '''
    p[0] = { 'WrapperProperty' : ( p[2], p[4] ) }

def p_group_property(p):
    '''
    group_property : GROUP_PROPERTY id_or_str EQUALS value
    '''
    p[0] = { 'GroupProperty' : ( p[2], p[4] ) }

def p_property(p):
    '''
    property : PROPERTY id_or_str EQUALS value
    '''
    p[0] = { 'Property' : ( p[2], p[4] ) }

def p_value(p):
    '''
    value : number
          | id_or_str
          | true_false
    '''
    p[0] = p[1]

def p_number(p):
    '''
    number : INTEGER
           | FLOATER
    '''
    p[0] = p[1]

def p_type_code(p):
    '''
    type_code : FLOAT
              | INT
              | TEXT
              | NONE
    '''
    p[0] = p[1]

def p_priv_code(p):
    '''
    priv_code : SPY
              | USER
              | MANAGER
              | READONLY
              | INTERNAL
    '''
    p[0] = p[1]

def p_true_false(p):
    '''
    true_false  : TRUE
                | FALSE
    '''
    p[0] = p[1]

#
# The CODE block
#
def p_code(p):
    '''
    code : CODE code_type id_or_str EQUALS LBRACE code_block RBRACE
         | CODE code_type id_or_str EQUALS LBRACE tcl_code_block RBRACE
         | CODE code_type id_or_str EQUALS TCL_BEG code_block TCL_END
    '''
    if p[3].lower() == 'preamble':
        name = 'preamble'
    elif p[3].lower() == 'postamble':
        name = 'postamble'
    elif p[3].lower() == 'mkdriver':
        name = 'mkDriver'
    elif p[3].lower() == 'mkwrapper':
        name = 'mkWrapper'
    p[0] = { 'Code' : { 'name' : p[3], 'type' : p[2], 'text' : p[6] }}

def p_code_type(p):
    '''
    code_type : READ_FUNCTION
              | FETCH_FUNCTION
              | WRITE_FUNCTION
              | CHECK_FUNCTION
              | PID_FUNCTION
              | CHECKRANGE_FUNCTION
              | CHECKLIMITS_FUNCTION
              | CHECKSTATUS_FUNCTION
              | HALT_FUNCTION
              | empty
    '''
    p[0] = p[1]

def p_tcl_code_block(p):
    '''
    tcl_code_block : AT_TCL code_block AT_END
    '''
    p[0] = p[2]

def p_code_block(p):
    '''code_block : empty
                  | code_block CODE_STRING
    '''
    if len(p) == 2:
        p[0] = []
    else:
        p[0] = p[1] + [p[2]]

def p_id_or_str(p):
    '''
    id_or_str : ID
              | text_string
    '''
    p[0] = p[1]

def p_text_string(p):
    '''
    text_string : TEXT_STRING1
                | TEXT_STRING2
    '''
    p[0] = p[1]

def p_empty(p):
    '''
    empty :
    '''
    pass

def p_error(t):
    message = "Syntax error at line %d" % lexer.lineno
    message += " " + repr(t)
    message += " " + repr(t.value)
    PrintParseError(message)

#
# Utility functions
#
def make_path(MyVar, ch = '_'):
    path = MyVar['path']
    if len(path) > 0:
        path = path.replace('/', ch)
        path += ch
    path += MyVar['name']
    return path

def generate_filename(MyDriver):
    global args
    old_name = "sct_%s.tcl" % MyDriver['name']
    new_name = "%s_sct.tcl" % MyDriver['name']
    if 'PathName' in MyDriver:
        full_old_name = os.path.join(MyDriver['PathName'], old_name)
        full_new_name = os.path.join(MyDriver['PathName'], new_name)
    else:
        full_old_name = old_name
        full_new_name = new_name

    # This block of code generates shell commands to help the old->new rename
    if Move:
        fd = open("git_mv.sh", "a")
        fd.write( "git mv " + full_old_name + " " + full_new_name + "\n")
        fd.close()
        fd = open("grep_sed.sh", "a")
        fd.write( "for f in $(grep " + old_name + " instrument -Irl" + "); do\n")
        fd.write( "  echo ${f}\n")
        fd.write( "  sed -i ${f} -e 's/" + old_name + "/" + new_name + "/'\n")
        fd.write( "done\n")
        fd.close()

    if args.sct == "before":
        MyDriver['filename'] = old_name
        MyDriver['fullname'] = full_old_name
    else:
        MyDriver['filename'] = new_name
        MyDriver['fullname'] = full_new_name

def parse_args(arg_str):
    '''
    Parse the TCL argument string into a list of identifiers (in order) plus
    a map of identifier to default value (or None) returned as a 2-tuple
    '''
    arg_list = re.findall(r'({[^}]+}|[A-Za-z0-9_]+)', arg_str)
    arg_lst = []
    arg_map = {}
    for arg in arg_list:
        if arg.startswith('{'):
            bits = arg[1:-1].split(None, 1)
            arg_lst.append(bits[0])
            arg_map[bits[0]] = bits[1]
        else:
            arg_lst.append(arg)
            arg_map[arg] = None
    return (arg_lst, arg_map)

#
# This section handles building a driver tree from the Abstract Syntax Tree
# generated by the parser. The driver tree has all of the defaults and
# cascading context explicitly stated to make the code generation simpler.
#
def init_context():
    global ContextStack, ContextIndex
    ContextStack = [{}]
    ContextIndex = 0
    ContextStack[ContextIndex]['type'] = 'none'
    ContextStack[ContextIndex]['priv'] = 'user'
    ContextStack[ContextIndex]['readable'] = 0
    ContextStack[ContextIndex]['writeable'] = 0
    ContextStack[ContextIndex]['driveable'] = None
    ContextStack[ContextIndex]['control'] = 'true'
    ContextStack[ContextIndex]['data'] = 'true'
    ContextStack[ContextIndex]['mutable'] = 'true'
    ContextStack[ContextIndex]['nxsave'] = 'true'
    ContextStack[ContextIndex]['read_function'] = 'rdValue'
    ContextStack[ContextIndex]['write_function'] = 'setValue'
    ContextStack[ContextIndex]['fetch_function'] = 'getValue'
    ContextStack[ContextIndex]['check_function'] = 'noResponse'
    ContextStack[ContextIndex]['checkrange_function'] = 'checkrange'
    ContextStack[ContextIndex]['path'] = ''

def push_context():
    global ContextStack, ContextIndex
    ContextIndex = ContextIndex + 1
    if len(ContextStack) <= ContextIndex:
        ContextStack.append({})
    ContextStack[ContextIndex] = {}
    for k in ContextStack[ContextIndex - 1].keys():
        ContextStack[ContextIndex][k] =  ContextStack[ContextIndex - 1][k]

def pop_context():
    global ContextStack, ContextIndex
    ContextIndex = ContextIndex - 1

def build_code(MyDriver, p):
    if Verbose:
        print 'Code:', p
        print "Function:", p['name']
    MyCode = {}
    MyCode['name'] = p['name']
    MyCode['reference_count'] = 0
    if 'type' in p:
        MyCode['type'] = p['type']
    MyCode['text'] = p['text']
    if Verbose:
        for line in p['text']:
            print "  Line:", line
    return MyCode

def build_variable(MyDriver, p):
    global FunctionTypes
    global DriveableFunctionTypes
    if Verbose:
        print 'Variable:', p
    MyVar = {}
    MyVar['Property'] = {}
    MyVar['Group'] = {}
    MyVar['Variable'] = {}
    # Copy items for this variable
    for item in p:
        if Verbose:
            print "Variable Item:", item
        for key in item.keys():
            if key == 'Property':
                MyVar['Property'][item[key][0]] = item[key][1]
            elif key == 'Group':
                pass # process nested groups at the bottom
            elif key == 'Variable':
                pass # process nested variables at the bottom
            else:
                MyVar[key] = item[key]
    # copy the defaults for missing items
    for key in ContextStack[ContextIndex]:
        if key == 'Property':
            for key2 in ContextStack[ContextIndex][key]:
                if key2 not in MyVar['Property']:
                    MyVar['Property'][key2] = ContextStack[ContextIndex][key][key2]
        elif not key in MyVar:
            MyVar[key] = ContextStack[ContextIndex][key]
    if 'sdsinfo' not in MyVar['Property']:
        MyVar['Property']['sdsinfo'] = '::nexus::scobj::sdsinfo'
    # set the type if not explicitly set
    if 'type' not in MyVar['Property']:
        if 'driveable' in MyVar and MyVar['driveable']:
            MyVar['Property']['type'] = 'drivable'
        else:
            MyVar['Property']['type'] = 'part'
    # if this variable is driveable
    if 'driveable' in MyVar and MyVar['driveable']:
        # insert defaults for missing driveable functions
        if 'checklimits_function' not in MyVar:
            MyVar['checklimits_function'] = 'checklimits'
        if 'checkstatus_function' not in MyVar:
            MyVar['checkstatus_function'] = 'checkstatus'
        if 'halt_function' not in MyVar:
            MyVar['halt_function'] = 'halt'

    for func in FunctionTypes + DriveableFunctionTypes:
        if func in MyVar and MyVar[func] != 'none':
            if Verbose:
                print 'Var:', MyVar['name'], 'Func:', func, '=', MyVar[func]
            if MyVar[func] not in MyDriver['Funcs']:
                MyDriver['Funcs'][MyVar[func]] = { 'type' : func, 'text' : [], 'reference_count' : 0 }
                if Verbose:
                    print MyVar['name'], 'Add func ' + MyVar[func], MyDriver['Funcs'][MyVar[func]]
            elif not MyDriver['Funcs'][MyVar[func]]['type'] == func:
                # allow override of type none else error message
                if not MyDriver['Funcs'][MyVar[func]]['type']:
                    if Verbose:
                        print MyVar['name'], 'Mod func type:', MyDriver['Funcs'][MyVar[func]], '= ' + func
                    MyDriver['Funcs'][MyVar[func]]['type'] = func
                else:
                    # TODO FIXME error message
                    message = 'Error: Function type mismatch: var = ' + str(MyVar) + ', code = ' + str(MyDriver['Funcs'][MyVar[func]]) + ', func = ' + str(func)
                    PrintPostError(message)
            MyDriver['Funcs'][MyVar[func]]['reference_count'] += 1
    if 'permlink' in MyVar:
        device_type, node_type = MyVar['permlink'].split('.')
        if node_type not in MyDriver['Permlink']:
            MyDriver['Permlink'][node_type] = []
        MyDriver['Permlink'][node_type] += [make_path(MyVar)]
    # Process the nested groups
    for item in p:
        for key in item.keys():
            if key == 'Group':
                if Verbose:
                    print "SubGroup Item:", item[key]
                push_context()
                if len(ContextStack[ContextIndex]['path']) > 0:
                    ContextStack[ContextIndex]['path'] += '/'
                ContextStack[ContextIndex]['path'] += MyVar['name']
                MyVar['Group'][item[key][0]['name']] = build_group(MyDriver, item[key])
                pop_context()
    # Process the nested variables
    for item in p:
        for key in item.keys():
            if key == 'Variable':
                if Verbose:
                    print "SubVariable Item:", item[key]
                push_context()
                if len(ContextStack[ContextIndex]['path']) > 0:
                    ContextStack[ContextIndex]['path'] += '/'
                ContextStack[ContextIndex]['path'] += MyVar['name']
                MyVar['Variable'][item[key][0]['name']] = build_variable(MyDriver, item[key])
                pop_context()
    if Verbose:
        print '==>>MyVar:', MyVar
    return MyVar

def build_group(MyDriver, p):
    if Verbose:
        print 'Group:', p[0]['name'], p
    push_context()
    MyGroup = {}
    MyGroup['Groups'] = {}
    MyGroup['Vars'] = {}
    # the sequence of both variables and non-variables is significant
    # Therefore, they have to be processed in a single sequence
    if p[0]['name']:
        if len(ContextStack[ContextIndex]['path']) > 0:
            ContextStack[ContextIndex]['path'] += '/'
        ContextStack[ContextIndex]['path'] += p[0]['name']
    MyGroup['path'] = ContextStack[ContextIndex]['path']
    for item in p:
        if 'Variable' in item:
            MyVar = build_variable(MyDriver, item['Variable'])
            MyGroup['Vars'][MyVar['name']] = MyVar
        elif 'Group' in item:
            MySubGroup = build_group(MyDriver, item['Group'])
            MyGroup['Groups'][MySubGroup['name']] = MySubGroup
        else:
            if Verbose:
                print "Group Item:", item
            if 'GroupProperty' in item:
                if 'GroupProperty' not in MyGroup:
                    MyGroup['GroupProperty'] = {}
                MyGroup['GroupProperty'][item['GroupProperty'][0]] = item['GroupProperty'][1]
            elif 'Property' in item:
                if 'Property' not in MyGroup:
                    MyGroup['Property'] = {}
                MyGroup['Property'][item['Property'][0]] = item['Property'][1]
                if 'Property' not in ContextStack[ContextIndex]:
                    ContextStack[ContextIndex]['Property'] = {}
                ContextStack[ContextIndex]['Property'][item['Property'][0]] = item['Property'][1]
            else:
                for key in item:
                    MyGroup[key] = item[key]
                    if key in ContextStack[ContextIndex]:
                        ContextStack[ContextIndex][key] = item[key]
    pop_context()
    adjust_group(MyGroup)
    return MyGroup

def adjust_group(MyGroup):
    if Verbose:
        print 'ante adjust_group', MyGroup
    MyData = None
    for var in MyGroup['Vars']:
        if Verbose:
            print "Var:", MyGroup['Vars'][var]
        if 'data' in MyGroup['Vars'][var]:
            if MyGroup['Vars'][var]['data'] == 'true':
                MyData = 'true'
                if 'klass' not in MyGroup['Vars'][var]['Property']:
                    MyGroup['Vars'][var]['Property']['klass'] = 'parameter'
            else:
                MyData = 'false'
    if MyData is None:
        for grp in  MyGroup['Groups']:
            if Verbose:
                print "Grp:", MyGroup['Groups'][grp]
            adjust_group(MyGroup['Groups'][grp])
            if 'data' in MyGroup['Groups'][grp]['GroupProperty']:
                if MyGroup['Groups'][grp]['GroupProperty']['data'] == 'true':
                    MyData = 'true'
                else:
                    MyData = 'false'
                break
    if MyData is not None:
        if 'GroupProperty' not in MyGroup:
            MyGroup['GroupProperty'] = {}
        if 'data' not in MyGroup['GroupProperty']:
            MyGroup['GroupProperty']['data'] = MyData
        if MyData:
            if 'klass' not in MyGroup['GroupProperty']:
                MyGroup['GroupProperty']['klass'] = '@none'
            if 'type' not in MyGroup['GroupProperty']:
                MyGroup['GroupProperty']['type'] = 'part'
    if Verbose:
        print 'post adjust_group', MyGroup

def check_func_code(MyDriver):
    for name in MyDriver['Funcs']:
        #print name
        left_paren_count = 0
        right_paren_count = 0
        left_brack_count = 0
        right_brack_count = 0
        left_brace_count = 0
        right_brace_count = 0
        for idx, line in enumerate(MyDriver['Funcs'][name]['text']):
            #print "%4d:" % (idx + 1), line
            left_paren_count += line.count('(')
            right_paren_count += line.count(')')
            left_brack_count += line.count('[')
            right_brack_count += line.count(']')
            left_brace_count += line.count('{')
            right_brace_count += line.count('}')
        if left_paren_count != right_paren_count:
            PrintPostError("Warning: Mismatched Parens in function %s (%d != %d)" % (name, left_paren_count, right_paren_count))
        if left_brack_count != right_brack_count:
            PrintPostError("Warning: Mismatched Brackets in function %s (%d != %d)" % (name, left_brack_count, right_brack_count))
        if left_brace_count != right_brace_count:
            PrintPostError("Warning: Mismatched Braces in function %s (%d != %d)" % (name, left_brace_count, right_brace_count))

def build_driver(MyDriver, TheTree):
    if Verbose:
        print "TheTree:", TheTree
    init_context()
    for item in [x for x in TheTree if 'Code' in x]:
        MyCode = build_code(MyDriver, item['Code'])
        MyDriver['Funcs'][MyCode['name']] = MyCode
    for item in [x for x in TheTree if 'Group' in x]:
        MyGroup = build_group(MyDriver, item['Group'])
        MyDriver['Groups'][MyGroup['name']] = MyGroup
    for item in TheTree:
        if Verbose:
            print "Driver Item:", item
        if 'Group' in item:
            continue
        elif 'Code' in item:
            continue
        else:
            if 'DriverProperty' in item:
                if 'DriverProperty' not in MyDriver:
                    MyDriver['DriverProperty'] = {}
                MyDriver['DriverProperty'][item['DriverProperty'][0]] = item['DriverProperty'][1]
                continue
            if 'WrapperProperty' in item:
                if 'WrapperProperty' not in MyDriver:
                    MyDriver['WrapperProperty'] = {}
                MyDriver['WrapperProperty'][item['WrapperProperty'][0]] = item['WrapperProperty'][1]
                continue
            for key in item:
                MyDriver[key] = item[key]
    for item in MyDriver['Permlink']:
        if len(MyDriver['Permlink'][item]) > 1:
            message = 'Error: duplicate permlink entries for "%s"' % item
            message += " " + repr(MyDriver['Permlink'][item])
            PrintPostError(message)
    if 'add_args' in MyDriver:
        MyDriver['add_args_lst'], MyDriver['add_args_map'] = parse_args(MyDriver['add_args'])
        if Verbose:
            print "ADD_ARGS:", MyDriver['add_args']
            arg_map = MyDriver['add_args_map']
            for arg in arg_map:
                print '  %s:' % arg, arg_map[arg]
    if 'make_args' in MyDriver:
        MyDriver['make_args_lst'], MyDriver['make_args_map'] = parse_args(MyDriver['make_args'])
        if Verbose:
            print "MAKE_ARGS:", MyDriver['make_args']
            arg_map = MyDriver['make_args_map']
            for arg in arg_map:
                print '  %s:' % arg, arg_map[arg]
    if 'protocol_args' in MyDriver:
        MyDriver['protocol_args_lst'], MyDriver['protocol_args_map'] = parse_args(MyDriver['protocol_args'])
        if Verbose:
            print "PROTOCOL_ARGS:", MyDriver['protocol_args']
            arg_map = MyDriver['protocol_args_map']
            for arg in arg_map:
                print '  %s:' % arg, arg_map[arg]
    if 'add_args_lst' in MyDriver and 'make_args_lst' in MyDriver:
        if MyDriver['add_args_lst'] != MyDriver['make_args_lst']:
            print "Add_Args:", MyDriver['add_args_lst']
            print "Make_Args:", MyDriver['make_args_lst']
    if Verbose:
        print "MyDriver:", MyDriver
#
# Driver Dump Functions
#
def dump_driver_vars(vars, indent):
    global FunctionTypes
    global DriveableFunctionTypes
    for item in sorted(vars):
        print indent + 'VAR %s = {' % item
        Comments = ['name', 'path']
        Deferred = ['Property', 'Variable', 'Group'] + Comments + FunctionTypes + DriveableFunctionTypes
        for Comment in sorted(Comments):
            if Comment in vars[item]:
                print indent + '  # %s = \'%s\'' % (Comment, vars[item][Comment])
        for subitem in sorted([i for i in vars[item] if i not in Deferred]):
            print indent + '  %s = \'%s\'' % (subitem, vars[item][subitem])
        for subitem in sorted([i for i in vars[item] if i in FunctionTypes]):
            print indent + '  %s = \'%s\'' % (subitem, vars[item][subitem])
        for subitem in sorted([i for i in vars[item] if i in DriveableFunctionTypes]):
            print indent + '  %s = \'%s\'' % (subitem, vars[item][subitem])
        for subitem in sorted([i for i in vars[item]['Property']]):
            print indent + '  Property \'%s\' = \'%s\'' % (subitem, vars[item]['Property'][subitem])
        # Dump the nested groups and vars
        dump_driver_groups(vars[item]['Group'], indent + '  ')
        dump_driver_vars(vars[item]['Variable'], indent + '  ')
        print indent + '}'

def dump_driver_groups(groups, indent):
    for item in sorted(groups):
        if item:
            print indent + 'GROUP ' + item + ' = {'
        else:
            print indent + 'GROUP = {'
        Comments = ['name', 'path']
        Deferred = ['Groups', 'Vars', 'GroupProperty'] + Comments
        for Comment in sorted(Comments):
            if Comment in groups[item]:
                print indent + '  # %s = \'%s\'' % (Comment, groups[item][Comment])
        for subitem in sorted([x for x in groups[item] if not x in Deferred]):
            print indent + ' ', subitem, '= \'%s\'' % groups[item][subitem]
        if 'GroupProperty' in groups[item]:
            for subitem in groups[item]['GroupProperty']:
                print indent + '  GroupProperty', subitem, '= \'%s\'' % groups[item]['GroupProperty'][subitem]
        dump_driver_vars(groups[item]['Vars'], indent + '  ')
        dump_driver_groups(groups[item]['Groups'], indent + '  ')
        print indent + '}'

def dump_driver_funcs(funcs):
    for item in sorted(funcs):
        if 'type' in funcs[item] and funcs[item]['type']:
            print '  CODE ' + funcs[item]['type'] + ' ' + item + ' = {'
        else:
            print '  CODE ' + item + ' = {'
        for line in funcs[item]['text']:
            print '    @%s' % line
        print '  }'

def dump_driver(MyDriver):
    print 'DRIVER ' + MyDriver['name'] + ' = {'
    Comments = ['PathName', 'Permlink']
    Comments += ['add_args_lst']
    Comments += ['add_args_map']
    Comments += ['make_args_lst']
    Comments += ['make_args_map']
    Comments += ['protocol_args_lst']
    Comments += ['protocol_args_map']
    Deferred =  ['Groups', 'Funcs', 'Deferred', 'name'] + Comments
    for Comment in sorted(Comments):
        if Comment in MyDriver:
            print '# %s = \'%s\'' % (Comment, MyDriver[Comment])
    for item in sorted([x for x in MyDriver if x not in Deferred]):
        print '  ' + item + ' =', '\'%s\'' % MyDriver[item]
    #print 'Groups:', MyDriver['Groups']
    dump_driver_groups(MyDriver['Groups'], '  ')
    #print 'Funcs:', MyDriver['Funcs']
    dump_driver_funcs(MyDriver['Funcs'])
    print '}'
#
# Code Generation Functions
#
def emit(txt):
    global NumberOfLinesOut
    NumberOfLinesOut += len(txt)
    for line in txt:
        fdo.write(line)
        if not line.endswith('\n'):
            fdo.write('\n')

def put_preamble(MyDriver):
    txt = []
    txt += ['# Generated driver for %s' % MyDriver['name']]
    txt += ['# vim: ft=tcl tabstop=8  softtabstop=2  shiftwidth=2  nocindent  smartindent']
    txt += ['#']
    txt += ['']
    txt += ['namespace eval %s {' % MyDriver['namespace']]
    txt += ['  set debug_threshold %s' % str( MyDriver['debug_threshold'])]
    if len(MyDriver['Permlink']) > 0:
        if 'make_args_lst' in MyDriver and 'id' in MyDriver['make_args_lst']:
            pass
        else:
            txt += ['  if { ![info exists ::scobj::permlink_device_counter]} {']
            txt += ['    set ::scobj::permlink_device_counter 0']
            txt += ['  }']
    func = 'preamble'
    if func in MyDriver['Funcs']:
        txt += ['# %s hook code starts' % func]
        txt += MyDriver['Funcs'][func]['text']
        txt += ['# %s hook code ends' % func]
    txt += ['}']
    txt += ['']
    txt += ['proc %s::debug_log {tc_root debug_level debug_string} {' % MyDriver['namespace']]
    txt += ['  set catch_status [ catch {']
    txt += ['    set debug_threshold [hgetpropval ${tc_root} debug_threshold]']
    txt += ['    if {${debug_level} >= ${debug_threshold}} {']
    txt += ['      set now [clock seconds]']
    txt += ['      set ts [clock format ${now} -format "%Y%m%d"]']
    txt += ['      set log_file_name "../log/%s_[basename ${tc_root}]_${ts}.log"' % MyDriver['name']]
    txt += ['      set fd [open "${log_file_name}" "a"]']
    txt += ['      set ts [clock format ${now} -format "%T"]']
    txt += ['      puts ${fd} "${ts} ${debug_string}"']
    txt += ['      close ${fd}']
    txt += ['    }']
    txt += ['  } catch_message ]']
    txt += ['}']
    txt += ['']
    txt += ['proc %s::sics_log {debug_level debug_string} {' % MyDriver['namespace']]
    txt += ['  set catch_status [ catch {']
    txt += ['    set debug_threshold ${%s::debug_threshold}' % MyDriver['namespace']]
    txt += ['    if {${debug_level} >= ${debug_threshold}} {']
    txt += ['      sicslog "%s::${debug_string}"' % MyDriver['namespace']]
    txt += ['    }']
    txt += ['  } catch_message ]']
    txt += ['}']
    emit(txt)

def put_write_function(MyDriver, func):
    txt = ['']
    txt += ['# function to write a parameter value on a device']
    txt += ['proc %s::%s {tc_root nextState cmd_str} {' % (MyDriver['namespace'], func)]
    txt += ['  set catch_status [ catch {']
    txt += ['    debug_log ${tc_root} 1 "%s tc_root=${tc_root} sct=[sct] cmd=${cmd_str}"' % func]
    txt += ['    if { [hpropexists [sct] geterror] } {']
    txt += ['      hdelprop [sct] geterror']
    txt += ['    }']
    txt += ['    set par [sct target]']
    txt += ['    set cmd "${cmd_str}${par}"']
    if func in MyDriver['Funcs'] and len(MyDriver['Funcs'][func]['text']) > 0:
        txt += ['# %s hook code starts' % func]
        txt += MyDriver['Funcs'][func]['text']
        txt += ['# %s hook code ends' % func]
        txt += ['    if { [hpropexists [sct] geterror] } {']
        txt += ['      debug_log ${tc_root} 9 "[sct] error: [sct geterror]"']
        txt += ['      error "[sct geterror]"']
        txt += ['    }']
    else:
        txt += ['# %s hook code goes here' % func]
    txt += ['    if { [hpropexists [sct] driving] } {']
    txt += ['      if { [hpropexists [sct] writestatus] && [sct writestatus] == "start" } {']
    txt += ['        sct driving 1']
    txt += ['      }']
    txt += ['    }']
    txt += ['    debug_log ${tc_root} 1 "%s sct send ${cmd}"' % func]
    txt += ['    if {![string equal -nocase -length 10 ${cmd} "@@NOSEND@@"]} {']
    txt += ['      sct send "${cmd}"']
    txt += ['    }']
    txt += ['    return ${nextState}']
    txt += ['  } catch_message ]']
    txt += ['  handle_exception ${catch_status} ${catch_message}']
    txt += ['}']
    emit(txt)

def put_check_function(MyDriver, func):
    txt = ['']
    txt += ['# function to check the write parameter on a device']
    txt += ['proc %s::%s {tc_root} {' % (MyDriver['namespace'], func)]
    txt += ['  set catch_status [ catch {']
    txt += ['    debug_log ${tc_root} 1 "%s tc_root=${tc_root} sct=[sct] resp=[sct result]"' % func]
    if func in MyDriver['Funcs'] and len(MyDriver['Funcs'][func]['text']) > 0:
        txt += ['# %s hook code starts' % func]
        txt += MyDriver['Funcs'][func]['text']
        txt += ['# %s hook code ends' % func]
    else:
        txt += ['# %s hook code goes here' % func]
    txt += ['    return "idle"']
    txt += ['  } catch_message ]']
    txt += ['  handle_exception ${catch_status} ${catch_message}']
    txt += ['}']
    emit(txt)

def put_fetch_function(MyDriver, func):
    txt = ['']
    txt += ['# function to request the read of a parameter on a device']
    txt += ['proc %s::%s {tc_root nextState cmd_str} {' % (MyDriver['namespace'], func)]
    txt += ['  set catch_status [ catch {']
    txt += ['    debug_log ${tc_root} 1 "%s tc_root=${tc_root} sct=[sct] cmd=${cmd_str}"' % func]
    txt += ['    if { [hpropexists [sct] geterror] } {']
    txt += ['      hdelprop [sct] geterror']
    txt += ['    }']
    txt += ['    set cmd "${cmd_str}"']
    if func in MyDriver['Funcs'] and len(MyDriver['Funcs'][func]['text']) > 0:
        txt += ['# %s hook code starts' % func]
        txt += MyDriver['Funcs'][func]['text']
        txt += ['# %s hook code ends' % func]
        txt += ['    if { [hpropexists [sct] geterror] } {']
        txt += ['      debug_log ${tc_root} 9 "[sct] error: [sct geterror]"']
        txt += ['      error "[sct geterror]"']
        txt += ['    }']
    else:
        txt += ['# %s hook code goes here' % func]
    txt += ['    debug_log ${tc_root} 1 "%s sct send ${cmd}"' % func]
    txt += ['    if {![string equal -nocase -length 10 ${cmd} "@@NOSEND@@"]} {']
    txt += ['      sct send "${cmd}"']
    txt += ['    }']
    txt += ['    return ${nextState}']
    txt += ['  } catch_message ]']
    txt += ['  handle_exception ${catch_status} ${catch_message}']
    txt += ['}']
    emit(txt)

def put_read_function(MyDriver, func):
    txt = ['']
    txt += ['# function to parse the read of a parameter on a device']
    txt += ['proc %s::%s {tc_root} {' % (MyDriver['namespace'], func)]
    txt += ['  set catch_status [ catch {']
    txt += ['    debug_log ${tc_root} 1 "%s tc_root=${tc_root} sct=[sct] result=[sct result]"' % func]
    txt += ['    if { [hpropexists [sct] geterror] } {']
    txt += ['      hdelprop [sct] geterror']
    txt += ['    }']
    txt += ['    set data [sct result]']
    txt += ['    set nextState "idle"']
    txt += ['    if {[string equal -nocase -length 7 ${data} "ASCERR:"]} {']
    txt += ['      # the protocol driver has reported an error']
    txt += ['      sct geterror "${data}"']
    txt += ['      error "[sct geterror]"']
    txt += ['    }']
    if func in MyDriver['Funcs'] and len(MyDriver['Funcs'][func]['text']) > 0:
        txt += ['# %s hook code starts' % func]
        txt += MyDriver['Funcs'][func]['text']
        txt += ['# %s hook code ends' % func]
        txt += ['    if { [hpropexists [sct] geterror] } {']
        txt += ['      debug_log ${tc_root} 9 "[sct] error: [sct geterror]"']
        txt += ['      error "[sct geterror]"']
        txt += ['    }']
    else:
        txt += ['# %s hook code goes here' % func]
    txt += ['    if { ${data} != [sct oldval] } {']
    txt += ['      debug_log ${tc_root} 1 "[sct] changed to new:${data}, from old:[sct oldval]"']
    txt += ['      sct oldval ${data}']
    txt += ['      sct update ${data}']
    txt += ['      sct utime readtime']
    txt += ['    }']
    txt += ['    return ${nextState}']
    txt += ['  } catch_message ]']
    txt += ['  handle_exception ${catch_status} ${catch_message}']
    txt += ['}']
    emit(txt)

def put_checkrange_function(MyDriver, func):
    txt = ['']
    txt += ['# check function for hset change']
    txt += ['proc %s::%s {tc_root} {' % (MyDriver['namespace'], func)]
    txt += ['  set catch_status [ catch {']
    txt += ['    debug_log ${tc_root} 1 "%s tc_root=${tc_root} sct=[sct] target=[sct target]"' % func]
    txt += ['    set setpoint [sct target]']
    txt += ['    if { [hpropexists [sct] lowerlimit] } {']
    txt += ['      set lolimit [sct lowerlimit]']
    txt += ['    } else {']
    txt += ['      # lowerlimit not set, use target']
    txt += ['      set lolimit [sct target]']
    txt += ['    }']
    txt += ['    if { [hpropexists [sct] upperlimit] } {']
    txt += ['      set hilimit [sct upperlimit]']
    txt += ['    } else {']
    txt += ['      # upperlimit not set, use target']
    txt += ['      set hilimit [sct target]']
    txt += ['    }']
    if func in MyDriver['Funcs'] and len(MyDriver['Funcs'][func]['text']) > 0:
        txt += ['# %s hook code starts' % func]
        txt += MyDriver['Funcs'][func]['text']
        txt += ['# %s hook code ends' % func]
    else:
        txt += ['# %s hook code goes here' % func]
    txt += ['    if { ${setpoint} < ${lolimit} || ${setpoint} > ${hilimit} } {']
    txt += ['      error "setpoint ${setpoint} violates limits (${lolimit}..${hilimit}) on [sct]"']
    txt += ['    }']
    txt += ['    return OK']
    txt += ['  } catch_message ]']
    txt += ['  handle_exception ${catch_status} ${catch_message}']
    txt += ['}']
    emit(txt)

def put_checklimits_function(MyDriver, func):
    txt = ['']
    txt += ['# checklimits function for driveable interface']
    txt += ['proc %s::%s {tc_root} {' % (MyDriver['namespace'], func)]
    txt += ['  set catch_status [ catch {']
    txt += ['    debug_log ${tc_root} 1 "%s tc_root=${tc_root} sct=[sct] target=[sct target]"' % func]
    txt += ['    set setpoint [sct target]']
    txt += ['    if { [hpropexists [sct] lowerlimit] } {']
    txt += ['      set lolimit [sct lowerlimit]']
    txt += ['    } else {']
    txt += ['      # lowerlimit not set, use target']
    txt += ['      set lolimit [sct target]']
    txt += ['    }']
    txt += ['    if { [hpropexists [sct] upperlimit] } {']
    txt += ['      set hilimit [sct upperlimit]']
    txt += ['    } else {']
    txt += ['      # upperlimit not set, use target']
    txt += ['      set hilimit [sct target]']
    txt += ['    }']
    if func in MyDriver['Funcs'] and len(MyDriver['Funcs'][func]['text']) > 0:
        txt += ['# %s hook code starts' % func]
        txt += MyDriver['Funcs'][func]['text']
        txt += ['# %s hook code ends' % func]
    else:
        txt += ['# %s hook code goes here' % func]
    txt += ['    if { ${setpoint} < ${lolimit} || ${setpoint} > ${hilimit} } {']
    txt += ['      sct driving 0']
    txt += ['      error "setpoint ${setpoint} violates limits (${lolimit}..${hilimit}) on [sct]"']
    txt += ['    }']
    txt += ['    return OK']
    txt += ['  } catch_message ]']
    txt += ['  handle_exception ${catch_status} ${catch_message}']
    txt += ['}']
    emit(txt)

def put_checkstatus_function(MyDriver, func):
    txt = ['']
    txt += ['# checkstatus function for driveable interface']
    txt += ['proc %s::%s {tc_root} {' % (MyDriver['namespace'], func)]
    txt += ['  set catch_status [ catch {']
    if func in MyDriver['Funcs'] and len(MyDriver['Funcs'][func]['text']) > 0:
        txt += ['# %s hook code starts' % func]
        txt += MyDriver['Funcs'][func]['text']
        txt += ['# %s hook code ends' % func]
    else:
        txt += ['# %s hook code goes here' % func]
    txt += ['    if {[sct driving]} {']
    txt += ['      set sp "[sct target]"']
    txt += ['      if {[hpropexists [sct] simulated] && [sct simulated] == "true"} {']
    txt += ['        set pv "${sp}"']
    txt += ['        hupdateif ${tc_root}/[sct driveable] ${sp}']
    txt += ['      } else {']
    txt += ['        set pv "[hval ${tc_root}/[sct driveable]]"']
    txt += ['      }']
    txt += ['      if { abs(${pv} - ${sp}) <= [sct tolerance] } {']
    txt += ['        if { [hpropexists [sct] settle_time] } {']
    txt += ['          if { [hpropexists [sct] settle_time_start] } {']
    txt += ['            if { [sct utime] - [sct settle_time_start] >= [sct settle_time]} {']
    txt += ['              sct driving 0']
    txt += ['              return "idle"']
    txt += ['            }']
    txt += ['            return "busy"']
    txt += ['          } else {']
    txt += ['            sct utime settle_time_start']
    txt += ['            return "busy"']
    txt += ['          }']
    txt += ['        }']
    txt += ['        sct driving 0']
    txt += ['        return "idle"']
    txt += ['      }']
    txt += ['      if { [hpropexists [sct] settle_time_start] } {']
    txt += ['        hdelprop [sct] settle_time_start']
    txt += ['      }']
    txt += ['      return "busy"']
    txt += ['    } else {']
    txt += ['      return "idle"']
    txt += ['    }']
    txt += ['  } catch_message ]']
    txt += ['  handle_exception ${catch_status} ${catch_message}']
    txt += ['}']
    emit(txt)

def put_halt_function(MyDriver, func):
    txt = ['']
    txt += ['# halt function for driveable interface']
    txt += ['proc %s::%s {tc_root} {' % (MyDriver['namespace'], func)]
    txt += ['  set catch_status [ catch {']
    txt += ['    debug_log ${tc_root} 1 "%s tc_root=${tc_root} sct=[sct] driving=[sct driving]"' % func]
    txt += ['    ### TODO hset [sct] [hval [sct]]']
    if func in MyDriver['Funcs'] and len(MyDriver['Funcs'][func]['text']) > 0:
        txt += ['# %s hook code starts' % func]
        txt += MyDriver['Funcs'][func]['text']
        txt += ['# %s hook code ends' % func]
    else:
        txt += ['# %s hook code goes here' % func]
    txt += ['    sct driving 0']
    txt += ['    return "idle"']
    txt += ['  } catch_message ]']
    txt += ['  handle_exception ${catch_status} ${catch_message}']
    txt += ['}']
    emit(txt)

def put_pid_function(MyDriver, func):
    txt = ['']
    txt += ['# pid function for PID control']
    txt += ['proc %s::%s {tc_root sp pv} {' % (MyDriver['namespace'], func)]
    txt += ['  set catch_status [ catch {']
    txt += ['    debug_log ${tc_root} 1 "%s tc_root=${tc_root} sct=[sct] pv=${pv} sp=${sp}"' % func]
    txt += ['    sct pid_error [expr {${sp} - ${pv}}]']
    txt += ['    set p_value [expr {[sct pid_pvalue] * [sct pid_error]}]']
    txt += ['    set d_value [expr {[sct pid_dvalue] * (${pv} - [sct oldval])}]']
    txt += ['    sct pid_deriv [sct pid_error]']
    txt += ['    sct pid_integ [expr {[sct pid_integ] + [sct pid_error] * [sct pid_ivalue]}]']
    txt += ['    if { [sct pid_integ] > [sct pid_imax] } {']
    txt += ['      sct pid_integ [sct pid_imax]']
    txt += ['    }']
    txt += ['    if { [sct pid_integ] < -[sct pid_imax] } {']
    txt += ['      sct pid_integ -[sct pid_imax]']
    txt += ['    }']
    txt += ['    set i_value [sct pid_integ]']
    txt += ['    set pid [expr {${p_value} + ${i_value} + ${d_value}}]']
    if func in MyDriver['Funcs'] and len(MyDriver['Funcs'][func]['text']) > 0:
        txt += ['# %s hook code starts' % func]
        txt += MyDriver['Funcs'][func]['text']
        txt += ['# %s hook code ends' % func]
    else:
        txt += ['# %s hook code goes here' % func]
    txt += ['    sct pid_output ${pid}']
    txt += ['  } catch_message ]']
    txt += ['  handle_exception ${catch_status} ${catch_message}']
    txt += ['  return ${pid}']
    txt += ['}']
    emit(txt)

def put_var(MyDriver, MyGroup, MyVar):
    readable_or_writeable = False
    txt = []
    postfix = []
    nodename = make_path(MyVar, '/')

    # Debugging
    #txt += ['# path = ' + MyVar['path']]
    #txt += ['# name = ' + nodename]

    # Check driveable attributes are present if required
    if 'driveable' in MyVar and MyVar['driveable']:
        for attr in ('lowerlimit', 'upperlimit', 'tolerance'):
            if attr not in MyVar:
                msg = 'Driveable: %s does not have required attribute: %s' % (nodename, attr)
                print 'Warning:', msg
                txt += ['    # Warning: ' + msg]
    # Check PID attributes are present if required
    if 'pid_function' in MyVar:
        for attr in ('pid_pvalue',
                        'pid_ivalue',
                        'pid_dvalue',
                        'pid_imax',
                        'pid_error',
                        'pid_deriv',
                        'pid_integ',
                        ):
            if attr not in MyVar['Property']:
                msg = 'PID: %s does not have required attribute: %s' % (nodename, attr)
                print 'Warning:', msg
                txt += ['    # Warning: ' + msg]

    txt += ['    hfactory ${scobj_hpath}/%s plain %s %s' % (nodename, MyVar['priv'], MyVar['type'])]
    if MyVar['readable'] > 0:
        readable_or_writeable = True
        fetch_func = MyVar['fetch_function']
        if fetch_func == 'none':
            fetch_func = 'getValue'
        read_func = MyVar['read_function']
        if 'read_command' in MyVar:
            read_command =  MyVar['read_command']
        else:
            read_command = ''
        txt += ['    hsetprop ${scobj_hpath}/%s read ${ns}::%s ${scobj_hpath} %s {%s}' % (nodename, fetch_func, read_func, read_command)]
        txt += ['    hsetprop ${scobj_hpath}/%s %s ${ns}::%s ${scobj_hpath}' % (nodename, read_func, read_func)]
    if MyVar['writeable'] > 0 or MyVar['driveable']:
        readable_or_writeable = True
        check_func = MyVar['check_function']
        checkrange_func = MyVar['checkrange_function']
        write_func = MyVar['write_function']
        if 'write_command' in MyVar:
            write_command =  MyVar['write_command']
        else:
            write_command = ''
        txt += ['    hsetprop ${scobj_hpath}/%s write ${ns}::%s ${scobj_hpath} %s {%s}' % (nodename, write_func, check_func, write_command)]
        txt += ['    hsetprop ${scobj_hpath}/%s %s ${ns}::%s ${scobj_hpath}' % (nodename, check_func, check_func)]
        txt += ['    hsetprop ${scobj_hpath}/%s check ${ns}::%s ${scobj_hpath}' % (nodename, checkrange_func)]
    if MyVar['driveable']:
        halt_func = MyVar['halt_function']
        checklimits_func = MyVar['checklimits_function']
        checkstatus_func = MyVar['checkstatus_function']
        txt += ['    hsetprop ${scobj_hpath}/%s driving 0' % nodename]
        txt += ['    hsetprop ${scobj_hpath}/%s checklimits ${ns}::%s ${scobj_hpath}' % (nodename, checklimits_func)]
        txt += ['    hsetprop ${scobj_hpath}/%s checkstatus ${ns}::%s ${scobj_hpath}' % (nodename, checkstatus_func)]
        txt += ['    hsetprop ${scobj_hpath}/%s halt ${ns}::%s ${scobj_hpath}' % (nodename, halt_func)]
        txt += ['    hsetprop ${scobj_hpath}/%s driveable %s' % (nodename, MyVar['driveable'])]
    if 'control' in MyVar:
        txt += ['    hsetprop ${scobj_hpath}/%s control %s' % (nodename, MyVar['control'])]
    if 'data' in MyVar:
        txt += ['    hsetprop ${scobj_hpath}/%s data %s' % (nodename, MyVar['data'])]
    if 'mutable' in MyVar:
        txt += ['    hsetprop ${scobj_hpath}/%s mutable %s' % (nodename, MyVar['mutable'])]
    if 'nxsave' in MyVar:
        txt += ['    hsetprop ${scobj_hpath}/%s nxsave %s' % (nodename, MyVar['nxsave'])]
    if 'lowerlimit' in MyVar:
        txt += ['    hsetprop ${scobj_hpath}/%s lowerlimit %s' % (nodename, MyVar['lowerlimit'])]
    if 'upperlimit' in MyVar:
        txt += ['    hsetprop ${scobj_hpath}/%s upperlimit %s' % (nodename, MyVar['upperlimit'])]
    if 'tolerance' in MyVar:
        txt += ['    hsetprop ${scobj_hpath}/%s tolerance %s' % (nodename, MyVar['tolerance'])]
    if 'units' in MyVar:
        txt += ['    hsetprop ${scobj_hpath}/%s units %s' % (nodename, MyVar['units'])]
    if 'allowed' in MyVar:
        txt += ['    hsetprop ${scobj_hpath}/%s values %s' % (nodename, MyVar['allowed'])]
    if 'permlink' in MyVar:
        device_type, node_type = MyVar['permlink'].split('.')
        if device_type.startswith("#"):
            if 'make_args_lst' in MyDriver and 'permlink' in MyDriver['make_args_lst']:
                idx = int(device_type[1:])
                device_type = '[string index ${permlink} %d]' % idx
            else:
                message = 'Error: permlink required in make_ags'
                PrintPostError(message)
        if 'make_args_lst' in MyDriver and 'id' in MyDriver['make_args_lst']:
            permlink = device_type + '[format "%02d" ${id}]' + node_type
        else:
            permlink = device_type + '${permlink_device_number}' + node_type
        txt += ['    hsetprop ${scobj_hpath}/%s permlink data_set "%s"' % (nodename, permlink)]
        txt += ['    hsetprop ${scobj_hpath}/%s @description "%s"' % (nodename, permlink)]
    if 'value' in MyVar:
        txt += ['    hsetprop ${scobj_hpath}/%s oldval %s' % (nodename, MyVar['value'])]
        txt += ['    hset     ${scobj_hpath}/%s        %s' % (nodename, MyVar['value'])]
    else:
        if MyVar['type'] == 'none':
            pass
        elif MyVar['type'] == 'int':
            txt += ['    hsetprop ${scobj_hpath}/%s oldval 0' % nodename]
        elif MyVar['type'] == 'float':
            txt += ['    hsetprop ${scobj_hpath}/%s oldval 0.0' % nodename]
        else:
            txt += ['    hsetprop ${scobj_hpath}/%s oldval UNKNOWN' % nodename]
    for key in sorted(MyVar['Property']):
        txt += ['    hsetprop ${scobj_hpath}/%s %s "%s"' % (nodename, key, MyVar['Property'][key])]
    # Generate <dev>_<group...>_<name> at runtime for nxalias
    if 'nxalias' not in MyVar['Property']:
        nxalias = '${name}_' + make_path(MyVar)
        txt += ['    hsetprop ${scobj_hpath}/%s nxalias "%s"' % (nodename, nxalias)]

    if readable_or_writeable:
        txt += ['']
        txt += ['    if {[string equal -nocase "${simulation_flag}" "false"]} {']
        if MyVar['readable'] > 0:
            poll_period = MyVar['readable']
            if poll_period < 1:
                poll_period = 1
            if poll_period > 3600:
                poll_period = 3600
            txt += ['      ${sct_controller} poll ${scobj_hpath}/%s %s' % (nodename, poll_period)]
        if MyVar['writeable'] > 0 or MyVar['driveable']:
            txt += ['      ${sct_controller} write ${scobj_hpath}/%s' % nodename]
        if MyVar['driveable']:
            # Generate <dev>_<group...>_<name> at runtime for driveable
            driveable = '${name}_' + make_path(MyVar)
            postfix += ['    ansto_makesctdrive %s ${scobj_hpath}/%s ${scobj_hpath}/%s ${sct_controller}' % (driveable, nodename, MyVar['driveable'])]
        txt += ['      hsetprop ${scobj_hpath}/%s simulated false' % nodename]
        txt += ['    } else {']
        txt += ['      %s::sics_log 9 "simulation_flag=${simulation_flag} => No poll/write for %s"' % (MyDriver['namespace'], MyDriver['name'])]
        txt += ['      hsetprop ${scobj_hpath}/%s simulated true' % nodename]
        txt += ['    }']

    # Process nested groups
    for grp in sorted(MyVar['Group']):
        txt += ['']
        infix = put_group(MyDriver, MyVar['Group'][grp])
        txt += infix

    # Process nested variables
    for var in sorted(MyVar['Variable']):
        txt += ['']
        MySubVar = MyVar['Variable'][var]
        infix, dfr = put_var(MyDriver, MyGroup, MySubVar)
        txt += infix
        postfix += dfr

    if 'conditional' in MyVar:
        for idx, line in enumerate(txt):
            if len(line) > 0:
                txt[idx] = '  ' + line
        txt.insert(0, '    if {%s} {' % MyVar['conditional'])
        txt.append('    }')
        if len(postfix) > 0:
            for idx, line in enumerate(postfix):
                if len(line) > 0:
                    postfix[idx] = '  ' + line
            postfix.insert(0, '    if {%s} {' % MyVar['conditional'])
            postfix.append('    }')

    return (txt, postfix)

def put_group(MyDriver, MyGroup):
    txt = []
    postfix = []
    if MyGroup['name']:
        txt += ['']
        txt += ['    hfactory ${scobj_hpath}/%s plain spy none' % MyGroup['path']]
    else:
        pass

    for var in sorted(MyGroup['Vars']):
        txt += ['']
        MyVar = MyGroup['Vars'][var]
        infix, dfr = put_var(MyDriver, MyGroup, MyVar)
        txt += infix
        postfix += dfr

    if MyGroup['name']:
        if 'GroupProperty' in MyGroup:
            for key in sorted(MyGroup['GroupProperty']):
                txt += ['    hsetprop ${scobj_hpath}/%s %s "%s"' % (MyGroup['path'], key, MyGroup['GroupProperty'][key])]
    elif len(MyGroup['path']) > 0:
        pass
    else:
        if 'GroupProperty' in MyGroup:
            txt += ['']
            for key in sorted(MyGroup['GroupProperty']):
                txt += ['    hsetprop ${scobj_hpath} %s "%s"' % (key, MyGroup['GroupProperty'][key])]

    for grp in sorted(MyGroup['Groups']):
        txt += put_group(MyDriver, MyGroup['Groups'][grp])

    txt += postfix

    if 'conditional' in MyGroup:
        for idx, line in enumerate(txt):
            if len(line) > 0:
                txt[idx] = '  ' + line
        if len(txt[0]) == 0:
            txt.pop(0)
        txt.insert(0, '    if {%s} {' % MyGroup['conditional'])
        txt.insert(0, '')
        txt.append('    }')

    return txt

def put_mkDriver(MyDriver):
    txt = ['']
    if 'make_args' in MyDriver:
        line = 'proc %s::mkDriver { sct_controller name device_class simulation_flag ip_address tcp_port %s } {' % (MyDriver['namespace'], MyDriver['make_args'])
    else:
        line = 'proc %s::mkDriver { sct_controller name device_class simulation_flag ip_address tcp_port } {' % (MyDriver['namespace'])
    txt += [line]
    if 'make_args_lst' in MyDriver:
        make_args = ' '.join(["${%s}"%arg for arg in MyDriver['make_args_lst']])
        txt += ['  %s::sics_log 9 "%s::mkDriver ${sct_controller} ${name} ${device_class} ${simulation_flag} ${ip_address} ${tcp_port} %s"' % (MyDriver['namespace'], MyDriver['namespace'], make_args)]
    else:
        txt += ['  %s::sics_log 9 "%s::mkDriver ${sct_controller} ${name} ${device_class} ${simulation_flag} ${ip_address} ${tcp_port}"' % (MyDriver['namespace'], MyDriver['namespace'])]
    txt += ['  set ns "[namespace current]"']
    txt += ['  set catch_status [ catch {']
    txt += ['']
    func = 'mkWrapper'
    if func in MyDriver['Funcs']:
        txt += ['# %s hook code starts' % func]
        txt += MyDriver['Funcs'][func]['text']
        txt += ['# %s hook code ends' % func]
    else:
        if len(MyDriver['Permlink']) > 0:
            if 'make_args_lst' in MyDriver and 'id' in MyDriver['make_args_lst']:
                pass
            else:
                txt += ['    set permlink_device_number [format "%02d" [incr ::scobj::permlink_device_counter]]']
                txt += ['']
        if 'sobj_priv_type' in MyDriver:
            priv_type = MyDriver['sobj_priv_type'].split()
            ms_line = '    MakeSICSObj ${name} SCT_OBJECT %s %s' % (priv_type[0], priv_type[1])
        else:
            ms_line = '    MakeSICSObj ${name} SCT_OBJECT'
        txt += [ms_line]
        txt += ['']
        txt += ['    sicslist setatt ${name} driver %s' % MyDriver['name']]
        txt += ['    sicslist setatt ${name} klass ${device_class}']
        txt += ['    sicslist setatt ${name} long_name ${name}']
        if 'DriverProperty' in MyDriver:
            for key in MyDriver['DriverProperty']:
                txt += ['    sicslist setatt ${name} %s "%s"' % (key,  MyDriver['DriverProperty'][key])]
        txt += ['']
        txt += ['    set scobj_hpath /sics/${name}']

        for group in sorted(MyDriver['Groups']):
            txt += put_group(MyDriver, MyDriver['Groups'][group])

        txt += ['    hsetprop ${scobj_hpath} driver %s' % MyDriver['name']]
        txt += ['    hsetprop ${scobj_hpath} klass ${device_class}']
        txt += ['    hsetprop ${scobj_hpath} data true']
        txt += ['    hsetprop ${scobj_hpath} debug_threshold %s' % str(MyDriver['debug_threshold'])]
        if len(MyDriver['Deferred']) > 0:
            txt += ['    if {[string equal -nocase "${simulation_flag}" "false"]} {']
            for line in MyDriver['Deferred']:
                txt += ['      ' + line]
            txt += ['    }']
        func = 'mkDriver'
        if func in MyDriver['Funcs']:
            txt += ['# %s hook code starts' % func]
            txt += MyDriver['Funcs'][func]['text']
            txt += ['# %s hook code ends' % func]
        else:
            txt += ['# %s hook code goes here' % func]
    txt += ['  } catch_message ]']
    txt += ['  handle_exception ${catch_status} ${catch_message}']
    txt += ['}']
    emit(txt)

def put_add_driver(MyDriver):
    txt = ['']
    if 'add_args' in MyDriver:
        line = 'proc %s::add_driver {name device_class simulation_flag ip_address tcp_port %s} {' % (MyDriver['namespace'], MyDriver['add_args'])
    else:
        line = 'proc %s::add_driver {name device_class simulation_flag ip_address tcp_port} {' % (MyDriver['namespace'])
    txt += [line]
    txt += ['  set catch_status [ catch {']
    if 'make_args_lst' in MyDriver:
        make_args = ' '.join(["${%s}"%arg for arg in MyDriver['make_args_lst']])
        txt += ['    %s::sics_log 9 "%s::add_driver ${name} ${device_class} ${simulation_flag} ${ip_address} ${tcp_port} %s"' % (MyDriver['namespace'], MyDriver['namespace'], make_args)]
    else:
        txt += ['    %s::sics_log 9 "%s::add_driver ${name} ${device_class} ${simulation_flag} ${ip_address} ${tcp_port}"' % (MyDriver['namespace'], MyDriver['namespace'])]
    if ('WrapperProperty' in MyDriver) and ('nosctcontroller' in MyDriver['WrapperProperty']):
        txt += ['    %s::sics_log 9 "No sctcontroller for %s"' % (MyDriver['namespace'], MyDriver['name'])]
    else:
        txt += ['    if {[string equal -nocase "${simulation_flag}" "false"]} {']
        txt += ['      if {[string equal -nocase "aqadapter" "${ip_address}"]} {']
        txt += ['        %s::sics_log 9 "makesctcontroller sct_${name} aqadapter ${tcp_port}"' % MyDriver['namespace']]
        txt += ['        makesctcontroller sct_${name} aqadapter ${tcp_port}']
        txt += ['      } else {']
        if 'protocol_args' in MyDriver:
            protocol_args = []
            for arg in MyDriver['protocol_args_lst']:
                if 'add_args_lst' in MyDriver and arg in MyDriver['add_args_lst']:
                    protocol_args.append('${%s}' % arg)
                elif arg in MyDriver['protocol_args_map'] and MyDriver['protocol_args_map'][arg] is not None:
                    protocol_args.append(MyDriver['protocol_args_map'][arg])
                else:
                    PrintPostError('Protocol arg %s is not in add_args and has no default' % arg)
            tmp = ' '.join(protocol_args).replace('\\', '\\\\').replace('"', '\\"')
            txt += ['        %s::sics_log 9 "makesctcontroller sct_${name} %s ${ip_address}:${tcp_port} %s"' % (MyDriver['namespace'], MyDriver['protocol'], tmp)]
            tmp = ' '.join(protocol_args)
            txt += ['        makesctcontroller sct_${name} %s ${ip_address}:${tcp_port} %s' % (MyDriver['protocol'], tmp)]
        else:
            txt += ['        %s::sics_log 9 "makesctcontroller sct_${name} %s ${ip_address}:${tcp_port}"' % (MyDriver['namespace'], MyDriver['protocol'])]
            txt += ['        makesctcontroller sct_${name} %s ${ip_address}:${tcp_port}' % MyDriver['protocol']]
        txt += ['      }']
        txt += ['    } else {']
        txt += ['      %s::sics_log 9 "simulation_flag=${simulation_flag} => Null sctcontroller for %s"' % (MyDriver['namespace'], MyDriver['name'])]
        txt += ['      %s::sics_log 9 "makesctcontroller sct_${name} aqadapter NULL"' % MyDriver['namespace']]
        txt += ['      makesctcontroller sct_${name} aqadapter NULL']
        txt += ['    }']
    if 'make_args_lst' in MyDriver:
        make_args = ' '.join(["${%s}"%arg for arg in MyDriver['make_args_lst']])
        txt += ['    %s::sics_log 1 "%s::mkDriver sct_${name} ${name} ${device_class} ${simulation_flag} ${ip_address} ${tcp_port} %s"' % (MyDriver['namespace'], MyDriver['namespace'], make_args)]
        txt += ['    %s::mkDriver sct_${name} ${name} ${device_class} ${simulation_flag} ${ip_address} ${tcp_port} %s' % (MyDriver['namespace'], make_args)]
    else:
        txt += ['    %s::sics_log 1 "%s::mkDriver sct_${name} ${name} ${device_class} ${simulation_flag} ${ip_address} ${tcp_port}"' % (MyDriver['namespace'], MyDriver['namespace'])]
        txt += ['    %s::mkDriver sct_${name} ${name} ${device_class} ${simulation_flag} ${ip_address} ${tcp_port}' % (MyDriver['namespace'])]
# TODO
#txt += ['    %s::sics_log "makesctemon ${name} /sics/${name}/emon/monmode /sics/${name}/emon/isintol /sics/${name}/emon/errhandler"' % (MyDriver['namespace'])]
#  txt += ['    makesctemon ${name} /sics/${name}/emon/monmode /sics/${name}/emon/isintol /sics/${name}/emon/errhandler']
    txt += ['  } catch_message ]']
    txt += ['  handle_exception ${catch_status} ${catch_message}']
    txt += ['}']
    emit(txt)

def put_postamble(MyDriver):
    txt = ['']
    txt += ['namespace eval %s {' % MyDriver['namespace']]
    txt += ['  namespace export debug_threshold']
    txt += ['  namespace export debug_log']
    txt += ['  namespace export sics_log']
    txt += ['  namespace export mkDriver']
    txt += ['  namespace export add_driver']
    func = 'postamble'
    if func in MyDriver['Funcs']:
        txt += ['# %s hook code starts' % func]
        txt += MyDriver['Funcs'][func]['text']
        txt += ['# %s hook code ends' % func]
    txt += ['}']
    txt += ['']
    if 'add_args' in MyDriver:
        line = 'proc add_%s {name ip_address tcp_port %s} {' % (MyDriver['name'], MyDriver['add_args'])
    else:
        line = 'proc add_%s {name ip_address tcp_port} {' % MyDriver['name']
    txt += [line]
    txt += ['  set simulation_flag "[string tolower [SplitReply [%s]]]"' % MyDriver['simulation_group']]
    line = '  %s::add_driver ${name} "%s"' % (MyDriver['namespace'], MyDriver['class'])
    for arg in ['simulation_flag', 'ip_address', 'tcp_port']:
        line += ' ${%s}' % arg
    if 'add_args_lst' in MyDriver:
        for arg in MyDriver['add_args_lst']:
            line += ' ${%s}' % arg
    txt += [line]
    txt += ['}']
    txt += ['']
    txt += ['clientput "file evaluation of %s"' % MyDriver['filename']]
    txt += ['%s::sics_log 9 "file evaluation of %s"' % (MyDriver['namespace'], MyDriver['filename'])]
    emit(txt)

def put_read_config(MyDriver):
    txt = ['']
    txt += ['proc %s::read_config {} {' % MyDriver['namespace']]
    txt += ['  set catch_status [ catch {']
    txt += ['    set ns "%s"' % MyDriver['namespace']]
    txt += ['    dict for {k u} $::config_dict {']
    txt += ['      if { [dict exists $u "implementation"] } {']
    txt += ['        set simulation_flag "[string tolower [SplitReply [%s]]]"' % MyDriver['simulation_group']]
    txt += ['        set device_class "%s"' % MyDriver['class']]
    txt += ['        if { !([dict exists $u "name"] && [dict exists $u "enabled"]) } {']
    txt += ['          continue']
    txt += ['        }']
    txt += ['        set enabled [string tolower [dict get $u "enabled"]]']
    txt += ['        if { ! ([string equal -nocase $enabled "true" ] || [string equal -nocase $enabled "always"]) } {']
    txt += ['          continue']
    txt += ['        }']
    txt += ['        if { [dict exists $u "simulation_group"] } {']
    txt += ['          set simulation_flag [SplitReply [[string tolower [dict get $u "simulation_group"]]]]']
    txt += ['        }']
    txt += ['        if { [dict exists $u "device_class"] } {']
    txt += ['          set device_class "[dict get $u "device_class"]"']
    txt += ['        }']
    txt += ['        set name [dict get $u name]']
    txt += ['        set implementation [dict get $u "implementation"]']
    txt += ['        if { !([dict exists $::config_dict $implementation]) } {']
    txt += ['          continue']
    txt += ['        }']
    txt += ['        set v [dict get $::config_dict $implementation]']
    txt += ['        if { !([dict exists $v "driver"]) } {']
    txt += ['          continue']
    txt += ['        }']
    txt += ['        if { [string equal -nocase [dict get $v "driver"] "%s"] } {' % MyDriver['name']]
    if ('WrapperProperty' in MyDriver) and ('nosctcontroller' in MyDriver['WrapperProperty']):
        txt += ['          %s::sics_log 9 "No sctcontroller for %s"' % (MyDriver['namespace'], MyDriver['name'])]
        txt += ['          set ip_address [dict get $v ip]']
        txt += ['          set tcp_port [dict get $v port]']
    else:
        txt += ['          if { ![string equal -nocase "${simulation_flag}" "false"] } {']
        txt += ['            set asyncqueue "null"']
        txt += ['            ${ns}::sics_log 9 "simulation_flag=${simulation_flag} => using null asyncqueue"']
        txt += ['            ${ns}::sics_log 9 "makesctcontroller sct_${name} aqadapter NULL"']
        txt += ['            makesctcontroller sct_${name} aqadapter NULL']
        txt += ['          } elseif { [dict exists $v "asyncqueue"] } {']
        txt += ['            set asyncqueue [dict get $v "asyncqueue"]']
        txt += ['            if { [string equal -nocase ${asyncqueue} "sct"] } {']
        txt += ['              set ip_address [dict get $v ip]']
        txt += ['              set tcp_port [dict get $v port]']
        if 'protocol_args_lst' in MyDriver:
            txt += ['              set arg_list [list]']
            txt += ['              set missing_list [list]']
            default_list = []
            for arg in [key for key in MyDriver['protocol_args_lst'] if MyDriver['protocol_args_map'][key] is not None]:
                default_list += [arg, MyDriver['protocol_args_map'][arg]]
            if len(default_list) > 0:
                txt += ['              array unset default_map']
                txt += ['              array set default_map [list %s]' % ' '.join(default_list)]
            txt += ['              foreach arg {' + ' '.join(MyDriver['protocol_args_lst']) + '} {']
            txt += ['                if {[dict exists $u $arg]} {']
            txt += ['                  lappend arg_list "[dict get $u $arg]"']
            txt += ['                } elseif {[dict exists $v $arg]} {']
            txt += ['                  lappend arg_list "[dict get $v $arg]"']
            if len(default_list) > 0:
                txt += ['                } elseif {[info exists default_map($arg)]} {']
                txt += ['                  lappend arg_list $default_map($arg)']
            txt += ['                } else {']
            txt += ['                  ${ns}::sics_log 9 "Missing configuration value $arg"']
            txt += ['                  lappend missing_list $arg']
            txt += ['                }']
            txt += ['              }']
            txt += ['              if { [llength $missing_list] > 0 } {']
            txt += ['                  error "$name is missing configuration values $missing_list"']
            txt += ['              }']
            protocol_args = ' {*}$arg_list'
        else:
            protocol_args = ''
        txt += ['              makesctcontroller sct_${name} %s ${ip_address}:${tcp_port}%s' % (MyDriver['protocol'], protocol_args)]
        txt += ['            } else {']
        txt += ['              makesctcontroller sct_${name} aqadapter ${asyncqueue}']
        txt += ['            }']
        txt += ['          } else {']
        txt += ['            if { [dict exists $v "asyncprotocol"] } {']
        txt += ['              set asyncprotocol [dict get $v "asyncprotocol"]']
        txt += ['            } else {']
        txt += ['              set asyncprotocol ${name}_protocol']
        txt += ['              MakeAsyncProtocol ${asyncprotocol}']
        txt += ['              if { [dict exists $v "sendterminator"] } {']
        txt += ['                ${asyncprotocol} sendterminator "[dict get $v "sendterminator"]"']
        txt += ['              } elseif { [dict exists $v "terminator"] } {']
        txt += ['                ${asyncprotocol} sendterminator "[dict get $v "terminator"]"']
        txt += ['              }']
        txt += ['              if { [dict exists $v "replyterminator"] } {']
        txt += ['                ${asyncprotocol} replyterminator "[dict get $v "replyterminator"]"']
        txt += ['              } elseif { [dict exists $v "terminator"] } {']
        txt += ['                ${asyncprotocol} replyterminator "[dict get $v "terminator"]"']
        txt += ['              }']
        txt += ['            }']
        txt += ['            set asyncqueue ${name}_queue']
        txt += ['            set ip_address [dict get $v ip]']
        txt += ['            set tcp_port [dict get $v port]']
        txt += ['            MakeAsyncQueue ${asyncqueue} ${asyncprotocol} ${ip_address} ${tcp_port}']
        txt += ['            if { [dict exists $v "timeout"] } {']
        txt += ['              ${asyncqueue} timeout "[dict get $v "timeout"]"']
        txt += ['            }']
        txt += ['            makesctcontroller sct_${name} aqadapter ${asyncqueue}']
        txt += ['          }']
    if 'make_args_lst' in MyDriver:
        txt += ['          set arg_list [list]']
        txt += ['          set missing_list [list]']
        default_list = []
        for arg in [key for key in MyDriver['make_args_lst'] if MyDriver['make_args_map'][key] is not None]:
            default_list += [arg, MyDriver['make_args_map'][arg]]
        if len(default_list) > 0:
            txt += ['          array unset default_map']
            txt += ['          array set default_map [list %s]' % ' '.join(default_list)]
        txt += ['          foreach arg {' + ' '.join(MyDriver['make_args_lst']) + '} {']
        txt += ['            if {[dict exists $u $arg]} {']
        txt += ['              lappend arg_list "[dict get $u $arg]"']
        txt += ['            } elseif {[dict exists $v $arg]} {']
        txt += ['              lappend arg_list "[dict get $v $arg]"']
        if len(default_list) > 0:
            txt += ['            } elseif {[info exists default_map($arg)]} {']
            txt += ['              lappend arg_list $default_map($arg)']
        txt += ['            } else {']
        txt += ['              ${ns}::sics_log 9 "Missing configuration value $arg"']
        txt += ['              lappend missing_list $arg']
        txt += ['            }']
        txt += ['          }']
        txt += ['          if { [llength $missing_list] > 0 } {']
        txt += ['              error "$name is missing configuration values $missing_list"']
        txt += ['          }']
        make_args = ' {*}$arg_list'
    else:
        make_args = ''
    txt += ['          ${ns}::mkDriver sct_${name} ${name} ${device_class} ${simulation_flag} ${ip_address} ${tcp_port}' + make_args]
    txt += ['        }']
    txt += ['      }']
    txt += ['    }']
    txt += ['  } catch_message ]']
    txt += ['  handle_exception ${catch_status} ${catch_message}']
    txt += ['}']
    emit(txt)

def put_check_config(MyDriver):
    txt = ['']
    txt += ['if { [info exists ::config_dict] } {']
    txt += ['  %s::read_config' % MyDriver['namespace']]
    txt += ['} else {']
    txt += ['  %s::sics_log 5 "No config dict"' % MyDriver['namespace']]
    txt += ['}']
    emit(txt)

def put_standard_code(MyDriver):
    # emit all of the functions in Funcs
    for func in sorted(MyDriver['Funcs']):
        theFunc = MyDriver['Funcs'][func]
        # Don't generate functions which are not referenced
        #if theFunc['reference_count'] == 0:
        #  continue
        if theFunc['type'] == 'read_function':
            put_read_function(MyDriver, func)
        elif theFunc['type'] == 'write_function':
            put_write_function(MyDriver, func)
        elif theFunc['type'] == 'fetch_function':
            put_fetch_function(MyDriver, func)
        elif theFunc['type'] == 'check_function':
            put_check_function(MyDriver, func)
        elif theFunc['type'] == 'checkrange_function':
            put_checkrange_function(MyDriver, func)
        elif theFunc['type'] == 'checklimits_function':
            put_checklimits_function(MyDriver, func)
        elif theFunc['type'] == 'checkstatus_function':
            put_checkstatus_function(MyDriver, func)
        elif theFunc['type'] == 'halt_function':
            put_halt_function(MyDriver, func)
        elif theFunc['type'] == 'pid_function':
            put_pid_function(MyDriver, func)

def generate_driver(MyDriver):
    global NumberOfLinesOut
    global fdo
    NumberOfLinesOut = 0
    generate_filename(MyDriver)
    fdo = open(MyDriver['fullname'], 'w')
    put_preamble(MyDriver)
    put_standard_code(MyDriver)
    put_mkDriver(MyDriver)
    put_add_driver(MyDriver)
    put_postamble(MyDriver)
    put_read_config(MyDriver)
    put_check_config(MyDriver)
    fdo.close()
    if CodeDump or Verbose:
        print "Code Fragments:", MyDriver['Funcs']
        for f in sorted(MyDriver['Funcs'].keys()):
            print "Function:", f, "Type:", MyDriver['Funcs'][f]['type'], '#Uses:', MyDriver['Funcs'][f]['reference_count']
            for l in MyDriver['Funcs'][f]['text']:
                print "  ", l
    if Verbose:
        print "Produced file %s with %d lines." % \
                ( MyDriver['filename'], NumberOfLinesOut)

def process_drivers(TheDrivers):
    if Verbose:
        print "TheDrivers:", TheDrivers
    for driver in TheDrivers:
        MyDriver = {'name':driver}
        MyDriver['namespace'] = '::scobj::%s' % driver
        MyDriver['debug_threshold'] = '5'
        MyDriver['Groups'] = {}
        MyDriver['Funcs'] = {}
        MyDriver['Permlink'] = {}
        MyDriver['Deferred'] = []
        build_driver(MyDriver, TheDrivers[driver])
        check_func_code(MyDriver)
        if Verbose:
            print "MyDriver:", MyDriver['name'], '=', MyDriver
        if DriverDump or Verbose:
            dump_driver(MyDriver)
        generate_driver(MyDriver)

def load_file(source_file, depth_list):
    global SourceFileList, SourceLineList
    # find the file and set the name
    SourceFile =  os.path.realpath(os.path.abspath(source_file))
    if not os.path.isfile(SourceFile):
        #print source_file, SourceFile, SourceFileList
        if len(SourceFileList) > 0:
            trial_name = os.path.join(os.path.dirname(SourceFileList[0]), source_file)
            #print trial_name
            if os.path.isfile(trial_name):
                SourceFile =  os.path.realpath(os.path.abspath(trial_name))
    if SourceFile in depth_list:
        PrintPostError('Error: recursive include of: %s' % SourceFile)
        for idx, name in enumerate(depth_list):
            PrintPostError('  ' * idx + name)
        raise Exception('Bad recursive include of "' + SourceFile + '"')
    SourceFileList.append(SourceFile)
    curr_file = len(SourceFileList) - 1
    fd = open(SourceFile, 'r')
    LocalData = []
    line_no = 0
    execing = False
    exec_input = []
    exec_line = 0
    for line in fd:
        line_no += 1
        line = line.rstrip('\n')
        if execing:
            match = re.match(r'\s*%end', line, flags=re.IGNORECASE)
            if match:
                #print "exec_input:"
                #for temp_line in exec_input:
                #    print "    " + temp_line
                kw = {}
                kw['exec_output'] = []
                exec('\n'.join(exec_input)) in kw
                #print "exec_output:"
                for line in kw['exec_output']:
                #    print "    " + line
                    LocalData.append(line)
                    SourceLineList.append((curr_file, exec_line))
                exec_input = []
                execing = False
            else:
                exec_input.append(line)
            continue
        match = re.match(r'\s*%exec', line, flags=re.IGNORECASE)
        if match:
            execing = True
            exec_line = line_no
            continue
        match = re.match(r'\s*%include\s+', line, flags=re.IGNORECASE)
        if match:
            new_source = re.sub(r'\s*%include\s+(.*)', r'\1', line, flags=re.IGNORECASE)
            LocalData += load_file(new_source, depth_list + [SourceFile])
            continue
        LocalData.append(line)
        SourceLineList.append((curr_file, line_no))
    fd.close()
    return LocalData

def dump_source_files(data):
    global SourceFileList, SourceLineList
    print "SourceFileList:", SourceFileList
    print "SourceLineList:", SourceLineList
    curr_file = -1
    for line_no, line in enumerate(data):
        if SourceLineList[line_no][0] != curr_file:
            curr_file = SourceLineList[line_no][0]
            print "File:", SourceFileList[curr_file]
        print "%4d:" % SourceLineList[line_no][1], line

def process_source(source_file):
    global PathName, SourceFile
    global TheDrivers
    global NumberOfLinesIn, NumberOfLinesOut
    global SourceData
    global PrintedFileName
    global SourceFileList, SourceLineList

    TheDrivers = {}

    PrintedFileName = -1
    NumberOfLinesIn = 0
    NumberOfLinesOut = 0
    SourceFileList = list()
    SourceLineList = list()
    PathName = os.path.realpath(os.path.abspath(os.path.dirname(source_file)))
    SourceData = load_file(source_file, [])
    NumberOfLinesIn = len(SourceData)
    start_line = lexer.lineno
    yaccer.parse('\n'.join(SourceData))
    stop_line = lexer.lineno
    if Verbose:
        print 'Consumed file %s with %d lines (%d, %d)' % \
                (source_file, NumberOfLinesIn, start_line, stop_line - 1)
    lexer.lineno = 1

    process_drivers(TheDrivers)
    if args.list:
        dump_source_files(SourceData)

def main():
    global lexer, yaccer
    global Verbose
    global Move
    global DriverDump
    global CodeDump
    global args
    import argparse

    # RELEASE-3_1="before", RELEASE-3_2="after"
    default_sct = "after"
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--code", help="dump code",
        action="store_true")
    parser.add_argument("-d", "--driver", help="dump driver",
        action="store_true")
    parser.add_argument("-l", "--list", help="list output",
        action="store_true")
    parser.add_argument("-m", "--move", help="generate move commands",
        action="store_true")
    parser.add_argument("--sct",
        help="where to put the sct in the filename [%s]" % default_sct,
        choices=["before", "after"], default=default_sct)
    parser.add_argument("-v", "--verbose", help="verbose output",
        action="store_true")
    parser.add_argument("driver_source", help="driver source file", nargs="*")
    args = parser.parse_args()
    if args.verbose:
        print args
    if args.code:
        CodeDump = True
    else:
        CodeDump = False
    if args.driver:
        DriverDump = True
    else:
        DriverDump = False
    if args.move:
        Move = True
    else:
        Move = False
    if args.verbose:
        Verbose = True
    else:
        Verbose = False
    source_files = args.driver_source    #
    if source_files and len(source_files) > 0:
        # Build the lexer
        #
        lexer = lex.lex()


        #
        # Build the parser
        #
        #yaccer = yacc.yacc(tabmodule="gen_sct",outputdir="/tmp",write_tables=0,debug=0)
        yaccer = yacc.yacc(debug=0)


        for source_file in source_files:
            process_source(source_file)

if __name__ == "__main__":
    main()
