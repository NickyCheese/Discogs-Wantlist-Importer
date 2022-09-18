#!/usr/bin/env python3

import discogs_client
import time,  os

# Script to import lines for delimitered file (like the Discogs Wantlist exported file)
# into a Discogs users wantlist.
# N.B. needs python oauthlib and discogs_client libraries installed
# Each line of the input file should specify a release in the below format (to match Discogs Wantlist exported files):
#
#   Catalog#,Artist,Title,Label,Format,Rating,Released,release_id,Notes (delimited by ',')
#   
# Only Artist and Title and release_id will be used, if there. 
#
# Scenarios:
# 1. all three available - searches for releases with artist and title, adds any matching the release_id
# 2. all three available - searches for releases with artist and title, none matches the release_id, adds release_id
# 3. only artist and title available - searches for releases with artist and title, adds all found
# 4. only release_id available - adds release_id
#    
# Flow of script:
# 1. asks for filename / token / format / add or remove
# 2. reads each line of the file, processes it and splits into delimited bits
# 3. searches Discogs for releases that match the info from each line
# 4. adds / removes matching releases to / from users Discogs wantlist
# 
# N.B. Errors (e.g. releases not added), Warnings, and Info Written to 'ImportDiscogsWantlist_output.txt' 
# 
# Inspired and indebted to https://github.com/SkipHendriks/Discogs-Wantlist-Adder

output_file = os.path.join(os.getcwd(),"ImportDiscogsWantlist_output.txt")
outfile = open(output_file, 'w')
outfile.close()

def addRecord(records):
    # Purpose: 
    #  add release to user wantlist
    # input is:
    #  'records' (list of discogs release objects) 
    # process:
    #  1. add each release to the users wantlist
    
    for record in records:
        text = "INFO: ADDING   :    " + str(record) 
        write_out(text)
        try:
            me.wantlist.add(record)
        except Exception:
            text = "ERROR: Failed to add release: " + str(record) 
            write_out(text)
        
def check_release_id(release_id, line_split):
    # Purpose: 
    #  check if the chosem release_id is the correct one
    # input is:
    #  'release_id' (string)
    #  'line_split' (list of strings)
    # process:
    #  1. check if 'release_id' is integer, 8 or less digits.
    #  2. if not check the split line for any other bit that fits this definition
    #  3. if found, then use the new bit as the release_id

    if not release_id.isdigit() or len(release_id) >8:
        release_id_found = False
        release_id = ""
        #check other bits from line
        for bit in line_split:
            if bit.isdigit() and len(bit) <= 8:
                if len(bit) != 4 and bit[0:1] not in ["19", "20"]:
                    release_id = bit
                    release_id_found = True
    else:
        release_id_found = True
        
    return (release_id, release_id_found) 

def findRecord(line, delimiter, record_format):
    # Purpose: 
    #  search for records match a lines info
    # input is:
    #  'line' (string) 
    #  'delimiter' (string) 
    #  'record_format' (string) 
    # process:
    #  1. process / split line and get useful info
    #  2. check if release id is in the info
    #  3. search Discogs for matching releases using artist / title / release_id
    #  4. if nothing found, search just for matching release_id

    #print("\nDEBUG: line:" + str(line.strip()))
    
    # process
    line_split = processLine(line, delimiter)
    artist = line_split[1]
    title  = line_split[2]
    # release_id should be the 8th bit of the split line, but sometimes
    # due to extra delimiters, it ends up as 9th or 10th. This is checked later.
    release_id = line_split[7]
            
    (release_id, release_id_found) = check_release_id(release_id, line_split)
    if  release_id_found == False:
        text = "WARNING: release_id not found for line: " + line.strip() 
        write_out(text)
    
    print("\nINFO: SEARCHING: release_id: " + release_id + "; artist: " + artist + "; title : " + title )
    
    # Skip search if artist or title is blamk
    if artist == "" or title == "":
        text = "ERROR: artist or title is blank.No search done for: " + line.strip() 
        write_out(text)
        return None
    
        
    # Search for all releases with artist / title for the format
    # returns a list of releases
    results = d.search(
        artist=artist,
        release_title=title,
        format=record_format,
        type="release"
    )

    # Check artist / title search results to see if ther are
    # any that match the record_id
    release_found  = 0
    return_results = []
    if len(results) > 0:
        if release_id_found == True:
            for result in results:
                result_str = str(result)
                release_number = result_str.split()[1]
                if release_number in line_split:
                    return_results.append(result)
                    release_id = release_number
                    release_found  = 1
            if release_found  == 0: 
                text = "WARNING: Release matching '" + release_id +  "' not found for line: " + line.strip()
                write_out(text)
                text = "WARNING: no releases added: " + line.strip()
                
        else:
            text = "WARNING: Specific release not found for line: " + line.strip()
            write_out(text)
            text = "WARNING: Adding all artist / title matched results: " + line.strip()
            write_out(text)
            return_results = results
            release_found  = 1
    else:
        text = "WARNING: artist / title not found for line: " + line.strip() 
        write_out(text)
        
    # If no artist / title matches found, just try the release_id
    if release_found == 0:
        print("Trying to search using the release id ONLY")
        try:
            # wait 5 secs between each check - otherwise fails because of too many requests
            time.sleep(5)
            return_results = [d.release(release_id)]
        except Exception:
            pass
            
    #If nothing found warn, else return results
    if len(return_results) == 0:
        text = "ERROR: NO RELEASE NOT FOUND AT ALL FOR LINE: " + line
        write_out(text)
        return None
    else:
        return return_results
        
def processLine(line,  delimiter):
    # Purpose: 
    #  process line to split it correctly
    # input is:
    #  'line' (string) 
    #  'delimiter' (string)
    # process:
    #  1. replace 7" and 12" as this '"' can cause problems with 2.
    #  2. remove any delimiters inside quotes, as this causes incorrect splitting of the line
    #  3. remove multiple spaces, other white space, etc.
    #  4. split the modified line at the delimiters
    
    quote_chars = ['"']
    split_words = ["Featuring",  "featuring",  "with",  "With", \
                    "con",  "Con", "Y",  "y",  "et",  "Et"]
    
    line = line.replace('"7""',  '"7inch')
    line = line.replace('"12""',  '"12inch')
    in_quotes = False
    line_mod = ""
    # check line for delimiters within quotes
    for letter in line:
        if letter in quote_chars:
            if in_quotes == False:
                in_quotes = True
            else:
                in_quotes = False
        else:
            # remove delimiters within quotes
            if not(letter == delimiter and in_quotes == True):
                line_mod = line_mod + letter
                
    # remove multiple space, other whitespace, etc.
    line_mod = " ".join(line_mod.split())
    # split line
    line_split = line_mod.split(delimiter)
    
    # process artist name
    artist_split = line_split[1].split()
    for bit in artist_split:
        # remove artist number e.g. 'The Band (3)' to 'The Band '
        if bit[0] == "(" and bit[-1] == ")" and bit[1:-1].isdigit():
            line_split[1] = line_split[1].replace(bit, "")
        # split main name e.g. 'The Band with Joe Smith' to 'The Band '
        if bit in split_words:
            line_split[1] = line_split[1].split(bit)[0]
    # remove multiple space, other whitespace, etc.
    line_split[1] = " ".join(line_split[1].split())
        
    return line_split
    
def readFile(filename, delimiter, remove, record_format):
    # Purpose: 
    #  read the wantlist file and process the data in it
    # input is:
    #  'filename' (string) 
    #  'delimiter' (string) 
    #  'remove' (boolean) 
    #  'record_format' (string) 
    # process:
    #  1. read each line of the file
    #  2. remove each release to the users wantlist
    #  3. search for matching releases on Discogs
    #  4. add / remove these releases
    
    title_line_text = ["Catalog", "Artist", "Title"]
        
    with open(filename) as f:
        for line in f:
            if any(x not in line for x in title_line_text):
                # wait 5 secs between each check - otherwise fails because of too many requests
                time.sleep(5)
                record = findRecord(line, delimiter, record_format)
                if record:
                    if remove is True:
                        removeRecord(record)
                    else:
                        addRecord(record)

def removeRecord(records):
    # Purpose: 
    #  remove release to user wantlist
    # input is:
    #  'records' (list of discogs release objects) 
    # process:
    #  1. remove each release to the users wantlist
    
    for record in records:
        text = "INFO: Remove: " + str(record)
        write_out(text)
        try:
            me.wantlist.remove(record)
        except Exception:
            text = "ERROR: Failed to remove release: " + str(record) 
            write_out(text)
        
def write_out(text):
    #Purpose:
    # write text to screen and an output file
    # input is:
    #  'text' (string) 
    # process:
    #  1. print text to screen#
    #  2. write text to output file
    print(text)
    with open(output_file, 'a') as outfile:
        outfile.write(text + "\n")

def main():
    # Purpose: 
    #  main routine
    # input is:
    #  none 
    # process:
    #  1. get user info
    #  2. get Discogs client info
    #  3. read and process the wantlist file
    
    # Output program Info
    print("INFO: Script to import lines for delimitered file (like the Discogs Wantlist exported file)")
    print("INFO: into a Discogs users wantlist.")
    print("INFO: N.B. needs python oauthlib and discogs_client libraries installed")
    print("INFO: Each line of the input file should specify a release in the below format (to match Discogs Wantlist exported files):")
    print("")
    print("INFO:   Catalog#,Artist,Title,Label,Format,Rating,Released,release_id,Notes (delimited by ',')")
    print("INFO:   ")
    print("INFO: Only Artist and Title and release_id will be used, if there. ")
    print("")
    print("INFO: Scenarios:")
    print("INFO: 1. all three available - searches for releases with artist and title, adds any matching the release_id")
    print("INFO: 2. all three available - searches for releases with artist and title, none matches the release_id, adds release_id")
    print("INFO: 3. only artist and title available - searches for releases with artist and title, adds all found")
    print("INFO: 4. only release_id available - adds release_id")
    print("INFO:    ")
    print("INFO: Flow of script:")
    print("INFO: 1. asks for filename / token / format / add or remove")
    print("INFO: 2. reads each line of the file, processes it and splits into delimited bits")
    print("INFO: 3. searches Discogs for releases that match the info from each line")
    print("INFO: 4. adds / removes matching releases to / from users Discogs wantlist")
    print("") 
    print("INFO: N.B. Errors (e.g. releases not added), Warnings, and Info Written to 'ImportDiscogsWantlist_output.txt'.")
    
    # Get user info
    file_not_found = True
    import_filename = ""
    user_token_value = ""
    record_format = ""
    delimiter = ""
    add_remove_question = False
    
    while file_not_found:
        import_filename = input("\nPlease enter the name of your list file: ")
        if os.path.exists(import_filename):
            file_not_found = False
        else:
            print("ERROR: File " + import_filename + " does not exist in the current directory.")
            
    while not user_token_value:
        print("\nYou need a user token for you account. You can get this from 'www.discogs.com/settings/developers'")
        user_token_value =  input("Please enter the user token for you account: ")
    
    record_format = input("\nPlease enter the format of your records (e.g. Vinyl, blank for everything!): ")
    
    while not delimiter:
        delimiter = input("\nPlease enter the delimiter for input file lines (e.g. for Discogs exported file ','): ")
    
    add_remove_question = input("\nAdd or Remove releases from Wantlist('a' or 'r'): ")
    remove = False
    if add_remove_question in ['r','R','Remove', 'remove']:
        remove = True

    # Get Discogs client info
    global d
    d = discogs_client.Client(
        'Discogs-Wantlist-Importer/0.1',
        user_token=user_token_value
    )
    global me
    me = d.identity()
    
    # Output Run Info
    if remove == False:
        print("\nINFO: Adding releases to Wantlist of :" + str(me))
    else:
        print("\nINFO: Removing releases from Wantlist of :" + str(me))
    print("INFO: from file      : " + import_filename)
    print("INFO: with delimiter : " + delimiter)
    print("INFO: using token    : " + user_token_value)
    if record_format == "":
        print("INFO: of format      : Any" )
    else:
        print("INFO: of format      : " + record_format)
    input("\nPress return to continue (ctrl-C to exit)")

    # Process the wantlist file
    readFile(import_filename, delimiter, remove, record_format)
    
    input("\nINFO: script finished- press return to exit")
    
if __name__ == "__main__":
    main()
