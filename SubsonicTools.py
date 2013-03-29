'''
Subsonic Tools | Command line tools for Subsonic Music Streamer

@author:     Jan Jonas, http://janjonas.net
@copyright:  2013
@license:    GPLv2 (http://www.gnu.org/licenses/gpl-2.0.html)

@contact:    mail@janjonas.net
'''

import sys
import os
import re
import requests
import xml.etree.ElementTree as ET
import urllib
from argparse import ArgumentParser
from argparse import RawDescriptionHelpFormatter

VERSION = 0.1
DEBUG = 0

verbose = 0;

subsonic_namespace = "http://subsonic.org/restapi"
subsonic_client = "Subsonic-Tools"
subsonic_apiVersion = "1.8.0"
subsonic_url = ""
subsonic_trustServerCert = 0 
subsonic_user = ""
subsonic_password = ""

def subsonic_call(command, params = []):
    url = "%s/rest/%s.view?v=%s&c=%s&%s" % (subsonic_url, command, subsonic_apiVersion, subsonic_client, urllib.urlencode(params))
    
    if verbose > 0: print "Call Subsonic API %s" % (url) 
    
    response = requests.get(url, verify= (subsonic_trustServerCert == 0), auth = (subsonic_user,subsonic_password))
    
    if response.status_code != 200:
        raise Exception("Subsonic REST API returned status code %s" % {response.status_code})

    root = ET.fromstring(response.text)
    error = (root.find("{%(ns)s}error" % {"ns": subsonic_namespace }))
    
    if error is not None:
        raise Exception("Error (Code: %(code)s, Text: %(text)s)" % {"code": error.get("code"), "text": error.get("message")})
    else:
        return root[0]; # First child is response object

def exportPlaylists(args):
    
    out = args.out
    prefix = ""
    if args.prefix is not None:
        prefix = args.prefix
     
    out = out + os.sep

    print "Exporting playlists to %s..." % out

    # Export playlists            
    playlists = subsonic_call("getPlaylists")
    for playlist in playlists.iter("{%(ns)s}playlist" % {"ns": subsonic_namespace}):
    
         playlist = subsonic_call("getPlaylist", {"id": playlist.get("id")})
         filename = "%s%s.m3u" % (out, re.sub('[:|*\\\/\?"]', '_', playlist.get("name")))
    
         print "  Save playlist '%s' as %s" % (playlist.get("name"), filename)
         
         file = open(filename, "w")
         for entry in playlist.iter("{%(ns)s}entry" % {"ns": subsonic_namespace }):
             file.write("%s%s\n" % (prefix, entry.get("path").encode("utf-8")))
         file.close()

    print "Done."    


def main(argv=None): # IGNORE:C0111

    if argv is None:
        argv = sys.argv
    else:
        sys.argv.extend(argv)

    program_name = os.path.basename(sys.argv[0])
    program_shortdesc = __import__('__main__').__doc__.split("\n")[1]
    program_license = '''%s

  Licensed under the GPLv2
  http://www.gnu.org/licenses/gpl-2.0.html
  
  Distributed on an "AS IS" basis without warranties
  or conditions of any kind, either express or implied.

USAGE
''' % (program_shortdesc)

    try:

        # Setup argument parser
        # ---------------------

        # Parent parser
        parser_parent = ArgumentParser(description=program_license, formatter_class=RawDescriptionHelpFormatter)
        parser_parent.add_argument('--version', action='version', version="Subsonic-Tools %s" % (VERSION))        
        subparsers = parser_parent.add_subparsers(title='Commands', description='Please specify one of the following commands')
        
        # Base command parser
        parser_commandBase = ArgumentParser(description=program_license, formatter_class=RawDescriptionHelpFormatter, add_help=False)
        parser_commandBase.add_argument("--url", dest="url", help="Subsonic server URL", required=True)
        parser_commandBase.add_argument("--trust-server-cert", dest="trustServerCert", action="count", help="Accept SSL server certificates from unknown certificate authorities")
        parser_commandBase.add_argument("-u", "--user", dest="user", help="Subsonic user", required=True)
        parser_commandBase.add_argument("-p", "--password", dest="password", help="Subsonic password", required=True)
        parser_commandBase.add_argument("-v", "--verbose", dest="verbose", action="count", help="Run in verbose level")
        
        # ExportPlaylists command parser
        parser_exportPlaylists = subparsers.add_parser('ExportPlaylists', parents=[parser_commandBase], help='Export playlists to a specific directory.')
        parser_exportPlaylists.add_argument("--out", dest="out", help="Output path", required=True)
        parser_exportPlaylists.add_argument("--prefix", dest="prefix", help="Relative or absolute path prefix that is added to all files in the playlists")
        parser_exportPlaylists.set_defaults(func=exportPlaylists)

        args = parser_parent.parse_args()

        # Set up global parameters
        global verbose
        global subsonic_url
        global subsonic_user
        global subsonic_password
        global subsonic_trustServerCert
        verbose = args.verbose
        subsonic_url = args.url
        subsonic_user = args.user
        subsonic_password = args.password
        subsonic_trustServerCert = args.trustServerCert
        
        # Call command
        args.func(args);
       
        return 0
    except KeyboardInterrupt:
        ### handle keyboard interrupt ###
        return 0
    except Exception, e:
        if DEBUG:
            raise(e)
        indent = len(program_name) * " "
        sys.stderr.write(program_name + ": " + repr(e) + "\n")
        sys.stderr.write(indent + "  for help use --help")
        return 2

if __name__ == "__main__":
    if DEBUG:
        sys.argv.append("-h")
        sys.argv.append("-v")
    sys.exit(main())