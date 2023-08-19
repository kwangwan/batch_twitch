# BATCH TWITCH

Collects Twitch chat.

## Installation

```bash
pip install -r requirements.txt
```

## Configuration

Configure the necessary settings in the config.json file.

- oauth: Obtain the oauth password from twitchapps.com/tmi and input it in the format oauth:<OauthPassword>.

- twitch_id: Input the Twitch ID to connect to the chat window.

- channels: Input the Twitch IDs of the channels from which to collect chat.

- output_formats: Specify the output format (text file format - textfile, Elasticsearch - elasticsearch).

- elasticsearch: (optional) Input Elasticsearch connection parameters.

- elasticsearch_index: (optional) Input the index for Elasticsearch.

- elasticsearch_bulk_size: (optional) Specify how many chat data entries to move to the index at once when transferring data to Elasticsearch.

## Execution

```bash
python run.py
```
