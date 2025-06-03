import logging
from itertools import zip_longest


logger = logging.getLogger(__name__)


# Function to get the value after the given word
def get_after_word(sentence, word):
    """
    Extracts the text immediately following a specific word in a sentence.

    Args:
        sentence: The input sentence (string).
        word: The word to search for (string).

    Returns:
        The text immediately following the word, or None if the word is not found
        or if it's the last word in the sentence.
    """
    index = sentence.find(word)
    if index == -1:
        return None  # Word not found

    index += len(word)

    if index >= len(sentence) or sentence[index : index + 1] == "":
        return None

    remaining_sentence = sentence[index:].strip()
    next_word = remaining_sentence.split(" ")[0]

    return next_word
