import json
import os

def load_dictionary(dictionary_file):
    """Load dictionary words from text file into a set for fast lookup."""
    try:
        with open(dictionary_file, 'r', encoding='utf-8') as f:
            # Read all words and convert to lowercase, strip whitespace
            dictionary_words = set(word.strip().lower() for word in f.readlines() if word.strip())
        print(f"Loaded {len(dictionary_words)} words from dictionary")
        return dictionary_words
    except FileNotFoundError:
        print(f"Error: Dictionary file '{dictionary_file}' not found")
        return None
    except Exception as e:
        print(f"Error reading dictionary file: {e}")
        return None

def filter_syllables_by_dictionary(json_data, dictionary_words):
    """Filter syllables to keep only those found in dictionary."""
    if 'syllables' not in json_data:
        print("No 'syllables' key found in JSON data")
        return json_data
    
    original_syllable_count = len(json_data['syllables'])
    filtered_syllables = []
    removed_syllables = []
    
    for syllable_entry in json_data['syllables']:
        syllable = syllable_entry['syllable'].lower()
        if syllable in dictionary_words:
            filtered_syllables.append(syllable_entry)
        else:
            removed_syllables.append(syllable_entry)
    
    # Update the JSON data
    json_data['syllables'] = filtered_syllables
    
    # Update metadata if it exists
    if 'metadata' in json_data:
        # Count total words (number of word entries)
        total_words = len(json_data.get('words', []))
        
        # Count words with frequency > 0
        words_with_frequency = 0
        if 'words' in json_data:
            words_with_frequency = sum(1 for word_entry in json_data['words'] if word_entry['frequency'] > 0)
        
        # Count total syllables (number of syllable entries after filtering)
        total_syllables = len(filtered_syllables)
        
        # Count syllables with frequency > 0
        syllables_with_frequency = sum(1 for syllable_entry in filtered_syllables if syllable_entry['frequency'] > 0)
        
        # Update metadata
        json_data['metadata']['total_words'] = total_words
        json_data['metadata']['words_with_frequency'] = words_with_frequency
        json_data['metadata']['total_syllables'] = total_syllables
        json_data['metadata']['syllables_with_frequency'] = syllables_with_frequency
        json_data['metadata']['phase'] = 'dictionary_filtered'
    
    print(f"Original syllables: {original_syllable_count}")
    print(f"Filtered syllables: {len(filtered_syllables)}")
    print(f"Removed syllables: {len(removed_syllables)}")
    
    if removed_syllables:
        print("\nFirst 10 removed syllables:")
        for i, syllable in enumerate(removed_syllables[:50]):
            print(f"  - {syllable['syllable']} (frequency: {syllable['frequency']})")
    
    # Print updated metadata
    if 'metadata' in json_data:
        print(f"\nUpdated metadata:")
        print(f"  - total_words: {json_data['metadata']['total_words']}")
        print(f"  - words_with_frequency: {json_data['metadata']['words_with_frequency']}")
        print(f"  - total_syllables: {json_data['metadata']['total_syllables']}")
        print(f"  - syllables_with_frequency: {json_data['metadata']['syllables_with_frequency']}")
    
    return json_data

def main():
    # File paths
    json_file = 'shan_dictionary.json'  # Your JSON file
    dictionary_file = 'dictionary.txt'  # Your dictionary file
    output_file = 'filtered_frequency_data.json'  # Output file
    
    # Check if files exist
    if not os.path.exists(json_file):
        print(f"Error: JSON file '{json_file}' not found")
        return
    
    if not os.path.exists(dictionary_file):
        print(f"Error: Dictionary file '{dictionary_file}' not found")
        return
    
    # Load dictionary
    dictionary_words = load_dictionary(dictionary_file)
    if dictionary_words is None:
        return
    
    # Load JSON data
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            json_data = json.load(f)
        print(f"Loaded JSON data from '{json_file}'")
    except FileNotFoundError:
        print(f"Error: JSON file '{json_file}' not found")
        return
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON file: {e}")
        return
    except Exception as e:
        print(f"Error reading JSON file: {e}")
        return
    
    # Filter syllables
    filtered_data = filter_syllables_by_dictionary(json_data, dictionary_words)
    
    # Save filtered data
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(filtered_data, f, indent=2, ensure_ascii=False)
        print(f"\nFiltered data saved to '{output_file}'")
    except Exception as e:
        print(f"Error saving filtered data: {e}")

if __name__ == "__main__":
    main()