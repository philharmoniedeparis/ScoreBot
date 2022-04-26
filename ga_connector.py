import logging
import json
from sanic import Blueprint, response
from sanic.request import Request
from typing import Text, Optional, List, Dict, Any

from rasa.core.channels.channel import UserMessage, OutputChannel
from rasa.core.channels.channel import InputChannel
from rasa.core.channels.channel import CollectingOutputChannel

logger = logging.getLogger(__name__)
CONNECTOR_ERROR_MSG = "Oups, je n'ai pas bien compris ce que vous m'avez dit. Essayez de reformuler votre question différemment svp."

class GoogleConnector(InputChannel):
    """A custom http input channel.
    This implementation is the basis for a custom implementation of a chat
    frontend. You can customize this to send messages to Rasa Core and
    retrieve responses from the agent."""

    @classmethod
    def name(cls):
        return "google_assistant"


    def blueprint(self, on_new_message):
        google_webhook = Blueprint('google_webhook', __name__)

        @google_webhook.route("/", methods=['GET'])
        async def health(request):
            return response.json({"status": "ok"})

        @google_webhook.route("/webhook", methods=['POST'])
        async def receive(request):
            payload = request.json
            logger.info(f'------------RAW JSON: {payload}')
            intent = payload['intent']['name']
            text = payload['intent']['query'].lower()
            session_id = payload["session"]["id"]
            logger.info(f'------------RAW TEXT: {text}')
            if intent == 'actions.intent.MAIN':	
                message = ""
            else:
                out = CollectingOutputChannel()			
                await on_new_message(UserMessage(text, out, input_channel="google_assistant"))
                responses = [m["text"] for m in out.messages]
                logger.info(f'------------RAW OUT: {out.messages}')
                message = responses[0] if len(responses) > 0 else CONNECTOR_ERROR_MSG
            r = {
                "session": {
                  "id": session_id,
                  "params": {}
                },
                "prompt": {
                  "override": False,
                  "firstSimple": {
                    "speech": message,
                    "text": message,
                  }
                },
                "scene": {
                  "name": "MatchAny",
                  "slots": {},
                  "next": {
                    "name": "MatchAny"
                  }
                }
              }

            return response.json(r)				

        return google_webhook