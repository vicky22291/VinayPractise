'''
Build a 2-dimensional representation of terrain that can represent with some land and water parts.

Part 1: We need a data-structure to efficiently represent this in-memory. We need the following two functions to be efficient:

# isLand(x, y): returns true if a point is a land
# addLand(x, y): sets a point to land

PART 2
Part 2: Extend the data-structure to add a method for getIslands() which returns the number of unique connected components of lands

Assumptions
Assume everything is water at the beginning.
Only 2 types of points can exist (land or water).

EXAMPLE
. . . . X .
X . . . X .
X X X . . .
. . . . . .

getIslands() == 2
'''


class LandAndWater:
    def __init__(self):
        self.isLands = []  ## Will be a list of Islands and each index will be used for getting the islands
        self.landToIslands = {}

    # O(n) n - number of islands seen so far.
    def addLand(self, x, y):
        for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
            adjX, adjY = x + dx, y + dy
            if (x, y) not in self.landToIslands:
                # print(f'{(x, y)} is not lands')
                if (adjX, adjY) in self.landToIslands:
                    ### Merging with an existing island
                    adjIslandIndex = self.landToIslands[(adjX, adjY)]
                    adjIsland = self.isLands[adjIslandIndex][0]
                    adjIsland.add((x, y))
                    self.landToIslands[(x, y)] = adjIslandIndex
                else:
                    ### Creating a new island
                    newIsland = set()
                    newIsland.add((x, y))
                    self.isLands.append([newIsland])
                    self.landToIslands[(x, y)] = len(self.isLands) - 1
            elif (adjX, adjY) in self.landToIslands:
                # print(f'Adjacent Island is present')
                ### Merging 2 islands if they are existing.
                curIslandIndex = self.landToIslands[(x, y)]
                adjIslandIndex = self.landToIslands[(adjX, adjY)]
                curIsland = self.isLands[curIslandIndex][0]
                adjIsland = self.isLands[adjIslandIndex][0]

                ### Tombstoning the curIslandIndex
                self.isLands[curIslandIndex].append(True)

                ## Adding all lands of curIsland to adjIsland can use set union or bulk operation.
                for lx, ly in curIsland:
                    adjIsland.add((lx, ly))
                    self.landToIslands[(lx, ly)] = adjIslandIndex

    # O(1)
    def isLand(self, x, y):
        return (x, y) in self.landToIslands

    # O(n) can be optimised to O(1) by adding a counter and updating during remove
    def getIslands(self):
        count = 0
        for value in self.isLands:
            if len(value) == 2 and value[1]:
                continue
            count += 1
        return count


lw = LandAndWater()

lw.addLand(2, 1)
print(f'Number of Islands: {lw.getIslands()}')
lw.addLand(2, 2)
print(f'Number of Islands: {lw.getIslands()}')
lw.addLand(0, 4)
# print(lw.isLand(0, 4))
print(f'Number of Islands: {lw.getIslands()}')
lw.addLand(1, 0)
print(f'Number of Islands: {lw.getIslands()}')
lw.addLand(1, 4)
print(f'Number of Islands: {lw.getIslands()}')
lw.addLand(2, 0)
print(f'Number of Islands: {lw.getIslands()}')
# print(f'Is Land: {lw.isLand(2, 2)}')
# print(f'Is Land: lw.isLand(1, 0)')
# print(f'Is Land: lw.isLand(7, 0)')
lw.addLand(3, 5)
print(f'Number of Islands: {lw.getIslands()}')