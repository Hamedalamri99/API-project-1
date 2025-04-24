import sys
import argparse
import logging
# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
def process_string(input_str: str) -> list[int]:
    """
    Process a string into a list of integer sums based on the following rules:
    1. Divide the input into groups: each 'z' starts a group that includes itself and subsequent characters
       if the last character in the group is 'z'; all other characters form single-character groups.
    2. Map each letter a-z to 1-26, and non-letters (e.g., '_', '-') to 0.
    3. Traverse the groups: for each group with value N, sum the next N groups and append the sum; skip 1+N groups.
    """
    logging.info(f"Input string: {input_str}")
    def get_char_value(char: str) -> int:
        """Return the alphabetical value of a character or 0 if non-alphabetic."""
        char = char.lower()
        return ord(char) - 96 if 'a' <= char <= 'z' else 0
    # Step 1: Create groups
    groups = []
    index = 0
    while index < len(input_str):
        if input_str[index].lower() == 'z':
            group = input_str[index]
            index += 1
            while group and group[-1].lower() == 'z' and index < len(input_str):
                group += input_str[index]
                index += 1
            groups.append(group)
        else:
            groups.append(input_str[index])
            index += 1
    logging.info(f"Groups created: {groups}")
    # Step 2: Calculate numeric values for each group
    group_values = [sum(get_char_value(char) for char in group) for group in groups]
    logging.info(f"Group values: {group_values}")
    # Step 3: Calculate portions
    results = []
    idx = 0
    while idx < len(group_values):
        current_value = group_values[idx]
        portion_sum = sum(group_values[idx + 1 : idx + 1 + current_value])
        results.append(portion_sum)
        idx += 1 + current_value
    # Step 4: Filter out 0 values from the results
    filtered_results = [value for value in results if value != 0]
    logging.info(f"Final results (filtered): {filtered_results}")
    return filtered_results
def interactive_prompt() -> None:
    """
    Option 1: Prompt the user to input a string.
    """
    user_input = input("Enter the string: ")
    print("Result:", process_string(user_input))
def command_line_arg() -> None:
    """
    Option 2: Read the string from a command-line argument.
    """
    parser = argparse.ArgumentParser(
        description="Process a string into sums based on the z-chain logic."
    )
    parser.add_argument(
        "input_string", help="The string to process, e.g., 'dz_a_aazzaaa'"
    )
    args = parser.parse_args()
    print(process_string(args.input_string))
if __name__ == "__main__":
    if len(sys.argv) == 1:
        interactive_prompt()
    else:
        command_line_arg()