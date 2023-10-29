from .backend import searchInDataBase


def main():
    search = searchInDataBase()
    results = search.searchEmails(input("Search for: "))

    print(results)

    search = searchInDataBase()
    results = search.searchEvents(input("Search for: "))

    print(results)


