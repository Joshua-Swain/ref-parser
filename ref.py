#!/usr/bin/python

import sys, string, tokenize

tokens = iter( sys.stdin.read().split() )
cur_token = None
top_ref = [None, { '+' : '+', 
                   '-' : '-', 
                   '*' : '*',
                   '/' : '/',
                   "'" : "'",
                   'car' : 'car',
                   'cdr' : 'cdr',
                   'cons' : 'cons',
                   'list' : 'list',
                   'let' : 'let',
                   'let*' : 'let*',
                   'define' : 'define'
                  }]


class ParseError(Exception):
  def __init__(self, value):
    self.value = value
  def __str__(self):
    return repr(self.value)

class EvalError(Exception):
  def __init__(self, value):
    self.value = value
  def __str__(self):
    return repr(self.value)

def lookahead():
  global cur_token

  if cur_token == None:
    try:
      cur_token = tokens.next()
    except:
      cur_token = None

  return cur_token


def next_token():
  global cur_token

  n = lookahead()
  cur_token = None
  return n


def add( a, b ):
  return a + b

def sub( a, b ):
  return a - b

def mul( a, b ):
  return a * b

def div( a, b ):
  return a / b


def do_arith_op( ref, op, l ):
  if len( l ) < 1:
    raise EvalError( op )

  r = do_eval( ref, l[0] )
  if not isinstance( r, int ):
    raise EvalError( op )

  for o in l[1:]:
    i = do_eval( ref, o )
    if isinstance( i, int ):
      r = op( r, i )
    else:
      raise EvalError( op )
 
  return r


def do_eval( ref, a ):
  if isinstance( a, list ): # list  
    if len( a ) < 1:
      raise EvalError( '( )' )

    op = do_eval( ref, a[0] )

    f = a
    a = None
    if op == "+":
      a = do_arith_op( ref, add, f[1:] )
    elif op == "-":
      a = do_arith_op( ref, sub, f[1:] )
    elif op == "*":
      a = do_arith_op( ref, mul, f[1:] )
    elif op == "/":
      a = do_arith_op( ref, div, f[1:] )
    elif op == "'":
      if len( f ) > 1:
        a = f[1]
    elif op == "car":
      if len( f ) > 1:
        l = do_eval( ref, f[1] )
        if isinstance( l, list ) and len( l ) > 0:
          a = l[0]
    elif op == "cdr":
      if len( f ) > 1:
        l = do_eval( ref, f[1] )
        if isinstance( l, list ) and len( l ) > 0:
          a = l[1:]
    elif op == "cons":
      if len( f ) > 2:
        h = do_eval( ref, f[1] )
        t = do_eval( ref, f[2] )
        if isinstance( t, list ):
          a = [ h ] + t
    elif op == "list":
      a = []
      for b in f[1:]:
        a = a + [do_eval( ref, b )]
    elif op == "define":
      if len( f ) > 2 and isinstance( f[1], str ):
        key = f[1]
        val = do_eval( ref, f[2] )
        map = ref[1]
        map[key] = val
        a = key
    elif op == "let":
      if len( f ) > 2 and isinstance( f[1], list ):
        newref = [ref, dict()]  # new ref environment
        map = newref[1] 

        binds = f[1]
        for b in binds:
          if isinstance( b, list ) and len( b ) > 1:
            key = b[0]
            val = do_eval( ref, b[1] )
            if isinstance( key, str ) and not str(key).isdigit():
              map[key] = val

        for e in f[2:]:
          a = do_eval( newref, e )
    elif op == "let*":
      if len( f ) > 2 and isinstance( f[1], list ):
        newref = [ref, dict()]  # new ref environment
        map = newref[1] 

        binds = f[1]
        for b in binds:
          if isinstance( b, list ) and len( b ) > 1:
            key = b[0]
            val = do_eval( newref, b[1] )
            if isinstance( key, str ) and not str(key).isdigit():
              map[key] = val

        for e in f[2:]:
          a = do_eval( newref, e )
    else:
      raise EvalError( 'unknown proc: ' + str( op ) )

    if a == None:
      raise EvalError( op )

    return a
  elif str(a).isdigit():   # int
    return a
  else:                    # id
    b = lookup( ref, a )
    return b

def lookup( ref, id ):
  map = ref[1]
  if id in map:
    return map[id]
  elif ref[0] != None:
    return lookup( ref[0], id )
  else:
    raise EvalError( "Cannot find: " + str( id ) )


def parseS():
  tok = lookahead()
    
  if tok != ")":
    return parseAtoms()
  else:
    raise ParseError( 'S' )
  

def parseAtoms():
  tok = lookahead()
    
  if tok == None or tok == ")":
    return []
  else:
    return parseAtom() + parseAtoms()
   

def parseAtom():
  tok = lookahead()
    
  if tok == "(":
    l = [ parseList() ]
  elif tok == "'":             # quote
    next_token()
    l = [[tok] + parseAtom()]
  elif( str(tok).isdigit() ):  # integer
    next_token()
    l = [int( tok )]
  elif tok != None:         # identifier
    next_token()
    l = [tok]
  else:
    raise ParseError( 'Atom' )

  return l


def parseList():
  tok = next_token()

  if tok == '(': 
    l = parseListBody()
    tok = next_token()
    if tok != ")":
      raise ParseError( 'List' )
  else:
    raise ParseError( 'List' )

  return l


def parseListBody():
  tok = lookahead()
  l = []

  if tok != None:
    return l + parseAtoms()
  else:
    raise ParseError( 'ListBody' )


def atom2str( l ):
  if isinstance( l, list ):
    if len( l ) < 1: 
      return "( )"
    elif l[0] == "'":
      return "' " + atom2str( l[1] )
    
    s = "("
    for a in l:
      s = s + " " + atom2str( a )
    return s + " )"
  else:
    return str( l )


def eval_result( ref, l ):
  for a in l:
    print atom2str( do_eval( ref, a ) )
 
try:
  l = parseS()
  if lookahead() != None:
    raise ParseError( 'S' )
  eval_result( top_ref, l )
except ParseError as p:
  print "Syntax Error while parsing " + str( p ) + " production"
except EvalError as p:
  print "Evaluation Error while evaluating " + str( p )

