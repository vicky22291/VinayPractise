"""
URL: https://leetcode.com/problems/bus-routes/
"""
from collections import defaultdict, deque
from typing import List


class Solution:
    def numBusesToDestination(self, routes: List[List[int]], source: int, target: int) -> int:
        """
        @lru_cache
        def isStopInRoute(route_index, stop, n):
            nonlocal routes
            route = routes[route_index]
            i = bisect_left(route, stop)
            return i < n and route[i] == stop, i

        @lru_cache
        def getBusesForStop(stop):
            nonlocal routes
            ans = []
            for ri, route in enumerate(routes):
                n = len(route)
                isStopPresent, i = isStopInRoute(ri, stop, n)
                if isStopPresent:
                    ans.append((i, ri, n))
            return ans

        if source == target:
            return 0
        q, nq, seen = getBusesForStop(source), {}, set()

        if len(q) == 0:
            return -1
        nBusesTaken = 0
        while len(q):
            i, ri, n = q.pop()
            route = routes[ri]
            seen.add(route[i])
            cur = route[i % n]
            if isStopInRoute(ri, target, n)[0]:
                return nBusesTaken + 1
            for stop in route:
                if stop != cur and stop not in nq and stop not in seen:
                    nq[stop] = getBusesForStop(stop)
            if len(q) == 0:
                nBusesTaken += 1
                for val in nq.values():
                    q.extend(val)
                nq = {}
        return -1
        """
        """
        possibleWith1Bus = defaultdict(set)
        for route in routes:
            for stop in route:
                for next_stop in route:
                    if next_stop != stop:
                        possibleWith1Bus[stop].add(next_stop)
        if source == target:
            return 0
        if source not in possibleWith1Bus:
            return -1
        q, nq, seen = [source], set(), set()
        nBusesTaken = 0
        while len(q):
            cStop = q.pop()
            seen.add(cStop)
            if target in possibleWith1Bus[cStop]:
                return nBusesTaken + 1
            nq.union(possibleWith1Bus[cStop] - seen)
            if len(q) == 0:
                q = list(nq)
                nq.clear()
                nBusesTaken += 1
        return -1
        """
        # Build a graph where each stop is associated with the buses that pass through it
        stop_to_buses = defaultdict(list)

        for bus_id, route in enumerate(routes):
            for stop in route:
                stop_to_buses[stop].append(bus_id)

        # Check if source and target stops are in the graph
        if source not in stop_to_buses or target not in stop_to_buses:
            return -1

        # If the source and target are the same stop, no buses are needed
        if source == target:
            return 0

        # Use BFS to find the minimum number of buses to reach the target stop
        queue = deque([source])
        buses_taken = set()
        stops_visited = set()
        res = 0

        while queue:
            # Increment the res for each level of stops
            res += 1
            stops_to_process = len(queue)

            for _ in range(stops_to_process):
                current_stop = queue.popleft()

                # Check buses passing through the current stop
                for bus_id in stop_to_buses[current_stop]:
                    if bus_id in buses_taken:
                        continue

                    buses_taken.add(bus_id)

                    # Check stops reachable from the current bus
                    for next_stop in routes[bus_id]:
                        if next_stop in stops_visited:
                            continue

                        # If the target is reached, return the res
                        if next_stop == target:
                            return res

                        # Add the next stop to the queue and mark it as visited
                        queue.append(next_stop)
                        stops_visited.add(next_stop)

        # If no valid route is found
        return -1