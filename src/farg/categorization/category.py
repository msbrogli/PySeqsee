"""Classes to deal with categories and their instances, including the base class for
categories.

An example will help describe all that happens here. We will use the category 'Ascending'
from Seqsee. Instances of this category are objects such as '(1 2 3)' and '(7 8 9 10)'.
Objects need to have CategorizableMixin in their class hierarchy: it provides methods to
store the discovered categories and their bindings.

A category is a class (deriving from Category).

Adding a category to an instance::

  bindings = item.DescribeAs(category)

The following also returns a binding, but does not store the membership information::

  bindings = category.IsInstance(item)

"""

from farg.exceptions import FargError
from farg.meta import MemoizedConstructor
from farg.ltm.storable import LTMStorableMixin

class Category(LTMStorableMixin):
  """The base class of any category in the FARG system.
  
  Any derivative class must define the following class methods:
  
  * IsInstance (which would return a binding),
  * FindMapping (given two categorizables, returns a mapping between the two)
  * ApplyMapping (given a mapping and a categorizable, returns a new item). 
  """
  __metaclass__ = MemoizedConstructor

  def IsInstance(self, object):
    """Is object an instance of this category?
    
    If it is not, `None` is returned. If it is, a binding object is returned.
    """
    raise FargError("IsInstance makes no sense on base category.")

  def FindMapping(self, categorizable1, categorizable2):
    """Finds a mapping between two objects based on a particular category."""
    raise FargError("IsInstance makes no sense on base category.")

  def ApplyMapping(self, categorizable, mapping):
    """Apply a mapping to a categorizable to obtain a different categorizable."""
    raise FargError("IsInstance makes no sense on base category.")
