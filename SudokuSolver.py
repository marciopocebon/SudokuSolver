#this way is a bit long winded
from yices import (yices_init,
                   yices_exit,
                   int_type,
                   int32,
                   term_t,
                   type_t,
                   distinct,
                   and2,
                   arith_eq_atom,
                   arith_leq_atom,
                   new_uninterpreted_term,
                   new_config,
                   new_context,
                   default_config_for_logic,
                   assert_formula,
                   check_context,
                   get_model,
                   get_int32_value,
                   free_context,
                   free_config
)


#this way we could use the yices_ prefixes everywhere and feel safe.
#from yices import *


from ctypes import ( c_int32 )


#probably things like this need to be moved into yices.py
def make_term_array(pyarray):
    """Makes a C term array object from a python array object"""
    retval = None
    if pyarray is not None:
        #weird python and ctype magic
        retval = (term_t * len(pyarray))(*pyarray)
    return retval

#probably things like this need to be moved into yices.py
def make_type_array(pyarray):
    """Makes a C term array object from a python array object"""
    retval = None
    if pyarray is not None:
        #weird python and ctype magic
        retval = (type_t * len(pyarray))(*pyarray)
    return retval


class SudokuSolver(object):

    """
    The Sudoku Solver, will solve when asked.

    iam: haven't really thought about the UI yet.


    """
    def __init__(self, game):
        self.game = game
        yices_init()
        self.logic = self.__createLogic()
        self.numerals = self.__createNumerals()
        self.config = new_config()
        default_config_for_logic(self.config, "QF_LIA")
        self.context = new_context(self.config)
        self.__generateConstraints()


    def __cleanUp(self):
        free_context(self.context)
        free_config(self.config)
        yices_exit()


    def __createLogic(self):
        """Creates the matrix of uninterpreted terms that represents the logical view of the board."""
        int_t = int_type()
        logic = [None] * 9
        for i in xrange(9):
            logic[i] = [None] * 9
            for j in range(9):
                logic[i][j] = new_uninterpreted_term(int_t)
        return logic

    def __createNumerals(self):
        numerals = {}
        for i in xrange(1, 10):
            numerals[i] = int32(i)
        return numerals


    def __generateConstraints(self):
        one = self.numerals[1]
        nine = self.numerals[9]


        # each x is between 1 and 9
        def between_1_and_9(x):
            return and2(arith_leq_atom(one, x), arith_leq_atom(x, nine))
        for i in xrange(9):
            for j in xrange(9):
                assert_formula(self.context, between_1_and_9(self.logic[i][j]))

        # all elements of the array x are distinct
        def all_distinct(x):
            n = len(x)
            a = make_term_array(x)
            return distinct(n, a)

        # All elements in a row must be distinct
        for i in xrange(9):
            assert_formula(self.context, all_distinct([self.logic[i][j] for j in xrange(9)]))  #I.e.  all_distinct(X[i])


        # All elements in a column must be distinct
        for i in xrange(9):
            assert_formula(self.context, all_distinct([self.logic[j][i] for j in xrange(9)]))

        # All elements in each 3x3 square must be distinct
        for k in xrange(3):
            for l in xrange(3):
                assert_formula(self.context, all_distinct([self.logic[i + 3 * l][j + 3 * k] for i in xrange(3) for j in xrange(3)]))


    def __addFacts(self):
        def set_value(context, position, value):
            (row, column) = position
            assert 1 <= row and row <= 9
            assert 1 <= column and column <= 9
            assert 1 <= value and value <= 9
            assert_formula(self.context, arith_eq_atom(self.logic[row - 1][column - 1], self.numerals[value]))


        for i in xrange(9):
            for j in xrange(9):
                value = self.game.puzzle[i][j]
                if value is not None:
                    set_value(self.context, (i, j), value)


    def solve(self):
        smt_stat = check_context(self.context, None)

        if smt_stat != 3:
            print 'No solution: smt_stat = {0}\n'.format(smt_stat)
        else:
            #print model
            model = get_model(self.context, 1)
            val = c_int32()
            for i in xrange(9):
                for j in xrange(9):
                    get_int32_value(model, self.logic[i][j], val)
                    print 'V({0}, {1}) = {2}'.format(i, j, val.value)
