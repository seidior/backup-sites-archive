#!/usr/bin/env python

import urllib.parse

def process_urls(input_file, output_file):
    # Dictionary to store URLs without scheme as keys and full URLs as values
    url_map = {}

    # Open the input file and process each line
    with open(input_file, 'r') as infile:
        for line in infile:
            # Strip leading and trailing whitespace (including newlines)
            stripped_line = line.lstrip()

            # Remove .pdf URLs
            if stripped_line.lower().endswith('.pdf'):
                continue

            # Correct URLs that start with 'http://https://'
            if stripped_line.startswith('http://https://'):
                stripped_line = stripped_line[7:]  # Remove the 'http://'

            # Parse the URL
            parsed_url = urllib.parse.urlparse(stripped_line)

            # Drop URLs without a '.' in the hostname
            if '.' not in parsed_url.netloc:
                continue

            # URL encode the path
            encoded_path = urllib.parse.quote(parsed_url.path)

            # Reconstruct the URL with the encoded path
            encoded_url = urllib.parse.urlunparse((
                parsed_url.scheme,
                parsed_url.netloc,
                encoded_path,
                parsed_url.params,
                parsed_url.query,
                parsed_url.fragment
            ))

            # Create a key that is the URL without the scheme
            url_key = urllib.parse.urlunparse((
                '',  # No scheme
                parsed_url.netloc,
                encoded_path,
                parsed_url.params,
                parsed_url.query,
                parsed_url.fragment
            ))

            # Normalize the key for comparison by adding a trailing slash if it doesn't exist
            normalized_key = url_key if url_key.endswith('/') else url_key + '/'

            # Logic to prioritize https over http and prefer trailing slashes
            if normalized_key in url_map:
                # Replace if the current URL is https and existing is http
                if parsed_url.scheme == 'https' or (encoded_url.endswith('/') and not url_map[normalized_key].endswith('/')):
                    url_map[normalized_key] = encoded_url
            else:
                # Add the URL if it's not already in the map
                url_map[normalized_key] = encoded_url

    # Write the unique URLs to the output file
    with open(output_file, 'w') as outfile:
        for url in sorted(url_map.values()):
            outfile.write(url + '\n')

# Specify the input and output files
input_filename = 'urls.txt'
output_filename = 'urls_uniq.txt'

# Process the URLs
process_urls(input_filename, output_filename)