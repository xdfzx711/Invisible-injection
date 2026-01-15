import tkinter as tk
import os


def convert_to_tag_chars(input_string):
    try:
        return ''.join(chr(0xE0000 + ord(ch)) if 0xE0000 + ord(ch) <= 0xE007F else ch for ch in input_string)
    except Exception as e:
        print(f"Error during conversion: {e}")
        return None


def copy_to_clipboard(string):
    root = tk.Tk()
    root.withdraw()
    root.clipboard_clear()
    root.clipboard_append(string)
    root.update()
    root.destroy()


def save_to_file(text, filename="output.txt"):
    try:
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        with open(filename, 'w', encoding='utf-8') as file:
            file.write(text + '\n')
        print(f" Saved to file: {os.path.abspath(filename)}")
        return True
    except Exception as e:
        print(f" Error saving to file: {e}")
        return False


def main():
    print(" Unicode Tag Character Converter")
    print("=" * 40)

    while True:
        user_input = input("\nEnter the text to convert (or type 'exit' to quit): ").strip()
        if user_input.lower() == 'exit':
            break
        if not user_input:
            print("Input cannot be empty!")
            continue

        result = convert_to_tag_chars(user_input)
        filename = "./output/basic_tag_characters.txt"

        if result:
            print("\n Conversion successful!")
            print(f" Preview: {result[:100]}{'...' if len(result) > 100 else ''}")

            copy_to_clipboard(result)
            save_to_file(result, filename)
            print(" Copied to clipboard")

            print("\n Stats:")
            print(f"   Original length: {len(user_input)} chars")
            print(f"   Result length:   {len(result)} chars")
            print(f"   Length increase: {len(result) - len(user_input)} chars")
        else:
            print(" Conversion failed!")


if __name__ == "__main__":
    main()
