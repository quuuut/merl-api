# Original work Copyright (c) 2024 SertraFurr
# Modified by quuuut 2026
#
# This file is a derivative of 'main.py' from the Talk-With-Merl project.
# Specific Modifications:
# - Renamed functions (initizalize_conversation -> init, ask_question -> ask).
# - Added a 5000-character input cap to prevent upstream API errors.
# - Refactored to support persistent sessions and OpenAI-compatible response parsing.
# - Implemented loop-based parsing for 'list' and 'text' response types.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at: http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

debug = False


def init(session):
    try:
        initialize_payload = {
            "clientId": "MINECRAFT_HELP",
            "conversationId": None,
            "country": "US",
            "forceReset": False,
            "greeting": "Hi there! <br/><br/> I'm Merl, your helpful Minecraft Support Virtual Agent <i>(in Beta)</i>, powered by AI! <br/><br/> I can answer questions you have about the Help Articles on this site. <br/><br/> Let's get you back to crafting!",
            "locale": "en-US",
        }

        url = "https://xsva.support.xboxlive.com/initialize_conversation"
        data = session.post(url, json=initialize_payload).json()
        if debug:
            print(
                "[DEBUG] Response from initizalize_conversation: ",
                data,
                "\n[DEBUG] USED PAYLOAD: ",
                initialize_payload,
            )
        return data
    except Exception as e:
        print(f"An error occurred during init: {e}")
        return None


def ask(session, json, etag, question):
    try:
        if len(question) >= 5000:
            return 413, etag, None
        url = "https://xsva.support.xboxlive.com/chat"
        payload = {
            "conversation_id": json["conversationId"],
            "eTag": etag if etag else json["eTag"],
            "customizationSelections": {
                "personaId": json["customizationSelections"]["personaId"]
            },
            "text": question,
        }
        response = session.post(url, json=payload).json()

        if debug:
            print(
                "[DEBUG] Response from ask_question: ",
                response,
                "\n[DEBUG] USED PAYLOAD: ",
                payload,
            )
        combined = ""
        for r in response["response"]:
            if "text" in r:
                combined += r["text"] + "\n"
            elif "list" in r:
                for item in r["list"]:
                    combined += "- " + item["text"] + "\n"
        return combined.strip(), response["eTag"], response["metadata"]["chatLlmCall"]
    except Exception as e:
        print(f"An error occurred: {e}")
        return None, etag, None
