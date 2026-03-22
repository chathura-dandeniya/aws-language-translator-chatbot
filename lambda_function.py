import boto3
import logging

logger = logging.getLogger()
logger.setLevel(logging.ERROR)


def lambda_handler(event, context):
    try:
        # Extract slot values from the Lex V2 event
        input_text = event['sessionState']['intent']['slots']['text']['value']['interpretedValue'].strip()
        language_slot = event['sessionState']['intent']['slots']['language']['value']['interpretedValue']

        # Validate input text is not empty
        if not input_text:
            raise ValueError("Input text is empty.")

        # Map Lex slot values to Amazon Translate language codes
        # To add a new language, add it here AND as a value in the Lex 'language' slot type
        language_codes = {
            'French': 'fr',
            'Japanese': 'ja',
            'Chinese': 'zh',
            'Spanish': 'es',
            'Sinhala': 'si'
        }

        # Validate the requested language is supported
        if language_slot not in language_codes:
            raise ValueError(f"Unsupported language: {language_slot}")

        target_language_code = language_codes[language_slot]

        # Initialize the Amazon Translate client
        translate_client = boto3.client('translate')

        # Call Amazon Translate
        # SourceLanguageCode='auto' allows Translate to detect the source language automatically,
        # so users can input text in any language without needing to specify the source
        response = translate_client.translate_text(
            Text=input_text,
            SourceLanguageCode='auto',
            TargetLanguageCode=target_language_code
        )

        translated_text = response['TranslatedText']

        # Build the Lex V2 response with the translated text
        lex_response = {
            "sessionState": {
                "dialogAction": {
                    "type": "Close"
                },
                "intent": {
                    "name": "TranslationIntent",
                    "state": "Fulfilled"
                }
            },
            "messages": [
                {
                    "contentType": "PlainText",
                    "content": translated_text
                }
            ]
        }

        return lex_response

    except Exception as error:
        # Log the full error to CloudWatch for debugging
        logger.error("Translation failed: %s", str(error))

        # Return a user-friendly error message back to the chatbot
        lex_error_response = {
            "sessionState": {
                "dialogAction": {
                    "type": "Close"
                },
                "intent": {
                    "name": "TranslationIntent",
                    "state": "Failed"
                }
            },
            "messages": [
                {
                    "contentType": "PlainText",
                    "content": "Sorry, I could not process your translation request. " + str(error)
                }
            ]
        }

        return lex_error_response
