import argparse

#Testing using argparse to parse command line arguments

def make_parser():
    """Make an argument parser with two positional arguments and an optional named argument.
    The first positional argument, wikipage, is not optional.
    The second positional argument, remote_name, is optional."""
    parser = argparse.ArgumentParser(description='Parse Wiki Page')
    parser.add_argument('wikipage',
                        help='the name of the wiki page to parse')
    parser.add_argument('output_file_name', nargs='?',
                        help='the name of the file to upload/write to')
    parser.add_argument('-r', '--redirect', dest='redirect',
                        help='the name of the remote page to redirect to')
    parser.add_argument('--s3',action='store_true',
                        help='upload file to S3? (Default = False)')
    parser.add_argument('--dryrun',action='store_true')
    #ToDo: add arguments --dryrun and --tofile? --verbose? --s3 --category
    return parser

def main():
    parser = make_parser()

    args = parser.parse_args()

    print(args.wikipage)

    #check if a different remote file name was set
    if args.output_file_name is not None:
        print(args.output_file_name)

    #should this file be marked as a redirect on S3?
    if args.redirect is not None:
        print ('Renaming ')
        print(args.redirect)

    if args.dryrun:
        print('Dry run - no files will be written or uploaded')

    if args.s3:
        if args.dryrun:
            print("Dry run - Upload file to S3 Web site")
        else:
            print('Uploading file to S3 Web site')

if __name__ == "__main__":
    main()