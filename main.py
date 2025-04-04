#РАЗДЕЛ 1
#Задание 1.1. Работа с математическими операциями в Python

#Считать с клавиатуры три произвольных числа, найти минимальное среди них и вывести на экран.
# n1 = float(input("1 число: "))
# n2 = float(input("2 число: "))
# n3 = float(input("3 число:"))
# min = min(n1, n2, n3)
#
# print("Минимальное число:", int(min))

#Считать с клавиатуры три произвольных числа, вывести в консоль те числа, которые попадают в интервал [1, 50].
# n1 = float(input("1 число:"))
# n2 = float(input("2 число:"))
# n3 = float(input("3 число:"))
# num = [n1, n2, n3]
# for x in num:
#   if 1 <= x <= 50:
#     if x:
#       print(x, sep='')
#     else:
#         print('Нет чисел в диапазоне')


#Считать с клавиатуры вещественное число m. Посчитать и вывести в консоль каждый член последовательности:
# [(1 * m), (2 * m), (3 * m), ..., (10 * m)]. Решить задачу используя циклическую конструкцию for.
# m = float(input("Введите вещественное число m: "))
# for i in range(1, 11):
#     result = i * m
#     print(f"{i} * {m} = {result}")
#
#Считать с клавиатуры непустую произвольную последовательность
# x = input("Введите последовательность целых чисел через пробел: ")
# numbers = []
# number = ""
# for char in x:
#     if char.isdigit() or char == '-':
#         number += char
#     elif char == ' ':
#         if number:
#             numbers.append(int(number))
#             number = ""
# if number:
#     numbers.append(int(number))
# sum = 0
# index = 0
# while index < len(numbers):
#     sum += numbers[index]
#     index += 1
# count = 0
# index = 0
# while index < len(numbers):
#     count += 1
#     index += 1
#
# print(f"Сумма всех чисел: {sum}")
# print(f"Количество всех чисел: {count}")
# #
#
#РАЗДЕЛ 2.7
# #2.7
# x = input("Введите произвольную строку: ")
# count = 0
# new = ""
# space = -1
#
#
# for i in range(len(x)):
#     if x[i] == ' ':
#         space = i
#         break
#
# for i in range(len(x)):
#     if i < space or space == -1:
#         if x[i] == '!':
#             new += '%'
#             count += 1
#         else:
#             new += x[i]
#     else:
#         new += x[i]
#
# print("Новая строка:", new)
# print("Количество замененных символов:", count)
#
# #РАЗДЕЛ 3.
# #3.7
# numbers = input("Введите целые числа, разделенные пробелом: ")
# m = []
# number = ""
# for char in numbers:
#     if char.isdigit() or char == '-':
#         number += char
#     elif char == ' ' and number:
#         m.append(int(number))
#         number = ""
# if number:
#     m.append(int(number))
# sum_even = 0
# mult_odd = 1

# for num in m:
#     if num % 2 == 0:
#         sum_even += num
#     else:
#         mult_odd *= num

# min_index = 0
# max_index = 0
# min_value = m[0]
# max_value = m[0]

# for i in range(len(m)):
#     if m[i] < min_value:
#         min_value = m[i]
#         min_index = i
#     if m[i] > max_value:
#         max_value = m[i]
#         max_index = i

# m[min_index], m[max_index] = m[max_index], m[min_index]


# print("Сумма четных элементов:", sum_even)
# print("Произведение нечетных элементов:", mult_odd)
# print("Массив, где минимальное и максимальное число поменялись местами:", m)
