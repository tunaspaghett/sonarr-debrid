
# Sonarr Real-Debrid Auto Downloader

## Overview
This script automatically downloads episodes from Sonarr using Real-Debrid. It integrates with Sonarr’s API to check for newly aired episodes and uses Real-Debrid to fetch the highest-quality torrents for those episodes.

## Features
- Automatic checking for aired episodes in Sonarr.
- Fetches torrents using Real-Debrid.
- Supports filtering out torrents based on language and HDR content.
- Saves download history to a JSON file.
- Can update libraries in Jellyfin.

## Prerequisites
- Python 3.x
- Real-Debrid API key
- Environment variables:
  - `API_KEY`: Sonarr API key
  - `HOST`: Sonarr host (default: `127.0.0.1`)
  - `PORT`: Sonarr port (default: `8989`)
  - `DEBRID_KEY`: Real-Debrid API key
  - `BANNED_WORDS`: (Optional) JSON list of banned words to filter out torrents
  - `HDR_MODE`: (Optional) Disable HDR filtering (true/false)
  - `JELLYFIN`: (Optional) Update Jellyfin library (true/false)
  - `JELLYFIN_HOST`: (Optional) Jellyfin host
  - `JELLYFIN_PORT`: (Optional) Jellyfin port
  - `JELLYFIN_API_TOKEN`: (Optional) Jellyfin API token

## Installation
1. Clone this repository:
   ```bash
   git clone https://github.com/tunaspaghett/sonarr-debrid
   cd sonarr-debrid
   ```

2. Create a `.env` file by copying the `env.example`:
   ```bash
   cp env.example .env
   ```

3. Create a `data.json` file by copying the `data.json.example`:
   ```bash
   cp data.json.example data.json
   ```
4. Install the requirements
  ```bash
  pip install -r requirements.txt
  ```

## Configuration
- Configure environment variables in the `.env` file according to your setup.

## Usage
To run the script:
```bash
python main.py
```

## Future Updates
- Plex integration
- Configurable timers
- Only update library when torrent found
- Quality filters

## Running the Script
The script will automatically fetch new episodes and initiate the download using Real-Debrid. It also integrates with Jellyfin if the `JELLYFIN` environment variable is set to `true`.

## Contributing
If you’d like to contribute to this project, please fork it and make changes accordingly. Pull requests are welcome!

## License
This project is licensed under the MIT License.
```

This markdown content is ready to be copied and used on your GitHub repository page. Replace `<repository_url>` with the actual URL of your GitHub repository.
