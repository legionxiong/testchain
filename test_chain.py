'''
Run tests in a chain, the chained actions would be picked up randomly or by some algorithm

@author: Lijin Xiong
'''

import random
import types
import json

def json2object(json_str=None, load=None):
    if json_str:
        try:
            load = json.loads(json_str)
        except Exception as e:
            raise e
    jsonobj = type("JSONOBJ", (object,), dict(__getattr__=lambda self, x: None))()
    # jsonobj = type("JSONOBJ", (object,), dict(__getattr__=lambda self, x: self.__dict__[x] if x in self.__dict__ else None))()
    if isinstance(load, types.DictType):
        for k in load.keys():
            obj = json2object(load=load[k])
            setattr(jsonobj, k, obj)
    elif isinstance(load, (types.ListType, types.StringType, types.IntType, types.UnicodeType)):
        return load
    else:
        raise Exception, 'Unsupported type'
    return jsonobj


class TestChain(object):
    def __init__(self, test_obj, chain_length=20):
        self.test_obj = test_obj
        test_ops = filter(lambda x, obj=test_obj: not x.startswith('_') 
                          and hasattr(eval('obj.%s' % x), '__call__'), dir(test_obj))
        self.chain_list = [o for o in test_ops if eval('test_obj.%s.__doc__' % o) is not None]
        self.test_list = [f for f in self.chain_list if json2object(eval('test_obj.%s.__doc__' % f)).step == '1']
        self.chain_length = chain_length
        self.test_chain = ''
        self.weights = {}

    def make_chain(self):
        test = json2object(eval('self.test_obj.%s.__doc__' % self.test_list[-1]))
        if test.weight:
            self.weights[self.test_list[-1]] = test.weight
        if test.must:
            if test.must.before:
                self.test_list.insert(-1, test.must.before)
            if test.must.after:
                for after_ops in test.must.after:
                    self.test_list.append(after_ops)
        next_list = test.next[:]
        for act in test.next:
            if self.weights.has_key(act):
                for _ in range(int(self.weights[act])):
                    next_list.append(act)
        self.test_list.append(random.choice(next_list))
        if test.delay:
            self.test_list.append(test.delay)
        self.chain_length -= 1
        if self.chain_length > 0:
            self.make_chain()
        self.test_chain = 'self.test_obj' + '.' + '().'.join(self.test_list) + '()'

    def run_test(self):
        eval(self.test_chain)