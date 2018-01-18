import sys

def cli():
    print('cli!')

if __name__ == '__main__':
    print( sys.argv[1] )
    number = input('gimme a numbah!\n')
    print(number)
