import unittest

from serpy.fields import Field, MethodField, IntField, FloatField, StrField
from serpy.serializer import Serializer, DictSerializer
from tests.obj import Obj


class TestSerializer(unittest.TestCase):

    def test_simple(self):

        class ASerializer(Serializer):

            a = Field()

            def make_object(self, data):
                return Obj(**data)

        a = Obj(a=5)
        self.assertEqual(ASerializer(instance=a).data['a'], 5)

        a = ASerializer(data={'a': 5}).instance
        self.assertEqual(a.a, 5)

    def test_data_and_obj_cached(self):
        class ASerializer(Serializer):

            a = Field()

            def make_object(self, data):
                return Obj(**data)

        a = Obj(a=5)
        serializer = ASerializer(instance=a)
        data1 = serializer.data
        data2 = serializer.data
        # Use assertTrue instead of assertIs for python 2.6.
        self.assertTrue(data1 is data2)

        serializer = ASerializer(data={'a': 5})
        obj1 = serializer.instance
        obj2 = serializer.instance
        # Use assertTrue instead of assertIs for python 2.6.
        self.assertTrue(obj1 is obj2)

    def test_inheritance(self):
        class ASerializer(Serializer):

            a = Field()

            def make_object(self, data):
                return Obj(**data)

        class CSerializer(Serializer):

            c = Field()

            def make_object(self, data):
                return Obj(**data)

        class ABSerializer(ASerializer):
            b = Field()

        class ABCSerializer(ABSerializer, CSerializer):
            pass

        a = Obj(a=5, b='hello', c=100)
        self.assertEqual(ASerializer(instance=a).data['a'], 5)
        data = ABSerializer(instance=a).data
        self.assertEqual(data['a'], 5)
        self.assertEqual(data['b'], 'hello')
        data = ABCSerializer(instance=a).data
        self.assertEqual(data['a'], 5)
        self.assertEqual(data['b'], 'hello')
        self.assertEqual(data['c'], 100)

        a = {'a': 5, 'b': 'hello', 'c': 100}
        serializer = ASerializer(data=a)
        self.assertEqual(serializer.instance.a, 5)
        serializer = ABSerializer(data=a)
        self.assertEqual(serializer.instance.a, 5)
        self.assertEqual(serializer.instance.b, 'hello')
        serializer = ABCSerializer(data=a)
        self.assertEqual(serializer.instance.a, 5)
        self.assertEqual(serializer.instance.b, 'hello')
        self.assertEqual(serializer.instance.c, 100)

    def test_many(self):
        class ASerializer(Serializer):

            a = Field()

        objs = [Obj(a=i) for i in range(5)]
        data = ASerializer(objs, many=True).data
        self.assertEqual(len(data), 5)
        self.assertEqual(data[0]['a'], 0)
        self.assertEqual(data[1]['a'], 1)
        self.assertEqual(data[2]['a'], 2)
        self.assertEqual(data[3]['a'], 3)
        self.assertEqual(data[4]['a'], 4)

    def test_serializer_as_field(self):
        class ASerializer(Serializer):

            a = Field()

        class BSerializer(Serializer):

            b = ASerializer()

        b = Obj(b=Obj(a=3))
        self.assertEqual(BSerializer(instance=b).data['b']['a'], 3)

    def test_serializer_as_field_many(self):
        class ASerializer(Serializer):

            a = Field()

        class BSerializer(Serializer):

            b = ASerializer(many=True)

        b = Obj(b=[Obj(a=i) for i in range(3)])
        b_data = BSerializer(instance=b).data['b']
        self.assertEqual(len(b_data), 3)
        self.assertEqual(b_data[0]['a'], 0)
        self.assertEqual(b_data[1]['a'], 1)
        self.assertEqual(b_data[2]['a'], 2)

    def test_serializer_as_field_call(self):
        class ASerializer(Serializer):

            a = Field()

        class BSerializer(Serializer):

            b = ASerializer(call=True)

        b = Obj(b=lambda: Obj(a=3))
        self.assertEqual(BSerializer(instance=b).data['b']['a'], 3)

    def test_serializer_method_field(self):
        class ASerializer(Serializer):

            a = MethodField()
            b = MethodField('add_9', 'sub_9')

            def get_a(self, obj):
                return obj.a + 5

            def set_a(self, obj, value):
                obj.a = value - 5

            def add_9(self, obj):
                return obj.b + 9

            def sub_9(self, obj, value):
                obj.b = value - 9

        a = Obj(a=2, b=2)
        data = ASerializer(instance=a).data
        self.assertEqual(data['a'], 7)
        self.assertEqual(data['b'], 11)
        data = {'a': 7, 'b': 11}

    def test_field_called(self):
        class ASerializer(Serializer):

            a = IntField()
            b = FloatField(call=True)
            c = StrField(attr='foo.bar.baz')

        o = Obj(a='5', b=lambda: '6.2', foo=Obj(bar=Obj(baz=10)))
        data = ASerializer(instance=o).data
        self.assertEqual(data['a'], 5)
        self.assertEqual(data['b'], 6.2)
        self.assertEqual(data['c'], '10')
        data = {'a': 5, 'b': 6.2, 'c': '10'}

    def test_dict_serializer(self):
        class ASerializer(DictSerializer):

            a = IntField()
            b = Field(attr='foo')

        d = {'a': '2', 'foo': 'hello'}
        data = ASerializer(instance=d).data
        self.assertEqual(data['a'], 2)
        self.assertEqual(data['b'], 'hello')

    def test_dotted_attr(self):
        class ASerializer(Serializer):

            a = Field('a.b.c')

        o = Obj(a=Obj(b=Obj(c=2)))
        data = ASerializer(instance=o).data
        self.assertEqual(data['a'], 2)

    def test_custom_field(self):

        class Add5Field(Field):
            def to_representation(self, value):
                return value + 5

            def to_internal_value(self, data):
                return data - 5

        class ASerializer(Serializer):

            a = Add5Field()

        o = Obj(a=10)
        data = ASerializer(instance=o).data
        self.assertEqual(data['a'], 15)

    def test_optional_field(self):
        class ASerializer(Serializer):

            a = IntField(required=False)

            def make_object(self, data):
                return Obj(**data)

        o = Obj(a=None)
        data = ASerializer(instance=o).data
        self.assertTrue(data['a'] is None)

        data = {'a': None}
        obj = ASerializer(data=data).instance
        self.assertTrue(obj.a is None)

        o = Obj(a='5')
        data = ASerializer(instance=o).data
        self.assertEqual(data['a'], 5)

        data = {'a': 5}
        obj = ASerializer(data=data).instance
        self.assertEqual(obj.a, 5)

        class ASerializer(Serializer):

            a = IntField()

            def make_object(self, data):
                return Obj(**data)

        o = Obj(a=None)
        self.assertRaises(TypeError, lambda: ASerializer(instance=o).data)

        data = {}
        instance = ASerializer(data=data).instance
        self.assertFalse(hasattr(instance, 'a'))

    def test_read_only_field(self):
        class ASerializer(Serializer):

            a = IntField(read_only=True)

        o = Obj(a='5')
        data = ASerializer(instance=o).data
        self.assertEqual(data['a'], 5)

    def test_serialization_requires_instance(self):
        class ASerializer(Serializer):

            a = IntField()

        self.assertRaises(AttributeError, lambda: ASerializer().data)

    def test_deserialization_requires_data(self):
        class ASerializer(Serializer):

            a = IntField()

        self.assertRaises(
            AttributeError,
            lambda: ASerializer().instance
        )

    def test_can_only_do_serialization_or_deserialization(self):
        class ASerializer(Serializer):

            a = IntField()

            def make_object(self, data):
                return Obj(**data)

        o = Obj(a='5')
        data = {'a': 5}
        serializer = ASerializer(instance=o, data=data)
        self.assertRaises(AttributeError, lambda: serializer.instance)


if __name__ == '__main__':
    unittest.main()
