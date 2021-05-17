import logging
import itertools

from sigmar.board import Element


class Action(object):
    def do(self, board):
        raise NotImplementedError


class RemoveSingle(Action):
    def __init__(self, h):
        self.h = h

    def do(self, board):
        board.take(self.h)


class RemovePair(Action):
    def __init__(self, h1, h2):
        self.h1 = h1
        self.h2 = h2

    def do(self, board):
        board.take(self.h1)
        board.take(self.h2)


class RemoveFive(Action):
    def __init__(self, h1, h2, h3, h4, h5):
        self.h1 = h1
        self.h2 = h2
        self.h3 = h3
        self.h4 = h4
        self.h5 = h5

    def do(self, board):
        board.take(self.h5)
        board.take(self.h1)
        board.take(self.h2)
        board.take(self.h3)
        board.take(self.h4)


def find_metals(board, open_elements):
    live_metals = {e: h for h, e in board.tiles if e in Element.Metals}
    if not live_metals:
        return

    lowest_metal = sorted(live_metals.keys())[0]
    lowest_metal_hex = live_metals[lowest_metal]
    if lowest_metal_hex not in open_elements:
        return

    if lowest_metal is Element.GOLD:
        yield RemoveSingle(lowest_metal_hex)
    else:
        for h, e in open_elements.items():
            if e is Element.QUICKSILVER:
                yield RemovePair(lowest_metal_hex, h)


def match_mors_vitae(board, open_elements):
    for h1, e1 in open_elements.items():
        if e1 is Element.MORS:
            for h2, e2 in open_elements.items():
                if e2 is Element.VITAE:
                    yield RemovePair(h1, h2)


def match_pairs(board, open_elements):
    cardinal_pairs = itertools.combinations(((h, e) for h, e in open_elements.items() if e in Element.Cardinals), 2)
    for (h1, e1), (h2, e2) in cardinal_pairs:
        if e1 == e2:
            yield RemovePair(h1, h2)

    salt_pairs = itertools.combinations((h for h, e in open_elements.items() if e is Element.SALT), 2)
    for h1, h2 in salt_pairs:
        yield RemovePair(h1, h2)


def match_cardinal_with_salt(board, open_elements):
    pairs = itertools.combinations(((h, e) for h, e in open_elements.items() if e in Element.Cardinals or e is Element.SALT), 2)
    for (h1, e1), (h2, e2) in pairs:
        if e1 is not Element.SALT and e2 is Element.SALT:
            yield RemovePair(h1, h2)


def match_cardinals_with_quintessence(board, open_elements):
    quintessences = [(h, e) for h, e in open_elements.items() if e is Element.QUINTESSENCE]
    if not quintessences:
        return
    cardinal_quadruplets = itertools.combinations(((h, e) for h, e in open_elements.items() if e in Element.Cardinals), 4)
    for (h5, e5) in quintessences:
        for (h1, e1), (h2, e2), (h3, e3), (h4, e4) in cardinal_quadruplets:
            if e1 is Element.AIR and e2 is Element.FIRE and e3 is Element.WATER and e4 is Element.EARTH:
                yield RemoveFive(h1, h2, h3, h4, h5)
        


ACTION_FACTORIES = [
    find_metals,
    match_mors_vitae,
    match_pairs,
    match_cardinal_with_salt,
    match_cardinals_with_quintessence,
]


class UnsolveableBoardError(Exception):
    pass


def solve_game(board):
    return _solve_game(board, set())


def _solve_game(board, seen_states):
    live_elements = [(h, e) for h, e in board.tiles if e is not None]
    if not live_elements:
        return []

    open_elements = {h: e for h, e in live_elements if board.is_open(h)}
    if not open_elements:
        raise UnsolveableBoardError

    for action_factory in ACTION_FACTORIES:
        for action in action_factory(board, open_elements):
            new_board = board.clone()
            action.do(new_board)

            if hash(new_board) in seen_states:
                continue

            try:
                return [action] + _solve_game(new_board, seen_states)
            except UnsolveableBoardError:
                seen_states.add(hash(new_board))

    raise UnsolveableBoardError
