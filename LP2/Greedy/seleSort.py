# Selection Sort in Python

# Function for Selection Sort
def selection_sort(arr):

    n = len(arr)

    # Traverse through entire array
    for i in range(n):

        # Assume current index has minimum element
        min_index = i

        # Find smallest element in remaining array
        for j in range(i + 1, n):

            if arr[j] < arr[min_index]:
                min_index = j

        # Swap smallest element with current element
        arr[i], arr[min_index] = arr[min_index], arr[i]

    return arr


# Driver Code
arr = [64, 25, 12, 22, 11]
'''
Take input from user
n = int(input("Enter number of elements: "))
arr = []
for _ in range(n):
    arr.append(int(input("Enter element: ")))
'''
print("Original Array:")
print(arr)

selection_sort(arr)

print("\nSorted Array:")
print(arr)

#time complexity: O(n^2)
#space complexity: O(1)