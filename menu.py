from familytree import FamilyTree
from personfactory import PersonFactory


def prompt_roots(factory: PersonFactory):
    print("Enter the two root people born in 1950.")

    a_first = input("First person's first name (default: Desmond): ").strip() or "Desmond"
    a_last = input("First person's last name (default: Jones): ").strip() or "Jones"

    b_first = input("Second person's first name (default: Molly): ").strip() or "Molly"
    b_last = input("Second person's last name (default: Jones): ").strip() or "Jones"

    a = factory.get_person(1950, last_name=a_last)
    a.first_name = a_first
    a.last_name = a_last

    b = factory.get_person(1950, last_name=b_last)
    b.first_name = b_first
    b.last_name = b_last

    return a, b


def run_cli(tree: FamilyTree) -> None:
    while True:
        print("\nAre you interested in:")
        print("(T)otal number of people in the tree")
        print("Total number of people in the tree by (D)ecade")
        print("(N)ames duplicated")
        print("(Q)uit")

        choice = input("> ").strip().upper()

        if choice == "Q":
            print("Bye.")
            return

        if choice == "T":
            print(f"The tree contains {tree.total_people()} people total")

        elif choice == "D":
            for decade, count in tree.total_by_decade().items():
                print(f"{decade}: {count}")

        elif choice == "N":
            duplicates = tree.duplicate_full_names()
            print(f"There are {len(duplicates)} duplicate names in the tree:")
            for name in duplicates:
                print(f"* {name}")

        else:
            print("Invalid choice.")


def main():
    print("Reading files...")
    factory = PersonFactory()
    factory.read_files()

    print("Generating family tree...")
    root_a, root_b = prompt_roots(factory)

    tree = FamilyTree(factory)
    tree.initialize_roots(root_a, root_b)
    tree.generate()

    run_cli(tree)


if __name__ == "__main__":
    main()