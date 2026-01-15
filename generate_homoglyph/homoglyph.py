#!/usr/bin/env python3
# -*- coding: utf-8 -*-

class HomoglyphGenerator:
    def __init__(self, load_digit_mapping=True, digit_mapping_file='unicode_confusables.json'):
        # Common homoglyph mapping table - Limited to 4 characters per letter
        self.homoglyphs = {
            # Latin letters - lowercase (4 characters each)
            'a': ['а', 'α', 'ɑ', 'ａ'],  # Cyrillic а, Greek α, Latin ɑ, Fullwidth a
            'b': ['ｂ', '𝐛', '𝑏', '𝒃'],  # Fullwidth b, Math bold b, Math italic b, Math bold italic b
            'c': ['с', 'ｃ', 'ⅽ', 'ϲ'],  # Cyrillic с, Fullwidth c, Roman numeral c, Greek lunate sigma
            'd': ['ｄ', '𝐝', '𝑑', '𝒅'],  # Fullwidth d, Math bold d, Math italic d, Math bold italic d
            'e': ['е', 'ｅ', '𝐞', '𝑒'],  # Cyrillic е, Fullwidth e, Math bold e, Math italic e
            'f': ['ｆ', '𝐟', '𝑓', '𝒇'],  # Fullwidth f, Math bold f, Math italic f, Math bold italic f
            'g': ['ｇ', '𝐠', '𝑔', '𝒈'],  # Fullwidth g, Math bold g, Math italic g, Math bold italic g
            'h': ['һ', 'ｈ', '𝐡', '𝒉'],  # Cyrillic һ, Fullwidth h, Math bold h, Math bold italic h
            'i': ['і', 'ｉ', '𝐢', '𝑖'],  # Cyrillic і, Fullwidth i, Math bold i, Math italic i
            'j': ['ｊ', '𝐣', '𝑗', '𝒋'],  # Fullwidth j, Math bold j, Math italic j, Math bold italic j
            'k': ['ｋ', '𝐤', '𝑘', '𝒌'],  # Fullwidth k, Math bold k, Math italic k, Math bold italic k
            'l': ['ｌ', '𝐥', '𝑙', '𝒍'],  # Fullwidth l, Math bold l, Math italic l, Math bold italic l
            'm': ['ｍ', '𝐦', '𝑚', '𝒎'],  # Fullwidth m, Math bold m, Math italic m, Math bold italic m
            'n': ['ｎ', '𝐧', '𝑛', '𝒏'],  # Fullwidth n, Math bold n, Math italic n, Math bold italic n
            'o': ['о', 'ο', 'ｏ', '𝐨'],  # Cyrillic о, Greek ο, Fullwidth o, Math bold o
            'p': ['р', 'ρ', 'ｐ', '𝐩'],  # Cyrillic р, Greek ρ, Fullwidth p, Math bold p
            'q': ['ｑ', '𝐪', '𝑞', '𝒒'],  # Fullwidth q, Math bold q, Math italic q, Math bold italic q
            'r': ['ｒ', '𝐫', '𝑟', '𝒓'],  # Fullwidth r, Math bold r, Math italic r, Math bold italic r
            's': ['ѕ', 'ｓ', '𝐬', '𝑠'],  # Cyrillic ѕ, Fullwidth s, Math bold s, Math italic s
            't': ['ｔ', '𝐭', '𝑡', '𝒕'],  # Fullwidth t, Math bold t, Math italic t, Math bold italic t
            'u': ['ｕ', '𝐮', '𝑢', '𝒖'],  # Fullwidth u, Math bold u, Math italic u, Math bold italic u
            'v': ['ν', 'ｖ', '𝐯', '𝑣'],  # Greek ν, Fullwidth v, Math bold v, Math italic v
            'w': ['ｗ', '𝐰', '𝑤', '𝒘'],  # Fullwidth w, Math bold w, Math italic w, Math bold italic w
            'x': ['х', 'χ', 'ｘ', '𝐱'],  # Cyrillic х, Greek χ, Fullwidth x, Math bold x
            'y': ['у', 'γ', 'ｙ', '𝐲'],  # Cyrillic у, Greek γ, Fullwidth y, Math bold y
            'z': ['ｚ', '𝐳', '𝑧', '𝒛'],  # Fullwidth z, Math bold z, Math italic z, Math bold italic z

            # Latin letters - uppercase (4 characters each)
            'A': ['А', 'Α', 'Ａ', '𝐀'],  # Cyrillic А, Greek Α, Fullwidth A, Math bold A
            'B': ['В', 'Β', 'Ｂ', '𝐁'],  # Cyrillic В, Greek Β, Fullwidth B, Math bold B
            'C': ['С', 'Ｃ', 'Ⅽ', '𝐂'],  # Cyrillic С, Fullwidth C, Roman numeral C, Math bold C
            'D': ['Ｄ', '𝐃', '𝐷', '𝑫'],  # Fullwidth D, Math bold D, Math italic D, Math bold italic D
            'E': ['Е', 'Ｅ', '𝐄', '𝐸'],  # Cyrillic Е, Fullwidth E, Math bold E, Math italic E
            'F': ['Ｆ', '𝐅', '𝐹', '𝑭'],  # Fullwidth F, Math bold F, Math italic F, Math bold italic F
            'G': ['Ｇ', '𝐆', '𝐺', '𝑮'],  # Fullwidth G, Math bold G, Math italic G, Math bold italic G
            'H': ['Н', 'Η', 'Ｈ', '𝐇'],  # Cyrillic Н, Greek Η, Fullwidth H, Math bold H
            'I': ['І', 'Ι', 'Ｉ', '𝐈'],  # Cyrillic І, Greek Ι, Fullwidth I, Math bold I
            'J': ['Ｊ', '𝐉', '𝐽', '𝑱'],  # Fullwidth J, Math bold J, Math italic J, Math bold italic J
            'K': ['К', 'Κ', 'Ｋ', '𝐊'],  # Cyrillic К, Greek Κ, Fullwidth K, Math bold K
            'L': ['Ｌ', '𝐋', '𝐿', '𝑳'],  # Fullwidth L, Math bold L, Math italic L, Math bold italic L
            'M': ['М', 'Μ', 'Ｍ', '𝐌'],  # Cyrillic М, Greek Μ, Fullwidth M, Math bold M
            'N': ['Ｎ', '𝐍', '𝑁', '𝑵'],  # Fullwidth N, Math bold N, Math italic N, Math bold italic N
            'O': ['О', 'Ο', 'Ｏ', '𝐎'],  # Cyrillic О, Greek Ο, Fullwidth O, Math bold O
            'P': ['Р', 'Ρ', 'Ｐ', '𝐏'],  # Cyrillic Р, Greek Ρ, Fullwidth P, Math bold P
            'Q': ['Ｑ', '𝐐', '𝑄', '𝑸'],  # Fullwidth Q, Math bold Q, Math italic Q, Math bold italic Q
            'R': ['Ｒ', 'ℛ', '𝐑', '𝑅'],  # Fullwidth R, Script R, Math bold R, Math italic R
            'S': ['Ѕ', 'Ｓ', '𝐒', '𝑆'],  # Cyrillic Ѕ, Fullwidth S, Math bold S, Math italic S
            'T': ['Т', 'Τ', 'Ｔ', '𝐓'],  # Cyrillic Т, Greek Τ, Fullwidth T, Math bold T
            'U': ['Ｕ', '𝐔', '𝑈', '𝑼'],  # Fullwidth U, Math bold U, Math italic U, Math bold italic U
            'V': ['Ｖ', '𝐕', '𝑉', '𝑽'],  # Fullwidth V, Math bold V, Math italic V, Math bold italic V
            'W': ['Ｗ', '𝐖', '𝑊', '𝑾'],  # Fullwidth W, Math bold W, Math italic W, Math bold italic W
            'X': ['Х', 'Χ', 'Ｘ', '𝐗'],  # Cyrillic Х, Greek Χ, Fullwidth X, Math bold X
            'Y': ['Υ', 'Ｙ', '𝐘', '𝑌'],  # Greek Υ, Fullwidth Y, Math bold Y, Math italic Y
            'Z': ['Ｚ', 'Ζ', '𝐙', '𝑍'],  # Fullwidth Z, Greek Ζ, Math bold Z, Math italic Z

        }

        # Load digit homoglyphs from JSON file if enabled
        if load_digit_mapping:
            digit_homoglyphs = self.load_digit_homoglyphs(digit_mapping_file)
            self.homoglyphs.update(digit_homoglyphs)

    def load_digit_homoglyphs(self, json_file='unicode_confusables.json', max_variants_per_digit=4):
        """
        Load digit homoglyphs from unicode_confusables.json file

        Args:
            json_file (str): Path to the JSON file containing confusable characters
            max_variants_per_digit (int): Maximum number of variants per digit (default 4)

        Returns:
            dict: Dictionary mapping digits to their homoglyph variants
        """
        import json
        import os

        digit_homoglyphs = {}

        # Check if file exists
        if not os.path.exists(json_file):
            print(f"Warning: {json_file} not found. Using default digit mapping.")
            # Return default simple mapping
            return {
                '0': ['０', '𝟎', '𝟘', '۰'],  # Fullwidth 0, Math bold 0, Math double-struck 0, Arabic-Indic digit zero
                '1': ['１', '𝟙', '𝟝', '۱'],  # Fullwidth 1, Math bold 1, Math double-struck 1, Arabic-Indic digit one
                '2': ['２', '𝟚', '𝟞', '۲'],  # Fullwidth 2, Math bold 2, Math double-struck 2, Arabic-Indic digit two
                '3': ['３', '𝟛', '𝟟', '۳'],  # Fullwidth 3, Math bold 3, Math double-struck 3, Arabic-Indic digit three
                '4': ['４', '𝟜', '𝟠', '۴'],  # Fullwidth 4, Math bold 4, Math double-struck 4, Arabic-Indic digit four
                '5': ['５', '𝟝', '𝟡', '۵'],  # Fullwidth 5, Math bold 5, Math double-struck 5, Arabic-Indic digit five
                '6': ['６', '𝟞', '𝟢', '۶'],  # Fullwidth 6, Math bold 6, Math double-struck 6, Arabic-Indic digit six
                '7': ['７', '𝟟', '𝟣', '۷'],  # Fullwidth 7, Math bold 7, Math double-struck 7, Arabic-Indic digit seven
                '8': ['８', '𝟠', '𝟤', '۸'],  # Fullwidth 8, Math bold 8, Math double-struck 8, Arabic-Indic digit eight
                '9': ['９', '𝟡', '𝟥', '۹'],  # Fullwidth 9, Math bold 9, Math double-struck 9, Arabic-Indic digit nine
            }

        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            confusables_map = data.get('confusables_map', {})

            # Build reverse mapping: for each digit 0-9, find all characters that are confusable with it
            for digit_char in '0123456789':
                digit_homoglyphs[digit_char] = []

            # Iterate through all entries to find characters confusable with digits
            for key, entry in confusables_map.items():
                char = entry.get('character', '')
                confusable_with = entry.get('confusable_with', {})
                confusable_char = confusable_with.get('character', '')

                # If this character is confusable with a digit
                if confusable_char in '0123456789':
                    if char not in digit_homoglyphs[confusable_char]:
                        digit_homoglyphs[confusable_char].append(char)

            # Prioritize mathematical fonts for better lookalike quality
            # Sort by preference: Mathematical > Segmented > Others
            priority_keywords = ['MATHEMATICAL BOLD', 'MATHEMATICAL DOUBLE-STRUCK', 
                               'MATHEMATICAL SANS-SERIF', 'SEGMENTED', 'OUTLINED']

            for digit in '0123456789':
                chars = digit_homoglyphs.get(digit, [])
                
                # Score each character based on priority keywords
                scored_chars = []
                for char in chars:
                    import unicodedata
                    try:
                        char_name = unicodedata.name(char)
                    except:
                        char_name = ''

                    score = 0
                    for i, keyword in enumerate(priority_keywords):
                        if keyword in char_name:
                            score = len(priority_keywords) - i
                            break

                    scored_chars.append((score, char))

                # Sort by score (descending) and take top max_variants_per_digit
                scored_chars.sort(key=lambda x: x[0], reverse=True)
                digit_homoglyphs[digit] = [char for score, char in scored_chars[:max_variants_per_digit]]

            print(f"Successfully loaded digit homoglyphs from {json_file}")
            print(f"Digits with mappings: {', '.join([d for d in '0123456789' if digit_homoglyphs.get(d)])}")

            return digit_homoglyphs

        except Exception as e:
            print(f"Error loading digit homoglyphs from {json_file}: {e}")
            print("Using default digit mapping as fallback.")
            # Return default simple mapping as fallback
            return {
                '0': ['０', '𝟎', '𝟘', '۰'],
                '1': ['１', '𝟙', '𝟝', '۱'],
                '2': ['２', '𝟚', '𝟞', '۲'],
                '3': ['３', '𝟛', '𝟟', '۳'],
                '4': ['４', '𝟜', '𝟠', '۴'],
                '5': ['５', '𝟝', '𝟡', '۵'],
                '6': ['６', '𝟞', '𝟢', '۶'],
                '7': ['７', '𝟟', '𝟣', '۷'],
                '8': ['８', '𝟠', '𝟤', '۸'],
                '9': ['９', '𝟡', '𝟥', '۹'],
            }

    def generate_variants(self, text, max_variants=None, mode='diverse'):
        """
        Generate homoglyph variants for the given text

        Args:
            text (str): Input text
            max_variants (int): Maximum number of variants (None for unlimited)
            mode (str): Generation mode - 'diverse', 'all', or 'random'

        Returns:
            list: List containing variants (excluding original text)
        """
        if mode == 'diverse':
            return self.generate_diverse_variants(text, max_variants)
        elif mode == 'all':
            return self.generate_all_variants(text, max_variants)
        else:  # random
            return self.generate_random_variants(text, max_variants or 5)

    def generate_all_variants(self, text, max_variants=None):
        """
        Generate all possible homoglyph variants systematically

        Args:
            text (str): Input text
            max_variants (int): Maximum number of variants (None for unlimited)

        Returns:
            list: List containing only the variants (excluding original text)
        """
        import itertools

        variants = set()  # Use set to avoid duplicates, do NOT include original text

        # Find positions in the text that can be replaced
        replaceable_positions = []
        replacement_options = []

        for i, char in enumerate(text):
            if char in self.homoglyphs and len(self.homoglyphs[char]) > 0:
                replaceable_positions.append(i)
                # Only include homoglyphs, NOT the original character
                # Limit to maximum 10 characters per position for better sampling diversity
                options = self.homoglyphs[char][:10]
                replacement_options.append(options)
            else:
                replacement_options.append([char])

        if not replaceable_positions:
            return []  # Return empty list if no replaceable characters

        # Generate all combinations using cartesian product
        print(f"Generating variants for text: '{text}'")
        print(f"Found {len(replaceable_positions)} replaceable positions")

        total_combinations = 1
        for options in replacement_options:
            total_combinations *= len(options)

        print(f"Total possible combinations: {total_combinations}")

        if max_variants and total_combinations > max_variants:
            print(f"Limiting to {max_variants} variants due to max_variants setting")

        count = 0
        for combination in itertools.product(*replacement_options):
            if max_variants and count >= max_variants:
                break

            variant = ''.join(combination)
            variants.add(variant)
            count += 1

            # Progress indicator for large sets
            if count % 1000 == 0:
                print(f"Generated {count} variants...")

        result = list(variants)
        print(f"Generated {len(result)} unique variants")
        return result

    def generate_diverse_variants(self, text, max_variants=None):
        """
        Generate diverse homoglyph variants with better sampling strategy

        Args:
            text (str): Input text
            max_variants (int): Maximum number of variants (None for unlimited)

        Returns:
            list: List of diverse variants
        """
        import itertools
        import random

        variants = set()

        # Find positions that can be replaced
        replaceable_positions = []
        replacement_options = []

        for i, char in enumerate(text):
            if char in self.homoglyphs and len(self.homoglyphs[char]) > 0:
                replaceable_positions.append(i)
                # Limit to 10 characters and shuffle for diversity
                options = self.homoglyphs[char][:10]
                random.shuffle(options)  # Randomize order for better sampling
                replacement_options.append(options)
            else:
                replacement_options.append([char])

        if not replaceable_positions:
            return []

        print(f"Generating diverse variants for text: '{text}'")
        print(f"Found {len(replaceable_positions)} replaceable positions")
        print(f"Max characters per position: 10")

        # Calculate total possible combinations
        total_combinations = 1
        for options in replacement_options:
            total_combinations *= len(options)

        print(f"Total possible combinations: {total_combinations}")

        if max_variants and total_combinations <= max_variants:
            # If we can generate all combinations, do so
            print("Generating all possible combinations...")
            for combination in itertools.product(*replacement_options):
                variant = ''.join(combination)
                if variant != text:  # Exclude original text
                    variants.add(variant)
        else:
            # Use smart sampling strategy
            if max_variants:
                print(f"Using smart sampling to generate {max_variants} diverse variants...")
            else:
                print("Using smart sampling to generate diverse variants...")

            # Strategy: Sample systematically to ensure diversity
            target_count = max_variants or min(10000, total_combinations)

            # Method 1: Systematic sampling with random offset
            step = max(1, total_combinations // target_count)
            offset = random.randint(0, step - 1) if step > 1 else 0

            count = 0
            for i, combination in enumerate(itertools.product(*replacement_options)):
                if max_variants and count >= max_variants:
                    break

                if (i + offset) % step == 0:
                    variant = ''.join(combination)
                    if variant != text:  # Exclude original text
                        variants.add(variant)
                        count += 1

            # Method 2: Fill remaining slots with pure random sampling
            if max_variants and len(variants) < max_variants:
                remaining = max_variants - len(variants)
                attempts = 0
                max_attempts = remaining * 10

                while len(variants) < max_variants and attempts < max_attempts:
                    attempts += 1
                    combination = []
                    for options in replacement_options:
                        combination.append(random.choice(options))

                    variant = ''.join(combination)
                    if variant != text:  # Exclude original text
                        variants.add(variant)

        result = list(variants)
        print(f"Generated {len(result)} unique diverse variants")
        return result

    def save_variants_to_json(self, original_text, variants, filename=None):
        """
        Save variants to JSON file with only domain names

        Args:
            original_text (str): Original input text
            variants (list): List of variant strings
            filename (str): Output filename (optional)

        Returns:
            str: Filename of saved file
        """
        import json
        from datetime import datetime

        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"domain_variants_{timestamp}.json"

        # Prepare data structure
        data = {
            "metadata": {
                "original_domain": original_text,
                "generated_time": datetime.now().isoformat(),
                "total_variants": len(variants),
                "generator": "HomoglyphGenerator"
            },
            "variants": variants
        }

        # Save to JSON file
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return filename
        except Exception as e:
            raise Exception(f"Failed to save JSON file: {e}")

    def generate_random_variants(self, text, max_variants=5):
        """
        Generate random homoglyph variants (original method)

        Args:
            text (str): Input text
            max_variants (int): Maximum number of variants

        Returns:
            list: List containing only the variants (excluding original text)
        """
        import random

        variants = []  # Do NOT include original text

        # Find positions in the text that can be replaced
        replaceable_positions = []
        for i, char in enumerate(text):
            if char in self.homoglyphs and len(self.homoglyphs[char]) > 0:
                replaceable_positions.append((i, char))

        if not replaceable_positions:
            return []  # Return empty list if no replaceable characters

        # Generate variants
        generated_count = 0
        attempts = 0
        max_attempts = max_variants * 10  # Avoid infinite loop

        while generated_count < max_variants and attempts < max_attempts:
            attempts += 1
            new_text = list(text)

            # Randomly choose characters to replace
            num_replacements = random.randint(1, min(3, len(replaceable_positions)))
            positions_to_replace = random.sample(replaceable_positions, num_replacements)

            for pos, original_char in positions_to_replace:
                # Randomly select a homoglyph replacement (limit to first 10 for consistency)
                available_replacements = self.homoglyphs[original_char][:10]
                replacement = random.choice(available_replacements)
                new_text[pos] = replacement

            new_variant = ''.join(new_text)
            if new_variant not in variants and new_variant != text:  # Exclude original text
                variants.append(new_variant)
                generated_count += 1

        return variants

    def show_unicode_info(self, text):
        """Display Unicode information for each character in the text"""
        print(f"Text: {text}")
        print("Character details:")
        for i, char in enumerate(text):
            print(f"  Position {i}: '{char}' (U+{ord(char):04X}) - {self.get_char_name(char)}")
        print()

    def get_char_name(self, char):
        """Get descriptive name of a character"""
        import unicodedata
        try:
            return unicodedata.name(char)
        except ValueError:
            return "Unknown character"

    def compare_texts(self, text1, text2):
        """Compare differences between two texts"""
        print(f"Text 1: {text1}")
        print(f"Text 2: {text2}")
        print(f"Visually identical: {'Yes' if text1 == text2 else 'No'}")
        print(f"Encoding identical: {'Yes' if text1.encode() == text2.encode() else 'No'}")

        if len(text1) == len(text2):
            print("Character differences:")
            for i, (c1, c2) in enumerate(zip(text1, text2)):
                if c1 != c2:
                    print(f"  Position {i}: '{c1}' (U+{ord(c1):04X}) vs '{c2}' (U+{ord(c2):04X})")
        else:
            print("Texts have different lengths")
        print()


def main():
    generator = HomoglyphGenerator()

    print("Homoglyph Generator")
    print("=" * 50)

    while True:
        print("\nChoose an operation:")
        print("1. Generate text variants")
        print("2. Show Unicode info of text")
        print("3. Compare two texts")
        print("4. Display available homoglyph mappings")
        print("5. Exit")

        choice = input("\nEnter choice (1-5): ").strip()

        if choice == '1':
            text = input("Enter domain name to generate variants: ")

            # Ask user for generation mode
            print("\nGeneration mode:")
            print("1. Generate DIVERSE variants (smart sampling, max 10 chars per position)")
            print("2. Generate ALL possible variants (systematic)")
            print("3. Generate random variants (limited)")
            mode = input("Choose mode (1, 2, or 3, default 1): ").strip() or "1"

            if mode == "1":
                # Generate diverse variants (recommended)
                max_limit = input("Enter maximum limit (default 1000): ").strip()
                max_variants = int(max_limit) if max_limit else 1000
                variants = generator.generate_variants(text, max_variants, mode='diverse')

            elif mode == "2":
                # Generate all variants
                max_limit = input("Enter maximum limit (press Enter for unlimited): ").strip()
                max_variants = int(max_limit) if max_limit else None

                if max_variants is None:
                    confirm = input("This may generate a very large number of variants. Continue? (y/N): ").strip().lower()
                    if confirm != 'y':
                        continue

                variants = generator.generate_variants(text, max_variants, mode='all')
            else:
                # Generate random variants
                max_variants = int(input("Enter max variants (default 5): ") or "5")
                variants = generator.generate_variants(text, max_variants, mode='random')

            print(f"\nGenerated {len(variants)} domain variants")

            # Show a preview of variants (first 10)
            print("\nPreview (first 10 variants):")
            for i, variant in enumerate(variants[:10]):
                print(f"{i + 1}. {variant}")

            if len(variants) > 10:
                print(f"... and {len(variants) - 10} more variants")

            # Automatically save to JSON file
            try:
                filename = input("\nEnter JSON filename (press Enter for auto-generated name): ").strip()
                if not filename:
                    filename = None

                saved_file = generator.save_variants_to_json(text, variants, filename)
                print(f"\nAll variants saved to: {saved_file}")
                print(f"Total variants: {len(variants)}")

            except Exception as e:
                print(f"Error saving JSON file: {e}")

                # Fallback to text file
                try:
                    fallback_filename = f"domain_variants_{text.replace('.', '_')}.txt"
                    with open(fallback_filename, 'w', encoding='utf-8') as f:
                        f.write(f"Original domain: {text}\n")
                        f.write(f"Generated {len(variants)} variants:\n\n")
                        for i, variant in enumerate(variants):
                            f.write(f"{variant}\n")
                    print(f"Variants saved to fallback file: {fallback_filename}")
                except Exception as e2:
                    print(f"Error saving fallback file: {e2}")

        elif choice == '2':
            text = input("Enter text to analyze: ")
            generator.show_unicode_info(text)

        elif choice == '3':
            text1 = input("Enter first text: ")
            text2 = input("Enter second text: ")
            generator.compare_texts(text1, text2)

        elif choice == '4':
            print("\nAvailable homoglyph mappings:")
            for original, alternatives in generator.homoglyphs.items():
                print(f"'{original}' -> {alternatives[:3]}{'...' if len(alternatives) > 3 else ''}")

        elif choice == '5':
            print("Goodbye!")
            break

        else:
            print("Invalid choice, please try again.")


if __name__ == "__main__":
    main()
