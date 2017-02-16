#!/usr/bin/env python3
import subprocess, csv, os

sourceCSV = 'out/to-run-convert-ly-on.csv'
rootDir = '../../The-Mutopia-Project/ftp/'
newvsn = '2.19.49'

def vsnInt(vsn):
    vsnList = vsn.split('.')
    vsnNum = int(vsnList[0]) * 1000000 + int(vsnList[1]) * 1000 + int(vsnList[2])
    return vsnNum

# we convert-ly any files not omitted and BETWEEN these two versions:
lower = vsnInt('2.18.2')
higher = vsnInt('2.19.49')

with open(sourceCSV, newline='') as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        vsn = vsnInt(row['ly-version'])

        if vsn > lower and vsn < higher and row['omit?'] != 'T':
            pathToDir = os.path.join(rootDir, row['path'])
            # pathToLy = pathToDir + row['filename']
            # stripFileName = row['filename'].split('.')
            # print(stripFileName[0])
            # print(row['mutopia-id'])

            # get list of all .ly and .ily files in directory and subdirectories
            lyFileList = []
            for dirpath, subdirnames, filenames in os.walk(pathToDir):
                # print('D: %s' % dirpath[len(rootDir):])
                # print('SDL:', subdirnames)
                # print('FL:', filenames)

                for f in filenames:
                    if f[-3:] == '.ly' or f[-4:] == '.ily' or f[-4:] == '.lyi':
                        lyFileList.append(os.path.join(dirpath, f))

                # if len(subdirnames) > 1:
                #     print("SUBDIR")
                # print(lyFileList)

            # print(row['ly-version'])
            # if row['mutopia-id'] == '334':
            # if len(lyFileList) > 1:

            print('____________________________')
            print(row['mutopia-id'])
            print(row['parse-order'], ': ', row['mutopiacomposer'], row['cn-title'])
            print('')

            for filepath in lyFileList:
                output = subprocess.call(['convert-ly', '-e',
                                          '--from=' + row['ly-version'],
                                          '--to=' + newvsn, filepath])
                print(output)
