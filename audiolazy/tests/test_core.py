# -*- coding: utf-8 -*-
# This file is part of AudioLazy, the signal processing Python package.
# Copyright (C) 2012-2013 Danilo de Jesus da Silva Bellini
#
# AudioLazy is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
# Created on Sat Oct 13 2012
# danilo [dot] bellini [at] gmail [dot] com
"""
Testing module for the lazy_core module
"""

import pytest
p = pytest.mark.parametrize

from types import GeneratorType
import operator

# Audiolazy internal imports
from ..lazy_core import OpMethod, AbstractOperatorOverloaderMeta, StrategyDict
from ..lazy_compat import meta


class TestOpMethod(object):

  def test_get_no_input(self):
    assert set(OpMethod.get()) == set(OpMethod.get("all"))

  def test_get_empty(self):
    for el in [OpMethod.get(None), OpMethod.get(None, without="+"),
               OpMethod.get(without="all"), OpMethod.get("+ -", "- +")]:
      assert isinstance(el, GeneratorType)
      assert list(el) == []

  @p("name", ["cmp", "almosteq", "div"])
  def test_get_wrong_input(self, name):
    for el in [OpMethod.get(name),
               OpMethod.get(without=name),
               OpMethod.get("all", without=name),
               OpMethod.get(name, without="all")]:
      with pytest.raises(ValueError) as exc:
        next(el)
      assert name in str(exc.value)
      assert ("unknown" in str(exc.value)) is (name != "div")

  def test_get_reversed(self):
    has_rev = sorted("+ - * / // % ** >> << & | ^".split())
    result_all_rev = list(OpMethod.get("r"))
    result_no_rev = list(OpMethod.get("all", without="r"))
    result_all = list(OpMethod.get("all"))
    assert len(result_all_rev) == len(has_rev)
    assert has_rev == sorted(op.symbol for op in result_all_rev)
    assert not any(el in has_rev for el in result_no_rev)
    assert set(result_no_rev).union(set(result_all_rev)) == set(result_all)

  @p(("symbol", "name"), {"+": "add",
                          "-": "sub",
                          "*": "mul",
                          "/": "truediv",
                          "//": "floordiv",
                          "%": "mod",
                          "**": "pow",
                          ">>": "rshift",
                          "<<": "lshift",
                          "~": "invert",
                          "&": "and",
                          "|": "or",
                          "^": "xor",
                          "<": "lt",
                          "<=": "le",
                          "==": "eq",
                          "!=": "ne",
                          ">": "gt",
                          ">=": "ge"}.items())
  def test_get_by_all_criteria_for_one_symbol(self, symbol, name):
    # Useful constants
    third_name = {"+": "pos",
                  "-": "neg"}
    without_binary = ["~"]
    has_rev = "+ - * / // % ** >> << & | ^".split()

    # Search by symbol
    result = list(OpMethod.get(symbol))

    # Dunder name
    for res in result:
      assert res.dname == res.name.join(["__", "__"])

    # Name, arity, reversed and function
    assert result[0].name == name
    assert result[0].arity == (1 if symbol in without_binary else 2)
    assert not result[0].rev
    func = getattr(operator, name.join(["__", "__"]))
    assert result[0].func is func
    if symbol in has_rev:
      assert result[1].name == "r" + name
      assert result[1].arity == 2
      assert result[1].rev
      assert result[0].func is result[1].func
    if symbol in third_name:
      assert result[2].name == third_name[symbol]
      assert result[2].arity == 1
      assert not result[2].rev
      unary_func = getattr(operator, third_name[symbol].join(["__", "__"]))
      assert result[2].func is unary_func
      assert not (result[0].func is result[2].func)

    # Length
    if symbol in third_name:
      assert len(result) == 3
    elif symbol in has_rev:
      assert len(result) == 2
    else:
      assert len(result) == 1

    # Search by name
    result_name = list(OpMethod.get(name))
    assert len(result_name) == 1
    assert result_name[0] is result[0]

    # Search by dunder name
    result_dname = list(OpMethod.get(name.join(["__", "__"])))
    assert len(result_dname) == 1
    assert result_dname[0] is result[0]

    # Search by function
    result_func = list(OpMethod.get(func))
    assert len(result_func) == min(2, len(result))
    assert result_func[0] is result[0]
    assert result_func[-1] is result[:2][-1]
    if symbol in third_name:
      result_unary_func = list(OpMethod.get(unary_func))
      assert len(result_unary_func) == 1
      assert result_unary_func[0] is result[2]

  def test_get_by_arity(self):
    comparison_symbols = "> >= == != < <=" # None is "reversed" here

    # Queries to be used
    res_unary = set(OpMethod.get("1"))
    res_binary = set(OpMethod.get("2"))
    res_reversed = set(OpMethod.get("r"))
    res_not_unary = set(OpMethod.get(without="1"))
    res_not_binary = set(OpMethod.get(without="2"))
    res_not_reversed = set(OpMethod.get(without="r"))
    res_not_reversed_nor_unary = set(OpMethod.get(without="r 1"))
    res_all = set(OpMethod.get("all"))
    res_comparison = set(OpMethod.get(comparison_symbols))

    # Compare!
    assert len(res_unary) == 3
    assert set(op.name for op in res_unary) == {"pos", "neg", "invert"}
    assert len(res_binary) == 2 * len(res_reversed) + len(res_comparison)
    assert all(op in res_binary for op in res_reversed)
    assert all(op in res_binary for op in res_not_reversed_nor_unary)
    assert all(op in res_binary for op in res_comparison)
    assert all(op in res_not_reversed_nor_unary for op in res_comparison)
    assert all(op in res_not_reversed for op in res_not_reversed_nor_unary)
    assert all(op in res_not_reversed for op in res_unary)
    assert all((op in res_reversed) or (op in res_not_reversed_nor_unary)
               for op in res_binary)
    assert all(op in res_binary for op in res_not_reversed_nor_unary)

    # Excluded middle: an operator is always either unary or binary
    assert len(res_all) == len(res_unary) + len(res_binary)
    assert not any(op in res_binary for op in res_unary)
    assert not any(op in res_unary for op in res_binary)
    assert res_not_unary == res_binary
    assert res_not_binary == res_unary

    # Query using other datatypes
    assert res_unary == set(OpMethod.get(1))
    assert res_binary == set(OpMethod.get(2))
    assert res_not_reversed_nor_unary == \
           set(OpMethod.get(without=["r", 1])) == \
           set(OpMethod.get(without=["r", "1"]))

  def test_mixed_format_query(self):
    a = set(OpMethod.get(["+", "invert", "sub rsub >"], without="radd"))
    b = set(OpMethod.get(["+ invert", "sub rsub >"], without="radd"))
    c = set(OpMethod.get(["add invert", "sub rsub >", operator.__pos__]))
    d = set(OpMethod.get("add invert pos sub rsub >"))
    e = set(OpMethod.get(["+ -", operator.__invert__, "__gt__"],
                         without="__radd__ neg"))
    assert a == b == c == d == e


class TestAbstractOperatorOverloaderMeta(object):

  def test_empty_directly_as_metaclass(self):
    with pytest.raises(TypeError):
      try:
        class unnamed(meta(metaclass=AbstractOperatorOverloaderMeta)):
          pass
      except TypeError as excep:
        msg = "Class 'unnamed' has no builder/template for operator method '"
        assert str(excep).startswith(msg)
        raise

  def test_empty_invalid_subclass(self):
    class MyAbstractClass(AbstractOperatorOverloaderMeta):
      pass
    with pytest.raises(TypeError):
      try:
        class DummyClass(meta(metaclass=MyAbstractClass)):
          pass
      except TypeError as excep:
        msg = "Class 'DummyClass' has no builder/template for operator method"
        assert str(excep).startswith(msg)
        raise


class TestStrategyDict(object):

  def test_1x_strategy(self):
    sd = StrategyDict()

    assert len(sd) == 0

    @sd.strategy("test", "t2")
    def sd(a):
      return a + 18

    assert len(sd) == 1

    assert sd["test"](0) == 18
    assert sd.test(0) == 18
    assert sd.t2(15) == 33
    assert sd(-19) == -1
    assert sd.default == sd["test"]


  def test_same_key_twice(self):
    sd = StrategyDict()

    @sd.strategy("data", "main", "data")
    def sd():
      return True

    @sd.strategy("only", "only", "main")
    def sd():
      return False

    assert len(sd) == 2 # Strategies
    assert sd["data"] == sd.default
    assert sd["data"] != sd["main"]
    assert sd["only"] == sd["main"]
    assert sd()
    assert sd["data"]()
    assert not sd["only"]()
    assert not sd["main"]()
    assert sd.data()
    assert not sd.only()
    assert not sd.main()
    sd_keys = list(sd.keys())
    assert ("data",) in sd_keys
    assert ("only", "main") in sd_keys


  @p("add_names", [("t1", "t2"), ("t1", "t2", "t3")])
  @p("mul_names", [("t3",),
                   ("t1", "t2"),
                   ("t1", "t3"),
                   ("t3", "t1"),
                   ("t3", "t2"),
                   ("t1", "t2", "t3"),
                   ("t1")
                  ])
  def test_2x_strategy(self, add_names, mul_names):
    sd = StrategyDict()

    @sd.strategy(*add_names)
    def sd(a, b):
      return a + b

    @sd.strategy(*mul_names)
    def sd(a, b):
      return a * b

    add_names_valid = [name for name in add_names if name not in mul_names]
    if len(add_names_valid) == 0:
      assert len(sd) == 1
    else:
      assert len(sd) == 2

    for name in add_names_valid:
      assert sd[name](5, 7) == 12
      assert sd[name](1, 3) == 4
    for name in mul_names:
      assert sd[name](5, 7) == 35
      assert sd[name](1, 3) == 3

    if len(add_names_valid) > 0:
      assert sd(-19, 3) == -16
    sd.default = sd[mul_names[0]]
    assert sd(-19, 3) == -57
