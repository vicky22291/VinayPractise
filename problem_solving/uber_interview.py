# Problem statement
"""
Given an array of integers, and an integer N, find the length of the longest “N-stable” continuous subarray. An array is defined to be “N-stable” when the pair-wise difference between any two elements in the array is smaller or equal to N. A subarray of a 0-indexed integer array is a contiguous non-empty sequence of elements within an array.

For instance, for array [ 4, 2, 3, 6, 2, 2, 3, 2, 7 ], and N = 1
The return value should be 4, since the longest 1-stable subarray is [ 2, 2, 3, 2].

[4, 2, 2, 2, 4, 4, 2, 2] N = 0
[10, 1, 2, 4, 7, 2] N = 5
[4, 8, 5, 1, 7, 9] N = 6
[1, 5, 2, 6, 7, 8, 10, 6, 5, 6] N = 4

Naive:
1. Length = N -> 1
2. Start from in N - 1 -> L
3. Find differences and if max < N then return the L

n^2 * n^2 = O(n^4)

mins = [(4, 0), (2, 1), (2, 1), (2, 1), (2, 1), (2, 1), (2, 1), (2, 1), (2, 1)]

index < start
maxs = [4, 4, 4, 6, 6, 6, 6, 6, 7]

min_element = 4
min_index = 0

[ 4, 2, 3, 6, 2, 2, 3, 2, 7 ]

ws = 0, 1, 2, 3, 4, 5, 6,
we = 0, 1, 2, 3, 4, 5, 6, 7, 8

min_index = 0, 1, 2, 3, 4, 5,
max_index = 0, 1, 2, 3, 4, 6, 8

max_length = 1, 1, 2, 3, 4

if min_index < start:
    con

4 - 4 = 0
4 - 2 = 2

start = 0
end = 0
window_max = 4
window_min = 4
max_length = 1

start = 0
end = 1
window_max = 4
window_min = 2 > N
start += 1

start = 1
end = 2 + 1
window_max = 6
window_min = 2 >= N
max_length = 2
start += 1

start = 1 + 1
end = 2 + 1
window_max = 6
window_min = 2 >= N
max_length = 2
start += 1

heapify = O(n)
n * n = n^2
heapupdate = O(logn)

sorted doubly linked list - insert O(n)
map = element, node - O(1)
"""

def get_max_continuous_length(arr, n):
    if len(arr) == 0:
        return 0
    larr = len(arr)
    ws = we = 0
    min_index = max_index = 0
    max_length = 0
    while ws <= we < larr :
        if min_index < ws:
            min_index = ws
            for index, ele in enumerate(arr[ws: (we + 1)]):
                if ele <= arr[min_index]:
                    min_index = ws + index
        if max_index < ws:
            max_index = ws
            for index, ele in enumerate(arr[ws: (we + 1)]):
                if ele >= arr[max_index]:
                    max_index = ws + index
        if arr[max_index] - arr[min_index] <= n:
            max_length = max(max_length, we - ws + 1)
            we += 1
            if we < larr:
                if arr[min_index] >= arr[we]:
                    min_index = we
                if arr[max_index] <= arr[we]:
                    max_index = we
        else:
            ws = max(min(min_index, max_index), ws + 1)
            if ws > we:
                we = ws
    return max_length

test_cases = [
    # [[ 4, 2, 3, 6, 2, 2, 3, 2, 7 ], 1],
    # [[4, 2, 2, 2, 4, 4, 2, 2], 0],
    # [[10, 1, 2, 4, 7, 2], 5],
    # [[4, 8, 5, 1, 7, 9], 6],
    # [[1, 5, 2, 6, 7, 8, 10, 6, 5, 6], 4],
    # [[34,24,70,27,40,26,32,47,11,36,12,97,58,12,84,74,83,44,30,50,40,6,42,24,41,75,39,32,43,13,70,79,75,77,12,32,29,3,32,52,10,35,71,10,94,10,3,82,2,38,97,46,64,61,20,13,65,100,42,10,66,86,23,23,100,20,19,41,40,14,91,66,78,38,17,27,19,70,93,5,100,41,80,87,71,96,89,27,23,39,56,69], 72],
]

for arr, n in test_cases:
    print(get_max_continuous_length(arr, n))