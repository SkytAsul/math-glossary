import csv

raw_file_name = input("Enter raw filename: ")
new_file_name = input("Enter new filename: ")

frequent_words = []
with open("frequent-words.txt", "r", newline = "") as file:
    for word in file:
        frequent_words.append(word.strip())

print(f"Removing {len(frequent_words)} words.")
print(frequent_words)

words = []
with open(raw_file_name, "r", newline = "") as file:
    reader = csv.reader(file)
    for word in reader:
        if word[0] in frequent_words:
            print(f"Removing {word[1]} occurrences of {word[0]}.")
        else:
            words.append(word)

with open(new_file_name, "w", newline = "") as file:
    writer = csv.writer(file)
    writer.writerows(words)

print(f"Written {len(words)} words!")