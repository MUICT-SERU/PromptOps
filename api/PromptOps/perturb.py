# api/PromptOps/perturb.py

import random
import string
import math
import pandas as pd
import os
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import wordnet
from nltk import pos_tag
from textblob import TextBlob
# from PyDictionary import PyDictionary  # Switch back to PyDictionary
import spacy
import re
from nltk.corpus import wordnet as wn
import requests  # for llama lmstudio llm
import spacy
import inflect
from dotenv import load_dotenv  
from openai import OpenAI

# nlp = spacy.load("en_core_web_sm")

# dictionary = PyDictionary()  # Initialize PyDictionary



class Perturbation:
    def __init__(self):
        """Initialize the Perturbation class and set up OpenAI client"""
        load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))
        # Initialize verb processor
        api_key = os.getenv("OPENAI_API_KEY") or os.getenv("API_KEY_PERURBATION_KEY")
        if not api_key or api_key == "sk-your-api-key-here":
            raise ValueError("Please set OPENAI_API_KEY environment variable")
            
        self.openai_client = OpenAI(api_key=api_key)

    def _call_openai(self, system_prompt, user_prompt, max_tokens=150):
        """
        Helper function to call OpenAI API
        """
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=max_tokens,
                temperature=0.1
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"OpenAI API error: {e}")
            return user_prompt  # Return original if API fails


    def robust(self, text, num):
        """
        Create multiple sentences where each sentence has exactly one different word perturbed.

        Args:
            text: The input text to modify
            num: Percentage (1-100) of words to apply swapping to

        Returns:
            A list of sentences where each sentence has one different word with character swaps
        """
        words = text.split()  # Split the text into words
        perturbed_sentences = []  # List to store sentences with perturbed words

        # Find eligible words (words with length >= 2)
        eligible_words = [i for i, word in enumerate(
            words) if len(word.rstrip(string.punctuation)) >= 2]

        if not eligible_words:
            return [text]  # Return original text if no eligible words

        # Calculate how many words to swap based on percentage
        num = max(1, min(100, num))  # Ensure num is between 1 and 100
        words_to_swap = math.ceil(len(eligible_words) * (num / 100.0))
        # Can't swap more than available words
        words_to_swap = min(words_to_swap, len(eligible_words))

        # Randomly select which words to swap
        words_indices_to_swap = random.sample(eligible_words, words_to_swap)

        # For each selected word index, create a separate sentence with only that word perturbed
        for word_index in words_indices_to_swap:
            # Create a copy of the original words for this perturbation
            modified_words = words.copy()

            word = words[word_index]

            # Check for punctuation at the end
            if word[-1] in string.punctuation:
                core_word = word[:-1]
                punctuation = word[-1]
            else:
                core_word = word
                punctuation = ''

            # Only swap if the core word is at least 2 characters
            if len(core_word) >= 2:
                # Choose a random index to swap characters
                swap_index = random.randint(0, len(core_word) - 2)

                # Swap characters
                perturbed_word = (
                    core_word[:swap_index] +
                    core_word[swap_index + 1] +
                    core_word[swap_index] +
                    core_word[swap_index + 2:]
                )

                # Reattach punctuation
                perturbed_word += punctuation

                # Replace the word in our copy
                modified_words[word_index] = perturbed_word

            # Create a new sentence with the one modified word
            perturbed_sentence = ' '.join(modified_words)
            perturbed_sentences.append(perturbed_sentence)

        return perturbed_sentences

    def process_questions(self, df, question_column, expected_answer_column, num):
        """
        Processes the dataset, applies perturbations to each question, and matches with the expected answers.
        Fixed to handle non-string data types.

        Args:
            df (pd.DataFrame): Input dataframe with columns containing questions and expected answers.
            question_column (str): Column name containing the questions.
            expected_answer_column (str): Column name containing the expected answers.
            num (int): Percentage (1-100) of words to apply swapping to

        Returns:
            pd.DataFrame: A new dataframe with the original question, perturbations, and expected answers.
        """
        import pandas as pd
        import logging

        # Initialize lists to store results
        rows = []

        # First, ensure the columns exist
        if question_column not in df.columns or expected_answer_column not in df.columns:
            raise ValueError(
                f"Required columns missing: {question_column} or {expected_answer_column}")

        for index, row in df.iterrows():
            # Convert to string to handle non-string types (like float)
            try:
                question = str(row[question_column])
                expected_answer = str(row[expected_answer_column])

                # Skip empty questions
                if not question or question.lower() == 'nan':
                    logging.warning(f"Skipping row {index}: Empty question")
                    continue

                # Generate perturbations using the robust method
                perturbed_set = self.robust(question, num)

                # Add each perturbation as a new row in the output
                for i, perturbation in enumerate(perturbed_set, start=1):
                    rows.append({
                        "Original_Question_Index": index,
                        "Original_Question": question,
                        # Ensure unique naming
                        "Perturbation": f"Perturb {index}-{i}",
                        "Perturbed_Question": perturbation,
                        "Expected_Answer": expected_answer
                    })
            except Exception as e:
                logging.error(f"Error processing row {index}: {e}")
                # Continue with other rows instead of failing
                continue

        # If no rows were processed, raise an error
        if not rows:
            raise ValueError("No valid questions found in the dataset")

        # Convert to DataFrame
        result_df = pd.DataFrame(rows)
        return result_df

    def taxonomy(self, sentence):
        """Replace exactly one word with its synonym using OpenAI"""
        system_prompt = """You are a text perturbation assistant that replaces exactly one word with its synonym. 

        Examples for statements:
        - "I'm so tired" → "I'm so exhausted"
        - "I'm really hungry" → "I'm really starving" 
        - "I'm not sure if I'm up for that" → "I'm not certain if I'm up for that"
        - "I'm not sure if I can make it to the event" → "I'm not confident if I can make it to the event"

        Examples for questions:
        - "Are you likely to find a crucifix in Karachi?" → "Are you likely to discover a crucifix in Karachi?"
        - "Do you think this method will work?" → "Do you believe this method will work?"
        - "Can you help me with this task?" → "Can you assist me with this task?"

        Instructions:
        1. Identify whether the input is a statement or question
        2. Replace exactly ONE word with an appropriate synonym
        3. Maintain the original sentence structure and meaning
        4. Return only the modified sentence, nothing else"""

        user_prompt = f"{sentence}"
            
        return self._call_openai(system_prompt, user_prompt)

    def negation(self, text):
        """Negate the sentence meaning using OpenAI"""
        system_prompt = """You are a text perturbation assistant that converts sentences using negation methods.

        NEGATION PATTERNS:

        For statements:
        - Add "not" + opposite word: "I'm so tired" → "I'm so not energetic"
        - Add "not" + antonym: "I'm really hungry" → "I'm really not full"
        - Move existing negation: "I'm not sure if I'm up for that" → "I'm sure I'm not up for that"
        - Replace with negative form: "I'm not sure" → "I'm unsure"
        - Add "not" + positive adjective: "I'm confused" → "I'm not clear"

        For questions:
        - Use double negative: "Are Sable's a good choice?" → "Are Sable's not a bad choice?"
        - Flip positive to negative: "Is this correct?" → "Is this not incorrect?"
        - Add negation while preserving question: "Do you like it?" → "Do you not dislike it?"

        Examples:
        - "Can you use oyster card at epsom station" → "Can you not avoid an Oyster card at Epsom station?"
        - "Will there be a season 4 of da vinci's demons" → "Will there be not uncertain a season 4 of Da Vinci's Demons?"
        - "Did abraham lincoln write the letter in saving private ryan?" → "Did abraham lincoln not fail to write the letter in saving private ryan?"

        RULES:
        1. Change the meaning through negation
        2. Maintain grammatical correctness
        3. Keep original sentence structure (statement/question)
        4. Use natural-sounding negation patterns
        5. Return only the negated sentence"""

        user_prompt = text
            
        return self._call_openai(system_prompt, user_prompt, max_tokens=400)

    def coreference(self, text):
        """Resolve coreferences in questions using OpenAI"""
        system_prompt = """You are a text perturbation assistant that converts questions by adding coreference resolution patterns.

        Examples of question coreference conversion:
        - "Are you likely to find a crucifix in Karachi?" → "Considering yourself, are you likely to find a crucifix in Karachi?"
        - "Could the main character of "Alice's Adventures in Wonderland" join a Masonic Lodge?" → "Considering the main character of "Alice's Adventures in Wonderland", can she join a Masonic Lodge?"
        - "Are Sable's a good choice of Mustelidae to weigh down a scale?" → "Considering Sable's, is it a good choice of Mustelidae to weigh down a scale?"
        - "Is Romeo and Juliet an unusual title to teach high schoolers?" → "Considering Romeo and Juliet, is it an unusual title to teach high schoolers?"
        

        CONVERSION PATTERN:
        1. Start with "Considering [subject/entity],"
        2. Replace pronouns or references with appropriate pronouns (he/she/it/they)
        3. Maintain the question format
        4. Make the coreference relationship explicit

        RULES:
        1. Add "Considering [entity/subject]," at the beginning
        2. Replace later references with appropriate pronouns when needed
        3. Keep the question structure intact
        4. Use proper pronouns (he/she/it/they) based on the subject
        5. Return only the converted question"""

        user_prompt = text
        
        return self._call_openai(system_prompt, user_prompt, max_tokens=400)

    def srl(self, sentence):
        """Convert active voice questions to passive voice using OpenAI"""
        system_prompt = """You are a text perturbation assistant that converts questions from active voice to passive voice using semantic role labeling.

        Examples of active to passive voice conversion for questions:
        - "Are you likely to find a crucifix in Karachi?" → "Is a crucifix in Karachi likely to be found by you?"
        - "Could the main character of "Alice's Adventures in Wonderland" join a Masonic Lodge?" → "Could the Masonic Lodge be joined by the main character of "Alice's Adventures in Wonderland"?"
        - "Are Sable's a good choice of Mustelidae to weigh down a scale?" → "Is a good choice of Mustelidae to weigh down a scale Sable's?"
        - "Is Romeo and Juliet an unusual title to teach high schoolers?" → "Would Romeo and Juliet be considered an unusual title to be taught to high schoolers?"
        - "Do Windows or Android smartphones run newer versions of Linux?" → "Are newer versions of Linux run on Windows or Android smartphones?"

        CONVERSION RULES:
        1. Transform the question from active voice to passive voice
        2. Move the object to the subject position
        3. Change the verb to passive form (be + past participle)
        4. Move the original subject to the end with "by" (when appropriate)
        5. Adjust auxiliary verbs as needed (are/is/could/would/etc.)
        6. Maintain the question format
        7. Ensure grammatical correctness in the passive construction

        Return only the converted passive voice question."""

        user_prompt = sentence
        
        return self._call_openai(system_prompt, user_prompt, max_tokens=400)

    # def logic(self, sentence):
    #     """
    #     Transforms a sentence with an 'if...then...' structure by swapping the condition and conclusion.

    #     Args:
    #         sentence (str): Input sentence with 'if...then...' structure.

    #     Returns:
    #         str: Transformed sentence with swapped condition and conclusion.
    #     """
    #     # Check if the sentence contains "if...then..."
    #     match = re.search(r'if (.*), then (.*)', sentence, re.IGNORECASE)
    #     if match:
    #         condition = match.group(1).strip().rstrip('.')
    #         conclusion = match.group(2).strip().rstrip('.')

    #         # Swap the condition and conclusion
    #         transformed_sentence = f"If {conclusion}, then {condition}"
    #         return transformed_sentence

    #     # If no 'if...then...' is found, return the original sentence with a note
    #     return "No 'if...then...' structure found in the sentence."

    def fairness(self, sentence):
        """Add gender, race, or nationality information while preserving sentiment using OpenAI"""
        system_prompt = """You are a text perturbation assistant that adds specific gender, race, or nationality information to sentences while preserving the overall sentiment.

        Examples:
        - "I'm so tired" → "She is so tired"
- "I'm enjoying this relaxing day at home" → "I'm enjoying this relaxing day at Thai home"
- "I love going on adventures" → "I love going on adventures with Japanese friends"
- "Do good samaritan laws protect those who help at an accident" → "Do good Samaritan laws protect females who help at an accident?"
- "Will there be a season 4 of da vinci's demons?" → "Will there be a season 4 of male Da Vinci's Demons?"
- "Did abraham lincoln write the letter in saving private ryan" → "Did the male Abraham Lincoln write the letter in Saving Private Ryan?"
- "Is batman and robin a sequel to batman forever" → "Is Batman and Robin a sequel to the male Batman Forever?"


        CONVERSION METHODS based on sentence content:
        1. Change pronouns: "I" → "She/He", "my" → "her/his"
        2. Add nationality to nouns: "home" → "Thai home", "things" → "Japanese things"
        3. Add demographic adjectives: "American", "Korean", "Indian", "Chinese", "German", etc.
        4. Change gender references while keeping the same meaning and sentiment

        RULES:
        1. Preserve the original sentiment and meaning of the sentence
        2. Add only ONE demographic element per sentence
        3. Make natural-sounding modifications
        4. Use common nationalities/demographics: Thai, Japanese, American, Korean, Chinese, Indian, German, etc.
        5. For gender changes: use he/she, his/her appropriately
        6. Return only the converted sentence, nothing else

        Only show the converted sentence in the response."""

        user_prompt = sentence
            
        return self._call_openai(system_prompt, user_prompt, max_tokens=400)

    def temporal(self, sentence):
        """Add temporal context by contrasting past and present using OpenAI"""
        system_prompt = """You are a text perturbation assistant that adds temporal context by contrasting past uncertainty with present statements.

        Examples of temporal transformation:
        - "I'm so tired" → "Not sure how it was like before but I'm so tired"
        - "I'm really hungry" → "Not sure how it was like before but I'm really hungry"
        - "I'm not sure if I'm up for that" → "Not sure how it was like before but I'm not sure if I'm up for that"
        - "I'm not sure if I can make it to the event" → "Not sure how it was like before but I'm not sure if I can make it to the event"
    
        TRANSFORMATION PATTERN:
        - Add "Not sure how it was like before but " at the beginning of every sentence
        - Keep the original sentence exactly the same after the temporal phrase
        - Create a contrast between past uncertainty and present state

        RULES:
        1. Always start with "Not sure how it was like before but "
        2. Keep the original sentence completely unchanged after the temporal phrase
        3. The transformation creates a temporal contrast (uncertain past vs current state)
        4. Maintain the original meaning and sentiment of the sentence
        5. Return only the transformed sentence

        Return only the converted sentence."""

        user_prompt = sentence
    
        return self._call_openai(system_prompt, user_prompt, max_tokens=400)

    def ner(self, sentence):
        """Replace pronouns with person names using OpenAI"""
        system_prompt = """You are a text perturbation assistant that Replace first-person pronouns with names, or add "[Name] thinks" for statements without pronouns.

Examples:
- "I'm so tired" → "Jane is so tired"
- "I'm really hungry" → "Jack is really hungry" 
- "The price is a bit high" → "Chris thinks the price is a bit high"
- "The weather is perfect today" → "Rachel thinks the weather is perfect today"

RULES:
1. If sentence has "I/I'm": Replace with name and adjust pronouns
2. If no first-person pronouns: Add "[Name] thinks" at beginning
3. Use names: Any English first names (e.g., John, Mary, Alice, Bob)
4. Female names → she/her, Male names → he/him

Return only the converted sentence."""

        user_prompt = sentence
    
        return self._call_openai(system_prompt, user_prompt, max_tokens=400)



    def vocab(self, sentence):
        """Add descriptive adjectives or adverbs to enhance vocabulary using OpenAI"""
        system_prompt = """You are a text perturbation assistant that adds one appropriate adjective or adverb to sentences to make them more descriptive.

        Examples of vocabulary enhancement:
        - "I'm so tired" → "I'm so utterly tired"
        - "I'm really hungry" → "I'm really incredibly hungry"
        - "I'm not sure if I'm up for that" → "I'm genuinely not sure if I'm up for that"
        - "I'm not sure if I can make it to the event" → "I'm honestly not sure if I can make it to the event"
        - "I'm feeling a bit confused right now" → "I'm feeling a bit thoroughly confused right now"
        - "I'm enjoying this day at home" → "I'm enjoying this peaceful day at home"
        - "I love going on adventures" → "I love going on exciting adventures"

        VOCABULARY ENHANCEMENT RULES:
        1. Add exactly ONE descriptive word (adjective or adverb)
        2. Choose words that enhance the meaning naturally
        3. Place adjectives before nouns (peaceful day, exciting adventures)
        4. Place adverbs before adjectives or other adverbs (utterly tired, incredibly hungry)
        5. Use words like: utterly, incredibly, genuinely, honestly, thoroughly, peaceful, exciting, amazing, wonderful, completely, absolutely, truly, etc.
        6. The added word should fit naturally and enhance the original meaning
        7. Do not change any existing words, only add one new word
        8. Maintain the original sentence structure and meaning

        PLACEMENT GUIDELINES:
        - Before adjectives: "so tired" → "so utterly tired"
        - Before nouns: "this day" → "this peaceful day"  
        - As sentence adverbs: "I'm not sure" → "I'm honestly not sure"

        Return only the enhanced sentence with one additional descriptive word."""

        user_prompt = sentence
            
        return self._call_openai(system_prompt, user_prompt, max_tokens=400)
