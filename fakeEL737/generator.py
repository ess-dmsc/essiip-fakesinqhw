import fnmatch
import os

class Generator:
    exe = None

    @staticmethod
    def find_impl(pattern, path):
        for root, dirs, files in os.walk(path):
            for name in files:
                if fnmatch.fnmatch(name, pattern):
                    return os.path.join(root, name)
        return None

    def find(self, path=None):
        paths = ['./build/',
                 '.',
                 '/opt/amor/simfiles/',
                 '/opt/software/sinq-amorsim/',
                 '/opt/amor/simfiles/']
        if path is not None:
            paths.insert(0, path)

        for p in paths:
            exe = self.find_impl('AMORgenerator', p)
            if exe:
                self.exe = exe
                return exe
        raise Exception("Can't find event generator in selected paths. Abort.")

    @staticmethod
    def validate(param):
        pos = [i for i, j in enumerate(param) if j == '-b']
        if not pos:
            return False
        return True


def main():
    g = Generator()
    g.find()
    print(g.exe)


if __name__ == "__main__":
    main()
