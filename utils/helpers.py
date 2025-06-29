import logging
from itertools import zip_longest
from typing import List, Dict, Any


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


def convert_string_hashmap(value: str | Dict, convert_to: str) -> Dict | str:
    # Convert string to dict
    if convert_to == "dict":
        string_replaced = value.replace(" | ", ",").replace(": ", ",")
        list_value = string_replaced.split(",")
        hashmap = {
            list_value[i]: list_value[i + 1] for i in range(0, len(list_value), 2)
        }
        logger.info(f"Converted from String to Dictionary: {hashmap}")
        return hashmap

    # Convert dict back to original string format
    elif convert_to == "string":
        converted_string = " | ".join(f"{key}: {value}" for key, value in value.items())
        logger.info(f"Converted from Dictionary to String: {converted_string}")
        return converted_string


def nf_get_in_prov_values(prefix_value, sms_voice_key, step_type):
    sms_voice_value = "Unli SMS" if sms_voice_key == "unli_sms" else "Unli Voice"
    double_flow_true = True if prefix_value == "double" else False

    if "data_prov" == step_type:
        step_type_name = (
            "Data Prov Extension With Keyword Mapping"
            if prefix_value == "double"
            else (
                "Data Extend Wallet Expiry"
                if prefix_value == "extend"
                else "Data Prov With Keyword Mapping"
            )
        )
    elif "sms_voice_service" == step_type:
        step_type_name = (
            f"In Add Wallet FUP - {sms_voice_value}"
            if prefix_value == "double"
            else (
                f"In Extend Wallet Expiry - {sms_voice_value}"
                if prefix_value == "extend"
                else f"In Prov Service - {sms_voice_value}"
            )
        )

    return step_type_name, double_flow_true
