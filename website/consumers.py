import json
from channels.generic.websocket import AsyncWebsocketConsumer


class UpdatesConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.group_name = 'site_updates'
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        try:
            await self.channel_layer.group_discard(self.group_name, self.channel_name)
        except Exception:
            pass

    # receive message from group
    async def site_update(self, event):
        # event should contain a JSON-serializable payload under 'data'
        # Signals may send a payload shaped { action, model, data: {...} }
        # Unwrap that so clients receive { model, action, data: {...} } where
        # data is the inner object (for example order fields).
        payload = event.get('data', {})
        # If payload itself contains a 'data' key, prefer that as the inner data
        inner = payload.get('data') if isinstance(payload, dict) and 'data' in payload else payload

        wrapper = {
            'data': inner or {},
            'action': payload.get('action') if isinstance(payload, dict) else None,
            'model': payload.get('model') if isinstance(payload, dict) else None,
        }

        # allow event-level model to override
        if event.get('model'):
            wrapper['model'] = event.get('model')

        await self.send(text_data=json.dumps(wrapper))
