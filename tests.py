import unittest
from unittest.mock import patch, MagicMock
from main import (
    set_env, connect_http, send_request, get_response, decode_response,
    has_aired, see_if_imdb_exists, get_json, save_json, insert_episode,
    send_torrent_io_request, check_torrentio, sort_results_by_seeders,
    filter_hdr, remove_different_languages, loop_results, find_magnet
)
from datetime import datetime, timedelta
import pytz
import os
import json


class TestScript(unittest.TestCase):

    @patch('os.getenv')
    def test_set_env(self, mock_getenv):
        mock_getenv.side_effect = lambda key, default=None: {
            "API_KEY": "test_api_key",
            "HOST": "test_host",
            "PORT": "8080"
        }.get(key, default)
        
        api_key, host, port = set_env()
        self.assertEqual(api_key, "test_api_key")
        self.assertEqual(host, "test_host")
        self.assertEqual(port, 8080)

    def test_connect_http(self):
        conn = connect_http("localhost", 8080)
        self.assertEqual(conn.host, "localhost")
        self.assertEqual(conn.port, 8080)

    @patch('http.client.HTTPConnection')
    def test_send_request(self, mock_http_connection):
        mock_conn = MagicMock()
        mock_http_connection.return_value = mock_conn
        
        send_request("test_api_key", mock_conn, "/test_endpoint")
        mock_conn.request.assert_called_once_with("GET", "/test_endpoint?apikey=test_api_key", '')

    def test_decode_response(self):
        mock_response = b'{"key": "value"}'
        decoded = decode_response(mock_response)
        self.assertEqual(decoded, '{"key": "value"}')

    def test_has_aired(self):
        future_date = (datetime.now(pytz.UTC) + timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
        past_date = (datetime.now(pytz.UTC) - timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
        
        self.assertFalse(has_aired({'airDateUtc': future_date}))
        self.assertTrue(has_aired({'airDateUtc': past_date}))

    def test_see_if_imdb_exists(self):
        episode_with_imdb = {"series": {"imdbId": "tt1234567"}}
        episode_without_imdb = {"series": {}}
        
        self.assertEqual(see_if_imdb_exists(episode_with_imdb), "tt1234567")
        self.assertEqual(see_if_imdb_exists(episode_without_imdb), "0")

    @patch('builtins.open', new_callable=unittest.mock.mock_open, read_data='[]')
    def test_get_json(self, mock_open):
        data = get_json('data.json')
        self.assertEqual(data, [])
        mock_open.assert_called_once_with('data.json', 'r')

    @patch('builtins.open', new_callable=unittest.mock.mock_open)
    @patch('json.dump')
    def test_save_json(self, mock_json_dump, mock_open):
        data = [{"id": 1}]
        save_json(data, 'data.json')
        mock_open.assert_called_once_with('data.json', 'w')
        mock_json_dump.assert_called_once_with(data, mock_open(), indent=4)

    @patch('main.get_json', return_value=[])
    @patch('main.save_json')
    def test_insert_episode(self, mock_save_json, mock_get_json):
        episode = {"id": 1, "series": {"title": "Test Series"}, "seasonNumber": 1, "episodeNumber": 1}
        insert_episode(episode, 'data.json')
        mock_get_json.assert_called_once_with('data.json')
        mock_save_json.assert_called_once()

    @patch('http.client.HTTPSConnection')
    def test_send_torrent_io_request(self, mock_https_connection):
        mock_conn = MagicMock()
        mock_https_connection.return_value = mock_conn
        mock_conn.getresponse.return_value.read.return_value = b'{"streams": []}'
        
        response = send_torrent_io_request("/test_url")
        self.assertEqual(response, '{"streams": []}')
        mock_conn.request.assert_called_once_with("GET", "/test_url", '', {})

    def test_sort_results_by_seeders(self):
        results = {
            "streams": [
                {"title": "torrent 1 👤 10 seeders"},
                {"title": "torrent 2 👤 20 seeders"}
            ]
        }
        sorted_results = sort_results_by_seeders(results)
        self.assertEqual(sorted_results[0]['title'], "torrent 2 👤 20 seeders")

    def test_filter_hdr(self):
        torrents = [
            {"title": "torrent HDR"},
            {"title": "torrent"}
        ]
        filtered = filter_hdr(torrents)
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0]['title'], "torrent")
        
    @patch("os.getenv", return_value='["/ 🇮🇹", "/ 🇷🇺"]')    
    def test_remove_different_languages(self,mock_gentenv):
        torrents = [
            {"title": "torrent / 🇮🇹"},
            {"title": "torrent no flag"}
        ]
        filtered = remove_different_languages(torrents)
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0]['title'], "torrent no flag")

    def test_find_magnet(self):
        torrent = {"infoHash": "12345"}
        magnet = find_magnet(torrent)
        self.assertEqual(magnet, "magnet:?xt=urn:btih:12345")


if __name__ == '__main__':
    unittest.main()
