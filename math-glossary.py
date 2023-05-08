from mediawikiapi import MediaWikiAPI, Config, RedirectError
from collections import Counter
from colorama import Fore, Back, Style, init
import re, csv, traceback, time

init()
api = MediaWikiAPI(config=Config(mediawiki_url="https://proofwiki.org/w/api.php"))

blacklisted_categories = ["Definition Disambiguation Pages", "Definitions/Language Definitions", "Definitions/Branches of Science", "Definitions/Fallacies and Mistakes‎", "Definitions/Miscellanea"]
blacklisted_sections = ["Sources", "Linguistic Note", "Also see", "Historical Note"]
allowed_categories = []
in_handling_categories = []

limit = 100
nested_limit = 20
handled_categories = []
handled_pages = []

sections_counter = Counter()
words_counter = Counter()

latex_regex = re.compile(r"\$.*\$", re.DOTALL)
word_regex = re.compile(r"^[\"'.,;:!?(]*([\w'-]+)[\"'.,;:!?)]*$")
punctuation_regex = re.compile(r"[\"'.,;:!?=()]")

def handle_cat(cat_title, nested_index):
    cat_title = cat_title.replace("Category:", "")
    
    print(f"Handling category {Fore.YELLOW + cat_title + Style.RESET_ALL}, nested index {nested_index}")
    if nested_index >= nested_limit:
        print(Fore.RED + "Exceeded nested limit!" + Style.RESET_ALL)
        return
    
    if not check_cat(cat_title):
        print(Fore.RED + "Blacklisted category!" + Fore.RESET)
        return
    
    handled_categories.append(cat_title)
    cat_pages = api.category_members(title = cat_title, cmlimit = limit, cmtype = "page")
    for page in cat_pages:
        try:
            handle_page(page)
        except KeyboardInterrupt as e:
            raise e
        except:
            print(f"{Fore.RED}Failed to handle page {page}{Fore.RESET}")
            traceback.print_exc()
    
    cat_categories = api.category_members(title = cat_title, cmlimit = limit, cmtype = "subcat")
    for nested_cat in cat_categories:
        handle_cat(nested_cat, nested_index + 1)

def check_cat(cat_title):
    if cat_title in blacklisted_categories:
        return False
    if cat_title in allowed_categories:
        return True
    
    if cat_title in in_handling_categories:
        print(f"{Fore.RED} Warning: circular categories detected, {cat_title} being used twice.{Fore.RESET}")
        return True
    in_handling_categories.append(cat_title)
    
    cat = api.page("Category:" + cat_title, auto_suggest = False, redirect = False, preload = False)
    for parent_cat in cat.categories:
        if not check_cat(parent_cat):
            blacklisted_categories.append(cat_title)
            in_handling_categories.remove(cat_title)
            return False
    in_handling_categories.remove(cat_title)
    allowed_categories.append(cat_title)
    return True

def handle_page(page_title):
    if page_title in handled_pages:
        return
    
    print(f"Handling page {Fore.GREEN + page_title + Style.RESET_ALL}")
    
    if page_title.startswith("Template:"):
        print(Fore.RED + "Template page!" + Fore.RESET)
        return
    
    handled_pages.append(page_title)
    try:
        page = api.page(page_title, auto_suggest = False, redirect = False, preload = False)
    except RedirectError as redirect: # for now setting "redirect = True" leads to an exception
        print(Fore.RED + "Warning, redirection cancelled!" + Fore.RESET)
        return
    
    if page.title != page_title:
        print(Fore.RED + "Warning, bad page title!" + Fore.RESET)
        handle_page(page.title)
        return
    
    for page_cat in page.categories:
        if not check_cat(page_cat):
            print(f"{Fore.RED}In blacklisted category!{Fore.RESET}")
            return
    
    words_count = 0
    for section in page.sections:
        words_count += handle_section(page, section)
    print(f"Counted {words_count} words!")

def handle_section(page, section_title):
    if section_title in blacklisted_sections:
        return 0
    
    if section_title.startswith("Example:"):
        return 0
    
    sections_counter.update([section_title])
    section_content = page.section(section_title)
    if section_content == None:
        return 0
    stripped_content = latex_regex.sub("", section_content)
    if stripped_content == None:
        return 0
    
    raw_words = stripped_content.split()
    words = []
    for word in raw_words:
        if word != section_title:
            word = word.lower()
            word_match = word_regex.match(word)
            if word_match == None:
                if punctuation_regex.fullmatch(word) == None:
                    print(f"Unknown word matching: {word}")
            else:
                words.append(word_match.group(1))
    
    words_counter.update(words)
    return len(words)

def print_table(list, headers=None):
    print(f" {Style.BRIGHT + Fore.YELLOW}{headers[0]:<29} {Fore.GREEN + headers[1]}")
    print(Fore.RESET + Style.DIM + "-" * 40 + Style.RESET_ALL)
    for row in list:
        print(f"{row[0]:<30} {row[1]}")

start_time = time.time()
try:
    handle_cat("Definitions/Branches of Mathematics", 0)
except KeyboardInterrupt:
    print()
    print(Fore.RED + "Interrupted!" + Fore.RESET)

end_time = time.time()
print(f"Elapsed time: {Fore.MAGENTA + str(int(end_time - start_time))}s")
print(Fore.RESET + Style.BRIGHT)
print(f"Finished counting {Fore.CYAN + str(sum(words_counter.values()))} words{Fore.RESET} in {Fore.GREEN + str(len(handled_pages))} pages{Fore.RESET} in {Fore.YELLOW + str(len(handled_categories))} categories{Fore.RESET}!")
print(Style.RESET_ALL)
print(Style.DIM + "=" * 40 + Style.NORMAL)
print_table(sections_counter.most_common(100), headers = ["Section", "Count"])
print(Style.DIM + "=" * 40 + Style.NORMAL)
print_table(words_counter.most_common(300), headers = ["Word", "Count"])
print(Style.DIM + "=" * 40 + Style.NORMAL)
print()

print("Writing file...")
with open("math-glossary-result.csv", "w", newline = "") as file:
    writer = csv.writer(file)
    writer.writerows(words_counter.most_common())

print("File written.")