# -*- coding: utf-8 -*-

"""
Class stores King on the board

| rank
| 7 8 ║♜ ♞ ♝ ♛ ♚ ♝ ♞ ♜
| 6 7 ║♟ ♟ ♟ ♟ ♟ ♟ ♟ ♟
| 5 6 ║… … … … … … … …
| 4 5 ║… … … … … … … …
| 3 4 ║… … … … … … … …
| 2 3 ║… … … … … … … …
| 1 2 ║♙ ♙ ♙ ♙ ♙ ♙ ♙ ♙
| 0 1 ║♖ ♘ ♗ ♕ ♔ ♗ ♘ ♖
| ----╚═══════════════
| ——---a b c d e f g h
| -----0 1 2 3 4 5 6 7
| ------file

| Copyright © 2016 Aubhro Sengupta. All rights reserved.
"""

import math
import itertools
from copy import copy

from .piece import Piece
from .rook import Rook
from ..core.algebraic import notation_const
from ..core.algebraic.location import Location
from ..core.algebraic.move import Move


class King(Piece):
    def __init__(self, input_color, location):
        """
        Creates a King.

        :type: input_color: Color
        :type: location: Location
        """
        super(King, self).__init__(input_color, location, "♚", "♔")
        self.has_moved = False
        self.cardinal_directions = self.cross_fn + self.diag_fn

    def __str__(self):
        return "K"

    def in_check_as_result(self, pos, move):
        """
        Finds if playing my move would make both kings meet.

        :type: pos: Board
        :type: move: Move
        :rtype: bool
        """
        test = copy(pos)
        test.update(move)
        test_king = test.get_king(move.color)

        return self.loc_adjacent_to_opponent_king(test_king.location, test)

    def loc_adjacent_to_opponent_king(self, location, position):
        """
        Finds if 2 kings are touching given the position of one of the kings.

        :type: location: Location
        :type: position: Board
        :rtype: bool
        """
        for fn in self.cardinal_directions:
            if fn(location).on_board() and \
                    isinstance(position.piece_at_square(fn(location)), King) and \
                    position.piece_at_square(fn(location)).color != self.color:
                return True

        return False

    def add(self, function, position):
        if function(self.location).on_board():

            loc_adj_in_check = self.loc_adjacent_to_opponent_king(function(self.location), position)

            if position.is_square_empty(function(self.location)) and not loc_adj_in_check:
                yield Move(end_loc=function(self.location),
                            piece=self,
                            status=notation_const.MOVEMENT,
                            start_rank=self.location.rank,
                            start_file=self.location.file)

            if not position.is_square_empty(function(self.location)) and \
                    position.piece_at_square(function(self.location)).color != self.color and \
                    not isinstance(position.piece_at_square(function(self.location)), King) and \
                    not loc_adj_in_check:
                yield Move(end_loc=function(self.location),
                        piece=self,
                        status=notation_const.CAPTURE,
                        start_rank=self.location.rank,
                        start_file=self.location.file)

    def square_empty_and_not_in_check(self, position, direction, times):
        """
        Checks if set of squares in between ``King`` and ``Rook`` are empty and safe
        for the king to castle.

        :type: position: Position
        :type: direction: function
        :type: times: int
        :rtype: bool
        """
        location = direction(self.location)

        for _ in range(times):

            if not position.is_square_empty(location):
                return False

            position.place_piece_at_square(King(self.color, location), location)
            in_check = position.piece_at_square(location).in_check(position)
            position.remove_piece_at_square(location)

            if in_check:
                return False

            location = direction(location)

        return True

    def rook_legal_for_castle(self, rook):
        """
        Decides if given rook exists, is off this color, and has not moved so it
        is eligible to castle.

        :type: rook: Rook
        :rtype: bool
        """
        return rook is not None and \
         isinstance(rook, Rook) and \
       rook.color == self.color and \
                   not rook.has_moved

    def add_castle(self, position):
        """
        Adds kingside and queenside castling moves if legal

        :type: position: Board
        """
        if self.has_moved or self.in_check(position):
            return []

        moves = []
        rook = position.piece_at_square(Location(self.location.rank, 7))

        if self.rook_legal_for_castle(rook) and \
                self.square_empty_and_not_in_check(position, lambda x: x.shift_right(), 2):
            moves.append(Move(end_loc=self.location.shift_right().shift_right(),
                              piece=self,
                              status=notation_const.KING_SIDE_CASTLE,
                              start_rank=self.location.rank,
                              start_file=self.location.file))

        rook = position.piece_at_square(Location(self.location.rank, 0))
        if self.rook_legal_for_castle(rook) and self.square_empty_and_not_in_check(position, lambda x: x.shift_left(), 3):
            moves.append(Move(end_loc=self.location.shift_left().shift_left(),
                              piece=self,
                              status=notation_const.QUEEN_SIDE_CASTLE,
                              start_rank=self.location.rank,
                              start_file=self.location.file))

        return moves

    def possible_moves(self, position):
        """
        Generates list of possible moves

        :type: position: Board
        :rtype: list
        """
        # Chain used to combine multiple generators
        for move in itertools.chain(*[self.add(fn, position) for fn in self.cardinal_directions]):
            yield move

        for move in self.add_castle(position):
            yield move

    def in_check(self, position):
        """
        Finds if the king is in check or if both kings are touching.

        :type: position: Board
        :return: bool
        """
        for piece in position:

            if piece is not None and piece.color != self.color:
                if isinstance(piece, King):
                    x = math.fabs(piece.location.file - self.location.file)
                    y = math.fabs(piece.location.rank - self.location.rank)

                    if x <= 1 and y <= 1:
                        return True

                    continue

                for move in piece.possible_moves(position):

                    if move.end_loc == self.location:
                        return True
        return False
