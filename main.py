import datetime
from urllib import request
import aiohttp
from deepgram import Deepgram
from dotenv import load_dotenv
import os
import dropbox
import json
import asyncio

load_dotenv()
DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY")
DROPBOX_ACCESS_TOKEN = os.getenv("DROPBOX_ACCESS_TOKEN")
dg_client = Deepgram(DEEPGRAM_API_KEY)

file_name = "example_file"  # Replace with the actual file name


async def download_file(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.read()


async def main():
    dropbox_link = request.data["link"]

    dropbox_link = dropbox_link.replace('dl=0', 'dl=1')
    MIME_TYPE = 'audio/wav'

    audio = await download_file(dropbox_link)
    deepgram = Deepgram(DEEPGRAM_API_KEY)

    source = {
        'buffer': audio,
        'mimetype': MIME_TYPE
    }

    response = await deepgram.transcription.prerecorded(
        source,
        {
            'model': 'nova',
            'output': 'srt',
            'utterances': True
        }
    )

    return response


def create_srt_from_deepgram_response(response):
    try:
        srt_content = ''
        for i, utterance in enumerate(response['results']['utterances']):
            start = datetime.datetime.fromtimestamp(
                utterance['start']).strftime('%H:%M:%S,%f')[:-3]
            end = datetime.datetime.fromtimestamp(
                utterance['end']).strftime('%H:%M:%S,%f')[:-3]
            srt_content += f'{i+1}\n{start} --> {end}\n{utterance["transcript"]}\n\n'

        return srt_content.encode()
    except Exception as e:
        print('Error creating srt file', e)
        return None


async def create_shared_link():
    dbx = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)

    try:
        response = await main()
        srt_content = create_srt_from_deepgram_response(response)

        if srt_content:
            # Upload the SRT content to Dropbox
            srt_path = f"/path/to/{file_name}.srt"  # Specify the desired path
            dbx.files_upload(srt_content, srt_path)

            # Create a shared link for the SRT file
            shared_link = dbx.sharing_create_shared_link(srt_path).url
        else:
            shared_link = None

        return shared_link

    except Exception as e:
        print('Error creating shared link', e)
        return None


async def handle_request():
    shared_link = await create_shared_link()
    result = {'transcription': shared_link}
    result_json = json.dumps(result)
    print(result_json)


if __name__ == '__main__':
    asyncio.run(handle_request())
