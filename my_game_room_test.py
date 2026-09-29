# Generic imports.
import copy
import unittest

# Game specific imports.
import my_game_item
import my_game_room


class _BrokenContent(object):
    """Content with no usable sort_id, to exercise failure paths."""
    pass


class TestRoom(unittest.TestCase):

    def setUp(self):
        self.game_room = my_game_room.Room()

    def test_state(self):
        self.game_room.state = 0
        self.assertEqual(self.game_room.state, 0)
        self.game_room.state = 1
        self.assertEqual(self.game_room.state, 1)
        self.game_room.state = 1
        self.assertEqual(self.game_room.state, 1)

    def test_add_content(self):
        self.game_room.state = 0
        self.game_room.AddContent("A")
        self.game_room.AddContent("A")
        self.game_room.AddContent("C")
        self.game_room.AddContent("A")
        self.game_room.AddContent("B")
        self.assertEqual(self.game_room.contents, ["A", "A", "A", "B", "C"])

    def test_remove_content(self):
        self.game_room.state = 0
        self.game_room.AddContent("C")
        self.game_room.AddContent("A")
        self.game_room.AddContent("B")
        self.game_room.AddContent("A")
        self.game_room.AddContent("B")
        self.game_room.AddContent("A")
        self.assertEqual(self.game_room.contents,
                         ["A", "A", "A", "B", "B", "C"])

        self.assertEqual(self.game_room.RemoveContent("A"), "A")
        self.assertEqual(self.game_room.contents, ["A", "A", "B", "B", "C"])

        self.assertEqual(self.game_room.RemoveContent("C"), "C")
        self.assertEqual(self.game_room.RemoveContent("C"), None)
        self.assertEqual(self.game_room.contents, ["A", "A", "B", "B"])

        self.assertEqual(self.game_room.RemoveContent("B"), "B")
        self.assertEqual(self.game_room.contents, ["A", "A", "B"])

        self.assertEqual(self.game_room.RemoveContent("A"), "A")
        self.assertEqual(self.game_room.RemoveContent("A"), "A")
        self.assertEqual(self.game_room.RemoveContent("A"), None)
        self.assertEqual(self.game_room.contents, ["B"])
        self.game_room.AddContent("A")
        self.assertEqual(self.game_room.contents, ["A", "B"])
        self.assertEqual(self.game_room.RemoveContent("A"), "A")
        self.assertEqual(self.game_room.RemoveContent("B"), "B")
        self.assertEqual(self.game_room.RemoveContent("B"), None)

    def test_display_content(self):
        self.game_room.state = 0
        self.game_room.AddContent("C")
        self.assertEqual(self.game_room.GetContentsDisplay(), ["1xC"])
        self.game_room.AddContent("A")
        self.assertEqual(self.game_room.GetContentsDisplay(), ["1xA", "1xC"])
        self.game_room.AddContent("B")
        self.assertEqual(self.game_room.GetContentsDisplay(),
                         ["1xA", "1xB", "1xC"])
        self.game_room.AddContent("A")
        self.assertEqual(self.game_room.GetContentsDisplay(),
                         ["2xA", "1xB", "1xC"])
        self.game_room.AddContent("B")
        self.assertEqual(self.game_room.GetContentsDisplay(),
                         ["2xA", "2xB", "1xC"])
        self.game_room.AddContent("A")
        self.assertEqual(self.game_room.GetContentsDisplay(),
                         ["3xA", "2xB", "1xC"])
        self.assertEqual(self.game_room.DebugInfo(),
                         ["STATE: 0", "CONTENTS: [3xA, 2xB, 1xC]"])
        self.assertEqual(self.game_room.RemoveContent("C"), "C")
        self.assertEqual(self.game_room.RemoveContent("C"), None)
        self.assertEqual(self.game_room.GetContentsDisplay(), ["3xA", "2xB"])
        self.assertEqual(self.game_room.RemoveContent("A"), "A")
        self.assertEqual(self.game_room.RemoveContent("A"), "A")
        self.assertEqual(self.game_room.RemoveContent("A"), "A")
        self.assertEqual(self.game_room.RemoveContent("A"), None)
        self.assertEqual(self.game_room.GetContentsDisplay(), ["2xB"])
        self.assertEqual(self.game_room.RemoveContent("B"), "B")
        self.assertEqual(self.game_room.RemoveContent("B"), "B")
        self.assertEqual(self.game_room.GetContentsDisplay(), [])
        self.assertEqual(self.game_room.DebugInfo(),
                         ["STATE: 0", "CONTENTS: []"])

    def test_change_state(self):
        self.game_room.state = 0

        self.assertTrue(self.game_room.TryChangeState(1))
        self.assertEqual(self.game_room.state, 1)

        self.assertFalse(self.game_room.TryChangeState(1))
        self.assertEqual(self.game_room.state, 1)


class TestRoomAtomicity(unittest.TestCase):
    """Table-driven checks: failed mutations roll back fully, do not pollute
    later operations, and produce order-independent deterministic results."""

    def setUp(self):
        self.game_room = my_game_room.Room()
        self.game_room.state = 0

    def test_add_content_failure_rolls_back(self):
        cases = [
            ("empty room", []),
            ("single item", ["A"]),
            ("multiple items", ["B", "A", "C"]),
        ]
        for label, initial in cases:
            with self.subTest(label=label):
                self.game_room.contents = list(initial)
                snapshot = copy.deepcopy(self.game_room.contents)
                with self.assertRaises(AttributeError):
                    self.game_room.AddContent(_BrokenContent())
                self.assertEqual(self.game_room.contents, snapshot)

    def test_failed_add_does_not_pollute_later_adds(self):
        cases = [
            ("from empty", [], ("C",), ["C"]),
            ("from non-empty", ["B", "A"], ("C", "A2"),
             ["A", "A2", "B", "C"]),
        ]
        for label, initial, later_adds, expected in cases:
            with self.subTest(label=label):
                self.game_room.contents = list(initial)
                with self.assertRaises(AttributeError):
                    self.game_room.AddContent(_BrokenContent())
                for item in later_adds:
                    self.game_room.AddContent(item)
                self.assertEqual(self.game_room.contents, expected)

    def test_contents_setter_sorts_and_is_atomic(self):
        cases = [
            ("already sorted", ["A", "B"], ["A", "B"]),
            ("reverse order", ["C", "B", "A"], ["A", "B", "C"]),
            ("duplicates", ["B", "A", "B", "A"], ["A", "A", "B", "B"]),
        ]
        for label, given, expected in cases:
            with self.subTest(label=label):
                self.game_room.contents = list(given)
                self.assertEqual(self.game_room.contents, expected)
        with self.subTest(label="failed setter keeps old contents"):
            self.game_room.contents = ["A"]
            snapshot = copy.deepcopy(self.game_room.contents)
            with self.assertRaises(AttributeError):
                self.game_room.contents = ["B", _BrokenContent()]
            self.assertEqual(self.game_room.contents, snapshot)

    def test_display_independent_of_insertion_order(self):
        cases = [
            ["A", "A", "B", "B", "C"],
            ["C", "B", "B", "A", "A"],
            ["B", "A", "C", "A", "B"],
        ]
        displays = []
        for given in cases:
            with self.subTest(given=given):
                room = my_game_room.Room()
                room.state = 0
                room.contents = list(given)
                displays.append((room.GetContentsDisplay(), room.DebugInfo()))
                self.assertEqual(displays[-1], displays[0])

    def test_game_items_sorted_by_sort_id(self):
        cases = [
            ["charcoal", "apple", "broom"],
            ["broom", "charcoal", "apple"],
        ]
        for names in cases:
            with self.subTest(names=names):
                room = my_game_room.Room()
                for name in names:
                    item = my_game_item.GameItem()
                    item.name = name
                    room.AddContent(item)
                self.assertEqual([i.name for i in room.contents],
                                 ["apple", "broom", "charcoal"])


class TestRoomStateMapperSnapshots(unittest.TestCase):
    """Deep-copy snapshot checks: stored descriptions cannot be clobbered
    through shared references, re-adds, or mutated return values."""

    def setUp(self):
        self.room_states = my_game_room.RoomStateMapper()

    def test_add_state_stores_snapshot(self):
        cases = [
            ("single desc", 0, ["clean"]),
            ("multi desc", 1, ["dark", "dusty"]),
        ]
        for label, sid, desc in cases:
            with self.subTest(label=label):
                snapshot = copy.deepcopy(desc)
                self.room_states.AddState(sid, desc)
                desc.append("MUTATED")
                desc[0] = "CLOBBERED"
                self.assertEqual(self.room_states.GetState(sid), snapshot)

    def test_get_state_returns_snapshot(self):
        cases = [0, 1]
        for sid in cases:
            with self.subTest(sid=sid):
                self.room_states.AddState(sid, ["original"])
                returned = self.room_states.GetState(sid)
                returned.append("MUTATED")
                returned[0] = "CLOBBERED"
                self.assertEqual(self.room_states.GetState(sid), ["original"])

    def test_readd_does_not_clobber_previous_snapshot(self):
        self.room_states.AddState(0, ["old"])
        first = self.room_states.GetState(0)
        self.room_states.AddState(0, ["new"])
        self.assertEqual(first, ["old"])
        self.assertEqual(self.room_states.GetState(0), ["new"])

    def test_shared_desc_list_stays_independent(self):
        desc = ["shared"]
        self.room_states.AddState(0, desc)
        self.room_states.AddState(1, desc)
        desc.append("MUTATED")
        self.assertEqual(self.room_states.GetState(0), ["shared"])
        self.assertEqual(self.room_states.GetState(1), ["shared"])
        self.room_states.GetState(0).append("MUTATED")
        self.assertEqual(self.room_states.GetState(1), ["shared"])

    def test_default_state_snapshot(self):
        default = ["default desc"]
        self.room_states.default_state = default
        default.append("MUTATED")
        self.assertEqual(self.room_states.GetState(999), ["default desc"])
        self.room_states.GetState(999).append("MUTATED")
        self.assertEqual(self.room_states.GetState(999), ["default desc"])


class TestRoomStateMapper(unittest.TestCase):

    def setUp(self):
        self.room_states = my_game_room.RoomStateMapper()

    def test_add_state(self):
        self.room_states.AddState(0, "Everything's fine.")
        self.assertEqual(len(self.room_states.all_states), 1)
        self.room_states.AddState(1, "Room is on fire!")
        self.assertEqual(len(self.room_states.all_states), 2)
        self.room_states.AddState(0, "Everything's OK!")
        self.assertEqual(len(self.room_states.all_states), 2)

    def test_get_state(self):
        self.room_states.AddState(0, "Everything's fine.")
        self.room_states.AddState(1, "Room is on fire!")
        self.room_states.AddState(0, "Everything's OK!")
        self.assertEqual(self.room_states.GetState(0), "Everything's OK!")
        self.assertEqual(self.room_states.GetState(1), "Room is on fire!")


if __name__ == '__main__':
    unittest.main()
