#!/usr/bin/env python3

"""
Shan Dictionary to JSON Converter
Converts dictionary.txt to structured JSON format with frequency analysis

Requirements:
pip install datasets transformers shannlp

Usage:
python shan_dict_converter.py
"""

import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, List, Tuple, Set
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

try:
    from datasets import load_dataset
    from shannlp import word_tokenize, syllable_tokenize
except ImportError as e:
    logger.error(f"Missing required packages: {e}")
    logger.error("Please install: pip install datasets transformers shannlp")
    exit(1)


class ShanDictionaryConverter:
    """Convert Shan dictionary.txt to structured JSON with frequency analysis."""
    
    def __init__(self, dict_file: str = "dictionary.txt", output_file: str = "shan_dictionary.json"):
        self.dict_file = Path(dict_file)
        self.output_file = Path(output_file)
        self.tokenizer = None
        self.syllable_segmenter = None
        self.dictionary_words = []
        self.word_frequencies = Counter()
        self.syllable_frequencies = Counter()
        
    def initialize_shannlp(self):
        """Initialize ShanNLP tools."""
        try:
            logger.info("Initializing ShanNLP tools...")
            self.tokenizer = word_tokenize
            self.syllable_segmenter = syllable_tokenize
            logger.info("ShanNLP tools initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize ShanNLP: {e}")
            logger.warning("Falling back to basic tokenization...")
            self.tokenizer = None
            self.syllable_segmenter = None
    
    def load_dictionary(self) -> List[str]:
        """Phase 1: Load dictionary.txt and extract words."""
        logger.info(f"Phase 1: Loading dictionary from {self.dict_file}")
        
        if not self.dict_file.exists():
            logger.error(f"Dictionary file {self.dict_file} not found!")
            return []
        
        try:
            with open(self.dict_file, 'r', encoding='utf-8') as f:
                words = [line.strip() for line in f if line.strip()]
            
            logger.info(f"Loaded {len(words)} words from dictionary")
            self.dictionary_words = words
            return words
            
        except Exception as e:
            logger.error(f"Error loading dictionary: {e}")
            return []
    
    def create_basic_json(self, words: List[str]) -> Dict:
        """Phase 1: Create basic JSON structure with uniform frequencies."""
        logger.info("Phase 1: Creating basic JSON structure...")
        
        basic_structure = {
            "metadata": {
                "total_words": len(words),
                "source": "dictionary.txt",
                "phase": "basic_conversion"
            },
            "words": [{"word": word, "frequency": 0} for word in words],
            "syllables": []
        }
        
        logger.info(f"Created basic structure with {len(words)} words")
        return basic_structure
    
    def load_shan_news_dataset(self) -> List[str]:
        """Phase 2: Load Shan news dataset from Hugging Face."""
        logger.info("Phase 2: Loading Shan news dataset from Hugging Face...")
        
        try:
            # Load the dataset
            dataset = load_dataset("NorHsangPha/shan-news-shannews_org")
            
            # Extract text content (assuming 'text' field exists)
            texts = []
            for split in dataset.keys():
                logger.info(f"Processing {split} split...")
                for item in dataset[split]:
                    # Adjust field name based on actual dataset structure
                    texts.append(item['title'])
                    texts.append(item['content'])
            
            logger.info(f"Loaded {len(texts)} articles from dataset")
            return texts
            
        except Exception as e:
            logger.error(f"Error loading Shan news dataset: {e}")
            logger.warning("Proceeding without frequency analysis...")
            return []
    
    def tokenize_text(self, text: str) -> List[str]:
        """Tokenize Shan text using ShanNLP or fallback method."""
        if self.tokenizer:
            try:
                return self.tokenizer(text, engine="newmm", keep_whitespace=False)
            except Exception as e:
                logger.warning(f"ShanNLP tokenization failed: {e}")
        
        # Fallback: simple whitespace tokenization with basic Shan text cleaning
        # Remove common punctuation and split on whitespace
        cleaned_text = re.sub(r'[^\u1000-\u109F\u1A20-\u1AAF\s]', ' ', text)
        tokens = cleaned_text.split()
        return [token.strip() for token in tokens if token.strip()]
    
    def segment_syllables(self, word: str) -> List[str]:
        """Segment Shan word into syllables using ShanNLP or fallback."""
        if self.syllable_segmenter:
            try:
                return self.syllable_segmenter(word)
            except Exception as e:
                logger.warning(f"ShanNLP syllable segmentation failed: {e}")
        
        # Fallback: treat each word as a single syllable
        return [word] if word else []
    
    def analyze_frequency(self, texts: List[str]) -> Tuple[Counter, Counter]:
        """Phase 2: Analyze word and syllable frequencies from corpus."""
        logger.info("Phase 2: Analyzing frequencies from corpus...")
        
        word_counter = Counter()
        syllable_counter = Counter()
        
        # Create set of dictionary words for faster lookup
        dict_word_set = set(self.dictionary_words)
        
        for i, text in enumerate(texts):
            if i % 100 == 0:
                logger.info(f"Processing article {i}/{len(texts)}")
            
            # Tokenize text
            tokens = self.tokenize_text(text)
            
            # Count word frequencies (only for words in dictionary)
            for token in tokens:
                if token in dict_word_set:
                    word_counter[token] += 1
                
                # Segment into syllables and count
                syllables = self.segment_syllables(token)
                for syllable in syllables if syllables else [token]:
                    syllable_counter[syllable] += 1
        
        logger.info(f"Found frequencies for {len(word_counter)} dictionary words")
        logger.info(f"Found {len(syllable_counter)} unique syllables")
        
        return word_counter, syllable_counter
    
    def update_json_with_frequencies(self, basic_json: Dict, word_frequencies: Counter, syllable_frequencies: Counter) -> Dict:
        """Phase 3: Update JSON with real frequency data."""
        logger.info("Phase 3: Updating JSON with frequency data...")
        
        # Update word frequencies
        for word_entry in basic_json["words"]:
            word = word_entry["word"]
            word_entry["frequency"] = word_frequencies.get(word, 0)
        
        # Sort words by frequency (descending)
        basic_json["words"].sort(key=lambda x: x["frequency"], reverse=True)
        
        # Update metadata
        basic_json["metadata"].update({
            "phase": "frequency_analysis_complete",
            "words_with_frequency": sum(1 for w in basic_json["words"] if w["frequency"] > 0),
            "total_syllables": len(syllable_frequencies)
        })
        
        logger.info(f"Updated frequencies for {basic_json['metadata']['words_with_frequency']} words")
        return basic_json
    
    def generate_syllable_data(self, syllable_frequencies: Counter) -> List[Dict]:
        """Phase 4: Generate syllable frequency data."""
        logger.info("Phase 4: Generating syllable frequency data...")
        
        # Create syllable entries sorted by frequency
        syllable_data = [
            {"syllable": syllable, "frequency": freq}
            for syllable, freq in syllable_frequencies.most_common()
        ]
        
        logger.info(f"Generated data for {len(syllable_data)} syllables")
        return syllable_data
    
    def save_json(self, data: Dict):
        """Save final JSON to file."""
        logger.info(f"Saving JSON to {self.output_file}")
        
        try:
            with open(self.output_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Successfully saved JSON to {self.output_file}")
            
        except Exception as e:
            logger.error(f"Error saving JSON: {e}")
    
    def run_conversion(self):
        """Run the complete 4-phase conversion process."""
        logger.info("Starting Shan dictionary conversion process...")
        
        # Initialize tools
        self.initialize_shannlp()
        
        # Phase 1: Load dictionary and create basic JSON
        words = self.load_dictionary()
        if not words:
            logger.error("No words loaded from dictionary. Exiting.")
            return
        
        basic_json = self.create_basic_json(words)
        
        # Phase 2: Load corpus and analyze frequencies
        texts = self.load_shan_news_dataset()
        if texts:
            word_freq, syllable_freq = self.analyze_frequency(texts)
            self.word_frequencies = word_freq
            self.syllable_frequencies = syllable_freq
            
            # Phase 3: Update JSON with frequencies
            basic_json = self.update_json_with_frequencies(basic_json, word_freq, syllable_freq)
            
            # Phase 4: Generate syllable data
            syllable_data = self.generate_syllable_data(syllable_freq)
            basic_json["syllables"] = syllable_data
        else:
            logger.warning("No corpus data available. Saving basic structure only.")
        
        # Save final JSON
        self.save_json(basic_json)
        
        # Print summary
        self.print_summary(basic_json)
    
    def print_summary(self, data: Dict):
        """Print conversion summary."""
        logger.info("\n" + "="*50)
        logger.info("CONVERSION SUMMARY")
        logger.info("="*50)
        logger.info(f"Total words in dictionary: {data['metadata']['total_words']}")
        logger.info(f"Words with frequency data: {data['metadata'].get('words_with_frequency', 0)}")
        logger.info(f"Total unique syllables: {data['metadata'].get('total_syllables', 0)}")
        
        if data['words']:
            top_words = data['words'][:5]
            logger.info("\nTop 5 most frequent words:")
            for word_entry in top_words:
                logger.info(f"  {word_entry['word']}: {word_entry['frequency']}")
        
        if data['syllables']:
            top_syllables = data['syllables'][:5]
            logger.info("\nTop 5 most frequent syllables:")
            for syl_entry in top_syllables:
                logger.info(f"  {syl_entry['syllable']}: {syl_entry['frequency']}")
        
        logger.info(f"\nOutput saved to: {self.output_file}")


def main():
    """Main function to run the converter."""
    converter = ShanDictionaryConverter()
    converter.run_conversion()


if __name__ == "__main__":
    main()
