# Discogs-Wantlist-Importer
Python script to import Discogs Wantlists from a delimitered file (like the Discogs Wantlist exported file)

I am a self-taught Python scripter, so this script may not be memory efficient, as fast as possible, and generally 'Pythonic'! Hopefully it is easy for others to read and understand what's going on :-)

I wrote this script to take an exported Discogs Wantlist file (edited if required) and the import to contents (add releases) into a different user's Wantlist

To run the Python script (ImportDiscogsWantlist.py):  
   Needs Python 3.x installed
   Need to install Discogs API Client (in a terminal use 'pip3 install discogs_client')
   
To run the Linux binary executable (ImportDiscogsWantlist_LINUX.bin):
   Doesn't need Python or anthing else installing

How to run:
1. Export a Discogs user's wantlist (https://www.discogs.com/users/export) as a '.csv' file.
2. Edit the file to remove / add releases. Lines must be of the below format - text delimited by ','. 
   The artist should be the second field, the title should be the third field and the release id should be the eighth field:

      Catalog#,Artist,Title,Label,Format,Rating,Released,release_id,Notes (delimited by ',')  

   Only Artist and Title and release_id will be used, if they are present.

3. Get a token for the NEW user from 'www.discogs.com/settings/developers'
4. Run the script (in a terminal) in the same directory as the modified / exported '.csv' file with one of the below commands:

    if using the Python script - 'python3 ImportDiscogsWantlist.py'
    if using the Linux binary executable - './ImportDiscogsWantlist_LINUX.bin'
    
5. Answer the questions, and the script will add the releases to the NEW user's Wantlist.
6. Any errors (unwritten releases) can be found in the output file 'ImportDiscogsWantlist_output.txt'

*** Inspired and indebted to https://github.com/SkipHendriks/Discogs-Wantlist-Adder
