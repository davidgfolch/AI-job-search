def generate_tables():
    for number in range(2, 11): # From 2 to 10
        print(f"--- Table of {number} ---")
        for multiplier in range(1, 11): # Standards usually go 1 to 10
            print(f"{number}x{multiplier}={number*multiplier}")
        print("")

if __name__ == "__main__":
    generate_tables()
