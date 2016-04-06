# Copied from http://mcts.ai/code/python.html

# This is a very simple implementation of the UCT Monte Carlo Tree Search algorithm in Python 2.7.
# The function UCT(rootstate, itermax, verbose = False) is towards the bottom of the code.
# It aims to have the clearest and simplest possible code, and for the sake of clarity, the code
# is orders of magnitude less efficient than it could be made, particularly by using a
# state.GetRandomMove() or state.DoRandomRollout() function.
#
# Example GameState classes for Nim, OXO and Othello are included to give some idea of how you
# can write your own GameState use UCT in your 2-player game. Change the game to be played in
# the UCTPlayGame() function at the bottom of the code.
#
# Written by Peter Cowling, Ed Powley, Daniel Whitehouse (University of York, UK) September 2012.
#
# Licence is granted to freely use and distribute for any sensible/legal purpose so long as this comment
# remains in any distributed code.
#
# For more information about Monte Carlo Tree Search check out our web site at www.mcts.ai

from math import *
import random

class GameState:
    """ A state of the game, i.e. the game board. These are the only functions which are
        absolutely necessary to implement UCT in any 2-player complete information deterministic
        zero-sum game, although they can be enhanced and made quicker, for example by using a
        GetRandomMove() function to generate a random move during rollout.
        By convention the players are numbered 1 and 2.
    """
    def __init__(self):
        self.playerJustMoved = 2 # At the root pretend the player just moved is player 2 - player 1 has the first move

    def Clone(self):
        """ Create a deep clone of this game state.
        """
        st = GameState()
        st.playerJustMoved = self.playerJustMoved
        return st

    def DoMove(self, move):
        """ Update a state by carrying out the given move.
            Must update playerJustMoved.
        """
        self.playerJustMoved = 3 - self.playerJustMoved

    def GetMoves(self):
        """ Get all possible moves from this state.
        """

    def GetResult(self, playerjm):
        """ Get the game result from the viewpoint of playerjm.
        """

    def __repr__(self):
        """ Don't need this - but good style.
        """
        pass


class NimState:
    """ A state of the game Nim. In Nim, players alternately take 1,2 or 3 chips with the
        winner being the player to take the last chip.
        In Nim any initial state of the form 4n+k for k = 1,2,3 is a win for player 1
        (by choosing k) chips.
        Any initial state of the form 4n is a win for player 2.
    """
    def __init__(self, ch):
        self.playerJustMoved = 2 # At the root pretend the player just moved is p2 - p1 has the first move
        self.chips = ch

    def Clone(self):
        """ Create a deep clone of this game state.
        """
        st = NimState(self.chips)
        st.playerJustMoved = self.playerJustMoved
        return st

    def DoMove(self, move):
        """ Update a state by carrying out the given move.
            Must update playerJustMoved.
        """
        assert move >= 1 and move <= 3 and move == int(move)
        self.chips -= move
        self.playerJustMoved = 3 - self.playerJustMoved

    def GetMoves(self):
        """ Get all possible moves from this state.
        """
        return range(1,min([4, self.chips + 1]))

    def GetResult(self, playerjm):
        """ Get the game result from the viewpoint of playerjm.
        """
        assert self.chips == 0
        if self.playerJustMoved == playerjm:
            return 1.0 # playerjm took the last chip and has won
        else:
            return 0.0 # playerjm's opponent took the last chip and has won

    def __repr__(self):
        s = "Chips:" + str(self.chips) + " JustPlayed:" + str(self.playerJustMoved)
        return s

class OXOState:
    """ A state of the game, i.e. the game board.
        Squares in the board are in this arrangement
        012
        345
        678
        where 0 = empty, 1 = player 1 (X), 2 = player 2 (O)
    """
    def __init__(self):
        self.playerJustMoved = 2 # At the root pretend the player just moved is p2 - p1 has the first move
        self.board = [0,0,0,0,0,0,0,0,0] # 0 = empty, 1 = player 1, 2 = player 2

    def Clone(self):
        """ Create a deep clone of this game state.
        """
        st = OXOState()
        st.playerJustMoved = self.playerJustMoved
        st.board = self.board[:]
        return st

    def DoMove(self, move):
        """ Update a state by carrying out the given move.
            Must update playerToMove.
        """
        assert move >= 0 and move <= 8 and move == int(move) and self.board[move] == 0
        self.playerJustMoved = 3 - self.playerJustMoved
        self.board[move] = self.playerJustMoved

    def GetMoves(self):
        """ Get all possible moves from this state.
        """
        return [i for i in range(9) if self.board[i] == 0]

    def GetResult(self, playerjm):
        """ Get the game result from the viewpoint of playerjm.
        """
        for (x,y,z) in [(0,1,2),(3,4,5),(6,7,8),(0,3,6),(1,4,7),(2,5,8),(0,4,8),(2,4,6)]:
            if self.board[x] == self.board[y] == self.board[z]:
                if self.board[x] == playerjm:
                    return 1.0
                else:
                    return 0.0
        if self.GetMoves() == []: return 0.5 # draw
        assert False # Should not be possible to get here

    def __repr__(self):
        s= ""
        for i in range(9):
            s += ".XO"[self.board[i]]
            if i % 3 == 2: s += "\n"
        return s

class OthelloState:
    """ A state of the game of Othello, i.e. the game board.
        The board is a 2D array where 0 = empty (.), 1 = player 1 (X), 2 = player 2 (O).
        In Othello players alternately place pieces on a square board - each piece played
        has to sandwich opponent pieces between the piece played and pieces already on the
        board. Sandwiched pieces are flipped.
        This implementation modifies the rules to allow variable sized square boards and
        terminates the game as soon as the player about to move cannot make a move (whereas
        the standard game allows for a pass move).
    """
    def __init__(self,sz = 8):
        self.playerJustMoved = 2 # At the root pretend the player just moved is p2 - p1 has the first move
        self.board = [] # 0 = empty, 1 = player 1, 2 = player 2
        self.size = sz
        assert sz == int(sz) and sz % 2 == 0 # size must be integral and even
        for y in range(sz):
            self.board.append([0]*sz)
        self.board[sz/2][sz/2] = self.board[sz/2-1][sz/2-1] = 1
        self.board[sz/2][sz/2-1] = self.board[sz/2-1][sz/2] = 2

    def Clone(self):
        """ Create a deep clone of this game state.
        """
        st = OthelloState()
        st.playerJustMoved = self.playerJustMoved
        st.board = [self.board[i][:] for i in range(self.size)]
        st.size = self.size
        return st

    def DoMove(self, move):
        """ Update a state by carrying out the given move.
            Must update playerToMove.
        """
        (x,y)=(move[0],move[1])
        assert x == int(x) and y == int(y) and self.IsOnBoard(x,y) and self.board[x][y] == 0
        m = self.GetAllSandwichedCounters(x,y)
        self.playerJustMoved = 3 - self.playerJustMoved
        self.board[x][y] = self.playerJustMoved
        for (a,b) in m:
            self.board[a][b] = self.playerJustMoved

    def GetMoves(self):
        """ Get all possible moves from this state.
        """
        return [(x,y) for x in range(self.size) for y in range(self.size) if self.board[x][y] == 0 and self.ExistsSandwichedCounter(x,y)]

    def AdjacentToEnemy(self,x,y):
        """ Speeds up GetMoves by only considering squares which are adjacent to an enemy-occupied square.
        """
        for (dx,dy) in [(0,+1),(+1,+1),(+1,0),(+1,-1),(0,-1),(-1,-1),(-1,0),(-1,+1)]:
            if self.IsOnBoard(x+dx,y+dy) and self.board[x+dx][y+dy] == self.playerJustMoved:
                return True
        return False

    def AdjacentEnemyDirections(self,x,y):
        """ Speeds up GetMoves by only considering squares which are adjacent to an enemy-occupied square.
        """
        es = []
        for (dx,dy) in [(0,+1),(+1,+1),(+1,0),(+1,-1),(0,-1),(-1,-1),(-1,0),(-1,+1)]:
            if self.IsOnBoard(x+dx,y+dy) and self.board[x+dx][y+dy] == self.playerJustMoved:
                es.append((dx,dy))
        return es

    def ExistsSandwichedCounter(self,x,y):
        """ Does there exist at least one counter which would be flipped if my counter was placed at (x,y)?
        """
        for (dx,dy) in self.AdjacentEnemyDirections(x,y):
            if len(self.SandwichedCounters(x,y,dx,dy)) > 0:
                return True
        return False

    def GetAllSandwichedCounters(self, x, y):
        """ Is (x,y) a possible move (i.e. opponent counters are sandwiched between (x,y) and my counter in some direction)?
        """
        sandwiched = []
        for (dx,dy) in self.AdjacentEnemyDirections(x,y):
            sandwiched.extend(self.SandwichedCounters(x,y,dx,dy))
        return sandwiched

    def SandwichedCounters(self, x, y, dx, dy):
        """ Return the coordinates of all opponent counters sandwiched between (x,y) and my counter.
        """
        x += dx
        y += dy
        sandwiched = []
        while self.IsOnBoard(x,y) and self.board[x][y] == self.playerJustMoved:
            sandwiched.append((x,y))
            x += dx
            y += dy
        if self.IsOnBoard(x,y) and self.board[x][y] == 3 - self.playerJustMoved:
            return sandwiched
        else:
            return [] # nothing sandwiched

    def IsOnBoard(self, x, y):
        return x >= 0 and x < self.size and y >= 0 and y < self.size

    def GetResult(self, playerjm):
        """ Get the game result from the viewpoint of playerjm.
        """
        jmcount = len([(x,y) for x in range(self.size) for y in range(self.size) if self.board[x][y] == playerjm])
        notjmcount = len([(x,y) for x in range(self.size) for y in range(self.size) if self.board[x][y] == 3 - playerjm])
        if jmcount > notjmcount: return 1.0
        elif notjmcount > jmcount: return 0.0
        else: return 0.5 # draw

    def __repr__(self):
        s= ""
        for y in range(self.size-1,-1,-1):
            for x in range(self.size):
                s += ".XO"[self.board[x][y]]
            s += "\n"
        return s

class ZombieDiceState:
    def __init__(self):
        self.playerScores = [0,0,0]
        self.round = 0
        self.lastRound = False
        self.tiebreaker = False
        self.ended = False

        self.StartRound()

        self.playerJustMoved = 1

    def Clone(self):
        """ Create a deep clone of this game state.
        """
        st = ZombieDiceState()

        st.playerScores = self.playerScores[:]
        st.round = self.round
        st.lastRound = self.lastRound
        st.tiebreaker = self.tiebreaker
        st.ended = self.ended

        st.playerJustMoved = self.playerJustMoved

        st.score = self.score
        st.brains = self.brains[:]
        st.shotguns = self.shotguns[:]
        st.hand = self.hand[:]
        st.cup = self.cup[:]

        return st

    def DoMove(self, move):
        """ Update a state by carrying out the given move.
            Must update playerJustMoved.
        """
        if (self.ended):
            return

        assert len(self.shotguns) < 3

        if (move == "ROLL"):
            self.DoRollHand()

            if (len(self.shotguns) >= 3):
                self.EndRound()

        elif (move == "KEEP"):
            self.EndRound()

        else:
            assert False

    def GetMoves(self):
        """ Get all possible moves from this state.
        """
        if self.ended:
            return []

        if self.rollCount == 0:
            return ["ROLL"]

        return ["ROLL", "KEEP"]

    def GetResult(self, playerjm):
        """ Get the game result from the viewpoint of playerjm.
        """
        assert self.ended
        if self.playerScores[playerjm] > self.playerScores[3 - playerjm]:
            return 1.0
        elif self.playerScores[playerjm] < self.playerScores[3 - playerjm]:
            return 0.0
        else:
            return 0.5

    def StartRound(self):
        self.round += 1
        self.rollCount = 0
        self.score = 0
        self.brains = []
        self.shotguns = []
        self.hand = []
        self.cup = ["red"] * 3 + ["yellow"] * 4 + ["green"] * 6

    def EndRound(self):
        self.playerJustMoved = 3 - self.playerJustMoved

        if (len(self.shotguns) < 3):
            self.playerScores[self.playerJustMoved] += self.score

        if self.tiebreaker:
            self.ended = True

        if self.lastRound and self.playerJustMoved == 2:
            self.tiebreaker = self.playerScores[1] == self.playerScores[2] # TODO won't work with more than two players
            self.ended = not self.tiebreaker

        if self.playerScores[self.playerJustMoved] >= 13:
            # once a player reaches 13 brains, it becomes the last round
            self.lastRound = True

        self.StartRound()

    def DoRollHand(self):
        # "ran out of dice", so put the rolled brains back into the cup
        if 3 - len(self.hand) > len(self.cup):
            self.cup.extend(self.brains)
            self.brains = []

        # add new dice to hand from cup until there are 3 dice in the hand
        while len(self.hand) < 3:
            newDie = random.choice(self.cup)
            self.cup.remove(newDie)
            self.hand.append(newDie)

        self.rollCount += 1

        for die in self.hand[:]:
            result = self.DoRollDie(die)

            if result == "shotgun":
                self.shotguns.append(die)
                self.hand.remove(die)

            if result == "brains":
                self.score += 1
                self.brains.append(die)
                self.hand.remove(die)


    def DoRollDie(self, die):
        """Returns the result of a single die roll as a dictionary with keys 'color' and 'icon'.
        The die parameter is a string of the color of the die (i.e. 'green', 'yellow', 'red').
        The 'color' values in the return dict are one of 'green', 'yellow', 'red'.
        The 'icon' values are one of 'shotgun', 'footsteps', 'brains'."""
        roll = random.randint(1, 6)
        if die == "red":
            if roll in (1, 2, 3):
                return "shotgun"
            elif roll in (4, 5):
                return "footsteps"
            elif roll in (6,):
                return "brains"
        elif die == "yellow":
            if roll in (1, 2):
                return "shotgun"
            elif roll in (3, 4):
                return "footsteps"
            elif roll in (5, 6):
                return "brains"
        elif die == "green":
            if roll in (1,):
                return "shotgun"
            elif roll in (2, 3):
                return "footsteps"
            elif roll in (4, 5, 6):
                return "brains"

    def __repr__(self):
        """ Don't need this - but good style.
        """
        s = "Player: " + str(3 - self.playerJustMoved) + "\n"
        s += "My Score: " + str(self.playerScores[3 - self.playerJustMoved]) + "\n"
        s += "Their Score: " + str(self.playerScores[self.playerJustMoved]) + "\n"
        s += "Round: " + str(self.round) + "\n"
        s += "Round Score: " + str(self.score) + "\n"
        s += "Rolls: " + str(self.rollCount) + "\n"
        s += "Brains: [" + ",".join(self.brains) + "]\n"
        s += "Shotguns: [" + ",".join(self.shotguns) + "]\n"
        s += "Hand: [" + ",".join(self.hand) + "]\n"
        s += "Cup: [" + ",".join(self.cup) + "]\n"
        return s

class Node:
    """ A node in the game tree. Note wins is always from the viewpoint of playerJustMoved.
        Crashes if state not specified.
    """
    def __init__(self, move = None, parent = None, state = None):
        self.move = move # the move that got us to this node - "None" for the root node
        self.parentNode = parent # "None" for the root node
        self.childNodes = []
        self.wins = 0
        self.visits = 0
        self.untriedMoves = state.GetMoves() # future child nodes
        self.playerJustMoved = state.playerJustMoved # the only part of the state that the Node needs later

    def UCTSelectChild(self):
        """ Use the UCB1 formula to select a child node. Often a constant UCTK is applied so we have
            lambda c: c.wins/c.visits + UCTK * sqrt(2*log(self.visits)/c.visits to vary the amount of
            exploration versus exploitation.
        """
        s = sorted(self.childNodes, key = lambda c: c.wins/c.visits + sqrt(2*log(self.visits)/c.visits))[-1]
        return s

    def AddChild(self, m, s):
        """ Remove m from untriedMoves and add a new child node for this move.
            Return the added child node
        """
        n = Node(move = m, parent = self, state = s)
        self.untriedMoves.remove(m)
        self.childNodes.append(n)
        return n

    def Update(self, result):
        """ Update this node - one additional visit and result additional wins. result must be from the viewpoint of playerJustmoved.
        """
        self.visits += 1
        self.wins += result

    def __repr__(self):
        return "[M:" + str(self.move) + " W/V:" + str(self.wins) + "/" + str(self.visits) + " U:" + str(self.untriedMoves) + "]"

    def TreeToString(self, indent):
        s = self.IndentString(indent) + str(self)
        for c in self.childNodes:
             s += c.TreeToString(indent+1)
        return s

    def IndentString(self,indent):
        s = "\n"
        for i in range (1,indent+1):
            s += "| "
        return s

    def ChildrenToString(self):
        s = ""
        for c in self.childNodes:
             s += str(c) + "\n"
        return s


def UCT(rootstate, itermax, verbose = False):
    """ Conduct a UCT search for itermax iterations starting from rootstate.
        Return the best move from the rootstate.
        Assumes 2 alternating players (player 1 starts), with game results in the range [0.0, 1.0]."""

    rootnode = Node(state = rootstate)

    for i in range(itermax):
        node = rootnode
        state = rootstate.Clone()

        if (verbose):
            print "\tSelect stage"

        # Select
        while node.untriedMoves == [] and node.childNodes != []: # node is fully expanded and non-terminal
            node = node.UCTSelectChild()
            state.DoMove(node.move)

        if (verbose):
            print "\tExpand stage"

        # Expand
        if node.untriedMoves != []: # if we can expand (i.e. state/node is non-terminal)
            m = random.choice(node.untriedMoves)
            state.DoMove(m)
            node = node.AddChild(m,state) # add child and descend tree

        if (verbose):
            print "\tRollout stage"

        # Rollout - this can often be made orders of magnitude quicker using a state.GetRandomMove() function
        while state.GetMoves() != []: # while state is non-terminal
            state.DoMove(random.choice(state.GetMoves()))

        if (verbose):
            print "\tBackpropagate stage"

        # Backpropagate
        while node != None: # backpropagate from the expanded node and work back to the root node
            node.Update(state.GetResult(node.playerJustMoved)) # state is terminal. Update node with result from POV of node.playerJustMoved
            node = node.parentNode

    sortedChildren = sorted(rootnode.childNodes, key = lambda c: c.visits)

    # Output some information about the tree - can be omitted
    if (verbose):
        print rootnode.TreeToString(0)
    else:
        print rootnode.ChildrenToString()

    return sortedChildren[-1].move # return the move that was most visited

def UCTPlayGame():
    """ Play a sample game between two UCT players where each player gets a different number
        of UCT iterations (= simulations = tree nodes).
    """
    # state = OthelloState(6) # uncomment to play Othello on a square board of the given size
    # state = OXOState() # uncomment to play OXO
    # state = NimState(15) # uncomment to play Nim with the given number of starting chips
    state = ZombieDiceState()

    while (state.GetMoves() != []):
        print str(state)
        if state.playerJustMoved == 1:
            m = UCT(rootstate = state, itermax = 1, verbose = False) # play with values for itermax and verbose = True
        else:
            m = UCT(rootstate = state, itermax = 10, verbose = False)
        print "Best Move: " + str(m) + "\n"
        state.DoMove(m)
    if state.GetResult(state.playerJustMoved) == 1.0:
        print "Player " + str(state.playerJustMoved) + " wins!"
        return state.playerJustMoved
    elif state.GetResult(state.playerJustMoved) == 0.0:
        print "Player " + str(3 - state.playerJustMoved) + " wins!"
        return 3 - state.playerJustMoved
    else:
        print "Nobody wins!"
        return 0

if __name__ == "__main__":
    """ Play a single game to the end using UCT for both players.
    """

    results = [0,0,0]

    for i in range(100):
        winner = UCTPlayGame()
        results[winner] += 1

    print "results " + str(results)
