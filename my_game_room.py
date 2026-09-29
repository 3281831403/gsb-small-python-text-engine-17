import copy

import my_game_utils


class RoomStateMapper(object):
    """Class to maintain all configured room states.

    This class, when instantiated, acts like a datastore mapping between a state
    ID and a description of a room, which is a list of adjectives.
    """

    def __init__(self):
        self._default_state = []
        self._all_states = {}

    @property
    def all_states(self):
        return self._all_states

    @property
    def default_state(self):
        return self._default_state

    @default_state.setter
    def default_state(self, s):
        self._default_state = copy.deepcopy(s)

    def AddState(self, sid, desc):
        """Add or potentially override an existing room state description.

        Stores a deep copy of desc so that later mutation or re-use of desc
        by the caller cannot clobber the stored description.

        Args:
          sid:  Integer room state ID.
          desc:  List of string descriptions.
        """
        self._all_states[sid] = copy.deepcopy(desc)

    def GetState(self, sid):
        """Returns a deep-copy snapshot of the description of the game state.

        Args:
          sid:  Integer room state ID.
        
        Returns:
          A copy of the list of string descriptions of the room state, a copy
          of the default state if the ID does not exist in the mapping.
        """
        return copy.deepcopy(self._all_states.get(sid, self._default_state))


class Room(object):
    """Object to abstract out concept of a room in the game."""
    
    def __init__(self):
        # A state class must implement a __str__ method for debugging.
        self._state = None
        # Contents are kept sorted.
        self._contents = []
    
    @property
    def state(self):
        return self._state

    @state.setter
    def state(self, s):
        self._state = s

    @property
    def contents(self):
        return self._contents

    @contents.setter
    def contents(self, c):
        # Contents are kept sorted no matter which mutation path is taken.
        # Sort before committing so a failed sort leaves the previous
        # contents untouched.
        self._contents = self._Sorted(c)

    @staticmethod
    def _SortKey(item):
        # Game items expose sort_id; plain string names sort as themselves.
        sort_id = getattr(item, "sort_id", None)
        if sort_id is not None:
            return sort_id
        if isinstance(item, str):
            return item
        raise AttributeError("sort_id is undefined for item: %r" % (item,))

    @classmethod
    def _Sorted(cls, contents):
        return sorted(contents, key=cls._SortKey)

    def AddContent(self, item):
        """Add content to this room.

        Takes ownership of the item.

        The add is atomic: the new sorted contents are built first and only
        committed on success, so a failure leaves the room contents exactly
        as they were and does not pollute later additions.

        Args:
          item:  Name of an item to put into the room.

        Raises:
          AttributeError if sort_id is undefined.
        """
        self._contents = self._Sorted(self._contents + [item])

    def RemoveContent(self, content_name):
        # Removing an item from a sorted list should still preserve the sorted
        # order of the list.
        return my_game_utils.RemoveContent(self._contents, content_name)

    def GetContentsDisplay(self):
        """Get the contents of the room to display."""
        return my_game_utils.GetContentsDisplay(self._contents)

    def TryChangeState(self, new_state):
        if new_state == self._state:
            return False
        self._state = new_state
        return True

    def __str__(self):
        return self.state.sid

    def DebugInfo(self):
        """Returns a list of debug info."""
        return ["STATE: %s" % str(self.state),
                "CONTENTS: [%s]" % ", ".join(self.GetContentsDisplay())
               ]
