import os, fnmatch

class Generator:

    # This list has to be in the favorite order: if multiple
    # executables are find the first will be used
    default_paths = [ '.',
                      './build/',
                      '/opt/amor/simfiles/',
                      '/opt/software/sinq-amorsim/',
                      '/opt/amor/simfiles/']
    exe = [];

    def find_impl(self,pattern, path):
        result = []
        for root, dirs, files in os.walk(path):
            for name in files:
                if fnmatch.fnmatch(name, pattern):
                    result.append(os.path.join(root, name))
        return result

    def find(self,path):
        exe = self.find_impl('AMORgenerator', path)
        if exe != []:
            self.exe = exe
            return
        for i in self.default_paths:
            exe = self.find_impl('AMORgenerator', i)
            if exe != []:
                self.exe = exe
                return

    def validate(self, param) :
        pos = [i for i, j in enumerate(param) if j == '-b']
        if pos != []:
            return True
        return False

def main() :
    g = Generator()
    g.find()
    print g.exe

if __name__ == "__main__":
    main()
